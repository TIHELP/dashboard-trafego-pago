# Dash Tráfego — BI de Campanhas por Unidade

Painel web (login + admin) com investimento, leads, CPL, faturamento e ROAS por unidade,
plataforma (Meta/Google) e período — filtro de data direto na tela, hospedado na Vercel.

Os dados ficam num **Postgres** (histórico), gravados por uma extração que roda a cada 2h
(Vercel Cron) ou sob demanda pelo botão "Rodar extração agora" no painel.

## Arquitetura

- `db.py` — toda a persistência (config + histórico) via Postgres. Sem isso não sobra nada salvo
  entre uma execução e outra, porque o disco da Vercel é apagado a cada invocação.
- `pipeline.py` — extrai do Meta/Google e grava no banco. Usado tanto pelo admin quanto pelo `main.py`.
- `admin_app.py` — o app Flask (login, formulário de config, botão de rodar, relatório).
- `api/index.py` + `vercel.json` — entrypoint e configuração da Vercel (rotas + cron a cada 2h).
- `main.py` — CLI local, só pra backfills grandes (a função da Vercel tem timeout curto).

## Deploy na Vercel

### 1. Banco de dados (Postgres)
Crie um banco gratuito em uma dessas opções (qualquer uma serve, é só Postgres padrão):
- **Vercel Postgres** (aba Storage do próprio projeto na Vercel — mais simples, já integra a env var sozinha)
- [Neon](https://neon.tech) ou [Supabase](https://supabase.com) (free tier, copie a connection string)

Guarde a connection string (formato `postgres://usuario:senha@host:5432/banco?sslmode=require`).

### 2. Subir o projeto
```bash
npm i -g vercel      # se ainda não tiver a CLI
cd D:\Usuario\Documents\dash-trafego
vercel
```
Ou conecte o repositório pelo painel da Vercel (Import Project). O `vercel.json` já define o build
Python e a rota do cron.

### 3. Variáveis de ambiente (Vercel → Project Settings → Environment Variables)
| Nome | Valor | Obrigatória |
|---|---|---|
| `DATABASE_URL` | connection string do passo 1 | sim |
| `FLASK_SECRET_KEY` | uma string aleatória longa (ex: gere com `python -c "import secrets;print(secrets.token_hex(32))"`) | sim — sem isso o login desloga sozinho a cada novo deploy |
| `CRON_SECRET` | outra string aleatória qualquer | sim — protege a rota `/cron` de ser chamada por qualquer um |

Depois de configurar, redeploy (`vercel --prod`) pra elas entrarem em vigor.

### 4. Primeiro acesso
Abra a URL que a Vercel deu (ex: `https://dash-trafego.vercel.app`). No primeiro acesso você define
a senha de admin, depois cadastra as unidades e credenciais — tudo pela tela, igual antes.

## Uso local (desenvolvimento)

```bash
pip install -r requirements.txt
set DATABASE_URL=postgres://...        # mesmo banco usado na Vercel, ou um separado pra testar
python admin_app.py
```
Abra [http://localhost:5000](http://localhost:5000).

Backfill grande (evita timeout da função na Vercel):
```bash
python main.py 2026-07-01 2026-07-19
```

## Atenção — limitações da Vercel pra esse tipo de app

- **Cron a cada 2h precisa do plano Pro.** No plano Hobby (gratuito), a Vercel permite no máximo
  1 execução de cron por dia — pra rodar de 2 em 2h é preciso o plano Pro. Se for ficar no Hobby,
  configure `vercel.json` pra rodar 1x/dia e complemente clicando em "Rodar extração agora" manualmente
  quando precisar de dados mais frescos no meio do dia.
- **Timeout de função**: por padrão a função tem poucos segundos (10s no Hobby). Se tiver muitas
  unidades, a extração de "hoje" pode não terminar a tempo. Se acontecer, ou reduz a frequência,
  ou (com plano Pro) aumenta `maxDuration` no `vercel.json`.
- **Biblioteca do Google Ads é pesada** (`google-ads` usa gRPC) — o primeiro deploy pode demorar mais
  pra buildar e o cold start (primeira requisição depois de um tempo parado) pode ser mais lento.
  Se o deploy falhar por tamanho de pacote, me avise que a gente troca a chamada do Google Ads pra
  usar a API REST diretamente em vez da lib oficial.

## Observações sobre os dados

- **Leads (Meta)**: soma as `actions` do tipo `lead`, `offsite_conversion.fb_pixel_lead`,
  `onsite_conversion.lead_grouped` e `onsite_conversion.messaging_conversation_started_7d` (campanhas de
  WhatsApp/"Conversas por mensagem"). Se uma unidade usar outro evento de resultado, ajuste
  `LEAD_ACTION_TYPES` em [extract_meta.py](extract_meta.py).
- **Faturamento (Meta)**: soma `action_values` de eventos de compra (pixel/CAPI). Campanhas de geração
  de lead sem checkout online não têm essa informação disponível na API — o faturamento real precisaria
  vir do CRM da franquia (fora do escopo deste projeto por enquanto).
- **Leads/Faturamento (Google)**: usa as conversões e valor de conversão configuradas na conta. Confirme
  que só a ação de conversão "Lead" está marcada como "principal", senão o número infla.
- **Campanhas com nome repetido**: se duas campanhas da mesma unidade/plataforma tiverem o mesmo nome
  no mesmo dia, os valores são somados automaticamente (evita erro de chave duplicada no banco).
