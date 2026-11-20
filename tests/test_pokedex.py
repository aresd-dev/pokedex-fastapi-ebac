import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import PokemonEntrada


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    # Um arquivo por teste evita interferência entre cenários.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'teste.db'}")
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def dados():
    return {"nome": "Pikachu", "tipo": "Elétrico", "nivel": 15, "ataque": 55}


@pytest.mark.parametrize("campo,valor", [
    ("nome", "  "), ("tipo", ""), ("nivel", 0), ("nivel", 101),
    ("ataque", 0), ("ataque", 256), ("nivel", True),
])
def test_modelo_rejeita_atributos_invalidos(dados, campo, valor):
    # Teste unitário do modelo, independente de HTTP e banco.
    with pytest.raises(ValidationError):
        PokemonEntrada(**{**dados, campo: valor})


def test_criar_buscar_atualizar_excluir(cliente, dados):
    resposta = cliente.post("/pokemons", json=dados)
    assert resposta.status_code == 201, resposta.text
    id = resposta.json()["id"]
    rota = f"/pokemons/{id}"
    assert cliente.get(rota).json() == {**dados, "id": id}

    # Um PUT substitui os atributos preservando a identidade.
    novos = {**dados, "nome": "Raichu", "ataque": 90}
    resposta = cliente.put(rota, json=novos)
    assert resposta.status_code == 200, resposta.text
    assert cliente.get(rota).json() == {**novos, "id": id}

    resposta = cliente.delete(rota)
    assert resposta.status_code == 204 and resposta.content == b""
    assert cliente.get(rota).status_code == 404, "O registro excluído ainda existe"


def test_lista_paginada(cliente, dados):
    assert cliente.get("/pokemons").json() == []
    for nome in ["Pikachu", "Raichu", "Eevee"]:
        assert cliente.post("/pokemons", json={**dados, "nome": nome}).status_code == 201
    resposta = cliente.get("/pokemons", params={"offset": 1, "limit": 1})
    assert resposta.status_code == 200
    assert [p["nome"] for p in resposta.json()] == ["Raichu"]
    assert cliente.get("/pokemons?limit=0").status_code == 422


def test_conflito_nao_altera_registro(cliente, dados):
    cliente.post("/pokemons", json=dados).raise_for_status()
    repetido = {**dados, "nome": "  PIKACHU  "}
    assert cliente.post("/pokemons", json=repetido).status_code == 409
    outro = cliente.post("/pokemons", json={**dados, "nome": "Eevee"}).json()
    rota = f"/pokemons/{outro['id']}"
    assert cliente.put(rota, json=repetido).status_code == 409
    assert cliente.get(rota).json() == outro, "Conflito de nome deve preservar os dados"


@pytest.mark.parametrize("metodo", ["GET", "PUT", "DELETE"])
def test_id_desconhecido(cliente, dados, metodo):
    resposta = cliente.request(metodo, "/pokemons/999", json=dados if metodo == "PUT" else None)
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pokémon não encontrado"


def test_validacao_http(cliente, dados):
    assert cliente.post("/pokemons", json={}).status_code == 422
    pokemon = cliente.post("/pokemons", json=dados).json()
    rota = f"/pokemons/{pokemon['id']}"
    assert cliente.put(rota, json={**dados, "tipo": " "}).status_code == 422
    assert cliente.get(rota).json() == pokemon
