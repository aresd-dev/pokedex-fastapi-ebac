from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Base, Pokemon, criar_engine
from .schemas import Erro, PokemonEntrada, PokemonSaida


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = criar_engine()
    try:
        Base.metadata.create_all(engine)
        app.state.engine = engine
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="Pokédex",
    version="1.0.0",
    description="Catálogo de Pokémon. Cada registro tem nome único, tipo, nível e ataque.",
    lifespan=lifespan,
    openapi_tags=[{"name": "Pokémon", "description": "Cadastro e consulta do catálogo."}],
)


def obter_sessao(request: Request):
    with Session(request.app.state.engine) as sessao:
        yield sessao


Banco = Annotated[Session, Depends(obter_sessao)]
NAO_ENCONTRADO = {404: {"model": Erro, "description": "ID inexistente"}}
DUPLICADO = {409: {"model": Erro, "description": "Nome já cadastrado"}}


def buscar_por_id(id: int, banco: Session) -> Pokemon:
    pokemon = banco.get(Pokemon, id)
    if pokemon is None:
        raise HTTPException(404, "Pokémon não encontrado")
    return pokemon


def salvar(pokemon: Pokemon, dados: PokemonEntrada, banco: Session) -> Pokemon:
    for campo, valor in dados.model_dump().items():
        setattr(pokemon, campo, valor)
    pokemon.chave_nome = dados.nome.casefold()
    banco.add(pokemon)
    try:
        banco.commit()
    except IntegrityError as erro:
        banco.rollback()
        if (getattr(erro.orig, "sqlstate", None) == "23505" or
                getattr(erro.orig, "sqlite_errorname", None) == "SQLITE_CONSTRAINT_UNIQUE"):
            raise HTTPException(409, "Nome já cadastrado") from erro
        raise
    banco.refresh(pokemon)
    return pokemon


@app.post("/pokemons", response_model=PokemonSaida, status_code=201,
          tags=["Pokémon"], summary="Cadastrar um Pokémon", responses=DUPLICADO)
def criar(dados: PokemonEntrada, banco: Banco):
    return salvar(Pokemon(), dados, banco)


@app.get("/pokemons", response_model=list[PokemonSaida], tags=["Pokémon"],
         summary="Listar Pokémon por ordem de cadastro")
def listar(banco: Banco, offset: Annotated[int, Query(ge=0)] = 0,
           limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return banco.scalars(select(Pokemon).order_by(Pokemon.id).offset(offset).limit(limit)).all()


@app.get("/pokemons/{id}", response_model=PokemonSaida, tags=["Pokémon"],
         summary="Consultar um Pokémon pelo ID", responses=NAO_ENCONTRADO)
def consultar(id: int, banco: Banco):
    return buscar_por_id(id, banco)


@app.put("/pokemons/{id}", response_model=PokemonSaida, tags=["Pokémon"],
         summary="Substituir os dados de um Pokémon", responses=NAO_ENCONTRADO | DUPLICADO)
def atualizar(id: int, dados: PokemonEntrada, banco: Banco):
    return salvar(buscar_por_id(id, banco), dados, banco)


@app.delete("/pokemons/{id}", status_code=204, tags=["Pokémon"],
            summary="Excluir um Pokémon", responses=NAO_ENCONTRADO)
def excluir(id: int, banco: Banco):
    banco.delete(buscar_por_id(id, banco))
    banco.commit()
    return Response(status_code=204)
