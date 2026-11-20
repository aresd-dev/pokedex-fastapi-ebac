from pydantic import BaseModel, ConfigDict, Field


class PokemonEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nome: str = Field(min_length=1, max_length=60, examples=["Pikachu"])
    tipo: str = Field(min_length=1, max_length=40, examples=["Elétrico"])
    nivel: int = Field(strict=True, ge=1, le=100, examples=[15])
    ataque: int = Field(strict=True, ge=1, le=255, examples=[55])


class PokemonSaida(PokemonEntrada):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(examples=[1])


class Erro(BaseModel):
    detail: str
