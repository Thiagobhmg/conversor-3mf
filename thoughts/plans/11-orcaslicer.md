# Plan — #11 Mirar o OrcaSlicer (pelo MCP)

Issue: [#11](https://github.com/Thiagobhmg/conversor-3mf/issues/11).
Pesquisa: [thoughts/research/11-orcaslicer.md](../research/11-orcaslicer.md).
Branch: `feat/11-orcaslicer`, worktree `.claude/worktrees/11-orcaslicer/`, base `origin/main` (`c156a65`).

## Decisões

- O "slicer" do conversor passa a poder ser o **OrcaSlicer**: `CONVERSOR3MF_SLICER` aponta para a instalação usada pelo
  MCP (`~/Apps/orcaslicer-mcp/current`). Nada de caminho pessoal no código; o padrão do Anycubic continua para quem não
  definir a variável.
- `print_settings_id` recebe o **`name` do perfil** (no OrcaSlicer, sem "0.4 nozzle"); no Anycubic o nome é o mesmo do
  arquivo, então nada muda lá.
- Conferência do arquivo convertido: pelo **MCP**, numa instância isolada (fluxo do agente). Pela linha de comando do
  OrcaSlicer, só com `--datadir` temporário, para nunca usar a pasta de dados de uma instância ou do Orca do sistema.
- Molde do fork: gerado pela linha de comando do OrcaSlicer a partir dos perfis de sistema (máquina e processo da
  Kobra X, `Generic PETG` com o padrão local e as cores do ACE). O valor 18 em `retraction_distances_when_cut` só existe
  para a linha de comando aceitar o projeto (função desligada). Automatizar isso é a #10, adaptada ao OrcaSlicer.

## Fases

### Fase 1 — Reconhecer a instalação do OrcaSlicer (`config.py`)
- `executavel_slicer` aceita também `orca-slicer.exe`, `Contents/MacOS/OrcaSlicer` e `bin/orca-slicer`.
- `eh_orca(executavel)` para o `verificar` saber qual slicer roda.
- Testes com instalação falsa do OrcaSlicer (pasta, perfis, executável).

**Critério:** com `CONVERSOR3MF_SLICER=~/Apps/orcaslicer-mcp/current`, `pasta_perfis()` aponta para os perfis do
OrcaSlicer e `perfil_de_processo("0.16mm High Quality @Anycubic Kobra X 0.4 nozzle")` resolve a herança.

### Fase 2 — Nome do processo (`conversor.py`)
- `_montar_config` grava `print_settings_id = perfil["name"]` quando existir; o aviso de estilo usa esse nome.
- Teste: perfil falso com `name` diferente do arquivo.

**Critério:** com os perfis do OrcaSlicer, o Jesus sai com `print_settings_id = "0.16mm High Quality @Anycubic Kobra X"`.

### Fase 3 — Conferência pela linha de comando sem tocar em pastas de dados (`verificar.py`)
- Para o OrcaSlicer, acrescentar `--datadir <temporário>` à chamada.
- Teste com `subprocess.run` simulado (confere o argumento).

**Critério:** nenhuma escrita em `~/.config/OrcaSlicer*` ao conferir; teste manual num projeto de uma placa.

### Fase 4 — Teste real (Issue #4)
- Molde pela linha de comando do OrcaSlicer (pesquisa §4), `ace definir`, `converter` do Jesus com `--mapa 5=3`.
- Conferir o 3MF: impressora, processo High Quality com o nome do OrcaSlicer, PETG do padrão, escolhas do designer.
- Abrir numa instância isolada do OrcaSlicer pelo MCP, fatiar as 3 placas e conferir o G-code. **Depende de o usuário
  registrar o MCP da instância isolada.**

### Fase 5 — Documentação e PR
- `AGENTS.md`/`docs/DEVELOPMENT.md`: o alvo do fork é o OrcaSlicer, como apontar `CONVERSOR3MF_SLICER`, como gerar o
  molde. PR com `Refs #11` enquanto a fase 4 depender do MCP; `Closes #11` quando concluída.

## Progresso

| Fase | Estado | Notas |
|---|---|---|
| 1 | concluída | `EXECUTAVEIS` com os do OrcaSlicer e `eh_orca`; 2 testes; 35 verdes. Instalação real: executável `bin/orca-slicer`, perfis `resources/profiles/Anycubic`, processo High Quality com herança resolvida (300 chaves, parede externa 60), 123 chaves de filamento. |
| 2 | concluída | `print_settings_id` = `name` do perfil; fixture da #3 passou a usar o nome real do Anycubic (igual ao arquivo) e há 1 teste com o nome do OrcaSlicer; 36 verdes. Prova negativa: sem a mudança, sai `… 0.4 nozzle`. |
| 3 | concluída | `--datadir` temporário e `--allow-newer-file` para o OrcaSlicer; 1 teste; 37 verdes. **Desvio:** a linha de comando 2.4.2 recusava o próprio arquivo ("File Version 2.6.0.51 not supported by current cli version 2.4.2", a versão `BambuStudio-02.06.00.51` que a interface do Orca também grava). Teste real com `panda_bookmark.3mf` convertido: `ok: true`, `conferido_no_slicer: true`; datas das pastas `~/.config/OrcaSlicer*` iguais antes e depois; nenhum processo sobrando. |
| 4 | parcial | Molde pela CLI do OrcaSlicer (padrão PETG, cores do ACE). Jesus com `--mapa 5=3`: 10 s, `0.16mm High Quality @Anycubic Kobra X`, pintura 12.792/1.365, peças 30/29/7, original intacto. **Achado:** a CLI do OrcaSlicer recusa o Jesus de 3 placas por `tree_support_wall_count = -1` (padrão Bambu levado como "escolha do modelo"; faixa do Orca 0–2) → Issue #12 (decisão pendente). **Bloqueada:** abrir pelo MCP numa instância isolada (registro do servidor é do usuário). |
| 5 | parcial | `AGENTS.md` e `docs/DEVELOPMENT.md` (alvo OrcaSlicer, `CONVERSOR3MF_SLICER`, molde pelo OrcaSlicer). PR em Draft com `Refs #11`. |
