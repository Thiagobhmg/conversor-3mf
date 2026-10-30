"""Leitura e reescrita da pintura multicolor (atributo paint_color dos triângulos).

Formato usado pelo Bambu Studio, OrcaSlicer e Anycubic Slicer Next: cada triângulo
pintado guarda uma árvore de subdivisões serializada como string hexadecimal.
A string é lida do último caractere para o primeiro, e cada dígito vira um "nibble"
de 4 bits. Cada nó da árvore começa com um nibble de código:

- bits 0-1: quantos lados foram divididos (0 = folha, 1-3 = nó com 2-4 filhos)
- bits 2-3: num nó dividido, o "lado especial"; numa folha, o estado (0-2),
  ou 3 = estado estendido: o próximo nibble + 3 (e se esse nibble for 15,
  o nibble seguinte + 18)

O estado de uma folha é o número do filamento (1, 2, 3...); 0 significa
"usa o filamento da peça".
"""

from __future__ import annotations

from collections import Counter

__all__ = ["decodificar", "codificar", "estados", "remapear", "PinturaInvalida"]


class PinturaInvalida(ValueError):
    pass


def _nibbles(texto: str) -> list[int]:
    try:
        return [int(c, 16) for c in reversed(texto)]
    except ValueError as erro:
        raise PinturaInvalida(f"caractere inválido em {texto!r}") from erro


def decodificar(texto: str) -> list:
    """Converte a string em uma lista de nós: ("folha", estado) ou ("divisao", codigo)."""
    dados = _nibbles(texto)
    nos: list = []
    pos = 0
    pendentes = 1  # nós que ainda faltam ler
    while pendentes:
        if pos >= len(dados):
            raise PinturaInvalida(f"string terminou antes da hora: {texto!r}")
        codigo = dados[pos]
        pos += 1
        pendentes -= 1
        lados = codigo & 0b11
        if lados:
            nos.append(("divisao", codigo))
            pendentes += lados + 1
            continue
        estado = codigo >> 2
        if estado == 3:
            if pos >= len(dados):
                raise PinturaInvalida(f"estado estendido incompleto: {texto!r}")
            extra = dados[pos]
            pos += 1
            if extra == 0b1111:
                if pos >= len(dados):
                    raise PinturaInvalida(f"estado estendido incompleto: {texto!r}")
                estado = dados[pos] + 18
                pos += 1
            else:
                estado = extra + 3
        nos.append(("folha", estado))
    if any(dados[pos:]):
        raise PinturaInvalida(f"sobraram dados no fim: {texto!r}")
    return nos


def codificar(nos: list) -> str:
    dados: list[int] = []
    for tipo, valor in nos:
        if tipo == "divisao":
            dados.append(valor)
        elif valor < 3:
            dados.append(valor << 2)
        elif valor < 18:
            dados += [0b1100, valor - 3]
        else:
            dados += [0b1100, 0b1111, valor - 18]
    return "".join("0123456789ABCDEF"[n] for n in reversed(dados))


def estados(texto: str) -> Counter:
    """Quantas folhas de cada estado (filamento) existem na string."""
    return Counter(valor for tipo, valor in decodificar(texto) if tipo == "folha")


def remapear(texto: str, mapa: dict[int, int]) -> str:
    """Troca os números de filamento das folhas segundo `mapa` (estado 0 fica 0)."""
    nos = [
        (tipo, mapa.get(valor, valor) if tipo == "folha" and valor else valor)
        for tipo, valor in decodificar(texto)
    ]
    return codificar(nos)
