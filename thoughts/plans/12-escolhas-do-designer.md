# Plan — #12 Só as escolhas do designer

Issue: [#12](https://github.com/Thiagobhmg/conversor-3mf/issues/12).
Pesquisa: [thoughts/research/12-escolhas-do-designer.md](../research/12-escolhas-do-designer.md).
Branch: `fix/12-escolhas-do-designer`, worktree `.claude/worktrees/12-escolhas-do-designer/`, **base
`feat/11-orcaslicer`** (PR #13): entra depois da #11.

## Decisões (opção A)

- Escolhas do designer = chaves de `different_settings_to_system[0]` do original. Delas, só as de `CHAVES_DO_MODELO`
  vão para a Kobra X (velocidades, temperaturas e ajustes da máquina dele continuam fora).
- `layer_height` sempre segue o original: é a escolha do perfil (0.16, 0.20…), não aparece como diferença, e o perfil
  da Kobra X pode não existir naquela altura.
- Sem `different_settings_to_system` no original, mantém o comportamento atual (não há como saber o que ele mudou).
- Mudanças do designer que não vão para a Kobra X viram um aviso, para ninguém achar que foram perdidas sem querer.
- `_montar_config` passa a devolver uma lista de avisos (o do estilo do processo e este).

## Fases

| Fase | Critério |
|---|---|
| 1. `_escolhas_do_designer` e o filtro em `_montar_config`; avisos | Suíte atual verde. |
| 2. Testes: original com diferenças declaradas, padrões de fábrica da origem e chave fora da faixa do Orca | O padrão da origem não vai; a escolha vai; o aviso cita o que ficou de fora; prova negativa sem a fase 1. |
| 3. Jesus real com o molde do OrcaSlicer e `--mapa 5=3` | `configuracoes_mantidas_do_modelo` só com `layer_height` (se diferir) ; linha de comando do Orca aceita as 3 placas. |
| 4. PR com `Closes #12` | Dependência da #11 registrada. |

## Progresso

| Fase | Estado | Notas |
|---|---|---|
| 1 | concluída | `_escolhas_do_designer`, filtro em `_montar_config`, aviso das mudanças que não vão; `_montar_config` devolve lista de avisos; 37 verdes. |
| 2 | concluída | `TestEscolhasDoDesigner` (2); 39 verdes. Prova negativa: sem a fase 1, o pé de elefante da origem (0.075) vai para a Kobra X. |
| 3 | concluída | Jesus com molde do OrcaSlicer e `--mapa 5=3`: nada levado da A1 (`configuracoes_mantidas_do_modelo` vazio; a altura já coincide), aviso cita `prime_tower_rib_wall`; `0.16mm High Quality @Anycubic Kobra X`, PETG 236 °C, original intacto. **A linha de comando do OrcaSlicer aceitou as 3 placas** ("Success.", 13 s), ao contrário do Anycubic Slicer Next. |
| 4 | concluída | PR com base `feat/11-orcaslicer` (diff só da #12); `Closes #12`. |
