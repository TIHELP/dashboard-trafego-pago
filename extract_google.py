"""Extração de dados do Google Ads (Google Ads API) por unidade."""
from google.ads.googleads.client import GoogleAdsClient

QUERY_TEMPLATE = """
    SELECT
        campaign.name,
        metrics.cost_micros,
        metrics.conversions,
        metrics.conversions_value
    FROM campaign
    WHERE segments.date BETWEEN '{since}' AND '{until}'
      AND campaign.status != 'REMOVED'
"""


def get_google_insights(customer_id: str, date_since: str, date_until: str,
                         google_ads_config: dict) -> list[dict]:
    """Retorna uma linha por campanha no período, com investimento, leads (conversões) e faturamento."""
    client = GoogleAdsClient.load_from_dict({**google_ads_config, "use_proto_plus": True})
    ga_service = client.get_service("GoogleAdsService")

    customer_id_clean = customer_id.replace("-", "")
    query = QUERY_TEMPLATE.format(since=date_since, until=date_until)

    rows = []
    response = ga_service.search_stream(customer_id=customer_id_clean, query=query)

    for batch in response:
        for row in batch.results:
            spend = row.metrics.cost_micros / 1_000_000
            leads = row.metrics.conversions
            faturamento = row.metrics.conversions_value
            cpl = spend / leads if leads else 0
            roas = faturamento / spend if spend else 0

            rows.append({
                "plataforma": "Google",
                "campanha": row.campaign.name,
                "investimento": round(spend, 2),
                "leads": round(leads, 1),
                "cpl": round(cpl, 2),
                "faturamento": round(faturamento, 2),
                "roas": round(roas, 2),
            })

    return rows
