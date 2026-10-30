"""Repintura por "ilhas": regiões contínuas da malha com a mesma cor.

Em modelos com relevo, cada detalhe (uma folha, uma estrela, um floco) costuma ser uma
ilha separada: topo e laterais ligados entre si e cercados por outra cor. Pintar no
slicer exige pegar topo e laterais com o pincel; aqui a ilha inteira muda de uma vez.

Fluxo: `mapa_de_ilhas` desenha o objeto com o número de cada ilha; quem olha a imagem
escolhe os números; `repintar_ilhas` grava um 3MF novo com as ilhas no slot escolhido.
Os números são estáveis enquanto o arquivo não muda.
"""

from __future__ import annotations

import io
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import cores, pintura

__all__ = ["Ilha", "carregar_objetos", "mapa_de_ilhas", "repintar_ilhas", "VISTAS"]

RE_OBJETO = re.compile(r'<object\b([^>]*?)\bid="(\d+)"([^>]*)>(.*?)</object>', re.S)
RE_COMPONENTE = re.compile(r"<component\b([^>]*)/>")
RE_VERTICE = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"')
RE_TRIANGULO = re.compile(r"<triangle ([^>]*?)\s*/>")
RE_INDICES = re.compile(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"')
RE_PINTURA = re.compile(r'\s*paint_color="([0-9A-Fa-f]*)"')

# vista: (eixo horizontal, eixo vertical, profundidade (maior = mais perto), normal visível)
VISTAS = {
    "cima": (np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])),
    "baixo": (np.array([1, 0, 0]), np.array([0, -1, 0]), np.array([0, 0, -1])),
    "frente": (np.array([1, 0, 0]), np.array([0, 0, 1]), np.array([0, -1, 0])),
    "tras": (np.array([-1, 0, 0]), np.array([0, 0, 1]), np.array([0, 1, 0])),
    "esquerda": (np.array([0, -1, 0]), np.array([0, 0, 1]), np.array([-1, 0, 0])),
    "direita": (np.array([0, 1, 0]), np.array([0, 0, 1]), np.array([1, 0, 0])),
}


@dataclass
class Malha:
    arquivo: str  # entrada no zip
    id: str  # id do <object> dentro do arquivo
    v: np.ndarray  # vértices já no espaço do objeto
    t: np.ndarray
    pinturas: list[str]
    estado: np.ndarray  # filamento de cada triângulo (o predominante, se subdividido)
    subdividido: np.ndarray
    base: int  # filamento da peça (vale para triângulos sem pintura)
    soldado: np.ndarray | None = None  # índice do vértice após juntar repetidos


@dataclass
class Ilha:
    numero: int
    malha: int
    triangulos: np.ndarray
    slot: int

    def resumo(self, objeto: "Objeto", cores_slots: list[str]) -> dict:
        m = objeto.malhas[self.malha]
        p = m.v[m.t[self.triangulos]].reshape(-1, 3)
        minimo, maximo = p.min(0), p.max(0)
        cor = cores_slots[self.slot - 1] if 0 < self.slot <= len(cores_slots) else "#808080"
        return {
            "ilha": self.numero,
            "slot_atual": self.slot,
            "cor_atual": f"{cores.nome_da_cor(cor)} {cor}",
            "triangulos": int(len(self.triangulos)),
            "centro_mm": [round(float(c), 1) for c in (minimo + maximo) / 2],
            "tamanho_mm": [round(float(c), 1) for c in maximo - minimo],
            "topo_z_mm": round(float(maximo[2]), 2),
        }


@dataclass
class Objeto:
    id: str
    nome: str
    malhas: list[Malha]
    ilhas: list[Ilha] = field(default_factory=list)


def _transformacao(texto: str | None) -> np.ndarray:
    m = np.eye(4)
    if texto:
        n = [float(x) for x in texto.split()]
        if len(n) == 12:
            m[:3, :3] = np.array(n[:9]).reshape(3, 3)
            m[3, :3] = n[9:]
    return m


def _ler_malha(arquivo: str, id_: str, corpo: str, matriz: np.ndarray, base: int) -> Malha | None:
    if "<mesh" not in corpo:
        return None
    v = np.array([[float(a), float(b), float(c)] for a, b, c in RE_VERTICE.findall(corpo)])
    tris, pinturas = [], []
    for attrs in RE_TRIANGULO.findall(corpo):
        i = RE_INDICES.search(attrs)
        tris.append((int(i.group(1)), int(i.group(2)), int(i.group(3))))
        p = RE_PINTURA.search(attrs)
        pinturas.append(p.group(1).upper() if p else "")
    t = np.array(tris, dtype=np.int64).reshape(-1, 3)
    estado = np.zeros(len(t), dtype=np.int64)
    subdividido = np.zeros(len(t), dtype=bool)
    cache: dict[str, tuple[int, bool]] = {}
    for i, texto in enumerate(pinturas):
        if not texto:
            estado[i] = base
            continue
        if texto not in cache:
            folhas = pintura.estados(texto)
            dominante = max(folhas.items(), key=lambda kv: kv[1])[0]
            cache[texto] = (dominante or base, len(folhas) > 1 or sum(folhas.values()) > 1)
        estado[i], subdividido[i] = cache[texto]
    v = (np.c_[v, np.ones(len(v))] @ matriz)[:, :3] if len(v) else v
    return Malha(arquivo, id_, v, t, pinturas, estado, subdividido, base)


def _extrusores(model_settings: str) -> dict[str, tuple[int, dict[str, int]]]:
    """id do objeto -> (filamento do objeto, {id da peça: filamento da peça})"""
    resultado = {}
    for bloco in re.findall(r"<object\b.*?</object>", model_settings, re.S):
        obj = re.search(r'<object id="(\d+)"', bloco).group(1)
        cabeca = bloco.split("<part", 1)[0]
        padrao = re.search(r'key="extruder" value="(\d+)"', cabeca)
        base = int(padrao.group(1)) if padrao else 1
        pecas = {}
        for parte in re.findall(r"<part\b.*?</part>", bloco, re.S):
            pid = re.search(r'<part id="(\d+)"', parte).group(1)
            ext = re.search(r'key="extruder" value="(\d+)"', parte)
            pecas[pid] = int(ext.group(1)) if ext and int(ext.group(1)) > 0 else base
        resultado[obj] = (base or 1, pecas)
    return resultado


_CACHE: dict[tuple, tuple[list[Objeto], list[str]]] = {}


def carregar_objetos(caminho: str | Path) -> tuple[list[Objeto], list[str]]:
    """Lê os objetos do projeto (com as peças posicionadas) e as cores dos slots.

    Guarda os dois últimos arquivos lidos: o mapa e a repintura costumam vir em seguida.
    """
    caminho = Path(caminho).resolve()
    estado = caminho.stat()
    chave = (str(caminho), estado.st_mtime_ns, estado.st_size)
    if chave not in _CACHE:
        while len(_CACHE) >= 2:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[chave] = _carregar_objetos(caminho)
    return _CACHE[chave]


def _carregar_objetos(caminho: Path) -> tuple[list[Objeto], list[str]]:
    import json

    with zipfile.ZipFile(caminho) as z:
        nomes = z.namelist()
        principal = z.read("3D/3dmodel.model").decode("utf8")
        ms = z.read("Metadata/model_settings.config").decode("utf8") if "Metadata/model_settings.config" in nomes else ""
        config = json.loads(z.read("Metadata/project_settings.config")) if "Metadata/project_settings.config" in nomes else {}
        cores_slots = [cores.normalizar(c) for c in config.get("filament_colour") or ["#FFFFFF"]]
        extrusores = _extrusores(ms)
        nomes_obj = {o: n for o, n in re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]*)"', ms)}
        corpos: dict[str, dict[str, str]] = {}  # arquivo -> {id do objeto: corpo}
        construidos = {m.group(1) for m in re.finditer(r'<item\b[^>]*?objectid="(\d+)"', principal)}
        objetos = []
        for _, id_, _, corpo in RE_OBJETO.findall(principal):
            if id_ not in construidos:
                continue
            base, pecas = extrusores.get(id_, (1, {}))
            malhas = []
            if "<components" in corpo:
                for attrs in RE_COMPONENTE.findall(corpo):
                    caminho_malha = re.search(r'p:path="/?([^"]+)"', attrs)
                    alvo = re.search(r'objectid="(\d+)"', attrs).group(1)
                    transf = re.search(r'transform="([^"]+)"', attrs)
                    arquivo = caminho_malha.group(1) if caminho_malha else "3D/3dmodel.model"
                    if arquivo not in corpos:
                        texto = principal if arquivo == "3D/3dmodel.model" else z.read(arquivo).decode("utf8")
                        corpos[arquivo] = {i: c for _, i, _, c in RE_OBJETO.findall(texto)}
                    if alvo in corpos[arquivo]:
                        m = _ler_malha(arquivo, alvo, corpos[arquivo][alvo],
                                       _transformacao(transf.group(1) if transf else None),
                                       pecas.get(alvo, base))
                        if m is not None:
                            malhas.append(m)
            else:
                m = _ler_malha("3D/3dmodel.model", id_, corpo, np.eye(4), base)
                if m is not None:
                    malhas.append(m)
            if malhas:
                objetos.append(Objeto(id_, nomes_obj.get(id_, f"objeto {id_}"), malhas))
    for objeto in objetos:
        objeto.ilhas = _ilhas(objeto)
    return objetos, cores_slots


def _ilhas(objeto: Objeto) -> list[Ilha]:
    brutas = []
    for indice, m in enumerate(objeto.malhas):
        if not len(m.t):
            continue
        # solda vértices repetidos (malhas vindas de STL)
        _, soldado = np.unique(np.round(m.v * 1e4).astype(np.int64), axis=0, return_inverse=True)
        soldado = soldado.reshape(-1)
        m.soldado = soldado
        n_vert = soldado.max() + 1
        no = soldado[m.t] + m.estado[:, None] * n_vert  # vértice separado por cor
        pai = list(range(int(no.max()) + 1))

        def raiz(a: int) -> int:
            while pai[a] != a:
                pai[a] = pai[pai[a]]
                a = pai[a]
            return a

        for a, b, c in no.tolist():
            ra = raiz(a)
            rb = raiz(b)
            if rb != ra:
                pai[rb] = ra
            rc = raiz(c)
            if rc != ra:
                pai[rc] = ra
        raizes = np.array([raiz(a) for a in no[:, 0].tolist()])
        for r in np.unique(raizes):
            tris = np.nonzero(raizes == r)[0]
            brutas.append((indice, tris, int(m.estado[tris[0]])))
    # ordem estável: maiores primeiro, depois posição
    def chave(item):
        indice, tris, _ = item
        centro = objeto.malhas[indice].v[objeto.malhas[indice].t[tris]].reshape(-1, 3).mean(0)
        return (-len(tris), indice, round(float(centro[0]), 2), round(float(centro[1]), 2), round(float(centro[2]), 2))

    brutas.sort(key=chave)
    return [Ilha(i + 1, indice, tris, slot) for i, (indice, tris, slot) in enumerate(brutas)]


def _rgb(cor: str) -> tuple[int, int, int]:
    return cores.rgb(cor)


def _desenhar(objeto: Objeto, cores_slots: list[str], vista: str, regiao: list[float] | None,
              largura: int, rotulos: bool, mudancas: dict[int, int] | None = None):
    eixo_x, eixo_y, eixo_z = VISTAS[vista]
    paleta = np.array([_rgb(c) for c in cores_slots] + [(128, 128, 128)], float)
    tris, numeros, slots = [], [], []
    for ilha in objeto.ilhas:
        m = objeto.malhas[ilha.malha]
        tris.append(m.v[m.t[ilha.triangulos]])
        numeros.append(np.full(len(ilha.triangulos), ilha.numero))
        slot = (mudancas or {}).get(ilha.numero, ilha.slot)
        slots.append(np.full(len(ilha.triangulos), slot if 0 < slot <= len(cores_slots) else len(paleta)))
    tri, numero, slot = np.concatenate(tris), np.concatenate(numeros), np.concatenate(slots)
    normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normal /= np.linalg.norm(normal, axis=1)[:, None] + 1e-12
    luz = normal @ eixo_z
    visivel = luz > 1e-3
    if not visivel.any():
        raise ValueError(f"nada visível na vista {vista}")
    tri, numero, luz = tri[visivel], numero[visivel], luz[visivel]
    cor = (paleta[slot[visivel] - 1] * (0.6 + 0.4 * luz)[:, None]).astype(int)
    ordem = np.argsort(tri.mean(1) @ eixo_z)  # mais longe primeiro
    plano = tri[ordem] @ np.c_[eixo_x, eixo_y]  # (n, 3, 2)
    cor, numero = cor[ordem], numero[ordem]
    x0, y0 = plano.reshape(-1, 2).min(0)
    x1, y1 = plano.reshape(-1, 2).max(0)
    if regiao:
        x0, y0, x1, y1 = regiao
    margem = 0.03 * max(x1 - x0, y1 - y0)
    x0, y0, x1, y1 = x0 - margem, y0 - margem, x1 + margem, y1 + margem
    escala = largura / (x1 - x0)
    altura = max(int((y1 - y0) * escala), 1)

    tela = np.empty_like(plano)
    tela[..., 0] = (plano[..., 0] - x0) * escala
    tela[..., 1] = (y1 - plano[..., 1]) * escala
    dentro = ((tela[..., 0].max(1) >= 0) & (tela[..., 0].min(1) <= largura)
              & (tela[..., 1].max(1) >= 0) & (tela[..., 1].min(1) <= altura))

    imagem = Image.new("RGB", (largura, altura), (58, 58, 68))
    ids = Image.new("I", (largura, altura), 0)
    d, di = ImageDraw.Draw(imagem), ImageDraw.Draw(ids)
    for pontos, c, n in zip(tela[dentro].tolist(), cor[dentro].tolist(), numero[dentro].tolist()):
        xy = [tuple(p) for p in pontos]
        d.polygon(xy, fill=tuple(c))
        di.polygon(xy, fill=n)

    area: dict[int, int] = {}
    if rotulos:
        mapa = np.array(ids)
        borda = np.zeros_like(mapa, dtype=bool)
        borda[:-1] |= mapa[:-1] != mapa[1:]
        borda[:, :-1] |= mapa[:, :-1] != mapa[:, 1:]
        pixels = np.array(imagem)
        pixels[borda] = (pixels[borda] * 0.35).astype(np.uint8)
        imagem = Image.fromarray(pixels)
        d = ImageDraw.Draw(imagem)
        try:
            fonte = ImageFont.truetype("arial.ttf", max(11, largura // 90))
        except OSError:
            fonte = ImageFont.load_default()
        valores, contagem = np.unique(mapa[mapa > 0], return_counts=True)
        minimo = max(12, (largura * altura) // 40000)
        for numero, qtd in sorted(zip(valores.tolist(), contagem.tolist()), key=lambda x: -x[1])[:250]:
            if qtd < minimo:
                continue
            area[numero] = qtd
            ys, xs = np.nonzero(mapa == numero)
            cx, cy = xs.mean(), ys.mean()
            k = np.argmin((xs - cx) ** 2 + (ys - cy) ** 2)  # ponto da própria ilha mais perto do centro
            d.text((int(xs[k]), int(ys[k])), str(numero), fill=(255, 255, 0), font=fonte,
                   anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    return imagem, area


def _png(imagem: Image.Image) -> bytes:
    saida = io.BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()


def _escolher(objetos: list[Objeto], objeto: str | None) -> Objeto:
    if objeto is None:
        return max(objetos, key=lambda o: sum(len(m.t) for m in o.malhas))
    for o in objetos:
        if o.id == str(objeto):
            return o
    raise ValueError(f"objeto {objeto} não existe; objetos: {[o.id for o in objetos]}")


def mapa_de_ilhas(caminho: str | Path, objeto: str | None = None, vista: str = "cima",
                  regiao: list[float] | None = None, largura: int = 1400, rotulos: bool = True) -> tuple[bytes, dict]:
    """Desenha o objeto com o número de cada ilha visível. Devolve (png, informações)."""
    if vista not in VISTAS:
        raise ValueError(f"vista deve ser uma de {list(VISTAS)}")
    objetos, cores_slots = carregar_objetos(caminho)
    alvo = _escolher(objetos, objeto)
    imagem, area = _desenhar(alvo, cores_slots, vista, regiao, largura, rotulos)
    por_numero = {i.numero: i for i in alvo.ilhas}
    info = {
        "objeto": alvo.id,
        "nome": alvo.nome,
        "outros_objetos": [{"objeto": o.id, "nome": o.nome} for o in objetos if o is not alvo],
        "slots": [{"slot": i + 1, "cor": f"{cores.nome_da_cor(c)} {c}"} for i, c in enumerate(cores_slots)],
        "vista": vista,
        "total_de_ilhas": len(alvo.ilhas),
        "ilhas_rotuladas": [por_numero[n].resumo(alvo, cores_slots) | {"pixels_visiveis": a}
                            for n, a in sorted(area.items())],
    }
    return _png(imagem), info


def repintar_ilhas(caminho: str | Path, mudancas: dict[int, int], objeto: str | None = None,
                   saida: str | Path | None = None) -> dict:
    """Grava um 3MF novo com as ilhas indicadas no slot escolhido ({ilha: slot})."""
    caminho = Path(caminho)
    objetos, cores_slots = carregar_objetos(caminho)
    alvo = _escolher(objetos, objeto)
    por_numero = {i.numero: i for i in alvo.ilhas}
    mudancas = {int(k): int(v) for k, v in mudancas.items()}
    for numero, slot in mudancas.items():
        if numero not in por_numero:
            raise ValueError(f"a ilha {numero} não existe (o objeto tem {len(alvo.ilhas)})")
        if not 1 <= slot <= len(cores_slots):
            raise ValueError(f"slot {slot} não existe (o projeto tem {len(cores_slots)})")
    if saida is None:
        saida = caminho.with_name(f"{caminho.stem}_repintado.3mf")
        n = 2
        while Path(saida).exists():
            saida = caminho.with_name(f"{caminho.stem}_repintado_{n}.3mf")
            n += 1
    saida = Path(saida)
    if saida.exists():
        raise ValueError(f"{saida} já existe; escolha outro nome")

    # (arquivo, id da malha) -> {triângulo: novo texto de pintura}
    trocas: dict[tuple[str, str], dict[int, str]] = {}
    resumo = Counter()
    for numero, slot in mudancas.items():
        ilha = por_numero[numero]
        m = alvo.malhas[ilha.malha]
        destino = trocas.setdefault((m.arquivo, m.id), {})
        mapa = {ilha.slot: slot}
        if ilha.slot == m.base:
            mapa[0] = slot

        def parcial(i: int) -> str:
            # só as partes da cor da ilha mudam; detalhes de outras cores ficam
            texto = destino.get(i, m.pinturas[i])
            nos = [(tipo, mapa.get(valor, valor) if tipo == "folha" else valor)
                   for tipo, valor in pintura.decodificar(texto)]
            return pintura.codificar(nos)

        for i in ilha.triangulos.tolist():
            destino[i] = parcial(i) if m.subdividido[i] else pintura.codificar([("folha", slot)])
        # triângulos mistos da borda que caíram em outra ilha mas têm um pedaço desta
        vertices = np.unique(m.soldado[m.t[ilha.triangulos]])
        mistos = np.nonzero(m.subdividido)[0]
        mistos = mistos[np.isin(m.soldado[m.t[mistos]], vertices).any(1)]
        na_ilha = set(ilha.triangulos.tolist())
        borda = 0
        for i in mistos.tolist():
            if i not in na_ilha and (ilha.slot in pintura.estados(m.pinturas[i])
                                     or (ilha.slot == m.base and 0 in pintura.estados(m.pinturas[i]))):
                destino[i] = parcial(i)
                borda += 1
        resumo[f"ilha {numero}: slot {ilha.slot} -> {slot}"] = len(ilha.triangulos) + borda

    arquivos = {a for a, _ in trocas}
    temporario = saida.with_suffix(".tmp")
    with zipfile.ZipFile(caminho) as entrada, zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED) as zsaida:
        for info in entrada.infolist():
            dados = entrada.read(info.filename)
            if info.filename in arquivos:
                texto = dados.decode("utf8")

                def objeto_novo(mo: re.Match) -> str:
                    alteracoes = trocas.get((info.filename, mo.group(2)))
                    if not alteracoes:
                        return mo.group(0)
                    contador = iter(range(1 << 62))

                    def triangulo(mt: re.Match) -> str:
                        i = next(contador)
                        if i not in alteracoes:
                            return mt.group(0)
                        attrs = RE_PINTURA.sub("", mt.group(1)).rstrip()
                        return f'<triangle {attrs} paint_color="{alteracoes[i]}"/>'

                    corpo = RE_TRIANGULO.sub(triangulo, mo.group(4))
                    return f"<object{mo.group(1)}id=\"{mo.group(2)}\"{mo.group(3)}>{corpo}</object>"

                dados = RE_OBJETO.sub(objeto_novo, texto).encode("utf8")
            zsaida.writestr(info, dados, compress_type=zipfile.ZIP_DEFLATED)
    temporario.replace(saida)
    return {"arquivo_repintado": str(saida), "objeto": alvo.id,
            "mudancas": [{"mudanca": k, "triangulos": v} for k, v in resumo.items()]}
