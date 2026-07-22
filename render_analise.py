"""Página de análise real do BI: gráficos, ranking por unidade e insights automáticos
(o que está bom, o que está ruim, o que pode melhorar). Separada do /relatorio (que fica
intacto pra apresentação na TV) — pensada pra quem vai avaliar a operação de verdade."""
import json

TEMPLATE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise · Tráfego Pago — Help Multas</title>
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
    --color-warning: #b8790a; --color-warning-bg: #fdf1dc;
    --color-danger: #c23b3b; --color-danger-bg: #fbe9e9;

    --chart-meta: #1f6f9c;
    --chart-google: var(--color-danger);

    --radius-sm: 8px; --radius-md: 14px; --radius-lg: 20px; --radius-pill: 999px;
    --shadow-sm: 0 1px 2px rgba(23, 36, 44, 0.08);
    --shadow-md: 0 6px 20px rgba(23, 36, 44, 0.10);
    --shadow-focus: 0 0 0 3px rgba(252, 191, 0, 0.45);

    --font-display: 'Poppins', 'Nunito Sans', system-ui, sans-serif;
    --font-body: 'Nunito Sans', system-ui, sans-serif;
  }}

  * {{ box-sizing: border-box; }}
  body {{
    font: 400 15px/1.6 var(--font-body);
    margin: 0; padding: clamp(16px, 1.6vw, 40px);
    background: var(--color-bg-page);
    color: var(--color-text-primary);
  }}

  .pagina {{ max-width: 1400px; margin: 0 auto; }}

  .cabecalho {{
    background: var(--color-bg-inverse);
    border-radius: var(--radius-lg);
    padding: clamp(16px, 1.4vw, 30px) clamp(18px, 1.8vw, 36px);
    margin-bottom: 20px;
    color: var(--color-text-on-inverse);
    box-shadow: var(--shadow-md);
    display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 16px;
  }}
  .cabecalho h1 {{ font: 700 clamp(20px, 1.9vw, 30px)/1.25 var(--font-display); margin: 0 0 4px 0; }}
  .cabecalho .subtitulo {{ font-size: 13px; color: var(--blue-100); }}

  .controles {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .controles label {{ font: 700 12px var(--font-body); color: var(--blue-100); }}
  .controles input[type=date] {{
    font: 600 13px var(--font-body); padding: 8px 14px; border-radius: var(--radius-pill);
    border: none; background: var(--yellow-500); color: var(--blue-900); cursor: pointer;
  }}
  .linha-atalhos {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; align-items: center; }}
  .atalhos-data button, .toggle-plataforma button, .link-tv {{
    font: 700 12px var(--font-body); padding: 5px 12px; border-radius: var(--radius-pill);
    border: 1px solid var(--blue-600); background: transparent; color: var(--blue-100);
    cursor: pointer; white-space: nowrap; text-decoration: none;
  }}
  .atalhos-data button:hover, .atalhos-data button.ativo,
  .toggle-plataforma button:hover, .toggle-plataforma button.ativo,
  .link-tv:hover {{ background: var(--blue-700); color: #fff; }}
  .toggle-plataforma {{ display: flex; gap: 6px; border-left: 1px solid var(--blue-700); padding-left: 10px; margin-left: 4px; }}
  .link-tv {{ border-color: var(--yellow-500); }}

  .atualizado {{ font-size: 12px; color: var(--blue-100); margin-top: 6px; text-align: right; }}

  .kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px; }}
  @media (max-width: 900px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
  .kpi-tile {{
    background: var(--color-surface-card); border-radius: var(--radius-md); padding: 14px 16px;
    box-shadow: var(--shadow-sm); border: 1px solid var(--color-border-default);
  }}
  .kpi-label {{ font: 700 11px var(--font-body); text-transform: uppercase; letter-spacing: .05em; color: var(--color-text-muted); margin-bottom: 6px; }}
  .kpi-valor {{ font: 700 22px var(--font-display); color: var(--color-text-primary); }}
  .kpi-valor.status-bom {{ color: var(--color-success); }}
  .kpi-valor.status-ruim {{ color: var(--color-danger); }}
  .kpi-valor.status-atencao {{ color: var(--color-warning); }}

  .insights-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }}
  @media (max-width: 900px) {{ .insights-grid {{ grid-template-columns: 1fr; }} }}
  .insight-card {{
    background: var(--color-surface-card); border-radius: var(--radius-lg); padding: 16px 18px;
    box-shadow: var(--shadow-sm); border: 1px solid var(--color-border-default); min-width: 0;
  }}
  .insight-card h3 {{ margin: 0 0 10px; font: 700 14px var(--font-display); display: flex; align-items: center; gap: 8px; }}
  .insight-card.bom h3 {{ color: var(--color-success); }}
  .insight-card.ruim h3 {{ color: var(--color-danger); }}
  .insight-card.melhorar h3 {{ color: var(--color-warning); }}
  .insight-card ul {{ margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.55; color: var(--color-text-secondary); }}
  .insight-card li {{ margin-bottom: 8px; }}

  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 1000px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
  .chart-card {{
    background: var(--color-surface-card); border-radius: var(--radius-lg); padding: 18px 20px;
    box-shadow: var(--shadow-sm); border: 1px solid var(--color-border-default); margin-bottom: 20px; min-width: 0;
  }}
  .chart-card.full {{ grid-column: 1 / -1; }}
  .chart-card h2 {{ font: 700 16px var(--font-display); margin: 0 0 14px; }}

  .legenda-chart {{ display: flex; gap: 16px; margin-bottom: 8px; font-size: 12px; font-weight: 700; color: var(--color-text-secondary); }}
  .legenda-item {{ display: flex; align-items: center; gap: 6px; }}
  .legenda-dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}
  .dot-investimento {{ background: var(--chart-meta); }}
  .dot-faturamento {{ background: var(--color-success); }}
  .dot-meta {{ background: var(--chart-meta); }}
  .dot-google {{ background: var(--chart-google); }}

  .svg-tendencia {{ width: 100%; height: 260px; overflow: visible; }}
  .grade-linha {{ stroke: var(--gray-200); stroke-width: 1; }}
  .grade-rotulo {{ fill: var(--color-text-muted); font-size: 10px; font-family: var(--font-body); }}
  .linha-investimento {{ fill: none; stroke: var(--chart-meta); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }}
  .linha-faturamento {{ fill: none; stroke: var(--color-success); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }}
  .ponto-hit {{ fill: transparent; cursor: pointer; }}

  .barra-linha {{ display: grid; grid-template-columns: 130px 1fr 92px; align-items: center; gap: 10px; padding: 5px 0; }}
  .barra-rotulo {{ font-size: 12px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .barra-trilha {{ position: relative; height: 14px; background: var(--gray-100); border-radius: 999px; display: flex; overflow: hidden; }}
  .barra-preenchida {{ height: 100%; border-radius: 999px; min-width: 6px; cursor: pointer; }}
  .barra-trilha-stack .barra-preenchida {{ border-radius: 0; }}
  .barra-trilha-stack .barra-preenchida:first-child {{ border-top-left-radius: 999px; border-bottom-left-radius: 999px; }}
  .barra-trilha-stack .barra-preenchida:last-child {{ border-top-right-radius: 999px; border-bottom-right-radius: 999px; }}
  .barra-meta.tem-google {{ margin-right: 2px; }}
  .barra-meta {{ background: var(--chart-meta); }}
  .barra-google {{ background: var(--chart-google); }}
  .barra-preenchida.status-bom {{ background: var(--color-success); }}
  .barra-preenchida.status-atencao {{ background: var(--color-warning); }}
  .barra-preenchida.status-ruim {{ background: var(--color-danger); }}
  .barra-valor {{ font-size: 12px; font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }}

  .vazio-chart {{ padding: 24px; text-align: center; color: var(--color-text-muted); font-size: 13px; }}

  #tooltipChart {{
    position: fixed; pointer-events: none; background: var(--blue-900); color: #fff;
    font-size: 12px; font-weight: 600; padding: 6px 10px; border-radius: 8px;
    box-shadow: var(--shadow-md); z-index: 100; opacity: 0; transition: opacity .1s ease;
    white-space: nowrap;
  }}
  #tooltipChart.visivel {{ opacity: 1; }}

  .vazio {{
    background: var(--color-surface-card); border-radius: var(--radius-lg); padding: 40px;
    text-align: center; color: var(--color-text-muted); box-shadow: var(--shadow-sm);
  }}
  footer {{ text-align: center; font-size: 12px; color: var(--color-text-muted); margin-top: 32px; }}
</style>
</head>
<body>
<div class="pagina">
<div class="cabecalho">
  <div>
    <h1>Análise · Tráfego Pago por Unidade</h1>
    <div class="subtitulo">Help Multas — diagnóstico de performance (Meta Ads &amp; Google Ads)</div>
  </div>
  <div>
    <div class="controles">
      <label for="dataDe">De</label>
      <input type="date" id="dataDe">
      <label for="dataAte">Até</label>
      <input type="date" id="dataAte">
    </div>
    <div class="linha-atalhos">
      <div class="atalhos-data">
        <button type="button" onclick="aplicarAtalho('7dias')">Últimos 7 dias</button>
        <button type="button" onclick="aplicarAtalho('mesAtual')">Mês atual</button>
        <button type="button" onclick="aplicarAtalho('tudo')">Tudo</button>
      </div>
      <div class="toggle-plataforma" id="togglePlataforma">
        <button type="button" data-plataforma="Combinado" class="ativo">Combinado</button>
        <button type="button" data-plataforma="Meta">Meta</button>
        <button type="button" data-plataforma="Google">Google</button>
      </div>
      <a href="/relatorio" class="link-tv">📺 Ver versão TV</a>
    </div>
    <div class="atualizado" id="atualizadoEm"></div>
  </div>
</div>

<div id="conteudo"></div>
<footer>Análise gerada a partir dos mesmos dados do relatório — Meta Graph API, Google Ads API e vendas reais (Agiliza).</footer>
</div>

<div id="tooltipChart"></div>

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
  const override = NOMES_FATURAMENTO[unidade];
  if (override === "__NENHUMA__") return 0;
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
function fmtMoedaAbrev(v) {{
  if (v >= 1000) return "R$ " + (v / 1000).toFixed(1).replace(".", ",") + "k";
  return "R$ " + v.toFixed(0);
}}
function fmtDataCurta(iso) {{
  const [, mes, dia] = iso.split("-");
  return `${{dia}}/${{mes}}`;
}}
function fmtISO(d) {{
  return d.toISOString().slice(0, 10);
}}
function hojeLocalISO() {{
  const d = new Date();
  return `${{d.getFullYear()}}-${{String(d.getMonth() + 1).padStart(2, "0")}}-${{String(d.getDate()).padStart(2, "0")}}`;
}}
function datasDisponiveis() {{
  return [...new Set(DADOS.map(r => r.data))].sort();
}}
function unidadesConhecidas() {{
  return [...new Set(DADOS.map(r => r.unidade))].sort();
}}

let plataformaAtiva = "Combinado";

function aplicarAtalho(tipo) {{
  const datas = datasDisponiveis();
  const hojeStr = hojeLocalISO();
  const hoje = new Date(hojeStr + "T00:00:00");
  const inicio = document.getElementById("dataDe");
  const fim = document.getElementById("dataAte");

  if (tipo === "7dias") {{
    const d = new Date(hoje); d.setDate(d.getDate() - 6);
    inicio.value = fmtISO(d); fim.value = hojeStr;
  }} else if (tipo === "mesAtual") {{
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    inicio.value = fmtISO(primeiroDia); fim.value = hojeStr;
  }} else if (tipo === "tudo") {{
    inicio.value = datas.length ? datas[0] : hojeStr;
    fim.value = hojeStr;
  }}
  render();
}}

function montarSeletorDeData() {{
  const datas = datasDisponiveis();
  const hojeStr = hojeLocalISO();
  if (datas.length === 0) return;
  const inicio = new Date(hojeStr + "T00:00:00");
  inicio.setDate(inicio.getDate() - 29);
  document.getElementById("dataDe").value = fmtISO(inicio) < datas[0] ? datas[0] : fmtISO(inicio);
  document.getElementById("dataAte").value = hojeStr;
  document.getElementById("dataDe").addEventListener("change", render);
  document.getElementById("dataAte").addEventListener("change", render);
}}

document.getElementById("togglePlataforma").addEventListener("click", (e) => {{
  const btn = e.target.closest("button");
  if (!btn) return;
  plataformaAtiva = btn.dataset.plataforma;
  document.querySelectorAll("#togglePlataforma button").forEach(b => b.classList.toggle("ativo", b === btn));
  render();
}});

// ---------- agregações ----------

function linhasDoPeriodo(inicio, fim) {{
  return DADOS.filter(r => r.data >= inicio && r.data <= fim);
}}

function resumoUnidades(linhas, inicio, fim, filtroPlataforma) {{
  const plataformas = filtroPlataforma === "Combinado" ? ["Meta", "Google"] : [filtroPlataforma];
  const linhasFiltradas = linhas.filter(r => plataformas.includes(r.plataforma));
  const resultado = [];
  for (const u of unidadesConhecidas()) {{
    const linhasUnidade = linhasFiltradas.filter(r => r.unidade === u);
    const investimento = linhasUnidade.reduce((s, r) => s + r.investimento, 0);
    const leads = linhasUnidade.reduce((s, r) => s + r.leads, 0);
    let faturamento = 0;
    for (const p of plataformas) faturamento += faturamentoRealDoPeriodo(u, inicio, fim, p);
    if (investimento === 0 && leads === 0 && faturamento === 0) continue;
    resultado.push({{
      unidade: u, investimento, leads, faturamento,
      cpl: leads ? investimento / leads : 0,
      roas: investimento ? faturamento / investimento : 0,
    }});
  }}
  return resultado;
}}

function resumoUnidadesPorPlataforma(linhas) {{
  const resultado = [];
  for (const u of unidadesConhecidas()) {{
    const investMeta = linhas.filter(r => r.unidade === u && r.plataforma === "Meta").reduce((s, r) => s + r.investimento, 0);
    const investGoogle = linhas.filter(r => r.unidade === u && r.plataforma === "Google").reduce((s, r) => s + r.investimento, 0);
    if (investMeta === 0 && investGoogle === 0) continue;
    resultado.push({{ unidade: u, investMeta, investGoogle, total: investMeta + investGoogle }});
  }}
  return resultado;
}}

function totalRede(resumo) {{
  const investimento = resumo.reduce((s, u) => s + u.investimento, 0);
  const leads = resumo.reduce((s, u) => s + u.leads, 0);
  const faturamento = resumo.reduce((s, u) => s + u.faturamento, 0);
  return {{
    investimento, leads, faturamento,
    cpl: leads ? investimento / leads : 0,
    roas: investimento ? faturamento / investimento : 0,
  }};
}}

function serieDiaria(inicio, fim, filtroPlataforma) {{
  const plataformas = filtroPlataforma === "Combinado" ? ["Meta", "Google"] : [filtroPlataforma];
  const unidades = unidadesConhecidas();
  const dias = [];
  let d = new Date(inicio + "T00:00:00");
  const dFim = new Date(fim + "T00:00:00");
  while (d <= dFim) {{
    const diaISO = fmtISO(d);
    const investimentoDia = DADOS.filter(r => r.data === diaISO && plataformas.includes(r.plataforma))
      .reduce((s, r) => s + r.investimento, 0);
    let faturamentoDia = 0;
    for (const u of unidades) {{
      for (const p of plataformas) faturamentoDia += faturamentoRealDoPeriodo(u, diaISO, diaISO, p);
    }}
    dias.push({{ data: diaISO, investimento: investimentoDia, faturamento: faturamentoDia }});
    d.setDate(d.getDate() + 1);
  }}
  return dias;
}}

// ---------- insights ----------

function gerarInsights(inicio, fim, filtroPlataforma) {{
  const linhasAtual = linhasDoPeriodo(inicio, fim);
  const resumoAtual = resumoUnidades(linhasAtual, inicio, fim, filtroPlataforma);
  const redeAtual = totalRede(resumoAtual);

  const diasPeriodo = Math.round((new Date(fim + "T00:00:00") - new Date(inicio + "T00:00:00")) / 86400000) + 1;
  const fimAnterior = new Date(inicio + "T00:00:00"); fimAnterior.setDate(fimAnterior.getDate() - 1);
  const inicioAnterior = new Date(fimAnterior); inicioAnterior.setDate(inicioAnterior.getDate() - diasPeriodo + 1);
  const inicioAnteriorISO = fmtISO(inicioAnterior), fimAnteriorISO = fmtISO(fimAnterior);
  const linhasAnterior = linhasDoPeriodo(inicioAnteriorISO, fimAnteriorISO);
  const resumoAnterior = resumoUnidades(linhasAnterior, inicioAnteriorISO, fimAnteriorISO, filtroPlataforma);
  const redeAnterior = totalRede(resumoAnterior);

  const bom = [], ruim = [], melhorar = [];

  if (redeAnterior.investimento > 0 && redeAtual.investimento > 0 && redeAnterior.roas > 0) {{
    const variacao = (redeAtual.roas - redeAnterior.roas) / redeAnterior.roas;
    if (variacao >= 0.1) bom.push(`ROAS geral da rede subiu de ${{redeAnterior.roas.toFixed(2)}}x para ${{redeAtual.roas.toFixed(2)}}x frente ao período anterior equivalente.`);
    else if (variacao <= -0.1) ruim.push(`ROAS geral da rede caiu de ${{redeAnterior.roas.toFixed(2)}}x para ${{redeAtual.roas.toFixed(2)}}x frente ao período anterior equivalente.`);
  }}

  const noPrejuizo = resumoAtual.filter(u => u.investimento > 0 && u.roas < 1).sort((a, b) => a.roas - b.roas);
  for (const u of noPrejuizo.slice(0, 4)) {{
    ruim.push(`${{u.unidade}} está no prejuízo em anúncios: ROAS ${{u.roas.toFixed(2)}}x (investiu ${{fmtMoeda(u.investimento)}}, faturou ${{fmtMoeda(u.faturamento)}}).`);
  }}

  const otimoRoas = resumoAtual.filter(u => u.roas >= 3).sort((a, b) => b.roas - a.roas);
  for (const u of otimoRoas.slice(0, 4)) {{
    bom.push(`${{u.unidade}} converte muito bem: ROAS ${{u.roas.toFixed(2)}}x no período.`);
  }}

  const semLeads = resumoAtual.filter(u => u.investimento > 0 && u.leads === 0);
  for (const u of semLeads.slice(0, 4)) {{
    ruim.push(`${{u.unidade}} investiu ${{fmtMoeda(u.investimento)}} e não gerou nenhum resultado registrado no período.`);
  }}

  const comLeads = resumoAtual.filter(u => u.leads > 0);
  if (comLeads.length >= 2) {{
    const cplMedio = comLeads.reduce((s, u) => s + u.cpl, 0) / comLeads.length;
    const caros = comLeads.filter(u => u.cpl > cplMedio * 1.4).sort((a, b) => b.cpl - a.cpl);
    for (const u of caros.slice(0, 3)) {{
      melhorar.push(`CPL de ${{u.unidade}} (${{fmtMoeda(u.cpl)}}) está ${{(((u.cpl / cplMedio) - 1) * 100).toFixed(0)}}% acima da média da rede (${{fmtMoeda(cplMedio)}}).`);
    }}
    const baratos = comLeads.filter(u => u.cpl < cplMedio * 0.7).sort((a, b) => a.cpl - b.cpl);
    for (const u of baratos.slice(0, 2)) {{
      bom.push(`${{u.unidade}} tem o CPL mais eficiente da rede: ${{fmtMoeda(u.cpl)}} (média: ${{fmtMoeda(cplMedio)}}).`);
    }}
  }}

  if (resumoAnterior.length) {{
    const mapaAnterior = Object.fromEntries(resumoAnterior.map(u => [u.unidade, u]));
    const deltas = [];
    for (const u of resumoAtual) {{
      const antes = mapaAnterior[u.unidade];
      if (antes && antes.investimento > 0 && u.investimento > 0) {{
        deltas.push({{ unidade: u.unidade, antes: antes.roas, depois: u.roas, delta: u.roas - antes.roas }});
      }}
    }}
    deltas.sort((a, b) => b.delta - a.delta);
    if (deltas.length) {{
      const melhor = deltas[0];
      if (melhor.delta > 0.3) bom.push(`${{melhor.unidade}} evoluiu o ROAS de ${{melhor.antes.toFixed(2)}}x para ${{melhor.depois.toFixed(2)}}x frente ao período anterior.`);
      const pior = deltas[deltas.length - 1];
      if (pior.delta < -0.3) ruim.push(`${{pior.unidade}} piorou o ROAS de ${{pior.antes.toFixed(2)}}x para ${{pior.depois.toFixed(2)}}x frente ao período anterior.`);
    }}
  }}

  if (filtroPlataforma === "Combinado") {{
    const redeMeta = totalRede(resumoUnidades(linhasAtual, inicio, fim, "Meta"));
    const redeGoogle = totalRede(resumoUnidades(linhasAtual, inicio, fim, "Google"));
    if (redeMeta.investimento > 0 && redeGoogle.investimento > 0) {{
      const diff = redeMeta.roas - redeGoogle.roas;
      if (Math.abs(diff) >= 1) {{
        const melhorP = diff > 0 ? "Meta" : "Google";
        const piorP = diff > 0 ? "Google" : "Meta";
        const roasMelhor = diff > 0 ? redeMeta.roas : redeGoogle.roas;
        const roasPior = diff > 0 ? redeGoogle.roas : redeMeta.roas;
        melhorar.push(`${{melhorP}} está performando bem melhor que ${{piorP}} na rede (ROAS ${{roasMelhor.toFixed(2)}}x contra ${{roasPior.toFixed(2)}}x) — vale considerar realocar parte da verba.`);
      }}
    }}
  }}

  if (!bom.length) bom.push("Nenhum destaque positivo relevante nesse período.");
  if (!ruim.length) ruim.push("Nenhum ponto crítico identificado nesse período.");
  if (!melhorar.length) melhorar.push("Nenhuma oportunidade clara identificada nesse período.");

  return {{ bom, ruim, melhorar }};
}}

// ---------- render dos blocos ----------

function statusClasseRoas(roas) {{
  if (roas >= 3) return "status-bom";
  if (roas < 1.5) return "status-ruim";
  return "status-atencao";
}}
function statusClasseCpl(cpl, media) {{
  if (!media) return "";
  if (cpl <= media * 0.8) return "status-bom";
  if (cpl > media * 1.3) return "status-ruim";
  return "status-atencao";
}}

function kpiTiles(rede) {{
  return `<div class="kpis">
    <div class="kpi-tile"><div class="kpi-label">Investimento</div><div class="kpi-valor">${{fmtMoeda(rede.investimento)}}</div></div>
    <div class="kpi-tile"><div class="kpi-label">Leads / Resultados</div><div class="kpi-valor">${{rede.leads.toFixed(0)}}</div></div>
    <div class="kpi-tile"><div class="kpi-label">CPL médio</div><div class="kpi-valor">${{fmtMoeda(rede.cpl)}}</div></div>
    <div class="kpi-tile"><div class="kpi-label">Faturamento</div><div class="kpi-valor">${{fmtMoeda(rede.faturamento)}}</div></div>
    <div class="kpi-tile"><div class="kpi-label">ROAS</div><div class="kpi-valor ${{statusClasseRoas(rede.roas)}}">${{rede.roas.toFixed(2)}}x</div></div>
  </div>`;
}}

function insightsHtml(insights) {{
  const bloco = (titulo, cls, icone, itens) => `
    <div class="insight-card ${{cls}}">
      <h3>${{icone}} ${{titulo}}</h3>
      <ul>${{itens.map(t => `<li>${{t}}</li>`).join("")}}</ul>
    </div>`;
  return `<div class="insights-grid">
    ${{bloco("O que está bom", "bom", "✅", insights.bom)}}
    ${{bloco("O que está ruim", "ruim", "⚠️", insights.ruim)}}
    ${{bloco("Pode melhorar", "melhorar", "💡", insights.melhorar)}}
  </div>`;
}}

function barraRanking(unidade, valor, valorFmt, maxValor, statusClasse, tip) {{
  const pct = maxValor ? Math.max((valor / maxValor) * 100, 2) : 2;
  return `<div class="barra-linha">
    <div class="barra-rotulo" title="${{unidade}}">${{unidade}}</div>
    <div class="barra-trilha">
      <div class="barra-preenchida ${{statusClasse}} tem-tip" style="width:${{pct}}%" data-tip="${{tip}}"></div>
    </div>
    <div class="barra-valor">${{valorFmt}}</div>
  </div>`;
}}

function graficoRankingRoas(resumo) {{
  const ordenado = [...resumo].filter(u => u.investimento > 0).sort((a, b) => b.roas - a.roas);
  if (!ordenado.length) return '<div class="vazio-chart">Sem dados suficientes no período.</div>';
  const max = Math.max(...ordenado.map(u => u.roas), 1);
  return ordenado.map(u => barraRanking(
    u.unidade, u.roas, u.roas.toFixed(2) + "x", max, statusClasseRoas(u.roas),
    `${{u.unidade}}: ROAS ${{u.roas.toFixed(2)}}x`
  )).join("");
}}

function graficoRankingCpl(resumo) {{
  const comLeads = resumo.filter(u => u.leads > 0);
  if (!comLeads.length) return '<div class="vazio-chart">Sem dados suficientes no período.</div>';
  const media = comLeads.reduce((s, u) => s + u.cpl, 0) / comLeads.length;
  const ordenado = [...comLeads].sort((a, b) => a.cpl - b.cpl);
  const max = Math.max(...ordenado.map(u => u.cpl), 1);
  return ordenado.map(u => barraRanking(
    u.unidade, u.cpl, fmtMoeda(u.cpl), max, statusClasseCpl(u.cpl, media),
    `${{u.unidade}}: CPL ${{fmtMoeda(u.cpl)}}`
  )).join("");
}}

function graficoInvestimentoPorUnidade(linhas) {{
  const resumo = resumoUnidadesPorPlataforma(linhas);
  if (!resumo.length) return '<div class="vazio-chart">Sem dados suficientes no período.</div>';
  const ordenado = [...resumo].sort((a, b) => b.total - a.total);
  const max = Math.max(...ordenado.map(u => u.total), 1);
  return ordenado.map(u => {{
    const pctMeta = max ? (u.investMeta / max) * 100 : 0;
    const pctGoogle = max ? (u.investGoogle / max) * 100 : 0;
    return `<div class="barra-linha">
      <div class="barra-rotulo" title="${{u.unidade}}">${{u.unidade}}</div>
      <div class="barra-trilha barra-trilha-stack">
        ${{u.investMeta ? `<div class="barra-preenchida barra-meta tem-tip ${{u.investGoogle ? 'tem-google' : ''}}" style="width:${{pctMeta}}%" data-tip="${{u.unidade}} · Meta: ${{fmtMoeda(u.investMeta)}}"></div>` : ""}}
        ${{u.investGoogle ? `<div class="barra-preenchida barra-google tem-tip" style="width:${{pctGoogle}}%" data-tip="${{u.unidade}} · Google: ${{fmtMoeda(u.investGoogle)}}"></div>` : ""}}
      </div>
      <div class="barra-valor">${{fmtMoeda(u.total)}}</div>
    </div>`;
  }}).join("");
}}

function graficoTendencia(serie) {{
  if (!serie.length) return '<div class="vazio-chart">Sem dados.</div>';
  const larguraTotal = 1000, alturaTotal = 260;
  const margemEsq = 58, margemDir = 16, margemTopo = 16, margemBase = 30;
  const larguraChart = larguraTotal - margemEsq - margemDir;
  const alturaChart = alturaTotal - margemTopo - margemBase;

  const maxValor = Math.max(...serie.map(d => Math.max(d.investimento, d.faturamento)), 1) * 1.15;
  const x = i => serie.length > 1 ? margemEsq + (i / (serie.length - 1)) * larguraChart : margemEsq + larguraChart / 2;
  const y = v => margemTopo + alturaChart - (v / maxValor) * alturaChart;

  const pontosInv = serie.map((d, i) => `${{x(i)}},${{y(d.investimento)}}`).join(" ");
  const pontosFat = serie.map((d, i) => `${{x(i)}},${{y(d.faturamento)}}`).join(" ");

  let grid = "";
  const passos = 4;
  for (let k = 0; k <= passos; k++) {{
    const valor = maxValor * (k / passos);
    const yy = y(valor);
    grid += `<line x1="${{margemEsq}}" y1="${{yy}}" x2="${{larguraTotal - margemDir}}" y2="${{yy}}" class="grade-linha" />`;
    grid += `<text x="${{margemEsq - 8}}" y="${{yy + 4}}" class="grade-rotulo" text-anchor="end">${{fmtMoedaAbrev(valor)}}</text>`;
  }}

  let rotulosX = "";
  const indices = serie.length > 2 ? [0, Math.floor((serie.length - 1) / 2), serie.length - 1] : serie.map((_, i) => i);
  for (const i of indices) {{
    rotulosX += `<text x="${{x(i)}}" y="${{alturaTotal - 8}}" class="grade-rotulo" text-anchor="middle">${{fmtDataCurta(serie[i].data)}}</text>`;
  }}

  let pontos = "";
  serie.forEach((d, i) => {{
    pontos += `<circle cx="${{x(i)}}" cy="${{y(d.investimento)}}" r="8" class="ponto-hit tem-tip" data-tip="${{fmtDataCurta(d.data)}} · Investimento: ${{fmtMoeda(d.investimento)}}"></circle>`;
    pontos += `<circle cx="${{x(i)}}" cy="${{y(d.faturamento)}}" r="8" class="ponto-hit tem-tip" data-tip="${{fmtDataCurta(d.data)}} · Faturamento: ${{fmtMoeda(d.faturamento)}}"></circle>`;
  }});

  return `<div class="legenda-chart">
      <span class="legenda-item"><span class="legenda-dot dot-investimento"></span>Investimento</span>
      <span class="legenda-item"><span class="legenda-dot dot-faturamento"></span>Faturamento</span>
    </div>
    <svg viewBox="0 0 ${{larguraTotal}} ${{alturaTotal}}" class="svg-tendencia" preserveAspectRatio="none">
      ${{grid}}
      <polyline points="${{pontosInv}}" class="linha-investimento" />
      <polyline points="${{pontosFat}}" class="linha-faturamento" />
      ${{rotulosX}}
      ${{pontos}}
    </svg>`;
}}

// ---------- tooltip (delegado, funciona em qualquer elemento re-renderizado) ----------

const tooltip = document.getElementById("tooltipChart");
document.addEventListener("mouseover", (e) => {{
  const alvo = e.target.closest(".tem-tip");
  if (!alvo) return;
  tooltip.textContent = alvo.dataset.tip;
  tooltip.classList.add("visivel");
}});
document.addEventListener("mousemove", (e) => {{
  if (!tooltip.classList.contains("visivel")) return;
  tooltip.style.left = (e.clientX + 14) + "px";
  tooltip.style.top = (e.clientY + 14) + "px";
}});
document.addEventListener("mouseout", (e) => {{
  if (e.target.closest(".tem-tip")) tooltip.classList.remove("visivel");
}});

// ---------- render principal ----------

function render() {{
  const de = document.getElementById("dataDe").value;
  const ate = document.getElementById("dataAte").value;
  const cont = document.getElementById("conteudo");

  if (!de || !ate) {{
    cont.innerHTML = '<div class="vazio">Selecione um período.</div>';
    return;
  }}
  const [inicio, fim] = de <= ate ? [de, ate] : [ate, de];
  const linhas = linhasDoPeriodo(inicio, fim);

  if (linhas.length === 0) {{
    cont.innerHTML = '<div class="vazio">Sem dados para o período selecionado.</div>';
    document.getElementById("atualizadoEm").textContent = "";
    return;
  }}

  const resumo = resumoUnidades(linhas, inicio, fim, plataformaAtiva);
  const rede = totalRede(resumo);
  const insights = gerarInsights(inicio, fim, plataformaAtiva);
  const serie = serieDiaria(inicio, fim, plataformaAtiva);

  let html = kpiTiles(rede);
  html += insightsHtml(insights);
  html += `<div class="chart-card full"><h2>Investimento x Faturamento no período</h2>${{graficoTendencia(serie)}}</div>`;
  html += '<div class="charts-grid">';
  html += `<div class="chart-card"><h2>Ranking de ROAS por unidade</h2>${{graficoRankingRoas(resumo)}}</div>`;
  html += `<div class="chart-card"><h2>Ranking de CPL por unidade (menor é melhor)</h2>${{graficoRankingCpl(resumo)}}</div>`;
  html += `<div class="chart-card full"><h2>Investimento por unidade (Meta x Google)</h2>${{graficoInvestimentoPorUnidade(linhas)}}</div>`;
  html += "</div>";

  cont.innerHTML = html;

  const maisRecente = linhas.reduce((a, b) => a.atualizado_em > b.atualizado_em ? a : b);
  const rotuloPeriodo = inicio === fim ? inicio : `${{inicio}} a ${{fim}}`;
  document.getElementById("atualizadoEm").textContent = `Período: ${{rotuloPeriodo}} · Última atualização: ${{maisRecente.atualizado_em}}`;
}}

montarSeletorDeData();
render();
</script>
</body>
</html>
"""


def render_analise(
    linhas: list[dict],
    faturamento_por_unidade_dia: dict | None = None,
    nomes_faturamento: dict | None = None,
) -> str:
    return TEMPLATE.format(
        dados_json=json.dumps(linhas, ensure_ascii=False),
        faturamento_json=json.dumps(faturamento_por_unidade_dia or {}, ensure_ascii=False),
        nomes_faturamento_json=json.dumps(nomes_faturamento or {}, ensure_ascii=False),
    )
