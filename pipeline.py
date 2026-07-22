"""Lógica de extração + gravação, compartilhada entre o admin_app (Vercel) e o main.py (CLI local)."""
from datetime import date, timedelta

from db import load_config, upsert_dia
from extract_meta import get_meta_insights
from extract_google import get_google_insights


def datas_do_periodo(data_inicio: str | None, data_fim: str | None) -> list[str]:
    if not data_inicio:
        # Sem período informado (chamada automática do cron a cada 2h): reprocessa ontem + hoje.
        # Evita perder dados de conversões que ocorrem perto da virada do dia (ex: rodar às 23h e
        # só de novo à 1h — sem isso, o intervalo 23h-23h59 do dia anterior nunca seria reextraído).
        ontem = (date.today() - timedelta(days=1)).isoformat()
        hoje = date.today().isoformat()
        return [ontem, hoje]
    if not data_fim:
        data_fim = data_inicio
    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio

    d0 = date.fromisoformat(data_inicio)
    d1 = date.fromisoformat(data_fim)
    dias = []
    d = d0
    while d <= d1:
        dias.append(d.isoformat())
        d += timedelta(days=1)
    return dias


def extrair_dia(data_ref: str, cfg: dict, log: list[str]) -> list[dict]:
    linhas = []
    for u in cfg["unidades"]:
        nome = u["unidade"]

        if u.get("meta_ad_account_id"):
            try:
                meta_rows = get_meta_insights(
                    u["meta_ad_account_id"], data_ref, data_ref,
                    cfg["meta_access_token"], cfg["meta_api_version"],
                )
            except Exception as e:
                log.append(f"    [ERRO Meta - {nome}] {e}")
                meta_rows = []
        else:
            log.append(f"    [AVISO Meta - {nome}] sem meta_ad_account_id configurado, pulando.")
            meta_rows = []

        if u.get("google_customer_id"):
            try:
                google_rows = get_google_insights(
                    u["google_customer_id"], data_ref, data_ref, cfg["google_ads_config"],
                )
            except Exception as e:
                log.append(f"    [ERRO Google - {nome}] {e}")
                google_rows = []
        else:
            log.append(f"    [AVISO Google - {nome}] sem google_customer_id configurado, pulando.")
            google_rows = []

        for row in meta_rows + google_rows:
            row["unidade"] = nome
            linhas.append(row)
    return linhas


def atualizar_periodo(data_inicio: str | None = None, data_fim: str | None = None) -> str:
    """Extrai e grava o período pedido (ou só hoje, se nada for passado). Retorna o log em texto."""
    cfg = load_config()
    dias = datas_do_periodo(data_inicio, data_fim)
    log: list[str] = []

    for data_ref in dias:
        log.append(f"Atualizando {data_ref}...")
        try:
            linhas = extrair_dia(data_ref, cfg, log)
            upsert_dia(data_ref, linhas)
            log.append(f"  {len(linhas)} linhas gravadas.")
        except Exception as e:
            log.append(f"  [ERRO ao gravar {data_ref}] {e}")

    return "\n".join(log)
