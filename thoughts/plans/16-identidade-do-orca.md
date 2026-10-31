# Plan — #16 O convertido herda a identidade do slicer do molde

Issue: [#16](https://github.com/Thiagobhmg/conversor-3mf/issues/16).
Pesquisa: [thoughts/research/16-identidade-do-orca.md](../research/16-identidade-do-orca.md).
Branch: `fix/16-identidade-do-orca`, worktree `.claude/worktrees/16-identidade-do-orca/`, base
`fix/12-escolhas-do-designer` (#14, que está sobre #13).

## Decisões

- O convertido herda do molde, além do `Application`, o cabeçalho do `slice_info.config` e a marca `OrcaSlicer` do
  `3dmodel.model`. Assim ele se apresenta como gravado pelo mesmo slicer que gravou o molde.
- `X-Conversor3mf` continua no cabeçalho (a purga ignora arquivos do conversor).
- Moldes salvos antes desta mudança (sem as marcas guardadas) seguem com o cabeçalho atual do Anycubic. Para o
  OrcaSlicer, basta rodar `ace definir` de novo.

## Fases

| Fase | Critério |
|---|---|
| 1. `definir_molde` guarda `_cabecalho` e `_orcaslicer`; `_montar_config` tira os dois do config; `converter` grava o cabeçalho do molde; `_ajustar_principal` põe ou tira a marca `OrcaSlicer` | Suíte atual verde. |
| 2. Testes com molde do OrcaSlicer (marcas no convertido, nada de `_` no `project_settings`) e molde do Anycubic (`X-ACNext` mantido) | Verdes; prova negativa sem a fase 1. |
| 2b. Diferenças dos filamentos: `different_settings_to_system[1..n]` = chaves em que o slot difere do perfil de sistema do seu filamento (herança resolvida); a posição da impressora fica vazia (o molde já exige a de sistema) | Teste com perfis falsos; prova negativa. |
| 3. Jesus reconvertido; reabrir a 5ª instância com ele | Sem aviso; bico 236 °C, mesas 80/75 °C aplicados; fatiar as 3 placas pelo MCP. |
| 4. PR com `Closes #16` (base `fix/12-escolhas-do-designer`) | Validações registradas. |

## Progresso

| Fase | Estado | Notas |
|---|---|---|
| 1 | concluída | `_orcaslicer` e `_cabecalho` no molde; marca `OrcaSlicer` no `3dmodel.model`; cabeçalho do molde no `slice_info`; 39 verdes. |
| 2 | concluída | `TestIdentidadeDoSlicer` (2); 41 verdes. Prova negativa: sem a fase 1 os dois falham. |
| 2b | concluída (achado no meio) | Com só as marcas, o projeto abriu sem aviso, mas o Orca ainda voltava os filamentos ao preset (230/75/70). Experimento: com `different_settings_to_system[1..4]` preenchido, ele aplicou 236/80/75. `ace.diferencas_dos_filamentos` + `_perfil` genérico; `TestDiferencasDosFilamentos` (1); 42 verdes; prova negativa: `['', '', '', '']`. Jesus real: cada slot lista exatamente as 6 chaves do padrão de PETG. |
| 3 | concluída | 5ª instância aberta com o Jesus: carregou sozinha (sem clique), 3 placas, impressora de sistema, `0.16mm High Quality @Anycubic Kobra X`, Generic PETG com 236/236 °C, mesa 80/75 °C marcados como alterados, escolhas estruturais iguais às do original. Fatiamento pelo MCP: placa 1 1h23min 16,7 g; placa 2 1h23min 16,7 g; placa 3 1h14min 14,1 g; aviso `bed_temperature_too_high_than_filament` (Cool Plate 75 °C do padrão > amolecimento do PETG no Orca). Renderização: faixa vermelha nas placas 1 e 2, marrom na 3 (variante de 4 cores do designer). |
| 4 | concluída | PR com base `fix/12-escolhas-do-designer`. |
