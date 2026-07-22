"""Extração de dados do Meta Ads (Graph API) por unidade."""
import requests

# A coluna "Resultados" do Gerenciador de Anúncios mostra uma métrica diferente dependendo do
# OBJETIVO da campanha (Leads, Mensagens/WhatsApp, Vendas, etc.) — não existe um action_type
# único que sirva pra todas. Por isso mapeamos o objetivo da campanha pra métrica certa.
MAPA_OBJETIVO_PARA_LEAD = {
    # Geração de cadastro (formulário nativo do Meta ou pixel do site)
    "OUTCOME_LEADS": ["lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"],
    "LEAD_GENERATION": ["lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"],
    # WhatsApp / Instagram Direct / Messenger ("Conversas por mensagem")
    "MESSAGES": ["onsite_conversion.messaging_conversation_started_7d"],
    "OUTCOME_ENGAGEMENT": ["onsite_conversion.messaging_conversation_started_7d", "lead", "post_engagement"],
    # Vendas / conversões no site
    "OUTCOME_SALES": ["offsite_conversion.fb_pixel_purchase", "onsite_conversion.purchase", "purchase", "lead"],
    "CONVERSIONS": ["offsite_conversion.fb_pixel_purchase", "onsite_conversion.purchase", "purchase", "lead"],
    # Tráfego / cliques no link
    "OUTCOME_TRAFFIC": ["link_click"],
    "LINK_CLICKS": ["link_click"],
}

# Usado só quando a campanha não tem "objective" retornado pela API (raro) ou o objetivo não
# está no mapa acima — ordem do mais específico pro mais genérico.
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


def get_meta_insights(ad_account_id: str, date_since: str, date_until: str,
                       access_token: str, api_version: str = "v23.0") -> list[dict]:
    """Retorna uma linha por campanha ativa no período, com investimento, leads (= coluna
    "Resultados" do Gerenciador, de acordo com o objetivo de cada campanha) e faturamento."""
    url = f"https://graph.facebook.com/{api_version}/{ad_account_id}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_name,objective,spend,actions,action_values,date_start,date_stop",
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
            objetivo = item.get("objective", "")
            prioridade_leads = MAPA_OBJETIVO_PARA_LEAD.get(objetivo, LEAD_ACTION_TYPES_PRIORIDADE_PADRAO)

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
