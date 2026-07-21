"""CLI local para backfills grandes (a função da Vercel tem timeout curto pra períodos longos).

Uso:
    python main.py                        # atualiza somente HOJE
    python main.py 2026-07-01 2026-07-19   # backfill de um período (dia a dia)

Requer DATABASE_URL configurada no ambiente, apontando pro mesmo Postgres usado no admin (Vercel).
"""
import sys

from pipeline import atualizar_periodo


def main():
    if len(sys.argv) == 3:
        log = atualizar_periodo(sys.argv[1], sys.argv[2])
    else:
        log = atualizar_periodo()
    print(log)


if __name__ == "__main__":
    main()
