"""CLI local para backfills grandes (a função da Vercel tem timeout curto pra períodos longos).

Uso:
    python main.py                        # atualiza somente HOJE
    python main.py 2026-07-01 2026-07-19   # backfill de um período (dia a dia)

Requer DATABASE_URL configurada (no .env local ou no ambiente), apontando pro mesmo Postgres usado no admin (Vercel).
"""
import sys

from dotenv import load_dotenv

load_dotenv()

from pipeline import atualizar_periodo  # noqa: E402


def main():
    if len(sys.argv) == 3:
        log = atualizar_periodo(sys.argv[1], sys.argv[2])
    else:
        log = atualizar_periodo()
    print(log)


if __name__ == "__main__":
    main()
