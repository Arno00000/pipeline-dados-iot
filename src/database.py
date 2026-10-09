"""Conexão com o PostgreSQL via SQLAlchemy.

As credenciais são lidas do arquivo .env na raiz do projeto
(nunca escritas no código).
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_engine() -> Engine:
    """Cria o engine do SQLAlchemy a partir das variáveis de ambiente."""
    required = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Variáveis ausentes no .env: {', '.join(missing)}. "
            "Copie .env.example para .env e preencha os valores."
        )
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"),
    )
    return create_engine(url, pool_pre_ping=True)


def test_connection(engine: Engine) -> str:
    """Executa uma consulta simples e devolve a versão do PostgreSQL."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT version()")).scalar()
