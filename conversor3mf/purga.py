"""Purga por par de cores (tabela "de -> para" do slicer).

A cada troca de cor o bico precisa expulsar o filamento anterior. Pouca purga deixa a
cor velha manchar a nova; purga demais desperdiça filamento. O quanto é preciso depende
do par: preto -> branco precisa de muito mais que branco -> preto.

O slicer guarda isso em `flush_volumes_matrix` (linha = cor de origem, coluna = destino,
em mm³). Na Kobra X o firmware lê essa tabela do cabeçalho do G-code e faz a purga ele
mesmo; a purga real é o valor da tabela × `flush_multiplier`.

Valor de cada par, nesta ordem:
1. o que o próprio Anycubic Slicer Next calculou para esse par em algum projeto salvo
   (aprendido do molde e de `aprender`), porque ele usa dados medidos para as cores oficiais;
2. senão, a fórmula do OrcaSlicer (FlushVolCalc) + o volume do bico.
Depois entram os ajustes de calibração do usuário: um fator por par e um fator geral.
"""

from __future__ import annotations

import colorsys
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

from . import cores
from .config import pasta_dados

__all__ = ["formula_orca", "calcular_matriz", "aprender", "ajustar_par", "definir_nivel",
           "carregar", "relatorio", "aplicar_no_config", "aplicar_em_arquivo", "NIVEIS"]

ARQUIVO = "purga.json"
NIVEIS = {"economia": 0.85, "normal": 1.0, "caprichado": 1.25}
APELIDOS_NIVEL = {"economy": "economia", "economía": "economia", "thorough": "caprichado",
                  "esmerado": "caprichado"}
MAIS = {"mais", "more", "más", "mas", "+"}
MENOS = {"menos", "less", "-"}
PASSO = 0.2  # cada "mais"/"menos" muda o par em 20%
LIMITES = (0.4, 3.0)
DENSIDADE_PLA = 1.24  # g/cm³, só para estimar gramas


def _par(de: str, para: str) -> str:
    return f"{cores.normalizar(de)}>{cores.normalizar(para)}"


def formula_orca(de: str, para: str) -> float:
    """Purga sugerida pelo OrcaSlicer (FlushVolCalc::calc_flush_vol_rgb), sem o volume do bico."""
    r1, g1, b1 = (c / 255 for c in cores.rgb(de))
    r2, g2, b2 = (c / 255 for c in cores.rgb(para))
    h1, s1, v1 = colorsys.rgb_to_hsv(r1, g1, b1)
    h2, s2, v2 = colorsys.rgb_to_hsv(r2, g2, b2)

    def ponto(h, s, v):
        return math.cos(2 * math.pi * h) * s * v, math.sin(2 * math.pi * h) * s * v

    hs = min(1.2, math.dist(ponto(h1, s1, v1), ponto(h2, s2, v2)))
    luz_de = 0.3 * r1 + 0.59 * g1 + 0.11 * b1
    luz_para = 0.3 * r2 + 0.59 * g2 + 0.11 * b2
    if luz_para >= luz_de:
        purga_luz = (luz_para - luz_de) ** 0.7 * 560
    else:
        purga_luz = (luz_de - luz_para) * 80
        hs = min(0.67 * v2 + 0.33 * v1, hs)
    purga_hs = 230 * hs
    # lei dos cossenos com 120°: sqrt(a² + b² + ab)
    return max(math.sqrt(purga_hs**2 + purga_luz**2 + purga_hs * purga_luz), 60)


def carregar() -> dict:
    caminho = pasta_dados() / ARQUIVO
    dados = json.loads(caminho.read_text(encoding="utf8")) if caminho.exists() else {}
    return {"base": dados.get("base", {}), "ajustes": dados.get("ajustes", {}), "geral": dados.get("geral", 1.0)}


def _salvar(dados: dict) -> None:
    pasta_dados().mkdir(parents=True, exist_ok=True)
    texto = {
        "_leia_me": "base: purga (mm³) que o Anycubic Slicer Next calculou para cada par 'de>para'. "
        "ajustes: fator de calibração por par. geral: fator para todos os pares.",
        **dados,
    }
    (pasta_dados() / ARQUIVO).write_text(json.dumps(texto, indent=2, ensure_ascii=False), encoding="utf8")


def aprender(projetos: list[str | Path]) -> int:
    """Guarda os pares que o Anycubic Slicer Next calculou em projetos salvos por ele.

    Aceita arquivos .3mf ou pastas. Só lê projetos gravados pelo próprio slicer (não os
    gerados por este conversor). Para cada par fica o valor mais frequente.
    Devolve quantos pares foram aprendidos.
    """
    dados = carregar()
    vistos: dict[str, Counter] = {}
    arquivos: list[Path] = []
    for p in map(Path, projetos):
        arquivos += sorted(p.glob("*.3mf")) if p.is_dir() else [p]
    for arquivo in arquivos:
        try:
            with zipfile.ZipFile(arquivo) as z:
                config = json.loads(z.read("Metadata/project_settings.config"))
                assinatura = z.read("Metadata/slice_info.config").decode("utf8", "replace")
        except (OSError, KeyError, ValueError, zipfile.BadZipFile):
            continue
        if ("X-ACNext" not in assinatura or "X-Conversor3mf" in assinatura
                or not str(config.get("printer_model", "")).startswith("Anycubic")):
            continue  # só projetos gravados pelo próprio Anycubic Slicer Next
        lista = config.get("filament_colour") or []
        matriz = config.get("flush_volumes_matrix") or []
        n = len(lista)
        if n < 2 or len(matriz) != n * n:
            continue
        for i in range(n):
            for j in range(n):
                if i != j and float(matriz[i * n + j]) > 0:
                    vistos.setdefault(_par(lista[i], lista[j]), Counter())[round(float(matriz[i * n + j]))] += 1
    for chave, contagem in vistos.items():
        dados["base"][chave] = contagem.most_common(1)[0][0]
    _salvar(dados)
    return len(vistos)


def _valor(de: str, para: str, dados: dict, volume_bico: float) -> tuple[float, str]:
    chave = _par(de, para)
    if chave in dados["base"]:
        base, origem = float(dados["base"][chave]), "slicer"
    else:
        base, origem = formula_orca(de, para) + volume_bico, "formula"
    return base * dados["ajustes"].get(chave, 1.0) * dados["geral"], origem


def calcular_matriz(lista_cores: list[str], volume_bico: float = 79.0) -> list[str]:
    dados = carregar()
    n = len(lista_cores)
    return [
        "0" if i == j else str(round(_valor(lista_cores[i], lista_cores[j], dados, volume_bico)[0]))
        for i in range(n) for j in range(n)
    ]


def _volume_bico(config: dict) -> float:
    try:
        return float((config.get("nozzle_volume") or ["79"])[0])
    except (TypeError, ValueError):
        return 79.0


def aplicar_no_config(config: dict) -> None:
    """Recalcula a tabela de purga do config para as cores dos filamentos dele."""
    lista = [cores.normalizar(c) for c in config.get("filament_colour") or []]
    if len(lista) >= 2:
        config["flush_volumes_matrix"] = calcular_matriz(lista, _volume_bico(config))


def _resolver(cor_ou_slot: str | int, lista_cores: list[str]) -> str:
    texto = str(cor_ou_slot).strip()
    if texto.isdigit():
        indice = int(texto)
        if not 1 <= indice <= len(lista_cores):
            raise ValueError(f"slot {indice} não existe (há {len(lista_cores)})")
        return lista_cores[indice - 1]
    return cores.normalizar(texto)


def ajustar_par(de: str | int, para: str | int, mudanca: str | float, lista_cores: list[str]) -> dict:
    """Aumenta/diminui a purga de um par. de/para: número do slot ou cor (#RRGGBB).

    mudanca: "mais" (+20%), "menos" (-20%) ou um fator (ex.: 1.5).
    """
    cor_de, cor_para = _resolver(de, lista_cores), _resolver(para, lista_cores)
    if cor_de == cor_para:
        raise ValueError("origem e destino são a mesma cor")
    dados = carregar()
    chave = _par(cor_de, cor_para)
    atual = dados["ajustes"].get(chave, 1.0)
    texto = str(mudanca).strip().lower()
    if texto in MAIS:
        novo = atual * (1 + PASSO)
    elif texto in MENOS:
        novo = atual * (1 - PASSO)
    else:
        novo = float(texto.replace(",", "."))
    dados["ajustes"][chave] = round(min(max(novo, LIMITES[0]), LIMITES[1]), 3)
    _salvar(dados)
    return {"par": chave, "fator_antes": atual, "fator_agora": dados["ajustes"][chave]}


def definir_nivel(nivel: str | float) -> float:
    """Fator geral: economia, normal, caprichado ou um número."""
    dados = carregar()
    texto = str(nivel).strip().lower()
    texto = APELIDOS_NIVEL.get(texto, texto)
    dados["geral"] = NIVEIS[texto] if texto in NIVEIS else float(texto.replace(",", "."))
    _salvar(dados)
    return dados["geral"]


def relatorio(lista_cores: list[str], multiplicador: float = 0.7, volume_bico: float = 79.0) -> dict:
    """Tabela legível: quanto cada troca purga de fato (mm³ e gramas aproximados)."""
    dados = carregar()
    trocas = []
    for i, de in enumerate(lista_cores):
        for j, para in enumerate(lista_cores):
            if i == j:
                continue
            valor, origem = _valor(de, para, dados, volume_bico)
            real = valor * multiplicador
            trocas.append({
                "de": f"slot {i + 1} ({cores.nome_da_cor(de)} {de})",
                "para": f"slot {j + 1} ({cores.nome_da_cor(para)} {para})",
                "tabela_mm3": round(valor),
                "purga_real_mm3": round(real),
                "gramas_por_troca": round(real / 1000 * DENSIDADE_PLA, 2),
                "origem": origem,
                "ajuste": dados["ajustes"].get(_par(de, para), 1.0),
            })
    return {"fator_geral": dados["geral"], "multiplicador_do_slicer": multiplicador, "trocas": trocas}


def aplicar_em_arquivo(arquivo: str | Path, saida: str | Path | None = None) -> dict:
    """Grava uma cópia do projeto com a tabela de purga recalculada (calibração atual)."""
    arquivo = Path(arquivo)
    if saida is None:
        saida = arquivo.with_name(f"{arquivo.stem}_purga.3mf")
        n = 2
        while Path(saida).exists():
            saida = arquivo.with_name(f"{arquivo.stem}_purga_{n}.3mf")
            n += 1
    saida = Path(saida)
    if saida.exists():
        raise ValueError(f"{saida} já existe; escolha outro nome")
    with zipfile.ZipFile(arquivo) as entrada:
        config = json.loads(entrada.read("Metadata/project_settings.config"))
        antes = list(config.get("flush_volumes_matrix") or [])
        aplicar_no_config(config)
        temporario = saida.with_suffix(".tmp")
        with zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED) as zsaida:
            for info in entrada.infolist():
                dados = entrada.read(info.filename)
                if info.filename == "Metadata/project_settings.config":
                    dados = json.dumps(config, indent=4, ensure_ascii=False).encode("utf8")
                zsaida.writestr(info, dados, compress_type=zipfile.ZIP_DEFLATED)
    temporario.replace(saida)
    lista = [cores.normalizar(c) for c in config.get("filament_colour") or []]
    return {
        "arquivo": str(saida),
        "tabela_antes": antes,
        "tabela_agora": config.get("flush_volumes_matrix"),
        **relatorio(lista, float(config.get("flush_multiplier", 0.7)), _volume_bico(config)),
    }
