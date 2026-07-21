"""Camada de persistência via Postgres — funciona local e na Vercel.

Defina a variável de ambiente DATABASE_URL com a connection string do banco
(Vercel Postgres, Neon, Supabase, etc), ex:
    postgres://usuario:senha@host:5432/banco?sslmode=require

Substitui o antigo trafego.db (SQLite) + config.json, que não sobrevivem
no filesystem efêmero da Vercel.
"""
import json
import os
from contextlib import contextmanager
from datetime import datetime

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL", "")

DEFAULT_CONFIG = {
    "admin_password_hash": None,
    "unidades": [],
    "meta_access_token": "",
    "meta_api_version": "v23.0",
    "google_ads_config": {
        "developer_token": "",
        "client_id": "",
        "client_secret": "",
        "refresh_token": "",
        "login_customer_id": "",
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_config (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS resultados (
    data DATE NOT NULL,
    unidade TEXT NOT NULL,
    plataforma TEXT NOT NULL,
    campanha TEXT NOT NULL,
    investimento DOUBLE PRECISION NOT NULL,
    leads DOUBLE PRECISION NOT NULL,
    cpl DOUBLE PRECISION NOT NULL,
    faturamento DOUBLE PRECISION NOT NULL,
    roas DOUBLE PRECISION NOT NULL,
    atualizado_em TEXT NOT NULL,
    PRIMARY KEY (data, unidade, plataforma, campanha)
);
"""


@contextmanager
def _conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada. Defina essa variável de ambiente com a connection "
            "string do Postgres (Vercel Postgres, Neon, Supabase, etc)."
        )
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def load_config() -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT data FROM app_config WHERE id = 1")
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "INSERT INTO app_config (id, data) VALUES (1, %s)",
                    (json.dumps(DEFAULT_CONFIG),),
                )
                return json.loads(json.dumps(DEFAULT_CONFIG))
            cfg = row[0]
            for key, value in DEFAULT_CONFIG.items():
                cfg.setdefault(key, value)
            return cfg


def save_config(cfg: dict):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO app_config (id, data) VALUES (1, %s)
                   ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data""",
                (json.dumps(cfg),),
            )


def _agregar_duplicatas(linhas: list[dict]) -> list[dict]:
    """Soma linhas que compartilham unidade+plataforma+campanha (ex: campanhas recorrentes
    com nome repetido), evitando violar a chave única da tabela."""
    agregado = {}
    for r in linhas:
        chave = (r["unidade"], r["plataforma"], r["campanha"])
        if chave not in agregado:
            agregado[chave] = {
                "unidade": r["unidade"], "plataforma": r["plataforma"], "campanha": r["campanha"],
                "investimento": 0.0, "leads": 0.0, "faturamento": 0.0,
            }
        agregado[chave]["investimento"] += r["investimento"]
        agregado[chave]["leads"] += r["leads"]
        agregado[chave]["faturamento"] += r["faturamento"]

    resultado = []
    for item in agregado.values():
        item["cpl"] = round(item["investimento"] / item["leads"], 2) if item["leads"] else 0
        item["roas"] = round(item["faturamento"] / item["investimento"], 2) if item["investimento"] else 0
        resultado.append(item)
    return resultado


def upsert_dia(data_ref: str, linhas: list[dict]):
    """Substitui todos os registros de uma data específica pelos novos valores extraídos agora."""
    agora = datetime.now().isoformat(timespec="seconds")
    linhas = _agregar_duplicatas(linhas)

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM resultados WHERE data = %s", (data_ref,))
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO resultados
                   (data, unidade, plataforma, campanha, investimento, leads, cpl, faturamento, roas, atualizado_em)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [
                    (
                        data_ref, r["unidade"], r["plataforma"], r["campanha"],
                        r["investimento"], r["leads"], r["cpl"], r["faturamento"], r["roas"], agora,
                    )
                    for r in linhas
                ],
            )


def load_all() -> list[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM resultados ORDER BY data, unidade, plataforma, campanha")
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["data"] = r["data"].isoformat()
            return rows
