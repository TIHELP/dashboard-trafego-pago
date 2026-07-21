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

CREATE TABLE IF NOT EXISTS faturamento (
    external_id BIGINT PRIMARY KEY,
    franchise_id TEXT,
    franchise_name TEXT NOT NULL,
    data DATE NOT NULL,
    client_name TEXT,
    gross_value DOUBLE PRECISION NOT NULL,
    surcharge DOUBLE PRECISION NOT NULL DEFAULT 0,
    discount DOUBLE PRECISION NOT NULL DEFAULT 0,
    net_value DOUBLE PRECISION NOT NULL,
    transit_authority TEXT,
    contact_source TEXT,
    proposal_source TEXT,
    importado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_faturamento_data_unidade ON faturamento (data, franchise_name);
"""


@contextmanager
def _conn():
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL não configurada. Defina essa variável de ambiente com a connection "
            "string do Postgres (Vercel Postgres, Neon, Supabase, etc)."
        )
    conn = psycopg2.connect(database_url)
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


def normalizar_nome_unidade(nome: str) -> str:
    """Remove o prefixo 'HELP MULTAS' e normaliza espaços/maiúsculas, pra casar o nome que vem
    do n8n (ex: 'HELP MULTAS CACERES') com o nome cadastrado no painel (ex: 'CACERES')."""
    if not nome:
        return ""
    nome = nome.strip().upper()
    for prefixo in ("HELP MULTAS - ", "HELP MULTAS "):
        if nome.startswith(prefixo):
            nome = nome[len(prefixo):]
            break
    return " ".join(nome.split())


def upsert_faturamento(registros: list[dict]) -> int:
    """Grava vendas vindas do n8n (dados já limpos). Idempotente por external_id — pode
    reenviar o mesmo lote/planilha várias vezes sem duplicar."""
    agora = datetime.now().isoformat(timespec="seconds")

    linhas = []
    for r in registros:
        dia, mes, ano = r["registration_date"].split("/")
        data_iso = f"{ano}-{mes}-{dia}"
        linhas.append((
            r["external_id"],
            r.get("franchise_id"),
            r["franchise_name"],
            data_iso,
            r.get("client_name"),
            float(r.get("gross_value", 0) or 0),
            float(r.get("surcharge", 0) or 0),
            float(r.get("discount", 0) or 0),
            float(r.get("net_value", 0) or 0),
            r.get("transit_authority"),
            r.get("contact_source"),
            r.get("proposal_source"),
            agora,
        ))

    with _conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO faturamento
                   (external_id, franchise_id, franchise_name, data, client_name, gross_value,
                    surcharge, discount, net_value, transit_authority, contact_source, proposal_source, importado_em)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (external_id) DO UPDATE SET
                       franchise_id = EXCLUDED.franchise_id,
                       franchise_name = EXCLUDED.franchise_name,
                       data = EXCLUDED.data,
                       client_name = EXCLUDED.client_name,
                       gross_value = EXCLUDED.gross_value,
                       surcharge = EXCLUDED.surcharge,
                       discount = EXCLUDED.discount,
                       net_value = EXCLUDED.net_value,
                       transit_authority = EXCLUDED.transit_authority,
                       contact_source = EXCLUDED.contact_source,
                       proposal_source = EXCLUDED.proposal_source,
                       importado_em = EXCLUDED.importado_em""",
                linhas,
            )
    return len(linhas)


def classificar_plataforma_por_contact_source(contact_source: str) -> str | None:
    """Decide se uma venda conta pra ROAS do Meta ou do Google, com base no contact_source
    (campo que o time de vendas preenche). Vendas de outras origens (Fachada, Já era cliente,
    Indicação de amigo, etc.) não entram no ROAS de nenhuma das duas — não vieram de anúncio."""
    if not contact_source:
        return None
    texto = contact_source.strip().lower()
    if "facebook" in texto or "instagram" in texto:
        return "Meta"
    if "google" in texto:
        return "Google"
    return None


def load_faturamento_por_unidade_dia() -> dict:
    """Retorna {"UNIDADE_NORMALIZADA|2026-07-02|Meta": net_value_total} pra somar no relatório
    (chave em string, pronta pra virar JSON e ser usada no front). Só entram vendas cujo
    contact_source indica que vieram do Meta (Facebook/Instagram) ou do Google."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT franchise_name, data, net_value, contact_source FROM faturamento")
            rows = cur.fetchall()

    totais = {}
    for r in rows:
        plataforma = classificar_plataforma_por_contact_source(r["contact_source"])
        if plataforma is None:
            continue
        chave = f"{normalizar_nome_unidade(r['franchise_name'])}|{r['data'].isoformat()}|{plataforma}"
        totais[chave] = totais.get(chave, 0.0) + r["net_value"]
    return totais
