"""Comparação de cores (CIEDE2000) e nomes de cores em português."""

from __future__ import annotations

import math

__all__ = ["normalizar", "rgb", "delta_e", "nome_da_cor", "qualidade"]


def normalizar(cor: str) -> str:
    """'#ff0080', 'FF0080', '#FF0080FF' -> '#FF0080'."""
    texto = cor.strip().lstrip("#").upper()
    if len(texto) == 3:
        texto = "".join(c * 2 for c in texto)
    if len(texto) not in (6, 8) or any(c not in "0123456789ABCDEF" for c in texto):
        raise ValueError(f"cor inválida: {cor!r}")
    return "#" + texto[:6]


def rgb(cor: str) -> tuple[int, int, int]:
    texto = normalizar(cor)[1:]
    return int(texto[0:2], 16), int(texto[2:4], 16), int(texto[4:6], 16)


def _lab(cor: str) -> tuple[float, float, float]:
    def linear(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(c) for c in rgb(cor))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(cor1: str, cor2: str) -> float:
    """Diferença percebida entre duas cores (CIEDE2000). Até ~10 é parecida."""
    l1, a1, b1 = _lab(cor1)
    l2, a2, b2 = _lab(cor2)
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    c_media = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(c_media**7 / (c_media**7 + 25**7)))
    a1l, a2l = a1 * (1 + g), a2 * (1 + g)
    c1l, c2l = math.hypot(a1l, b1), math.hypot(a2l, b2)
    h1 = math.degrees(math.atan2(b1, a1l)) % 360
    h2 = math.degrees(math.atan2(b2, a2l)) % 360

    dl = l2 - l1
    dc = c2l - c1l
    if c1l * c2l == 0:
        dh = 0.0
    elif abs(h2 - h1) <= 180:
        dh = h2 - h1
    elif h2 - h1 > 180:
        dh = h2 - h1 - 360
    else:
        dh = h2 - h1 + 360
    dh_grande = 2 * math.sqrt(c1l * c2l) * math.sin(math.radians(dh / 2))

    l_media = (l1 + l2) / 2
    cl_media = (c1l + c2l) / 2
    if c1l * c2l == 0:
        h_media = h1 + h2
    elif abs(h1 - h2) <= 180:
        h_media = (h1 + h2) / 2
    elif h1 + h2 < 360:
        h_media = (h1 + h2 + 360) / 2
    else:
        h_media = (h1 + h2 - 360) / 2
    t = (
        1
        - 0.17 * math.cos(math.radians(h_media - 30))
        + 0.24 * math.cos(math.radians(2 * h_media))
        + 0.32 * math.cos(math.radians(3 * h_media + 6))
        - 0.20 * math.cos(math.radians(4 * h_media - 63))
    )
    sl = 1 + 0.015 * (l_media - 50) ** 2 / math.sqrt(20 + (l_media - 50) ** 2)
    sc = 1 + 0.045 * cl_media
    sh = 1 + 0.015 * cl_media * t
    rt = (
        -2
        * math.sqrt(cl_media**7 / (cl_media**7 + 25**7))
        * math.sin(math.radians(60 * math.exp(-(((h_media - 275) / 25) ** 2))))
    )
    return math.sqrt(
        (dl / sl) ** 2 + (dc / sc) ** 2 + (dh_grande / sh) ** 2 + rt * (dc / sc) * (dh_grande / sh)
    )


def qualidade(diferenca: float) -> str:
    if diferenca < 12:
        return "boa"
    if diferenca < 25:
        return "aproximada"
    return "ruim"


_NOMES = {
    "#FFFFFF": "branco",
    "#000000": "preto",
    "#808080": "cinza",
    "#C0C0C0": "prata",
    "#FF0000": "vermelho",
    "#8B0000": "vinho",
    "#FFA500": "laranja",
    "#FFFF00": "amarelo",
    "#FFD700": "dourado",
    "#008000": "verde",
    "#90EE90": "verde-claro",
    "#006400": "verde-escuro",
    "#0000FF": "azul",
    "#1E78C8": "azul",
    "#87CEEB": "azul-claro",
    "#000080": "azul-marinho",
    "#00FFFF": "ciano",
    "#800080": "roxo",
    "#EE82EE": "lilás",
    "#FFC0CB": "rosa",
    "#FF00FF": "magenta",
    "#8B4513": "marrom",
    "#D2B48C": "bege",
    "#F5DEB3": "pele",
}


def nome_da_cor(cor: str) -> str:
    return min(_NOMES.items(), key=lambda item: delta_e(cor, item[0]))[1]
