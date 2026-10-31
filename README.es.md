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
- **Ajusta la purga para cada par de colores.** La tabla de purga (cuánto filamento se descarta en cada
  cambio de color) se recalcula para los carretes que realmente están en tu ACE, y puedes calibrar cada
  par: "el blanco salió grisáceo después del negro" → más purga solo de negro → blanco.
- **Nunca sobrescribe nada.** Guarda `<nombre>_KobraX.3mf` junto al original.

## Requisitos

- Windows con **Anycubic Slicer Next** instalado. Se detecta solo; si no, define
  `CONVERSOR3MF_SLICER` con su carpeta.
- En Linux, el paquete de Anycubic Slicer Next del AUR (`anycubicslicernext-bin`), en
  `/opt/AnycubicSlicerNext`, también se detecta; en otra ubicación, define `CONVERSOR3MF_SLICER`.
  Probado en Manjaro con Anycubic Slicer Next 2.0.0.5.
- **Python 3.10 o superior**.
- Una **Kobra X** con ACE. Otras impresoras Anycubic pueden funcionar, pero no están
  probadas (ver [Limitaciones](#limitaciones)).

**Probado con:** firmware 2.0.2.8 de la Kobra X y Anycubic Slicer Next 2.0.0.3. Si usas otras
versiones y algo se comporta distinto, abre un issue indicando tus versiones.

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

**Claude Desktop (app de chat):** abre Configuración → Desarrollador → Editar configuración,
añade el servidor a `claude_desktop_config.json` y reinicia la app:

```json
{
  "mcpServers": {
    "conversor3mf": { "command": "python", "args": ["-m", "conversor3mf.servidor_mcp"] }
  }
}
```

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

## Paso a paso: hablando con Claude

Escribe en tu idioma, como se lo pedirías a un amigo. Estas son las peticiones que mejor
funcionan, en el orden en que sueles necesitarlas.

**1. La primera vez: muéstrale tu ACE a Claude**

Sincroniza el ACE en Anycubic Slicer Next, guarda cualquier proyecto y pide:

> "Configura mi ACE usando el proyecto C:\Users\yo\Documents\cualquier_proyecto.3mf"

Claude lee las ranuras y te las muestra. Comprueba que los colores y materiales coinciden con
los carretes que tienes cargados.

**2. Cada vez que cambies un carrete**

> "Cambié la ranura 4 por un PLA amarillo"
>
> "¿Qué hay en mi ACE ahora?"

Para un material que todavía no está en ninguna ranura (ABS, TPU…), repite el paso 1 con un
proyecto que lo use.

**3. Convertir un archivo**

Indica siempre la **ruta completa** del archivo, o la carpeta y el nombre:

> "Convierte C:\Descargas\posavasos.3mf para mi Kobra X"

Primero Claude muestra **a qué ranura irá cada color** y avisa de los problemas. Después:

- Si todo está bien: "adelante".
- Si un color no tiene un carrete parecido, cambia el carrete y avísale ("puse un PLA verde
  en la ranura 4"), o fuerza una ranura: "pon el naranja (filamento 3) en la ranura 3".
- Si el modelo tiene más colores que ranuras, dile cuáles juntar: "usa la ranura del negro
  para el negro y el gris oscuro".

**4. Varios archivos a la vez**

> "Lista los 3MF de C:\Descargas y convierte los que sean para impresoras Bambu"

**5. Repintar partes del modelo ("islas")**

Usa el archivo convertido (`..._KobraX.3mf`) y di **qué** y **de qué color**:

> "En C:\Descargas\posavasos_KobraX.3mf, pon las hojas de acebo en verde y las estrellas en
> rojo"

Claude dibuja un mapa numerado de cada región del mismo color, elige los números y muestra
una vista previa del resultado. Consejos:

- Describe la parte por su **forma, posición o color actual**: "las estrellitas blancas",
  "las hojas alrededor del borde", "los puntos rojos del gorro".
- En figuras 3D, pide **otra vista**: "mira de frente" (o desde atrás, la izquierda, la
  derecha, abajo).
- Si los números están amontonados, pide **zoom**: "haz zoom en la esquina superior
  izquierda".
- Corrígelo con los números del mapa: "la isla 42 no, era la 32".
- Nada se sobrescribe: cada repintado crea un archivo nuevo `..._repintado.3mf`.

**6. Comprobar antes de imprimir**

> "Comprueba C:\Descargas\posavasos_KobraX.3mf en el slicer"

En proyectos con más de una placa, abre también el archivo en Anycubic Slicer Next y échale
un vistazo (ver [Limitaciones](#limitaciones)).

**7. Calibrar la purga (color manchado o demasiado desperdicio)**

Cada cambio de color descarta algo de filamento. Muy poco y el color anterior mancha el nuevo; demasiado
desperdicia filamento. Después de una impresión, cuéntale a Claude lo que viste:

> "El blanco salió grisáceo justo después del negro"
>
> "Muéstrame cuánto purga cada cambio de color"
>
> "Quiero ahorrar filamento, usa la purga en nivel economía"

Claude sube (o baja) solo ese par, un 20% cada vez, y lo recuerda para las próximas conversiones.
Para aplicarlo a un archivo ya convertido: "aplica la purga nueva a posavasos_KobraX.3mf" (guarda
`..._purga.3mf`). Consejo: "aprende la purga de mis proyectos en C:\Impresiones" le enseña los valores
que Anycubic Slicer Next calculó para tus colores.

**Lo que Claude no hace:** iniciar la impresión, cambiar ajustes dentro del slicer ni
descargar modelos de MakerWorld. Descarga el 3MF tú mismo y luego pídelo.

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
| `purga mostrar` / `ajustar 2 1 más` / `nivel economía` / `aprender` / `aplicar` | `purge show` / `adjust 2 1 more` / `level economy` / `learn` / `apply` | `purga mostrar` / `ajustar 2 1 mais` / `nivel economia` / `aprender` / `aplicar` |

Para forzar un idioma, usa `--idioma es` (o `en`, `pt`) o la variable `CONVERSOR3MF_IDIOMA`.
Ejecuta `conversor3mf --help` para ver todo.

## Cómo funciona

- **Formato de los colores.** El 3MF de Bambu y Orca guarda números de filamento, no
  colores. La pintura de cada triángulo es un árbol de subdivisiones codificado en
  hexadecimal, con el número de filamento en cada hoja. El conversor decodifica ese árbol,
  cambia los números y lo vuelve a codificar. El resto del archivo no se toca.
- **Ajustes de la impresora.** Vienen de un proyecto guardado por tu propio Anycubic Slicer
  Next, así que el paquete no distribuye perfiles de Anycubic.
- **Purga.** El firmware de la Kobra X lee la tabla de purga (`flush_volumes_matrix`) de la cabecera
  del G-code y purga por su cuenta; la purga real es tabla × `flush_multiplier` (0,7). Cada par usa el
  valor que Anycubic Slicer Next calculó para él en tus proyectos guardados, o la fórmula de OrcaSlicer
  más el volumen de la boquilla, por tu calibración.
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
