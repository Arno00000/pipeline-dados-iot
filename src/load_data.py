"""Pipeline de carga: CSV do Kaggle -> limpeza (Pandas) -> PostgreSQL.

Uso:  python src/load_data.py

O script é idempotente: a cada execução a tabela é esvaziada (TRUNCATE)
e recarregada dentro de uma única transação, então rodar duas vezes
não duplica os dados. Ao final, as views de sql/views.sql são (re)criadas.
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import PROJECT_ROOT, get_engine, test_connection

CSV_PATH = PROJECT_ROOT / "data" / "IOT-temp.csv"
VIEWS_PATH = PROJECT_ROOT / "sql" / "views.sql"
TABLE = "temperature_readings"

# Mapeamento: nome original no CSV -> nome no banco
COLUMN_MAP = {
    "id": "reading_id",
    "room_id/id": "room_id",
    "noted_date": "noted_at",
    "temp": "temperature",
    "out/in": "location",
}

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    reading_id  TEXT PRIMARY KEY,
    room_id     TEXT      NOT NULL,
    noted_at    TIMESTAMP NOT NULL,
    temperature SMALLINT  NOT NULL,
    location    TEXT      NOT NULL CHECK (location IN ('In', 'Out'))
);
CREATE INDEX IF NOT EXISTS idx_{TABLE}_noted_at ON {TABLE} (noted_at);
"""


def extract(path: Path) -> pd.DataFrame:
    """Lê o CSV bruto."""
    if not path.exists():
        sys.exit(
            f"CSV não encontrado em {path}.\n"
            "Rode 'python src/download_data.py' ou baixe do Kaggle."
        )
    return pd.read_csv(path)


def transform(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Limpa, tipa e valida os dados. Devolve o DataFrame e estatísticas."""
    stats = {"lidos": len(raw)}

    missing = set(COLUMN_MAP) - set(raw.columns)
    if missing:
        sys.exit(f"Colunas esperadas ausentes no CSV: {missing}")

    df = raw.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())].copy()

    # Texto: remove espaços extras
    for col in ["reading_id", "room_id", "location"]:
        df[col] = df[col].astype("string").str.strip()

    # Data no formato DD-MM-YYYY HH:MM (ex.: 08-12-2018 09:30 = 8 de dezembro)
    df["noted_at"] = pd.to_datetime(df["noted_at"], format="%d-%m-%Y %H:%M", errors="coerce")
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    # Nulos (inclui datas/temperaturas que não puderam ser convertidas)
    stats["nulos"] = int(df.isna().any(axis=1).sum())
    df = df.dropna()

    # Validação de domínio
    valid = df["location"].isin(["In", "Out"]) & df["temperature"].between(-50, 100)
    stats["invalidos"] = int((~valid).sum())
    df = df[valid]

    # Duplicidades: linha idêntica ou mesmo id de leitura
    before = len(df)
    df = df.drop_duplicates().drop_duplicates(subset="reading_id")
    stats["duplicados"] = before - len(df)

    df["temperature"] = df["temperature"].astype("int16")
    df = df.sort_values("noted_at").reset_index(drop=True)
    stats["validos"] = len(df)
    return df, stats


def load(df: pd.DataFrame, engine) -> int:
    """Recria o conteúdo da tabela numa transação única e aplica as views."""
    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
        conn.execute(text(f"TRUNCATE TABLE {TABLE}"))
        df.to_sql(TABLE, conn, if_exists="append", index=False,
                  method="multi", chunksize=5000)
        conn.execute(text(VIEWS_PATH.read_text(encoding="utf-8")))
        return conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar()


def main() -> None:
    print("== Pipeline IoT: carga de dados ==")
    engine = get_engine()
    try:
        version = test_connection(engine)
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"[ERRO] Não foi possível conectar ao PostgreSQL: {exc}\n"
                 "O contêiner está rodando? (docker compose up -d)")
    print(f"[OK] Conectado: {version.split(',')[0]}")

    raw = extract(CSV_PATH)
    print(f"[OK] CSV lido: {CSV_PATH.name} ({len(raw):,} linhas, colunas: {list(raw.columns)})")

    df, stats = transform(raw)
    print(f"     Registros lidos ........ {stats['lidos']:,}")
    print(f"     Nulos removidos ........ {stats['nulos']:,}")
    print(f"     Inválidos removidos .... {stats['invalidos']:,}")
    print(f"     Duplicados removidos ... {stats['duplicados']:,}")
    print(f"     Registros válidos ...... {stats['validos']:,}")

    inserted = load(df, engine)
    print(f"[OK] Inseridos em {TABLE}: {inserted:,}")
    print("[OK] Views criadas: temperatura_media_ambiente, leituras_por_hora, temperatura_por_dia")
    if inserted != stats["validos"]:
        sys.exit("[ERRO] Quantidade no banco difere dos registros válidos!")
    print("Carga concluída. Próximo passo: python src/validate_db.py")


if __name__ == "__main__":
    main()
