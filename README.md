# Pokédex com FastAPI e PostgreSQL

API para cadastrar espécies de Pokémon e manter um catálogo local. O ID é gerado pelo banco. Cada nome é único mesmo quando muda a caixa das letras ou há espaços nas pontas. O nível vai de 1 a 100 e o ataque de 1 a 255.

## Executar com Docker Compose

1. Clone o repositório e entre na pasta que contém `docker-compose.yml`.
2. Copie `.env.example` para `.env` com `cp .env.example .env` (PowerShell: `Copy-Item .env.example .env`). Preencha `POSTGRES_PASSWORD` com uma senha local. O arquivo já traz o nome do banco, usuário e porta HTTP. O Git ignora o arquivo preenchido.
3. Com o Docker em execução, rode `docker compose up -d --build --wait`.
4. Abra [Swagger UI](http://localhost:8000/docs) e use **Try it out**. A especificação JSON fica em [OpenAPI](http://localhost:8000/openapi.json) e a documentação alternativa em [ReDoc](http://localhost:8000/redoc). Se mudar `API_PORT`, ajuste os links.
5. Para encerrar, rode `docker compose down`. O PostgreSQL guarda os dados no volume `dados`; `down -v` também apaga esse volume.

O banco só é acessível na rede interna do Compose. A API aguarda o PostgreSQL responder antes de criar a tabela pelo SQLAlchemy. Fora do Compose, a aplicação também aceita `DATABASE_URL` no ambiente (driver PostgreSQL: `postgresql+psycopg`).

## Endpoints

| Método e caminho | Resultado | Erros previstos |
| --- | --- | --- |
| POST /pokemons | 201, novo registro com ID | 409 nome duplicado; 422 dados inválidos |
| GET /pokemons | 200, lista em ordem de ID; aceita offset e limit (1–100) | 422 paginação inválida |
| GET /pokemons/{id} | 200, registro completo | 404 ID inexistente |
| PUT /pokemons/{id} | 200, substitui os quatro atributos | 404 inexistente; 409 nome duplicado; 422 dados inválidos |
| DELETE /pokemons/{id} | 204, corpo vazio | 404 ID inexistente |

Exemplo de corpo para POST ou PUT:

```json
{"nome":"Pikachu","tipo":"Elétrico","nivel":15,"ataque":55}
```

Na criação, a resposta inclui os mesmos campos mais o ID, por exemplo `{"id":1,"nome":"Pikachu","tipo":"Elétrico","nivel":15,"ataque":55}`. Para conferir a exclusão, busque o mesmo ID: a API responde 404 com `{"detail":"Pokémon não encontrado"}`.

## Testes

Use Python 3.12 em um ambiente virtual ativado, na raiz do repositório:

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q
```

Os testes unitários exercitam as regras de entrada. Os testes HTTP usam a aplicação real e um arquivo SQLite temporário novo por cenário. Cobrem o ciclo de vida do registro, paginação, conflitos com rollback, campos inválidos e IDs inexistentes. No [GitHub Actions](../../actions), o mesmo projeto também sobe com PostgreSQL e Docker, testa a unicidade e verifica se o registro continua disponível depois que ambos os containers são recriados.

## Organização e histórico

- `app/db.py`: tabela, restrições e conexão; `app/schemas.py`: contrato de entrada e saída.
- `app/main.py`: rotas, sessões, transações e documentação.
- `tests/test_pokedex.py`: testes de modelo e endpoints.
- `Dockerfile`, `docker-compose.yml` e `.env.example`: execução em containers.
- `.github/workflows/testes.yml`: testes automatizados do projeto.

O desenvolvimento foi versionado em etapas: modelo e conexão (`20c26ba`), CRUD e OpenAPI (`7edf3d0`), testes (`a8c8201`) e infraestrutura (`a0afdcd`), seguidos desta documentação e do CI. Use `git log --oneline --reverse` para revisar o histórico completo.
