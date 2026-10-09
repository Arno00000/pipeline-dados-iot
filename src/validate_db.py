"""Valida, direto no PostgreSQL, que os dados e as views estão corretos.

Uso:  python src/validate_db.py
"""
import pandas as pd

from database import get_engine

CHECKS = {
    "Total de registros":
        "SELECT COUNT(*) AS total FROM temperature_readings",
    "Primeiros registros":
        "SELECT * FROM temperature_readings ORDER BY noted_at, reading_id LIMIT 5",
    "Últimos registros":
        "SELECT * FROM temperature_readings ORDER BY noted_at DESC, reading_id LIMIT 5",
    "Mínima, máxima e média (°C)":
        """SELECT MIN(temperature) AS minima, MAX(temperature) AS maxima,
                  ROUND(AVG(temperature)::numeric, 2) AS media,
                  MIN(noted_at) AS inicio, MAX(noted_at) AS fim
           FROM temperature_readings""",
    "Registros por ambiente":
        "SELECT location, COUNT(*) AS registros FROM temperature_readings GROUP BY location",
    "Valores nulos por coluna":
        """SELECT COUNT(*) FILTER (WHERE reading_id IS NULL)  AS reading_id,
                  COUNT(*) FILTER (WHERE room_id IS NULL)     AS room_id,
                  COUNT(*) FILTER (WHERE noted_at IS NULL)    AS noted_at,
                  COUNT(*) FILTER (WHERE temperature IS NULL) AS temperature,
                  COUNT(*) FILTER (WHERE location IS NULL)    AS location
           FROM temperature_readings""",
    "View 1 - temperatura_media_ambiente":
        "SELECT * FROM temperatura_media_ambiente",
    "View 2 - leituras_por_hora (amostra)":
        "SELECT * FROM leituras_por_hora LIMIT 6",
    "View 3 - temperatura_por_dia (amostra)":
        "SELECT * FROM temperatura_por_dia LIMIT 6",
}


def main() -> None:
    engine = get_engine()
    pd.set_option("display.width", 140)
    for title, sql in CHECKS.items():
        df = pd.read_sql(sql, engine)
        print(f"\n== {title} ==")
        print(df.to_string(index=False))
        if df.empty:
            raise SystemExit(f"[ERRO] '{title}' não retornou dados.")
    print("\n[OK] Validação concluída: tabela e 3 views retornam dados.")


if __name__ == "__main__":
    main()
