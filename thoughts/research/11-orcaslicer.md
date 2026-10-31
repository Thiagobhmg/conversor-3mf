# Research — #11 Mirar o OrcaSlicer (pelo MCP)

Issue: [#11](https://github.com/Thiagobhmg/conversor-3mf/issues/11). Base: `main` com #2 e #3 (`c156a65`).
Documento descritivo (2026-10-30), sem propor mudanças.

## 1. Decisões do usuário que delimitam a pesquisa

- O fork funciona com o **OrcaSlicer pelo MCP**, não com o Anycubic Slicer Next.
- Impressora: o perfil **de sistema** da Kobra X. Filamento: o **padrão local de PETG**. Escolhas do arquivo original
  mantidas.
- Teste: `jesus+makerworld.3mf` com o filamento 5 (amarelo, uma faixa no peito) no slot vermelho (`5=3`).

## 2. A instalação do OrcaSlicer do MCP

- `~/Apps/orcaslicer-mcp/current` → `2.4.2-mcp.13` (AppImage extraída): `AppRun`, `bin/orca-slicer`, `lib/`,
  `resources/profiles/<fabricante>/{machine,process,filament}`. `AppRun` exporta `APPDIR`, `LC_ALL=C` e ajustes de
  Wayland/NVIDIA antes de executar o binário.
- Instâncias usam `--datadir ~/.config/OrcaSlicer-MCP[-n]`; cada datadir tem `system/Anycubic/…` (cópia dos perfis da
  build) e `user/default/…` (presets do usuário: três variantes de impressora, dois processos; nenhum filamento salvo).
- Também existe um OrcaSlicer do sistema (`/usr/sbin/orca-slicer`, datadir `~/.config/OrcaSlicer`), que não é o do MCP.

## 3. Perfis da Kobra X no OrcaSlicer

- Os mesmos arquivos do Anycubic Slicer Next: máquina `Anycubic Kobra X 0.4 nozzle`; processos `0.08`–`0.28mm
  Standard` e `0.12/0.16/0.20mm High Quality @Anycubic Kobra X 0.4 nozzle`; filamentos `Anycubic PETG` e
  `Generic PETG @Anycubic Kobra X 0.4 nozzle` (as sessões usam o `Generic PETG`).
- **Herança na mesma pasta:** processo → `fdm_process_common`; filamento → `fdm_filament_pet` → `fdm_filament_common`;
  máquina → `fdm_machine_common`. `ace.perfil_de_processo` já resolve `inherits` pelo nome do arquivo na mesma pasta.
- **Nome ≠ arquivo nos processos:** o JSON `0.16mm High Quality @Anycubic Kobra X 0.4 nozzle.json` tem
  `name = "0.16mm High Quality @Anycubic Kobra X"` (sem "0.4 nozzle"). Filamentos e máquina têm nome igual ao arquivo.
  No Anycubic Slicer Next os três têm nome igual ao arquivo. Os presets de processo do usuário herdam dos nomes sem
  "0.4 nozzle". Hoje o conversor grava em `print_settings_id` o nome montado (com "0.4 nozzle",
  [conversor.py](../../conversor3mf/conversor.py) `_escolher_processo`), que existe como arquivo, mas não como nome de
  preset no OrcaSlicer.
- A máquina de sistema traz `retraction_distances_when_cut = ["0"]` com `enable_long_retraction_when_cut = "0"` e
  `long_retractions_when_cut = ["0"]` (função desligada).

## 4. Linha de comando do OrcaSlicer

- `AppRun --datadir <pasta> --help`: mesmas opções do Bambu/Anycubic (`--load-settings`, `--load-filaments`,
  `--export-3mf`, `--slice`, `--datadir`). Com `--datadir` numa pasta vazia, nada é escrito fora dela; o
  `result.json` vai para a pasta atual.
- Gerar projeto com os perfis de sistema (achatados ou não) **falha** com saída 238: "retraction_distances_when_cut: 0
  not in range [10, 18]" — a linha de comando valida o valor que o próprio perfil de sistema traz.
- Com a máquina achatada e esse valor em 18 (sem efeito: a retração longa no corte está desligada), a linha de comando
  grava o projeto: impressora `Anycubic Kobra X 0.4 nozzle`, processo `0.20mm Standard @Anycubic Kobra X`,
  4 × `Generic PETG` com 236/236 °C, mesa 80/75 °C e as cores do ACE, `different_settings_to_system` vazio, sem perfis
  embutidos, 650 chaves, `Application = BambuStudio-02.06.00.51`, sem a assinatura `X-ACNext`.

## 5. O que o conversor faz hoje com um slicer (pontos de contato)

- `config.executavel_slicer`: só reconhece `AnycubicSlicerNext.exe`, `Contents/MacOS/AnycubicSlicerNext` e
  `bin/AnycubicSlicerNext`. Uma pasta do OrcaSlicer em `CONVERSOR3MF_SLICER` não é reconhecida, então não há perfis.
- `config.pasta_perfis`: `resources/profiles/Anycubic` (mesmo caminho no OrcaSlicer).
- `verificar`: roda `<executável> --export-3mf saida arquivo` sem `--datadir`. Com o OrcaSlicer isso usaria a pasta
  de dados padrão (`~/.config/OrcaSlicer`, do Orca do sistema).
- `purga.aprender`: só aprende de projetos com `X-ACNext`; sem eles, a fórmula do OrcaSlicer é usada.
- `ace.definir_molde` aceita o projeto da §4 (impressora Anycubic, sem diferenças, sem perfis embutidos).

## 6. OrcaSlicer pelo MCP nesta sessão

Só o MCP da instância compartilhada (13130) está disponível; registrar outro servidor MCP é configuração do Claude Code
e foi recusado ao agente (autoalteração). A 3ª instância (13132) está aberta e sem servidor registrado.
