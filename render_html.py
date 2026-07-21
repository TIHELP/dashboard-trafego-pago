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
    font: 400 16px/1.6 var(--font-body);
    margin: 0; padding: 24px 24px 64px;
    background: var(--color-bg-page);
    color: var(--color-text-primary);
  }}

  .cabecalho {{
    background: var(--color-bg-inverse);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    margin-bottom: 20px;
    color: var(--color-text-on-inverse);
    box-shadow: var(--shadow-md);
    display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 16px;
    position: sticky; top: 12px; z-index: 10;
  }}
  .cabecalho h1 {{
    font: 700 22px/1.25 var(--font-display);
    margin: 0 0 4px 0;
    letter-spacing: -0.01em;
  }}
  .cabecalho .subtitulo {{ font-size: 12px; color: var(--blue-100); }}

  .controles {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .controles label {{ font: 700 13px var(--font-body); color: var(--blue-100); }}
  .controles select, .controles input[type=date] {{
    font: 600 14px var(--font-body);
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
    font: 700 12px var(--font-body);
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

  .atualizado {{ font-size: 12px; color: var(--blue-100); margin-top: 6px; text-align: right; }}

  .colunas {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  @media (max-width: 820px) {{
    .colunas {{ grid-template-columns: 1fr; }}
    .cabecalho {{ position: static; flex-direction: column; align-items: stretch; }}
    .cabecalho > div:last-child {{ width: 100%; }}
    .controles {{ justify-content: space-between; }}
    .controles input[type=date] {{ flex: 1; min-width: 0; }}
    .atualizado {{ text-align: left; }}
  }}
  @media (max-width: 480px) {{
    body {{ padding: 16px 12px 48px; }}
    .cabecalho {{ padding: 16px 18px; }}
    .cabecalho h1 {{ font-size: 18px; }}
    .plataforma-card {{ padding: 14px 14px; }}
    table {{ font-size: 12px; }}
    thead th, tbody td {{ padding: 7px 6px; }}
  }}

  .plataforma-card {{
    background: var(--color-surface-card);
    border-radius: var(--radius-lg);
    padding: 20px 22px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--color-border-default);
  }}
  .plataforma-card h2 {{
    font: 600 20px var(--font-display);
    margin: 0 0 14px 0;
    color: var(--color-text-primary);
    display: flex; align-items: center; gap: 10px;
  }}
  .plataforma-card h2 .dot {{
    width: 10px; height: 10px; border-radius: 50%;
    flex-shrink: 0;
  }}
  .plataforma-card.meta h2 .dot {{ background: var(--blue-600); }}
  .plataforma-card.google h2 .dot {{ background: var(--color-danger); }}

  .tabela-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; min-width: 480px; }}
  thead th {{
    text-align: left; padding: 8px 12px;
    font: 700 12px var(--font-body);
    letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--color-text-secondary);
    border-bottom: 2px solid var(--color-border-default);
    white-space: nowrap;
  }}
  tbody td {{ padding: 10px 12px; border-bottom: 1px solid var(--color-border-default); white-space: nowrap; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}

  tr.total td {{
    font-weight: 700;
    background: var(--blue-050);
  }}
  tr.total td:first-child {{ border-top-left-radius: var(--radius-sm); border-bottom-left-radius: var(--radius-sm); }}
  tr.total td:last-child {{ border-top-right-radius: var(--radius-sm); border-bottom-right-radius: var(--radius-sm); }}

  .roas-bom {{ color: var(--color-success); font-weight: 700; }}
  .roas-ruim {{ color: var(--color-danger); font-weight: 700; }}

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
    </div>
    <div class="atualizado" id="atualizadoEm"></div>
  </div>
</div>

<div id="conteudo"></div>
<footer>Gerado automaticamente a partir da Meta Graph API e Google Ads API.</footer>

<script>
const DADOS = {dados_json};

function fmtMoeda(v) {{
  return "R$ " + v.toLocaleString("pt-BR", {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
}}

function datasDisponiveis() {{
  return [...new Set(DADOS.map(r => r.data))].sort();
}}

function fmtISO(d) {{
  return d.toISOString().slice(0, 10);
}}

function aplicarAtalho(tipo) {{
  const datas = datasDisponiveis();
  if (datas.length === 0) return;
  const maisRecente = datas[datas.length - 1];
  const hoje = new Date(maisRecente + "T00:00:00");
  const inicio = document.getElementById("dataDe");
  const fim = document.getElementById("dataAte");

  if (tipo === "hoje") {{
    inicio.value = maisRecente;
    fim.value = maisRecente;
  }} else if (tipo === "ontem") {{
    const d = new Date(hoje); d.setDate(d.getDate() - 1);
    inicio.value = fmtISO(d);
    fim.value = fmtISO(d);
  }} else if (tipo === "7dias") {{
    const d = new Date(hoje); d.setDate(d.getDate() - 6);
    inicio.value = fmtISO(d);
    fim.value = maisRecente;
  }} else if (tipo === "mesAtual") {{
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    inicio.value = fmtISO(primeiroDia);
    fim.value = maisRecente;
  }} else if (tipo === "tudo") {{
    inicio.value = datas[0];
    fim.value = maisRecente;
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

function totalizar(linhas) {{
  const inv = linhas.reduce((s, r) => s + r.investimento, 0);
  const leads = linhas.reduce((s, r) => s + r.leads, 0);
  const fat = linhas.reduce((s, r) => s + r.faturamento, 0);
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
    <td>${{unidade}}</td>
    <td class="num">${{fmtMoeda(m.investimento)}}</td>
    <td class="num">${{m.leads.toFixed(0)}}</td>
    <td class="num">${{fmtMoeda(m.cpl)}}</td>
    <td class="num">${{fmtMoeda(m.faturamento)}}</td>
    <td class="num ${{roasClasse(m.roas)}}">${{m.roas.toFixed(2)}}x</td>
  </tr>`;
}}

function cardPlataforma(plataforma, linhasPlataforma) {{
  const cls = plataforma === "Meta" ? "meta" : "google";
  const unidades = [...new Set(linhasPlataforma.map(r => r.unidade))];

  let linhasHtml = "";
  for (const unidade of unidades) {{
    const linhasUnidade = linhasPlataforma.filter(r => r.unidade === unidade);
    const tot = totalizar(linhasUnidade);
    linhasHtml += linhaHtml(unidade, tot, false);
  }}
  const totalGeral = totalizar(linhasPlataforma);
  linhasHtml += linhaHtml("TOTAL DO PERÍODO", totalGeral, true);

  return `<div class="plataforma-card ${{cls}}">
    <h2><span class="dot"></span>${{plataforma}}</h2>
    <div class="tabela-wrap">
      <table>
        <thead><tr>
          <th>Unidade</th>
          <th class="num">Investimento</th><th class="num">Leads</th>
          <th class="num">CPL</th><th class="num">Faturamento</th><th class="num">ROAS</th>
        </tr></thead>
        <tbody>${{linhasHtml}}</tbody>
      </table>
    </div>
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
  html += meta.length ? cardPlataforma("Meta", meta) : '<div class="plataforma-card meta"><h2><span class="dot"></span>Meta</h2><div class="vazio">Sem dados.</div></div>';
  html += google.length ? cardPlataforma("Google", google) : '<div class="plataforma-card google"><h2><span class="dot"></span>Google</h2><div class="vazio">Sem dados.</div></div>';
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

montarSeletorDeData();
render();
</script>
</body>
</html>
"""


def render_report(linhas: list[dict]) -> str:
    return TEMPLATE.format(dados_json=json.dumps(linhas, ensure_ascii=False))
