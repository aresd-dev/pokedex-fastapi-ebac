import os

from sqlalchemy import CheckConstraint, String, URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Pokemon(Base):
    __tablename__ = "pokemons"
    __table_args__ = (
        CheckConstraint("nivel BETWEEN 1 AND 100"),
        CheckConstraint("ataque BETWEEN 1 AND 255"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    # Chave interna: preserva a grafia exibida, mas impede duplicatas por caixa.
    chave_nome: Mapped[str] = mapped_column(String(180), unique=True)
    tipo: Mapped[str] = mapped_column(String(40))
    nivel: Mapped[int]
    ataque: Mapped[int]


def criar_engine():
    if url := os.getenv("DATABASE_URL"):
        return create_engine(url, pool_pre_ping=True)
    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
    )
    return create_engine(url, pool_pre_ping=True)
