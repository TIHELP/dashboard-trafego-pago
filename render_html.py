"""Monta o BI em HTML único e interativo (design system Help Multas): filtro de data client-side, sem servidor."""
import json

TEMPLATE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BI Tráfego Pago — Help Multas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --blue-900: #243746; --blue-800: #2c4356; --blue-700: #375367; --blue-600: #4a6a80;
    --blue-100: #e6ecf0; --blue-050: #f2f6f8;
    --yellow-500: #fcbf00; --yellow-600: #e0a900; --yellow-100: #fff3cc; --yellow-050: #fffaeb;
    --white: #ffffff; --black: #17242c;
    --gray-900: #1b2a34; --gray-700: #4b5f6c; --gray-500: #7c8e98; --gray-300: #b7c3ca; --gray-200: #d8e0e4; --gray-100: #eef2f4;

    --color-bg-page: var(--blue-050);
    --color-bg-inverse: var(--blue-900);
    --color-surface-card: var(--white);
    --color-text-primary: var(--blue-900);
    --color-text-secondary: var(--gray-700);
    --color-text-on-inverse: var(--white);
    --color-text-muted: var(--gray-500);
    --color-border-default: var(--gray-200);
    --color-accent: var(--yellow-500);
    --color-success: #2f8f5b; --color-success-bg: #e6f5ec;
    --color-danger: #c23b3b; --color-danger-bg: #fbe9e9;

    --radius-sm: 8px; --radius-md: 14px; --radius-lg: 20px; --radius-pill: 999px;
    --shadow-sm: 0 1px 2px rgba(23, 36, 44, 0.08);
    --shadow-md: 0 6px 20px rgba(23, 36, 44, 0.10);
    --shadow-focus: 0 0 0 3px rgba(252, 191, 0, 0.45);

    --font-display: 'Poppins', 'Nunito Sans', system-ui, sans-serif;
    --font-body: 'Nunito Sans', system-ui, sans-serif;
  }}

  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font: 400 clamp(15px, 0.95vw, 20px)/1.6 var(--font-body);
    margin: 0; padding: clamp(16px, 1.6vw, 40px);
    background: var(--color-bg-page);
    color: var(--color-text-primary);
  }}

  .pagina {{ max-width: 1900px; margin: 0 auto; }}

  .cabecalho {{
    background: var(--color-bg-inverse);
    border-radius: var(--radius-lg);
    padding: clamp(16px, 1.4vw, 30px) clamp(18px, 1.8vw, 36px);
    margin-bottom: clamp(16px, 1.4vw, 28px);
    color: var(--color-text-on-inverse);
    box-shadow: var(--shadow-md);
    display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 16px;
    position: sticky; top: 12px; z-index: 10;
  }}
  .cabecalho h1 {{
    font: 700 clamp(20px, 1.9vw, 34px)/1.25 var(--font-display);
    margin: 0 0 4px 0;
    letter-spacing: -0.01em;
  }}
  .cabecalho .subtitulo {{ font-size: clamp(12px, 0.8vw, 16px); color: var(--blue-100); }}

  .controles {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .controles label {{ font: 700 clamp(12px, 0.75vw, 15px) var(--font-body); color: var(--blue-100); }}
  .controles select, .controles input[type=date] {{
    font: 600 clamp(13px, 0.85vw, 16px) var(--font-body);
    padding: 8px 14px;
    border-radius: var(--radius-pill);
    border: none;
    background: var(--yellow-500);
    color: var(--blue-900);
    cursor: pointer;
  }}
  .controles select:focus, .controles input[type=date]:focus {{ outline: none; box-shadow: var(--shadow-focus); }}
  .atalhos-data {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
  .atalhos-data button {{
    font: 700 clamp(11px, 0.7vw, 14px) var(--font-body);
    padding: 5px 12px;
    border-radius: var(--radius-pill);
    border: 1px solid var(--blue-600);
    background: transparent;
    color: var(--blue-100);
    cursor: pointer;
    white-space: nowrap;
  }}
  .atalhos-data button:hover, .atalhos-data button.ativo {{
    background: var(--blue-700);
    color: #fff;
  }}
  #btnApresentacao {{
    border-color: var(--yellow-500);
  }}
  #btnApresentacao.ativo {{
    background: var(--yellow-500);
    color: var(--blue-900);
    border-color: var(--yellow-500);
  }}
  .link-analise {{
    font: 700 clamp(11px, 0.7vw, 14px) var(--font-body);
    padding: 5px 12px;
    border-radius: var(--radius-pill);
    border: 1px solid var(--blue-600);
    background: transparent;
    color: var(--blue-100);
    text-decoration: none;
    white-space: nowrap;
  }}
  .link-analise:hover {{ background: var(--blue-700); color: #fff; }}

  .atualizado {{ font-size: clamp(11px, 0.7vw, 14px); color: var(--blue-100); margin-top: 6px; text-align: right; }}

  .colunas {{
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 20px;
  }}
  @media (max-width: 900px) {{
    .colunas {{ grid-template-columns: 1fr; }}
    .cabecalho {{ position: static; flex-direction: column; align-items: stretch; }}
    .cabecalho > div:last-child {{ width: 100%; }}
    .controles {{ justify-content: space-between; }}
    .controles input[type=date] {{ flex: 1; min-width: 0; }}
    .atualizado {{ text-align: left; }}
  }}

  /* Em telas estreitas, a tabela vira uma lista de "cartões" (rótulo + valor empilhados)
     em vez de colunas — evita tanto scroll lateral quanto texto sobreposto. */
  @media (max-width: 560px) {{
    table {{ table-layout: auto; }}
    thead {{ display: none; }}
    tbody, tr {{ display: block; width: 100%; }}
    tr {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px 12px;
      padding: 14px 4px;
      border-bottom: 1px solid var(--color-border-default);
    }}
    tr.total {{ border-radius: var(--radius-sm); }}
    td {{
      display: flex;
      flex-direction: column;
      padding: 0 !important;
      border-bottom: none !important;
    }}
    td::before {{
      content: attr(data-label);
      font: 700 11px var(--font-body);
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--color-text-secondary);
      margin-bottom: 2px;
    }}
    td[data-label="Unidade"] {{ grid-column: 1 / -1; }}
    td.num {{ text-align: left; }}
  }}

  .plataforma-card {{
    min-width: 0;
    background: var(--color-surface-card);
    border-radius: var(--radius-lg);
    padding: 18px 20px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--color-border-default);
  }}
  .plataforma-card h2 {{
    font: 700 16px var(--font-display);
    margin: 0 0 12px 0;
    color: var(--color-text-primary);
    display: flex; align-items: center; gap: 10px;
  }}
  .plataforma-card h2 .dot {{
    width: 9px; height: 9px; border-radius: 50%;
    flex-shrink: 0;
  }}
  .plataforma-card.meta h2 .dot {{ background: var(--blue-600); }}
  .plataforma-card.google h2 .dot {{ background: var(--color-danger); }}

  table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
  thead th {{
    text-align: left; padding: 6px 8px;
    font: 700 10px var(--font-body);
    letter-spacing: 0.05em; text-transform: uppercase;
    color: var(--color-text-secondary);
    border-bottom: 2px solid var(--color-border-default);
    position: sticky;
    top: var(--offset-cabecalho, 90px);
    background: var(--color-surface-card);
    z-index: 5;
  }}
  thead th:first-child {{ width: 24%; }}
  tbody td {{
    padding: 8px 8px;
    border-bottom: 1px solid var(--color-border-default);
    font-size: 12px;
    font-weight: 700;
    overflow-wrap: break-word;
  }}
  tbody td:first-child {{ white-space: normal; }}
  tbody td.num {{ white-space: nowrap; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.num {{
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-primary);
  }}

  tr.total td {{
    font-weight: 700;
    background: var(--blue-050);
  }}
  tr.total td:first-child {{ border-top-left-radius: var(--radius-sm); border-bottom-left-radius: var(--radius-sm); }}
  tr.total td:last-child {{ border-top-right-radius: var(--radius-sm); border-bottom-right-radius: var(--radius-sm); }}

  .roas-bom {{ color: var(--color-success) !important; }}
  .roas-ruim {{ color: var(--color-danger) !important; }}

  .vazio {{
    background: var(--color-surface-card);
    border-radius: var(--radius-lg);
    padding: 40px; text-align: center;
    color: var(--color-text-muted);
    box-shadow: var(--shadow-sm);
  }}

  footer {{ text-align: center; font-size: 12px; color: var(--color-text-muted); margin-top: 32px; }}
</style>
</head>
<body>
<div class="pagina">
<div class="cabecalho">
  <div>
    <h1>BI · Tráfego Pago por Unidade</h1>
    <div class="subtitulo">Help Multas — Meta Ads &amp; Google Ads</div>
  </div>
  <div>
    <div class="controles">
      <label for="dataDe">De</label>
      <input type="date" id="dataDe">
      <label for="dataAte">Até</label>
      <input type="date" id="dataAte">
    </div>
    <div class="atalhos-data">
      <button type="button" onclick="aplicarAtalho('hoje')">Hoje</button>
      <button type="button" onclick="aplicarAtalho('ontem')">Ontem</button>
      <button type="button" onclick="aplicarAtalho('7dias')">Últimos 7 dias</button>
      <button type="button" onclick="aplicarAtalho('mesAtual')">Mês atual</button>
      <button type="button" onclick="aplicarAtalho('tudo')">Tudo</button>
      <button type="button" id="btnApresentacao" onclick="alternarApresentacao()">▶ Modo apresentação</button>
      <a href="/analise" class="link-analise">📊 Ver análise</a>
    </div>
    <div class="atualizado" id="atualizadoEm"></div>
  </div>
</div>

<div id="conteudo"></div>
<footer>Gerado automaticamente a partir da Meta Graph API e Google Ads API.</footer>
</div>

<script>
const DADOS = {dados_json};
const FATURAMENTO_REAL = {faturamento_json};
const NOMES_FATURAMENTO = {nomes_faturamento_json};

function normalizarNomeUnidade(nome) {{
  if (!nome) return "";
  nome = nome.trim().toUpperCase();
  for (const prefixo of ["HELP MULTAS - ", "HELP MULTAS "]) {{
    if (nome.startsWith(prefixo)) {{ nome = nome.slice(prefixo.length); break; }}
  }}
  return nome.split(/\\s+/).join(" ");
}}

function faturamentoRealDoPeriodo(unidade, inicio, fim, plataforma) {{
  // Se a unidade tiver um "nome no Agiliza" diferente cadastrado no painel, usa ele pra
  // cruzar com as vendas — em vez do próprio nome da unidade (útil quando o sistema de
  // vendas usa um nome genérico/diferente do nome da unidade nos anúncios).
  const override = NOMES_FATURAMENTO[unidade];
  if (override === "__NENHUMA__") return 0; // marcado explicitamente como "não existe no Agiliza"
  const nomeParaCruzar = override || unidade;
  const unidadeNorm = normalizarNomeUnidade(nomeParaCruzar);
  let total = 0;
  let d = new Date(inicio + "T00:00:00");
  const dFim = new Date(fim + "T00:00:00");
  while (d <= dFim) {{
    const chave = `${{unidadeNorm}}|${{fmtISO(d)}}|${{plataforma}}`;
    total += FATURAMENTO_REAL[chave] || 0;
    d.setDate(d.getDate() + 1);
  }}
  return total;
}}

function fmtMoeda(v) {{
  return "R$ " + v.toLocaleString("pt-BR", {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
}}

function datasDisponiveis() {{
  return [...new Set(DADOS.map(r => r.data))].sort();
}}

function fmtISO(d) {{
  return d.toISOString().slice(0, 10);
}}

function hojeLocalISO() {{
  const d = new Date();
  const ano = d.getFullYear();
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${{ano}}-${{mes}}-${{dia}}`;
}}

function aplicarAtalho(tipo) {{
  const datas = datasDisponiveis();
  const hojeStr = hojeLocalISO();
  const hoje = new Date(hojeStr + "T00:00:00");
  const inicio = document.getElementById("dataDe");
  const fim = document.getElementById("dataAte");

  if (tipo === "hoje") {{
    inicio.value = hojeStr;
    fim.value = hojeStr;
  }} else if (tipo === "ontem") {{
    const d = new Date(hoje); d.setDate(d.getDate() - 1);
    inicio.value = fmtISO(d);
    fim.value = fmtISO(d);
  }} else if (tipo === "7dias") {{
    const d = new Date(hoje); d.setDate(d.getDate() - 6);
    inicio.value = fmtISO(d);
    fim.value = hojeStr;
  }} else if (tipo === "mesAtual") {{
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    inicio.value = fmtISO(primeiroDia);
    fim.value = hojeStr;
  }} else if (tipo === "tudo") {{
    inicio.value = datas.length ? datas[0] : hojeStr;
    fim.value = hojeStr;
  }}
  render();
}}

function montarSeletorDeData() {{
  const datas = datasDisponiveis();
  if (datas.length === 0) return;
  document.getElementById("dataDe").value = datas[datas.length - 1];
  document.getElementById("dataAte").value = datas[datas.length - 1];
  document.getElementById("dataDe").addEventListener("change", render);
  document.getElementById("dataAte").addEventListener("change", render);
}}

function totalizar(linhas, unidade, inicio, fim, plataforma) {{
  const inv = linhas.reduce((s, r) => s + r.investimento, 0);
  const leads = linhas.reduce((s, r) => s + r.leads, 0);
  // Faturamento vem das vendas reais (planilha/CRM), filtrado pelo contact_source de cada venda:
  // só entra no card do Meta o que veio de Facebook/Instagram, e no do Google só o que veio de Google.
  const fat = faturamentoRealDoPeriodo(unidade, inicio, fim, plataforma);
  return {{
    investimento: inv, leads: leads, faturamento: fat,
    cpl: leads ? inv / leads : 0,
    roas: inv ? fat / inv : 0,
  }};
}}

function roasClasse(roas) {{
  if (roas >= 3) return "roas-bom";
  if (roas < 1.5) return "roas-ruim";
  return "";
}}

function linhaHtml(unidade, m, isTotal) {{
  return `<tr${{isTotal ? ' class="total"' : ''}}>
    <td data-label="Unidade">${{unidade}}</td>
    <td class="num" data-label="Investimento">${{fmtMoeda(m.investimento)}}</td>
    <td class="num" data-label="Leads">${{m.leads.toFixed(0)}}</td>
    <td class="num" data-label="CPL">${{fmtMoeda(m.cpl)}}</td>
    <td class="num" data-label="Faturamento">${{fmtMoeda(m.faturamento)}}</td>
    <td class="num ${{roasClasse(m.roas)}}" data-label="ROAS">${{m.roas.toFixed(2)}}x</td>
  </tr>`;
}}

function cardPlataforma(plataforma, linhasPlataforma, inicio, fim) {{
  const cls = plataforma === "Meta" ? "meta" : "google";
  const unidades = [...new Set(linhasPlataforma.map(r => r.unidade))];

  let linhasHtml = "";
  let totalGeral = {{ investimento: 0, leads: 0, faturamento: 0 }};
  for (const unidade of unidades) {{
    const linhasUnidade = linhasPlataforma.filter(r => r.unidade === unidade);
    const tot = totalizar(linhasUnidade, unidade, inicio, fim, plataforma);
    linhasHtml += linhaHtml(unidade, tot, false);
    totalGeral.investimento += tot.investimento;
    totalGeral.leads += tot.leads;
    totalGeral.faturamento += tot.faturamento;
  }}
  totalGeral.cpl = totalGeral.leads ? totalGeral.investimento / totalGeral.leads : 0;
  totalGeral.roas = totalGeral.investimento ? totalGeral.faturamento / totalGeral.investimento : 0;
  linhasHtml += linhaHtml("TOTAL DO PERÍODO", totalGeral, true);

  return `<div class="plataforma-card ${{cls}}">
    <h2><span class="dot"></span>${{plataforma}}</h2>
    <table>
      <thead><tr>
        <th>Unidade</th>
        <th class="num">Investimento</th><th class="num">Leads</th>
        <th class="num">CPL</th><th class="num">Faturamento</th><th class="num">ROAS</th>
      </tr></thead>
      <tbody>${{linhasHtml}}</tbody>
    </table>
  </div>`;
}}

function render() {{
  const de = document.getElementById("dataDe").value;
  const ate = document.getElementById("dataAte").value;
  const cont = document.getElementById("conteudo");

  if (!de || !ate) {{
    cont.innerHTML = '<div class="vazio">Selecione um período.</div>';
    return;
  }}

  const [inicio, fim] = de <= ate ? [de, ate] : [ate, de];
  const doPeriodo = DADOS.filter(r => r.data >= inicio && r.data <= fim);

  if (doPeriodo.length === 0) {{
    cont.innerHTML = '<div class="vazio">Sem dados para o período selecionado.</div>';
    document.getElementById("atualizadoEm").textContent = "";
    return;
  }}

  const meta = doPeriodo.filter(r => r.plataforma === "Meta");
  const google = doPeriodo.filter(r => r.plataforma === "Google");

  let html = '<div class="colunas">';
  html += meta.length ? cardPlataforma("Meta", meta, inicio, fim) : '<div class="plataforma-card meta"><h2><span class="dot"></span>Meta</h2><div class="vazio">Sem dados.</div></div>';
  html += google.length ? cardPlataforma("Google", google, inicio, fim) : '<div class="plataforma-card google"><h2><span class="dot"></span>Google</h2><div class="vazio">Sem dados.</div></div>';
  html += '</div>';

  cont.innerHTML = html;

  const maisRecente = doPeriodo.reduce((a, b) => a.atualizado_em > b.atualizado_em ? a : b);
  const rotuloPeriodo = inicio === fim ? inicio : `${{inicio}} a ${{fim}}`;
  document.getElementById("atualizadoEm").textContent = `Período: ${{rotuloPeriodo}} · Última atualização: ${{maisRecente.atualizado_em}}`;
}}

let apresentacaoAtiva = false;
let apresentacaoTimer = null;

function pararApresentacao() {{
  apresentacaoAtiva = false;
  clearInterval(apresentacaoTimer);
  document.getElementById("btnApresentacao").classList.remove("ativo");
  document.getElementById("btnApresentacao").textContent = "▶ Modo apresentação";
}}

function passoApresentacao() {{
  const noFim = window.innerHeight + window.scrollY >= document.body.scrollHeight - 2;
  if (noFim) {{
    clearInterval(apresentacaoTimer);
    setTimeout(() => {{
      if (!apresentacaoAtiva) return;
      window.scrollTo({{ top: 0, behavior: "smooth" }});
      setTimeout(() => {{
        if (apresentacaoAtiva) apresentacaoTimer = setInterval(passoApresentacao, 45);
      }}, 1200);
    }}, 4000); // pausa alguns segundos no final antes de voltar ao topo
  }} else {{
    window.scrollBy(0, 1);
  }}
}}

function alternarApresentacao() {{
  apresentacaoAtiva = !apresentacaoAtiva;
  const btn = document.getElementById("btnApresentacao");
  if (apresentacaoAtiva) {{
    btn.classList.add("ativo");
    btn.textContent = "⏸ Parar apresentação";
    apresentacaoTimer = setInterval(passoApresentacao, 45);
  }} else {{
    pararApresentacao();
  }}
}}

// qualquer interação manual do usuário cancela a rolagem automática
["wheel", "touchstart", "keydown"].forEach(evt => {{
  window.addEventListener(evt, () => {{ if (apresentacaoAtiva) pararApresentacao(); }}, {{ passive: true }});
}});

function ajustarOffsetCabecalho() {{
  const cabecalho = document.querySelector(".cabecalho");
  if (!cabecalho) return;
  const topGap = parseInt(getComputedStyle(cabecalho).top, 10) || 0;
  const offset = cabecalho.offsetHeight + topGap + 4;
  document.documentElement.style.setProperty("--offset-cabecalho", offset + "px");
}}

window.addEventListener("resize", ajustarOffsetCabecalho);

montarSeletorDeData();
render();
ajustarOffsetCabecalho();
</script>
</body>
</html>
"""


def render_report(
    linhas: list[dict],
    faturamento_por_unidade_dia: dict | None = None,
    nomes_faturamento: dict | None = None,
) -> str:
    return TEMPLATE.format(
        dados_json=json.dumps(linhas, ensure_ascii=False),
        faturamento_json=json.dumps(faturamento_por_unidade_dia or {}, ensure_ascii=False),
        nomes_faturamento_json=json.dumps(nomes_faturamento or {}, ensure_ascii=False),
    )
