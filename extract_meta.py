"""Extração de dados do Meta Ads (Graph API) por unidade."""
import requests

# Ordem de prioridade: o Meta às vezes reporta o MESMO evento sob vários action_types ao mesmo
# tempo (ex: "onsite_conversion.lead_grouped" é um rollup que já inclui "lead" dentro dele).
# Por isso pegamos só o primeiro tipo que existir na lista, do mais específico pro mais genérico —
# somar todos que batem contava o mesmo lead 2-3x.
LEAD_ACTION_TYPES_PRIORIDADE = [
    "onsite_conversion.messaging_conversation_started_7d",  # WhatsApp / Conversas por mensagem
    "offsite_conversion.fb_pixel_lead",  # pixel do site
    "lead",
    "onsite_conversion.lead_grouped",  # rollup genérico, só usa se nada mais específico existir
]
PURCHASE_ACTION_TYPES_PRIORIDADE = [
    "offsite_conversion.fb_pixel_purchase",
    "onsite_conversion.purchase",
    "purchase",
]


def _extract_value_prioridade(actions, tipos_prioridade, value_key="value"):
    """Pega o valor de apenas UM action_type (o primeiro da lista de prioridade que existir),
    em vez de somar todos — evita contar o mesmo evento repetido sob nomes diferentes."""
    if not actions:
        return 0.0
    valores = {a.get("action_type"): float(a.get(value_key, 0) or 0) for a in actions}
    for tipo in tipos_prioridade:
        if tipo in valores:
            return valores[tipo]
    return 0.0


def get_meta_insights(ad_account_id: str, date_since: str, date_until: str,
                       access_token: str, api_version: str = "v23.0") -> list[dict]:
    """Retorna uma linha por campanha ativa no período, com investimento, leads e faturamento."""
    url = f"https://graph.facebook.com/{api_version}/{ad_account_id}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_name,spend,actions,action_values,date_start,date_stop",
        "time_range": f'{{"since":"{date_since}","until":"{date_until}"}}',
        "access_token": access_token,
        "limit": 200,
    }

    rows = []
    while url:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("data", []):
            spend = float(item.get("spend", 0) or 0)
            leads = _extract_value_prioridade(item.get("actions"), LEAD_ACTION_TYPES_PRIORIDADE)
            faturamento = _extract_value_prioridade(item.get("action_values"), PURCHASE_ACTION_TYPES_PRIORIDADE)
            cpl = spend / leads if leads else 0
            roas = faturamento / spend if spend else 0

            rows.append({
                "plataforma": "Meta",
                "campanha": item.get("campaign_name"),
                "investimento": round(spend, 2),
                "leads": int(leads),
                "cpl": round(cpl, 2),
                "faturamento": round(faturamento, 2),
                "roas": round(roas, 2),
            })

        # paginação
        paging = data.get("paging", {})
        url = paging.get("next")
        params = None  # a URL de next já vem com todos os params

    return rows
