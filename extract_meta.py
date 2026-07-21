"""Extração de dados do Meta Ads (Graph API) por unidade."""
import requests

LEAD_ACTION_TYPES = {
    "lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped",
    # campanhas de WhatsApp ("Conversas por mensagem") usam esse evento em vez de "lead"
    "onsite_conversion.messaging_conversation_started_7d",
}
# Nota: os tipos acima não coexistem numa mesma campanha (cada campanha otimiza para um objetivo só),
# então somá-los não gera contagem duplicada.
PURCHASE_ACTION_TYPES = {"purchase", "offsite_conversion.fb_pixel_purchase", "onsite_conversion.purchase"}


def _extract_value(actions, wanted_types, value_key="value"):
    if not actions:
        return 0.0
    total = 0.0
    for a in actions:
        if a.get("action_type") in wanted_types:
            total += float(a.get(value_key, 0) or 0)
    return total


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
            leads = _extract_value(item.get("actions"), LEAD_ACTION_TYPES)
            faturamento = _extract_value(item.get("action_values"), PURCHASE_ACTION_TYPES)
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
