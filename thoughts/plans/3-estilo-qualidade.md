# Plan — #3 Manter o estilo de qualidade do processo original

Issue: [#3](https://github.com/Thiagobhmg/conversor-3mf/issues/3).
Pesquisa: [thoughts/research/3-estilo-qualidade.md](../research/3-estilo-qualidade.md).
Branch: `improve/3-estilo-qualidade`, worktree `.claude/worktrees/3-estilo-qualidade/`, base `origin/main`
(`a82d05f`), independente da #2 no código.

## Decisões

- Estilo do original = `High Quality` se o `print_settings_id` original contém "High Quality" (sem diferenciar
  maiúsculas); senão `Standard`. Os outros nomes da Bambu são só a altura (pesquisa §2).
- O estilo do original é tentado primeiro; os demais seguem a ordem atual como reserva.
- Quando o perfil achado não tem o estilo do original, a conversão **avisa** (ex.: 0,08 mm High Quality →
  0.08mm Standard, que é o que existe).
- `_escolher_processo` e `_montar_config` passam a devolver também esse aviso (são privadas, com um chamador cada).

## Fases

### Fase 1 — Escolha pelo estilo do original (`conversor.py`)
- `_estilo_original(fonte)` e a nova ordem em `_escolher_processo`, que devolve `(perfil, nome, aviso)`.
- `_montar_config` repassa o aviso; `converter` o põe em `avisos`.

**Critério:** suíte antiga verde (22).

### Fase 2 — Testes (`tests/test_conversao.py`)
Instalação falsa (layout do Windows) com `process/` contendo 0.16 Standard (`sparse_infill_speed` 250),
0.16 High Quality (`sparse_infill_speed` 100) e 0.08 Standard:
- `0.16mm High Quality @BBL A1` → `0.16mm High Quality @Anycubic Kobra X 0.4 nozzle`, `sparse_infill_speed` 100, sem
  aviso de estilo;
- `0.16mm Optimal @BBL A1` → `0.16mm Standard …`;
- `0.08mm High Quality @BBL A1` (altura 0,08) → `0.08mm Standard …` com aviso.

**Critério:** testes novos verdes, e o primeiro falha sem a fase 1 (prova negativa).

### Fase 3 — Validação e PR
- Suíte inteira, `git diff --check origin/main`.
- Conferência com os perfis reais do Anycubic Slicer Next: precisa da detecção no Linux (#2). Fazer num worktree
  temporário com #2 + #3 juntos, ou registrar como pendente para a #4.
- Commits: código e testes (`feat`/`fix`) separados de `thoughts/`. PR com `Closes #3`.

## Progresso

| Fase | Estado | Notas |
|---|---|---|
| 1 | concluída | `_estilo_original`; `_escolher_processo` e `_montar_config` devolvem o aviso; suíte antiga verde (22). |
| 2 | concluída | `TestEstiloDoProcesso` (3); 25 verdes. Prova negativa: sem a fase 1, o teste de High Quality falha com o comportamento antigo (`0.16mm Standard`) e o do aviso também. |
| 3 | concluída | `git diff --check` ok; PR [#8](https://github.com/Thiagobhmg/conversor-3mf/pull/8). **Pendente:** conferência com perfis reais no Linux, na validação combinada da #4 (depende do #7). |
