# conversor3mf

[![testes](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml/badge.svg)](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml)

**Print MakerWorld multicolor models on an Anycubic Kobra X without recoloring anything.**
[Português](README.pt-BR.md) · [Español](README.es.md)

Most multicolor 3MF files on MakerWorld are made for Bambu Lab printers. When you open
one in Anycubic Slicer Next, the colors come in the file's filament order, not the order
of the spools in your ACE. After syncing the ACE they end up swapped. Painted models are
the worst case: the per-object color menu only shows one color, so you end up repainting
by hand.

conversor3mf rewrites the project so that **each color of the model goes to the ACE slot
where that spool already is**. It also includes an MCP server, so you can ask Claude to do
it for you.

> Not affiliated with Anycubic or Bambu Lab. All trademarks belong to their owners.
> Respect each model's license: the tool converts files you downloaded for your own use
> and never redistributes anything.

## What it does

- **Remaps colors.** Rewrites per-triangle paint, the filament of each part and
  per-layer filament changes to your ACE slot order. It picks the closest color
  (CIEDE2000) and merges identical colors.
- **Opens as a native Kobra X project.** No "Printer parameter switching" dialog and no
  geometry-only import.
- **Keeps the designer's choices.** Layer height, walls, infill, supports, brim, ironing
  and fuzzy skin carry over. Speeds and temperatures come from the Kobra X system profile.
- **Recenters plates.** Objects on every plate are centered on the 260 mm Kobra X bed.
- **Warns you.** It flags colors with no similar spool, more colors than ACE slots, and
  PLA/PETG mixes.
- **Recolors whole regions ("islands").** Turns all holly leaves green or all stars red,
  including the side walls of raised details, without touching the paint brush.
- **Tunes the purge for each color pair.** The purge table (how much filament is flushed on each
  color change) is recalculated for the spools really in your ACE, and you can calibrate each pair:
  "white came out gray after black" → more purge only for black → white.
- **Never overwrites anything.** It writes `<name>_KobraX.3mf` next to the original.

## Requirements

- Windows with **Anycubic Slicer Next** installed. It is detected automatically; if not,
  set `CONVERSOR3MF_SLICER` to its folder.
- **Python 3.10+**.
- An Anycubic **Kobra X** with ACE. Other Anycubic printers may work but are untested;
  see [Limitations](#limitations).

**Tested with:** Kobra X firmware 2.0.2.8 and Anycubic Slicer Next 2.0.0.3. If you use other
versions and something behaves differently, please open an issue with your versions.

## Install

```bash
pip install conversor3mf
```

### Use with Claude (MCP)

```bash
claude mcp add conversor3mf --scope user -- conversor3mf-mcp
```

If you use [uv](https://docs.astral.sh/uv/), you can skip the `pip install` step:
`claude mcp add conversor3mf --scope user -- uvx --from conversor3mf conversor3mf-mcp`

**Claude Desktop (chat app):** open Settings → Developer → Edit Config and add the server to
`claude_desktop_config.json`, then restart the app:

```json
{
  "mcpServers": {
    "conversor3mf": { "command": "python", "args": ["-m", "conversor3mf.servidor_mcp"] }
  }
}
```

Then just ask, in any language:

> "Convert C:\Downloads\coaster.3mf for my Kobra X"
>
> "I swapped slot 4 for a yellow PLA"
>
> "In the coaster, make the holly leaves green and the stars red"

Claude shows where each color will go before converting. When recoloring, it looks at a
numbered map of the model.

## First-time setup: tell it what is in your ACE

1. In Anycubic Slicer Next, select the Kobra X, sync the ACE and save any project.
2. Run this command, or ask Claude to "set up my ACE from that project":

   ```bash
   conversor3mf ace setup "C:\path\to\saved_project.3mf"
   ```

This saves the printer profile and your slot colors and materials. When you only change a
spool's color, update it like this:

```bash
conversor3mf ace slot 4 --color "#FFD700" --type PLA
```

For a material that is not in any slot yet (ABS, TPU…), save a new project with it and run
`ace setup` again.

Your data lives in `%APPDATA%\conversor3mf`. Change it with `CONVERSOR3MF_DADOS`.

## Step by step: talking to Claude

Write in your own language, the way you'd ask a friend. These are the prompts that work
best, in the order you'll usually need them.

**1. First time: show Claude your ACE**

Sync the ACE in Anycubic Slicer Next, save any project, then:

> "Set up my ACE using the project C:\Users\me\Documents\any_project.3mf"

Claude reads the slots and lists them back. Check that colors and materials match the
spools you actually have loaded.

**2. Whenever you swap a spool**

> "I swapped slot 4 for a yellow PLA"
>
> "What's in my ACE right now?"

For a material that isn't in any slot yet (ABS, TPU…), repeat step 1 with a project that
uses it.

**3. Converting a file**

Always give the **full path** of the file, or the folder plus the file name:

> "Convert C:\Downloads\coaster.3mf for my Kobra X"

Claude first shows **which slot each color goes to** and warns about problems. Then:

- If everything looks right: "go ahead".
- If a color has no similar spool, you can swap the spool and tell Claude ("I loaded a
  green PLA in slot 4"), or force a slot: "put the orange (filament 3) in slot 3".
- If the model has more colors than slots, tell it which ones to merge: "use the black slot
  for both the black and the dark gray".

**4. Several files at once**

> "List the 3MF files in C:\Downloads and convert the ones made for Bambu printers"

**5. Recoloring parts of a model ("islands")**

Use the converted file (`..._KobraX.3mf`) and describe **what** and **which color**:

> "In C:\Downloads\coaster_KobraX.3mf, make the holly leaves green and the stars red"

Claude draws a numbered map of every same-color region, picks the numbers and shows a
preview of the result. Tips:

- Describe the part by **shape, position or current color**: "the small white stars", "the
  leaves around the border", "the red dots on the hat".
- For 3D figures, ask for **another view**: "look from the front" (or back, left, right,
  bottom).
- If numbers are crowded, ask it to **zoom**: "zoom into the top-left corner".
- Correct it with the numbers from the map: "not island 42, I meant 32".
- Nothing is overwritten: each repaint creates a new `..._repintado.3mf` file.

**6. Checking before you print**

> "Check C:\Downloads\coaster_KobraX.3mf in the slicer"

For projects with more than one plate, also open the file in Anycubic Slicer Next and take
a look (see [Limitations](#limitations)).

**7. Calibrating the purge (color bleeding or too much waste)**

Each color change flushes some filament. Too little and the old color stains the new one; too much
wastes filament. After a print, tell Claude what you saw:

> "The white came out grayish right after the black"
>
> "Show me how much each color change purges"
>
> "I want to save filament, use the economy purge level"

Claude raises (or lowers) only that pair, by 20% each time, and remembers it for the next
conversions. To apply it to a file you already converted: "apply the new purge to coaster_KobraX.3mf"
(it writes `..._purga.3mf`). Tip: "learn the purge from my projects in C:\Prints" teaches it the
values Anycubic Slicer Next calculated for your colors.

**What Claude can't do:** start a print, change settings inside the slicer, or download
models from MakerWorld. Download the 3MF yourself, then ask.

## Command line

```bash
conversor3mf plan    model.3mf                    # show which slot each color goes to
conversor3mf convert model.3mf --map 1=3          # convert; force filament 1 into slot 3
conversor3mf islands model_KobraX.3mf --view top  # numbered map of color regions
conversor3mf repaint model_KobraX.3mf 32=4,3=3    # recolor islands 32 and 3
conversor3mf verify  model_KobraX.3mf             # reopen in Anycubic Slicer Next and compare
```

Every command and option also works in **Portuguese and Spanish**, so use whichever feels
natural. Help and error messages follow the language you type in, or your system language:

| English | Português | Español |
|---|---|---|
| `inspect` | `inspecionar` | `inspeccionar` |
| `plan` | `planejar` | `planificar` |
| `convert` | `converter` | `convertir` |
| `verify` | `verificar` | `verificar` |
| `islands` | `ilhas` | `islas` |
| `repaint` | `repintar` | `repintar` |
| `ace show` / `setup` / `slot` | `ace mostrar` / `definir` / `slot` | `ace mostrar` / `configurar` / `ranura` |
| `--map` `--output` `--no-verify` | `--mapa` `--saida` `--sem-verificar` | `--mapa` `--salida` `--sin-verificar` |
| `--view top/bottom/front/back/left/right` | `--vista cima/baixo/frente/tras/esquerda/direita` | `--vista arriba/abajo/frente/atras/izquierda/derecha` |
| `--color` `--type` `--name` | `--cor` `--tipo` `--nome` | `--color` `--tipo` `--nombre` |
| `purge show` / `adjust 2 1 more` / `level economy` / `learn` / `apply` | `purga mostrar` / `ajustar 2 1 mais` / `nivel economia` / `aprender` / `aplicar` | `purga mostrar` / `ajustar 2 1 más` / `nivel economía` / `aprender` / `aplicar` |

Force a language with `--language en` (or `pt`, `es`) or the `CONVERSOR3MF_IDIOMA`
variable. Run `conversor3mf --help` for the full list.

## How it works

- **Color format.** A Bambu/Orca 3MF stores filament numbers, not colors. The paint of each
  triangle is a hex-encoded subdivision tree with a filament number on every leaf. The
  converter decodes that tree, swaps the numbers and encodes it back. Every other part of
  the file is left untouched.
- **Printer settings.** They come from a project saved by your own Anycubic Slicer Next,
  so no Anycubic profiles are shipped with this package.
- **Purge.** The Kobra X firmware reads the purge table (`flush_volumes_matrix`) from the G-code
  header and flushes by itself; the real purge is table × `flush_multiplier` (0.7). Each pair uses the
  value Anycubic Slicer Next calculated for it in your saved projects, or the OrcaSlicer formula plus
  the nozzle volume, times your calibration.
- **Islands.** Connected triangles of the same color, after welding duplicate vertices.
  When a triangle has several colors, recoloring only changes the leaves of that island's
  color, including on the island's border.
- **Color changes by height.** Some models are not painted at all: the designer switches
  filament at fixed heights (for example, black from 3.8 mm and white again from 7.6 mm). These
  changes are converted too, but the Prepare screen of the slicer shows the model with fewer
  colors, sometimes only one. The colors only appear in the Preview after slicing, so there is
  no need to recolor the parts by hand. The plan warns you when a model works like this.

## Limitations

- **Verification of multi-plate projects.** Anycubic Slicer Next 2.0.0.3 crashes from the
  command line on any project with more than one plate. Those projects are only checked
  internally, so open them in the slicer before slicing.
- **Distance between plates in the slicer.** Multi-plate projects are laid out side by side
  in the slicer, with a gap between plates. The bed itself is 260 × 260 mm; the distance
  from one plate to the next (314.4 mm sideways, 328.8 mm down) was measured from projects
  saved by Anycubic Slicer Next 2.0.0.3 for the Kobra X. Other printers fall back to
  1.2 × the bed size, which is what Bambu Studio uses.
- **More colors than slots.** Similar colors get merged. For multi-plate projects you can
  print plate by plate and use `--map`.
- **Mesh-only 3MF files.** Files without a slicer project inside have no colors to
  convert.

## Development

```bash
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\python -m unittest discover -s tests
```

The tests use synthetic 3MF files built in `tests/fixtures.py` and do not need the slicer.
`ferramentas/testar_na_interface.ps1` opens a file in the slicer GUI, takes a screenshot
and closes it.

## License

MIT
