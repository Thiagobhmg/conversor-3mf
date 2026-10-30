# conversor3mf

[![testes](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml/badge.svg)](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml)

**Imprime modelos multicolor de MakerWorld en una Anycubic Kobra X sin volver a colorear nada.**
[English](README.md) · [Português](README.pt-BR.md)

La mayoría de los 3MF multicolor de MakerWorld están hechos para impresoras Bambu Lab. Al
abrirlos en Anycubic Slicer Next, los colores entran en el orden de filamentos del archivo,
no en el orden de los carretes de tu ACE. Después de sincronizar el ACE, quedan cambiados.
Con los modelos pintados es peor: el menú del objeto muestra un solo color y terminas
repintando a mano.

conversor3mf reescribe el proyecto para que **cada color del modelo vaya a la ranura del ACE
donde ya está ese carrete**. También incluye un servidor MCP, así que puedes pedirle a Claude
que lo haga por ti.

> Proyecto independiente, sin relación con Anycubic ni Bambu Lab. Las marcas pertenecen a
> sus dueños. Respeta la licencia de cada modelo: la herramienta solo convierte archivos que
> descargaste para tu propio uso y no redistribuye nada.

## Qué hace

- **Reordena los colores.** Reescribe la pintura de cada triángulo, el filamento de cada
  pieza y los cambios de filamento por capa al orden de tus ranuras. Elige el color más
  parecido (CIEDE2000) y junta los colores repetidos.
- **Abre como proyecto nativo de la Kobra X.** Sin el diálogo "Printer parameter switching"
  y sin cargar solo la geometría.
- **Mantiene las decisiones del diseñador.** Altura de capa, paredes, relleno, soportes,
  borde, planchado y fuzzy skin. Las velocidades y temperaturas vienen del perfil de fábrica
  de la Kobra X.
- **Centra las placas.** Las piezas de cada placa quedan centradas en la cama de 260 mm.
- **Te avisa.** Señala colores sin un carrete parecido, más colores que ranuras y mezclas de
  PLA y PETG.
- **Repinta regiones enteras ("islas").** Por ejemplo, todas las hojas de acebo en verde o
  todas las estrellas en rojo, incluidas las paredes laterales de los relieves, sin usar el
  pincel.
- **Nunca sobrescribe nada.** Guarda `<nombre>_KobraX.3mf` junto al original.

## Requisitos

- Windows con **Anycubic Slicer Next** instalado. Se detecta solo; si no, define
  `CONVERSOR3MF_SLICER` con su carpeta.
- **Python 3.10 o superior**.
- Una **Kobra X** con ACE. Otras impresoras Anycubic pueden funcionar, pero no están
  probadas (ver [Limitaciones](#limitaciones)).

## Instalación

```bash
pip install conversor3mf
```

### Con Claude (MCP)

```bash
claude mcp add conversor3mf --scope user -- conversor3mf-mcp
```

Si usas [uv](https://docs.astral.sh/uv/), puedes saltarte el `pip install`:
`claude mcp add conversor3mf --scope user -- uvx --from conversor3mf conversor3mf-mcp`

Después, solo pídelo:

> "Convierte C:\Descargas\posavasos.3mf para mi Kobra X"
>
> "Cambié la ranura 4 por un PLA amarillo"
>
> "En el posavasos, pon las hojas de acebo en verde y las estrellas en rojo"

Claude muestra a qué ranura irá cada color antes de convertir. Para repintar, mira un mapa
numerado del modelo.

## Primera configuración: dile qué hay en tu ACE

1. En Anycubic Slicer Next, elige la Kobra X, sincroniza el ACE y guarda cualquier proyecto.
2. Ejecuta este comando, o pídele a Claude "configura mi ACE con ese proyecto":

   ```bash
   conversor3mf ace configurar "C:\ruta\al\proyecto_guardado.3mf"
   ```

Esto guarda el perfil de la impresora y el color y material de cada ranura. Si solo cambias
el color de un carrete, actualízalo así:

```bash
conversor3mf ace ranura 4 --color "#FFD700" --tipo PLA
```

Para un material que todavía no está en ninguna ranura (ABS, TPU…), guarda un proyecto nuevo
con él y vuelve a ejecutar `ace configurar`.

Tus datos se guardan en `%APPDATA%\conversor3mf`. Puedes cambiarlo con `CONVERSOR3MF_DADOS`.

## Línea de comandos

```bash
conversor3mf planificar modelo.3mf                    # muestra a qué ranura va cada color
conversor3mf convertir  modelo.3mf --mapa 1=3         # convierte; fuerza el filamento 1 en la ranura 3
conversor3mf islas      modelo_KobraX.3mf --vista arriba  # mapa numerado de regiones de color
conversor3mf repintar   modelo_KobraX.3mf 32=4,3=3    # repinta las islas 32 y 3
conversor3mf verificar  modelo_KobraX.3mf             # reabre en Anycubic Slicer Next y compara
```

Todos los comandos y opciones también funcionan en **portugués e inglés**: usa lo que te
resulte más natural. La ayuda y los mensajes de error salen en el idioma en que escribes el
comando, o en el del sistema:

| Español | English | Português |
|---|---|---|
| `inspeccionar` | `inspect` | `inspecionar` |
| `planificar` | `plan` | `planejar` |
| `convertir` | `convert` | `converter` |
| `verificar` | `verify` | `verificar` |
| `islas` | `islands` | `ilhas` |
| `repintar` | `repaint` | `repintar` |
| `ace mostrar` / `configurar` / `ranura` | `ace show` / `setup` / `slot` | `ace mostrar` / `definir` / `slot` |
| `--mapa` `--salida` `--sin-verificar` | `--map` `--output` `--no-verify` | `--mapa` `--saida` `--sem-verificar` |
| `--vista arriba/abajo/frente/atras/izquierda/derecha` | `--view top/bottom/front/back/left/right` | `--vista cima/baixo/frente/tras/esquerda/direita` |
| `--color` `--tipo` `--nombre` | `--color` `--type` `--name` | `--cor` `--tipo` `--nome` |

Para forzar un idioma, usa `--idioma es` (o `en`, `pt`) o la variable `CONVERSOR3MF_IDIOMA`.
Ejecuta `conversor3mf --help` para ver todo.

## Cómo funciona

- **Formato de los colores.** El 3MF de Bambu y Orca guarda números de filamento, no
  colores. La pintura de cada triángulo es un árbol de subdivisiones codificado en
  hexadecimal, con el número de filamento en cada hoja. El conversor decodifica ese árbol,
  cambia los números y lo vuelve a codificar. El resto del archivo no se toca.
- **Ajustes de la impresora.** Vienen de un proyecto guardado por tu propio Anycubic Slicer
  Next, así que el paquete no distribuye perfiles de Anycubic.
- **Islas.** Son triángulos conectados del mismo color, después de unir vértices repetidos.
  En triángulos con varios colores, el repintado solo cambia las partes del color de la
  isla, también en el borde.

## Limitaciones

- **Verificación de proyectos con varias placas.** Anycubic Slicer Next 2.0.0.3 se cierra
  desde la línea de comandos con cualquier proyecto de más de una placa. Esos proyectos solo
  se comprueban internamente; ábrelos en el slicer antes de laminar.
- **Distancia entre placas en el slicer.** En proyectos con varias placas, el slicer dibuja
  las placas una al lado de otra, con un espacio entre ellas. La cama en sí mide
  260 × 260 mm; la distancia de una placa a la siguiente (314,4 mm hacia el lado y 328,8 mm
  hacia abajo) se midió en proyectos guardados por Anycubic Slicer Next 2.0.0.3 para la
  Kobra X. En otras impresoras, el conversor usa 1,2 × el tamaño de la cama, como Bambu
  Studio.
- **Más colores que ranuras.** Los colores parecidos se juntan. En proyectos con varias
  placas, puedes imprimir placa por placa y usar `--mapa`.
- **3MF solo con malla.** Los archivos sin un proyecto del slicer dentro no tienen colores
  que convertir.

## Desarrollo

```bash
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\python -m unittest discover -s tests
```

Las pruebas usan archivos 3MF sintéticos creados en `tests/fixtures.py` y no necesitan el
slicer. `ferramentas/testar_na_interface.ps1` abre un archivo en la interfaz del slicer, toma
una captura de pantalla y lo cierra.

## Licencia

MIT
