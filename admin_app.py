"""Painel de administração: login básico + configuração via interface, sem editar código.

Local: python admin_app.py, depois abra http://localhost:5000
Vercel: exposto via api/index.py (veja vercel.json)
"""
import os
import secrets
from functools import wraps

from dotenv import load_dotenv

load_dotenv()  # lê .env na pasta do projeto (só localmente — na Vercel as env vars vêm do painel).
# Precisa rodar antes dos imports abaixo, porque db.py lê DATABASE_URL assim que é importado.

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, Response  # noqa: E402
from werkzeug.security import generate_password_hash, check_password_hash  # noqa: E402

from db import (  # noqa: E402
    load_config, save_config, load_all, upsert_faturamento,
    load_faturamento_por_unidade_dia, load_nomes_franquia_faturamento,
)
from pipeline import atualizar_periodo  # noqa: E402
from render_html import render_report  # noqa: E402
from render_analise import render_analise  # noqa: E402

app = Flask(__name__)


def _get_secret_key() -> str:
    """Em produção (Vercel), defina FLASK_SECRET_KEY nas variáveis de ambiente — sem isso,
    a sessão de login se perde a cada novo deploy/instância fria."""
    env_key = os.environ.get("FLASK_SECRET_KEY")
    if env_key:
        return env_key

    # fallback só pra desenvolvimento local, persiste num arquivo local
    key_file = ".flask_secret"
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    try:
        with open(key_file, "w", encoding="utf-8") as f:
            f.write(key)
    except OSError:
        pass  # filesystem read-only (ex: serverless sem env var configurada)
    return key


app.secret_key = _get_secret_key()

BASE_STYLE = """
<style>
  :root {
    --blue-900:#243746; --blue-800:#2c4356; --blue-700:#375367; --blue-600:#4a6a80;
    --blue-100:#e6ecf0; --blue-050:#f2f6f8;
    --yellow-500:#fcbf00; --yellow-600:#e0a900;
    --gray-700:#4b5f6c; --gray-300:#b7c3ca; --gray-200:#d8e0e4; --gray-100:#eef2f4;
    --white:#fff; --danger:#c23b3b; --danger-bg:#fbe9e9; --success:#2f8f5b; --success-bg:#e6f5ec;
    --radius-md:14px; --radius-lg:20px; --radius-pill:999px;
    --shadow-sm:0 1px 2px rgba(23,36,44,.08); --shadow-md:0 6px 20px rgba(23,36,44,.10);
    --font-display:'Poppins','Nunito Sans',system-ui,sans-serif;
    --font-body:'Nunito Sans',system-ui,sans-serif;
  }
  * { box-sizing: border-box; }
  body { font:400 16px/1.6 var(--font-body); margin:0; background:var(--blue-050); color:var(--blue-900); }
  .topo { background:var(--blue-900); color:#fff; padding:20px 28px; display:flex; justify-content:space-between; align-items:center; box-shadow:var(--shadow-md); }
  .topo h1 { font:700 20px var(--font-display); margin:0; }
  .topo a { color:var(--blue-100); font-size:13px; text-decoration:none; }
  .wrap { max-width:900px; margin:0 auto; padding:28px 20px 60px; }
  .card { background:#fff; border-radius:var(--radius-lg); padding:24px 26px; margin-bottom:20px; box-shadow:var(--shadow-sm); border:1px solid var(--gray-200); }
  .card h2 { font:600 18px var(--font-display); margin:0 0 16px; }
  label { display:block; font:700 12px var(--font-body); letter-spacing:.04em; text-transform:uppercase; color:var(--gray-700); margin-bottom:4px; }
  input[type=text], input[type=password], input[type=date], select {
    width:100%; padding:10px 12px; border:1px solid var(--gray-300); border-radius:10px;
    font:400 14px var(--font-body); margin-bottom:14px;
  }
  input:focus { outline:none; border-color:var(--yellow-500); box-shadow:0 0 0 3px rgba(252,191,0,.3); }
  button, .btn {
    font:700 14px var(--font-body); padding:10px 20px; border-radius:var(--radius-pill);
    border:none; cursor:pointer; display:inline-block; text-decoration:none;
  }
  .btn-primary { background:var(--yellow-500); color:var(--blue-900); }
  .btn-primary:hover { background:var(--yellow-600); }
  .btn-secondary { background:var(--gray-100); color:var(--blue-900); }
  .btn-danger { background:var(--danger-bg); color:var(--danger); }
  .unidade-row { display:grid; grid-template-columns:1fr 1fr 1fr 1fr auto; gap:10px; align-items:start; margin-bottom:6px; }
  .flash { padding:12px 16px; border-radius:10px; margin-bottom:16px; font-size:14px; }
  .flash.ok { background:var(--success-bg); color:var(--success); }
  .flash.erro { background:var(--danger-bg); color:var(--danger); }
  .login-box { max-width:360px; margin:80px auto; }
  pre { background:var(--blue-900); color:#e6ecf0; padding:14px; border-radius:10px; font-size:12px; overflow-x:auto; max-height:300px; white-space:pre-wrap; }
  .hint { font-size:12px; color:var(--gray-700); margin:-8px 0 14px; }
  .periodo-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:6px; }
  .atalhos { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
  .atalhos button { font-size:12px; padding:6px 12px; }

  .combo-franquia { position:relative; }
  .combo-franquia input.combo-input { margin-bottom:0; cursor:text; }
  .combo-franquia input.combo-input.combo-nenhuma { color:var(--danger); font-weight:700; }
  .combo-lista {
    display:none; position:absolute; top:calc(100% + 4px); left:0; right:0; z-index:20;
    background:#fff; border:1px solid var(--gray-200); border-radius:10px;
    box-shadow:var(--shadow-md); max-height:220px; overflow-y:auto; padding:4px;
  }
  .combo-lista.aberta { display:block; }
  .combo-opcao {
    padding:8px 10px; border-radius:8px; cursor:pointer; font-size:13px;
    display:flex; align-items:center; justify-content:space-between; gap:8px;
  }
  .combo-opcao:hover, .combo-opcao.destacada { background:var(--yellow-500); color:var(--blue-900); }
  .combo-opcao.opcao-nenhuma { color:var(--danger); font-weight:700; border-bottom:1px solid var(--gray-200); margin-bottom:4px; }
  .combo-opcao.opcao-nenhuma:hover, .combo-opcao.opcao-nenhuma.destacada { background:var(--danger-bg); color:var(--danger); }
  .combo-vazio { padding:8px 10px; font-size:13px; color:var(--gray-700); }
</style>
"""


def login_obrigatorio(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logado"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    cfg = load_config()
    primeiro_acesso = not cfg.get("admin_password_hash")

    if request.method == "POST":
        senha = request.form.get("senha", "")

        if primeiro_acesso:
            confirmar = request.form.get("confirmar", "")
            if len(senha) < 4:
                flash("Senha muito curta (mínimo 4 caracteres).", "erro")
            elif senha != confirmar:
                flash("As senhas não conferem.", "erro")
            else:
                cfg["admin_password_hash"] = generate_password_hash(senha)
                save_config(cfg)
                session["logado"] = True
                return redirect(url_for("admin"))
        else:
            if check_password_hash(cfg["admin_password_hash"], senha):
                session["logado"] = True
                return redirect(url_for("admin"))
            flash("Senha incorreta.", "erro")

    return render_template_string(f"""
    {BASE_STYLE}
    <div class="wrap login-box">
      <div class="card">
        <h2>{'Definir senha de admin' if primeiro_acesso else 'Login'}</h2>
        {{% with messages = get_flashed_messages(with_categories=true) %}}
          {{% for cat, msg in messages %}}<div class="flash {{{{cat}}}}">{{{{msg}}}}</div>{{% endfor %}}
        {{% endwith %}}
        <form method="post">
          <label>Senha</label>
          <input type="password" name="senha" autofocus required>
          {{% if primeiro_acesso %}}
          <label>Confirmar senha</label>
          <input type="password" name="confirmar" required>
          {{% endif %}}
          <button class="btn-primary" type="submit">{'Criar senha e entrar' if primeiro_acesso else 'Entrar'}</button>
        </form>
      </div>
    </div>
    """, primeiro_acesso=primeiro_acesso)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_obrigatorio
def admin():
    cfg = load_config()
    nomes_franquia = load_nomes_franquia_faturamento()
    return render_template_string(TEMPLATE_ADMIN, cfg=cfg, resultado_execucao=None, nomes_franquia=nomes_franquia)


@app.route("/salvar", methods=["POST"])
@login_obrigatorio
def salvar():
    cfg = load_config()

    nomes = request.form.getlist("unidade_nome")
    metas = request.form.getlist("unidade_meta")
    googles = request.form.getlist("unidade_google")
    nomes_faturamento = request.form.getlist("unidade_nome_faturamento")

    unidades = []
    for nome, meta_id, google_id, nome_fat in zip(nomes, metas, googles, nomes_faturamento):
        if nome.strip():
            unidades.append({
                "unidade": nome.strip(),
                "meta_ad_account_id": meta_id.strip(),
                "google_customer_id": google_id.strip(),
                "nome_faturamento": nome_fat.strip(),
            })
    cfg["unidades"] = unidades

    cfg["meta_access_token"] = request.form.get("meta_access_token", "").strip()
    cfg["meta_api_version"] = request.form.get("meta_api_version", "v23.0").strip()

    cfg["google_ads_config"] = {
        "developer_token": request.form.get("google_developer_token", "").strip(),
        "client_id": request.form.get("google_client_id", "").strip(),
        "client_secret": request.form.get("google_client_secret", "").strip(),
        "refresh_token": request.form.get("google_refresh_token", "").strip(),
        "login_customer_id": request.form.get("google_login_customer_id", "").strip(),
    }

    save_config(cfg)
    flash("Configuração salva com sucesso.", "ok")
    return redirect(url_for("admin"))


@app.route("/rodar-agora", methods=["POST"])
@login_obrigatorio
def rodar_agora():
    cfg = load_config()

    data_inicio = request.form.get("data_inicio", "").strip() or None
    data_fim = request.form.get("data_fim", "").strip() or None

    log = atualizar_periodo(data_inicio, data_fim)
    nomes_franquia = load_nomes_franquia_faturamento()
    return render_template_string(TEMPLATE_ADMIN, cfg=cfg, resultado_execucao=log, nomes_franquia=nomes_franquia)


@app.route("/cron")
def cron():
    """Chamado automaticamente pelo Vercel Cron (veja vercel.json). Protegido pelo CRON_SECRET:
    a Vercel manda esse valor sozinha no header Authorization quando a env var está configurada."""
    esperado = os.environ.get("CRON_SECRET")
    recebido = request.headers.get("Authorization", "")
    if not esperado or recebido != f"Bearer {esperado}":
        return Response("Não autorizado.", status=401)

    log = atualizar_periodo()
    return Response(log, mimetype="text/plain")


@app.route("/webhook/faturamento", methods=["POST"])
def api_faturamento():
    """Recebe o array JSON de vendas já limpo pelo n8n e grava no banco (idempotente por
    external_id). Chame com header: Authorization: Bearer <FATURAMENTO_SECRET>"""
    esperado = os.environ.get("FATURAMENTO_SECRET")
    recebido = request.headers.get("Authorization", "")
    if not esperado or recebido != f"Bearer {esperado}":
        return {"erro": "não autorizado"}, 401

    registros = request.get_json(silent=True)
    if not isinstance(registros, list):
        return {"erro": "corpo da requisição precisa ser uma lista JSON de vendas"}, 400

    try:
        total = upsert_faturamento(registros)
    except Exception as e:
        return {"erro": str(e)}, 400

    return {"gravados": total}, 200


TEMPLATE_ADMIN = BASE_STYLE + """
<div class="topo">
  <h1>Admin · BI Tráfego Pago</h1>
  <a href="{{ url_for('logout') }}">Sair</a>
</div>
<div class="wrap">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}<div class="flash {{cat}}">{{msg}}</div>{% endfor %}
  {% endwith %}

  <div class="card">
    <h2>Executar agora</h2>
    <p class="hint">Escolha o período que quer buscar (ou deixe em branco para atualizar somente hoje).</p>
    <form method="post" action="{{ url_for('rodar_agora') }}" id="formRodar">
      <div class="periodo-row">
        <div><label>Data início</label><input type="date" name="data_inicio" id="dataInicio"></div>
        <div><label>Data fim</label><input type="date" name="data_fim" id="dataFim"></div>
      </div>
      <div class="atalhos">
        <button type="button" class="btn-secondary" onclick="setPeriodo('hoje')">Somente hoje</button>
        <button type="button" class="btn-secondary" onclick="setPeriodo('ontem')">Somente ontem</button>
        <button type="button" class="btn-secondary" onclick="setPeriodo('mesAtual')">Mês atual (dia 01 até hoje)</button>
        <button type="button" class="btn-secondary" onclick="setPeriodo('mesPassado')">Mês passado inteiro</button>
        <button type="button" class="btn-secondary" onclick="setPeriodo('limpar')">Limpar</button>
      </div>
      <button class="btn-primary" type="submit">Rodar extração agora</button>
    </form>
    <p class="hint" style="margin-top:12px;">Períodos longos podem estourar o tempo limite da função na Vercel —
      pra backfills grandes, rode <code>python main.py DATA_INICIO DATA_FIM</code> localmente (mesmo banco).</p>
    {% if resultado_execucao is not none %}
      <p style="margin-top:16px;"><strong>Log da execução:</strong></p>
      <pre>{{ resultado_execucao }}</pre>
    {% endif %}
    <p style="margin-top:16px;">
      <a class="btn btn-secondary" href="{{ url_for('ver_relatorio') }}" target="_blank">📺 Abrir relatório (TV)</a>
      <a class="btn btn-secondary" href="{{ url_for('ver_analise') }}" target="_blank">📊 Abrir análise</a>
    </p>
  </div>

  <form method="post" action="{{ url_for('salvar') }}">
    <div class="card">
      <h2>Unidades</h2>
      <p class="hint">Uma linha por unidade franqueada. Deixe o campo em branco se a unidade ainda não usa aquela plataforma.
        Digite pra buscar a "Franquia no Agiliza" só se o nome de vendas for diferente do nome da unidade aqui
        (ex: a franquia aparece só como "Curitiba" no Agiliza, mas aqui ela é "Curitiba Tarumã"). Deixe em branco pra
        continuar usando o cruzamento automático pelo nome da unidade, ou escolha "Não contabilizar" se essa unidade
        realmente não tem registro de vendas no Agiliza.</p>
      <div id="listaUnidades">
        {% for u in cfg.unidades %}
        <div class="unidade-row">
          <div><label>Nome da unidade</label><input type="text" name="unidade_nome" value="{{ u.unidade }}"></div>
          <div><label>Meta Ad Account ID</label><input type="text" name="unidade_meta" value="{{ u.meta_ad_account_id }}" placeholder="act_XXXXXXXXXX"></div>
          <div><label>Google Customer ID</label><input type="text" name="unidade_google" value="{{ u.google_customer_id }}" placeholder="123-456-7890"></div>
          <div>
            <label>Franquia no Agiliza</label>
            <div class="combo-franquia">
              <input type="text" class="combo-input {{ 'combo-nenhuma' if u.nome_faturamento == '__NENHUMA__' }}"
                     autocomplete="off" placeholder="Buscar ou deixar em branco..."
                     value="{{ 'Não contabilizar' if u.nome_faturamento == '__NENHUMA__' else (u.nome_faturamento or '') }}">
              <input type="hidden" name="unidade_nome_faturamento" value="{{ u.nome_faturamento or '' }}">
              <div class="combo-lista"></div>
            </div>
          </div>
          <div><label>&nbsp;</label><button type="button" class="btn-danger" onclick="this.closest('.unidade-row').remove()">Remover</button></div>
        </div>
        {% endfor %}
      </div>
      <button type="button" class="btn-secondary" onclick="adicionarUnidade()">+ Adicionar unidade</button>
    </div>

    <div class="card">
      <h2>Meta (Facebook/Instagram Ads)</h2>
      <label>Access Token</label>
      <input type="text" name="meta_access_token" value="{{ cfg.meta_access_token }}">
      <label>Versão da API</label>
      <input type="text" name="meta_api_version" value="{{ cfg.meta_api_version }}">
    </div>

    <div class="card">
      <h2>Google Ads</h2>
      <label>Developer Token</label>
      <input type="text" name="google_developer_token" value="{{ cfg.google_ads_config.developer_token }}">
      <label>Client ID</label>
      <input type="text" name="google_client_id" value="{{ cfg.google_ads_config.client_id }}">
      <label>Client Secret</label>
      <input type="text" name="google_client_secret" value="{{ cfg.google_ads_config.client_secret }}">
      <label>Refresh Token</label>
      <input type="text" name="google_refresh_token" value="{{ cfg.google_ads_config.refresh_token }}">
      <label>Login Customer ID (conta MCC, sem hífen)</label>
      <input type="text" name="google_login_customer_id" value="{{ cfg.google_ads_config.login_customer_id }}">
    </div>

    <button class="btn-primary" type="submit">Salvar configuração</button>
  </form>
</div>

<template id="templateUnidadeRow">
  <div class="unidade-row">
    <div><label>Nome da unidade</label><input type="text" name="unidade_nome"></div>
    <div><label>Meta Ad Account ID</label><input type="text" name="unidade_meta" placeholder="act_XXXXXXXXXX"></div>
    <div><label>Google Customer ID</label><input type="text" name="unidade_google" placeholder="123-456-7890"></div>
    <div>
      <label>Franquia no Agiliza</label>
      <div class="combo-franquia">
        <input type="text" class="combo-input" autocomplete="off" placeholder="Buscar ou deixar em branco...">
        <input type="hidden" name="unidade_nome_faturamento" value="">
        <div class="combo-lista"></div>
      </div>
    </div>
    <div><label>&nbsp;</label><button type="button" class="btn-danger" onclick="this.closest('.unidade-row').remove()">Remover</button></div>
  </div>
</template>
<script>
const NOMES_FRANQUIA = {{ nomes_franquia | tojson }};
const VALOR_NENHUMA = "__NENHUMA__";

function adicionarUnidade() {
  const tpl = document.getElementById("templateUnidadeRow");
  const clone = tpl.content.cloneNode(true);
  document.getElementById("listaUnidades").appendChild(clone);
  document.querySelectorAll(".combo-franquia:not([data-init])").forEach(initComboFranquia);
}

function initComboFranquia(container) {
  container.setAttribute("data-init", "1");
  const input = container.querySelector(".combo-input");
  const hidden = container.querySelector("input[type=hidden]");
  const lista = container.querySelector(".combo-lista");

  function renderLista(filtro) {
    const termo = (filtro || "").trim().toLowerCase();
    const opcoes = NOMES_FRANQUIA.filter(n => !termo || n.toLowerCase().includes(termo));

    let html = '<div class="combo-opcao opcao-nenhuma" data-valor="' + VALOR_NENHUMA + '" data-texto="Não contabilizar">'
      + '✕ Não contabilizar (essa unidade não existe no Agiliza)</div>';
    if (opcoes.length === 0) {
      html += '<div class="combo-vazio">Nenhuma franquia encontrada.</div>';
    } else {
      for (const nome of opcoes) {
        html += '<div class="combo-opcao" data-valor="' + nome + '" data-texto="' + nome + '">' + nome + '</div>';
      }
    }
    lista.innerHTML = html;
    lista.classList.add("aberta");

    lista.querySelectorAll(".combo-opcao").forEach(op => {
      op.addEventListener("mousedown", (e) => {
        e.preventDefault();
        hidden.value = op.dataset.valor;
        input.value = op.dataset.texto;
        input.classList.toggle("combo-nenhuma", op.dataset.valor === VALOR_NENHUMA);
        lista.classList.remove("aberta");
      });
    });
  }

  input.addEventListener("focus", () => renderLista(input.value === "Não contabilizar" ? "" : input.value));
  input.addEventListener("input", () => {
    hidden.value = "";
    input.classList.remove("combo-nenhuma");
    renderLista(input.value);
  });
  input.addEventListener("blur", () => {
    setTimeout(() => {
      lista.classList.remove("aberta");
      // se o texto digitado não bate com nenhuma opção escolhida, considera em branco (auto)
      if (hidden.value === "" && input.value.trim() !== "") {
        const match = NOMES_FRANQUIA.find(n => n.toLowerCase() === input.value.trim().toLowerCase());
        if (match) { hidden.value = match; input.value = match; }
        else { input.value = ""; }
      }
    }, 150);
  });
}

document.querySelectorAll(".combo-franquia").forEach(initComboFranquia);

function fmtISO(d) {
  return d.toISOString().slice(0, 10);
}

function setPeriodo(tipo) {
  const inicio = document.getElementById("dataInicio");
  const fim = document.getElementById("dataFim");
  const hoje = new Date();

  if (tipo === "limpar") { inicio.value = ""; fim.value = ""; return; }
  if (tipo === "hoje") { inicio.value = fmtISO(hoje); fim.value = fmtISO(hoje); return; }
  if (tipo === "ontem") {
    const ontem = new Date(hoje); ontem.setDate(ontem.getDate() - 1);
    inicio.value = fmtISO(ontem); fim.value = fmtISO(ontem); return;
  }
  if (tipo === "mesAtual") {
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    inicio.value = fmtISO(primeiroDia); fim.value = fmtISO(hoje); return;
  }
  if (tipo === "mesPassado") {
    const primeiroDiaMesPassado = new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1);
    const ultimoDiaMesPassado = new Date(hoje.getFullYear(), hoje.getMonth(), 0);
    inicio.value = fmtISO(primeiroDiaMesPassado); fim.value = fmtISO(ultimoDiaMesPassado); return;
  }
}
</script>
"""


def _nomes_faturamento(cfg: dict) -> dict:
    return {
        u["unidade"]: u["nome_faturamento"]
        for u in cfg["unidades"]
        if u.get("nome_faturamento")
    }


@app.route("/relatorio")
@login_obrigatorio
def ver_relatorio():
    cfg = load_config()
    return render_report(load_all(), load_faturamento_por_unidade_dia(), _nomes_faturamento(cfg))


@app.route("/analise")
@login_obrigatorio
def ver_analise():
    cfg = load_config()
    return render_analise(load_all(), load_faturamento_por_unidade_dia(), _nomes_faturamento(cfg))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
