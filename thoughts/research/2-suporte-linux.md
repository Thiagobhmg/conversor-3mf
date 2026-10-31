# Research — #2 Rodar no Linux

Issue: [#2](https://github.com/Thiagobhmg/conversor-3mf/issues/2). Base: `a82d05f` (upstream/main em 2026-10-30).
Documento descritivo: registra o código e o ambiente como estão, sem propor mudanças.

## 1. Onde o conversor procura o slicer

Tudo está em [conversor3mf/config.py](../../conversor3mf/config.py).

| Função | Linha | O que faz hoje |
|---|---|---|
| `pasta_dados()` | [19](../../conversor3mf/config.py#L19) | `CONVERSOR3MF_DADOS`; senão `%APPDATA%` (Windows), `~/Library/Application Support` (macOS) ou `$XDG_CONFIG_HOME`/`~/.config` (Linux) + `conversor3mf`. Já trata o Linux. |
| `_do_registro()` | [29](../../conversor3mf/config.py#L29) | Só no Windows: varre as chaves `Uninstall` do registro atrás de "Anycubic Slicer Next" e devolve as pastas de `DisplayIcon`, `UninstallString` e `InstallLocation`. Fora do Windows devolve `[]`. |
| `pasta_slicer()` | [65](../../conversor3mf/config.py#L65) | Monta candidatos nesta ordem: `CONVERSOR3MF_SLICER` (pasta, ou a pasta-mãe se for arquivo; `""`, `nenhum` e `none` devolvem `None`, como nos testes), registro, e então `ProgramFiles`/`ProgramFiles(x86)`/`LOCALAPPDATA` (Windows) ou `/Applications/AnycubicSlicerNext.app` (macOS). **Não há candidato para Linux.** Devolve o primeiro candidato para o qual `executavel_slicer` acha algo. |
| `executavel_slicer(pasta)` | [87](../../conversor3mf/config.py#L87) | Procura `pasta/AnycubicSlicerNext.exe` ou `pasta/Contents/MacOS/AnycubicSlicerNext`. **Nenhum dos dois existe no Linux.** |
| `pasta_perfis()` | [97](../../conversor3mf/config.py#L97) | `pasta/resources/profiles/Anycubic` ou `pasta/Contents/Resources/profiles/Anycubic`, a partir de `pasta_slicer()`. |

Consequência no Linux: `pasta_slicer()`, `executavel_slicer()` e `pasta_perfis()` devolvem `None`, com ou sem
`CONVERSOR3MF_SLICER=/opt/AnycubicSlicerNext` (a pasta indicada também passa por `executavel_slicer`).

## 2. Quem usa essas funções

| Chamador | Linha | Uso | Efeito de `None` |
|---|---|---|---|
| `verificar.verificar` | [verificar.py:22](../../conversor3mf/verificar.py#L22) | Executa `[executavel, "--export-3mf", saida, arquivo]` com `cwd` num diretório temporário e timeout de 300 s ([L43](../../conversor3mf/verificar.py#L43)); projetos com mais de uma placa pulam a execução ([L27](../../conversor3mf/verificar.py#L27)). | Devolve `ok: False` com "não achei o Anycubic Slicer Next". Visível ao usuário. |
| `ace._chaves_de_filamento` | [ace.py:56](../../conversor3mf/ace.py#L56) | União das chaves de todos os `filament/*.json` dos perfis, mais 4 fixas, menos as de metadados. | Ficam só as 4 fixas: `filament_colour`, `filament_colour_info`, `filament_settings_id`, `default_filament_colour`. |
| `ace.perfil_de_processo` | [ace.py:70](../../conversor3mf/ace.py#L70) | Lê `process/<nome>.json` e resolve `inherits` pelo nome. | `None`. |
| `ace.definir_molde` | [ace.py:107](../../conversor3mf/ace.py#L107) | Volta as chaves de processo do molde ao perfil de fábrica. | O processo do molde fica como foi salvo. |
| `conversor._escolher_processo` | [conversor.py:254](../../conversor3mf/conversor.py#L254) | Procura `"{altura:.2f}mm {estilo} @{printer_settings_id}"` nos estilos `Standard`, `High Quality`, `Draft`, `Extra Draft`. | Usa o `print_settings_id` do molde, sem perfil de fábrica. |

### `ace.aplicar_slots` ([ace.py:191](../../conversor3mf/ace.py#L191))

Para cada slot cujo tipo difere do tipo do molde na mesma posição, procura a primeira posição do molde com o tipo
novo (`tipos_molde.index(slot.tipo)`, [L199](../../conversor3mf/ace.py#L199)) e copia de lá todas as chaves de
`_chaves_de_filamento()` cujo valor no config é lista com tamanho igual ao número de slots. Depois grava a cor do
slot em `filament_colour` (e `filament_colour_info`).

Com as 4 chaves fixas, a troca PLA → PETG copia só `filament_colour`, `filament_colour_info` e
`filament_settings_id` (as que existem como lista de tamanho n). `filament_type`, `nozzle_temperature` e as demais
ficam com os valores do material antigo. `carregar()` e `alterar_slot()` só aceitam tipos que já existem no molde.

## 3. Ambiente Linux observado (Manjaro, 2026-10-30)

- Pacote AUR `anycubicslicernext-bin` **2.0.0.5-1** (`https://github.com/ANYCUBIC-3D/AnycubicSlicer`).
- Programa: `/opt/AnycubicSlicerNext/bin/AnycubicSlicerNext`. Bibliotecas em `/opt/AnycubicSlicerNext/lib`.
- Lançador `/usr/bin/AnycubicSlicerNext` (bash): exporta `LD_LIBRARY_PATH=/opt/AnycubicSlicerNext/lib:…`,
  **`LC_NUMERIC=C`** (acréscimo local; o comentário diz que, em pt_BR, o parser de G-code lê vírgula decimal e o app
  fecha sozinho) e faz `exec` do programa. O mesmo arquivo responde em `/usr/sbin/AnycubicSlicerNext`.
- Perfis: `/opt/AnycubicSlicerNext/resources/profiles/Anycubic/{machine,process,filament}`. 382 arquivos de
  filamento; a união das chaves (regra de `_chaves_de_filamento`) dá **128 chaves**, incluindo `filament_type`,
  `nozzle_temperature`, `nozzle_temperature_initial_layer`, `hot_plate_temp`, `textured_plate_temp`,
  `filament_max_volumetric_speed`, `pressure_advance` e `filament_start_gcode`. Nenhuma chave de máquina com lista
  de 4 pontos (`printable_area`, `bed_exclude_area`) entra nessa união.
- Processos da Kobra X 0.4: 0.08 Standard; 0.12, 0.16 e 0.20 em Standard e High Quality; 0.24 e 0.28 Standard. Os
  arquivos não têm `inherits` (já vêm achatados).
- `Anycubic PETG @Anycubic Kobra X 0.4 nozzle`: `filament_type` `["PETG"]`, `nozzle_temperature` `["230"]`.
- Linha de comando: `AnycubicSlicerNext --help` pelo lançador funciona sem interface gráfica (saída 0) e lista
  `--export-3mf`, `--export-3mf-dir`, `--load-settings`, `--load-filaments` e `--slice` (saída completa guardada
  localmente em `.local/logs/slicer-help.txt`, não versionada).
- A pasta de configuração do slicer no Linux é `~/.config/AnycubicSlicerNext` (`system/`, `user/<id>/`).
- Toda execução pela linha de comando (até `--help`) grava um `result.json` na **pasta atual**. O `verificar` já roda
  o slicer com `cwd` num diretório temporário, então esse arquivo some junto com ele.

## 4. Testes existentes

- 22 testes (`unittest`), verdes no Linux com Python 3.13.13 neste worktree.
- `tests/test_conversao.py` e `tests/test_purga.py`: `setUp` cria pasta temporária, aponta `CONVERSOR3MF_DADOS`
  para ela e põe `CONVERSOR3MF_SLICER=nenhum`; o molde sintético (`tests/fixtures.py`) tem os slots
  PLA, PLA, PETG, PETG com `nozzle_temperature` 210, 210, 240, 240.
- `test_verificar_sem_slicer` confere a resposta sem slicer.
- **Não há teste** para a detecção do slicer (`config.py`) nem para trocar o tipo de um slot e converter.

## 5. Comportamento a preservar

- Windows: registro, `ProgramFiles`, `ProgramFiles(x86)`, `LOCALAPPDATA` (`AnycubicSlicerNext` e
  `Programs/AnycubicSlicerNext`), executável `AnycubicSlicerNext.exe`, perfis em `resources/profiles/Anycubic`.
- macOS: `/Applications/AnycubicSlicerNext.app`, executável em `Contents/MacOS`, perfis em
  `Contents/Resources/profiles/Anycubic`.
- `CONVERSOR3MF_SLICER` com `""`, `nenhum` ou `none` desliga o slicer (os testes dependem disso).
