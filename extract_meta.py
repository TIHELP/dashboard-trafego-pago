"""Extração de dados do Meta Ads (Graph API) por unidade."""
import requests

# O Meta decide o que mostrar na coluna "Resultados" com base no optimization_goal do conjunto
# de anúncios (não do objetivo da campanha, que é mais genérico) — esse mapa reproduz a mesma
# lógica, então funciona pra qualquer tipo de campanha sem precisar adivinhar.
MAPA_OTIMIZACAO_PARA_RESULTADO = {
    "LEAD_GENERATION": ["lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"],
    "QUALITY_LEAD": ["lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"],
    "OFFSITE_CONVERSIONS": ["offsite_conversion.fb_pixel_lead", "offsite_conversion.fb_pixel_purchase", "lead", "purchase"],
    "ONSITE_CONVERSIONS": ["onsite_conversion.lead_grouped", "lead"],
    "CONVERSATIONS": ["onsite_conversion.messaging_conversation_started_7d"],
    "REPLIES": ["onsite_conversion.messaging_first_reply", "onsite_conversion.messaging_conversation_started_7d"],
    "LINK_CLICKS": ["link_click"],
    "LANDING_PAGE_VIEWS": ["landing_page_view"],
    "PURCHASE": ["purchase", "offsite_conversion.fb_pixel_purchase", "onsite_conversion.purchase"],
    "APP_INSTALLS": ["mobile_app_install"],
    "POST_ENGAGEMENT": ["post_engagement"],
    "PAGE_LIKES": ["like"],
    "THRUPLAY": ["video_view"],
}

# Usado só se não conseguirmos descobrir o optimization_goal do conjunto de anúncios (ex: erro
# de permissão na API) — ordem do mais específico pro mais genérico.
LEAD_ACTION_TYPES_PRIORIDADE_PADRAO = [
    "onsite_conversion.messaging_conversation_started_7d",
    "offsite_conversion.fb_pixel_lead",
    "lead",
    "onsite_conversion.lead_grouped",
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


def _get_optimization_goal_por_campanha(ad_account_id: str, access_token: str, api_version: str) -> dict:
    """Busca o optimization_goal de cada campanha (via os conjuntos de anúncios dela) —
    é esse valor que decide qual métrica aparece na coluna "Resultados" do Gerenciador."""
    url = f"https://graph.facebook.com/{api_version}/{ad_account_id}/adsets"
    params = {"fields": "campaign_id,optimization_goal", "limit": 500, "access_token": access_token}

    mapa = {}
    while url:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            campanha_id = item.get("campaign_id")
            goal = item.get("optimization_goal")
            if campanha_id and goal and campanha_id not in mapa:
                mapa[campanha_id] = goal
        paging = data.get("paging", {})
        url = paging.get("next")
        params = None

    return mapa


def get_meta_insights(ad_account_id: str, date_since: str, date_until: str,
                       access_token: str, api_version: str = "v23.0") -> list[dict]:
    """Retorna uma linha por campanha ativa no período, com investimento, leads (= coluna
    "Resultados" do Gerenciador, de acordo com o optimization_goal de cada campanha) e faturamento."""
    try:
        goals_por_campanha = _get_optimization_goal_por_campanha(ad_account_id, access_token, api_version)
    except Exception:
        goals_por_campanha = {}

    url = f"https://graph.facebook.com/{api_version}/{ad_account_id}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_id,campaign_name,spend,actions,action_values,date_start,date_stop",
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
            goal = goals_por_campanha.get(item.get("campaign_id"))
            prioridade_leads = MAPA_OTIMIZACAO_PARA_RESULTADO.get(goal, LEAD_ACTION_TYPES_PRIORIDADE_PADRAO)

            leads = _extract_value_prioridade(item.get("actions"), prioridade_leads)
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
