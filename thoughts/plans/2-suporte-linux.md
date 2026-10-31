# Plan — #2 Rodar no Linux

Issue: [#2](https://github.com/Thiagobhmg/conversor-3mf/issues/2).
Pesquisa: [thoughts/research/2-suporte-linux.md](../research/2-suporte-linux.md).
Branch: `fix/2-suporte-linux`, worktree `.claude/worktrees/2-suporte-linux/`, base `origin/main` (`a82d05f`).

## Decisões

- **Detectar pela pasta de instalação, não pelo `PATH`.** No Linux, o candidato padrão é `/opt/AnycubicSlicerNext`
  (layout do pacote AUR: `bin/`, `lib/`, `resources/`). O lançador em `/usr/bin` é um script: derivar a instalação
  dele daria `/usr`, onde não há perfis. Instalações em outro lugar usam `CONVERSOR3MF_SLICER`.
- **Executar o binário com o ambiente que o lançador montaria** (`LD_LIBRARY_PATH` com `<instalação>/lib` e
  `LC_NUMERIC=C`), em vez de depender do lançador. Assim funciona também com `CONVERSOR3MF_SLICER` apontando para
  uma pasta fora do `PATH`.
- **Sem perfis, recusar a troca de tipo de slot na conversão** (antes de gravar qualquer arquivo), com mensagem
  dizendo o que fazer. Uma verificação só, em `ace.aplicar_slots`, que é por onde toda conversão passa.
- Windows e macOS não mudam. Código no estilo do autor: português, funções curtas, comentários só onde o motivo não
  é óbvio.

## Fases

### Fase 1 — Achar a instalação no Linux (`config.py`)
- `executavel_slicer(pasta)` aceita também `pasta/bin/AnycubicSlicerNext`.
- `pasta_slicer()` ganha os candidatos de Linux (constante `PASTAS_LINUX = (Path("/opt/AnycubicSlicerNext"),)`) e,
  quando `CONVERSOR3MF_SLICER` aponta para um arquivo, testa a pasta dele e a pasta acima (`bin/` → instalação).
- Testes novos em `tests/test_config.py`, com uma instalação falsa numa pasta temporária: pasta, executável e
  perfis achados por `CONVERSOR3MF_SLICER` (pasta e arquivo) e pelo candidato padrão de Linux (constante trocada no
  teste, `sys.platform` simulado).

**Critério:** os testes novos e os 22 antigos passam; com a instalação real, `pasta_slicer()` →
`/opt/AnycubicSlicerNext` e `pasta_perfis()` → `.../resources/profiles/Anycubic`.

### Fase 2 — Rodar o slicer no Linux (`config.py`, `verificar.py`)
- `config.ambiente_slicer(executavel)`: no Linux devolve uma cópia de `os.environ` com `LD_LIBRARY_PATH` prefixado
  por `<instalação>/lib` (quando existir) e `LC_NUMERIC=C`; nos outros sistemas devolve `None` (herda o ambiente).
- `verificar` passa `env=config.ambiente_slicer(executavel)` ao `subprocess.run`.
- Testes: o ambiente montado no Linux simulado e a chamada de `verificar` com `subprocess.run` simulado (confere
  `env`), sem executar o slicer.

**Critério:** testes verdes; `verificar` num projeto real de uma placa, salvo pelo Anycubic Slicer Next, roda o
slicer de verdade no Linux e devolve `ok: True`, `conferido_no_slicer: True` (teste manual, saída em `.local/`).

### Fase 3 — Recusar a troca de tipo sem perfis (`ace.py`)
- Em `aplicar_slots`, se algum slot tem tipo diferente do molde na mesma posição e `pasta_perfis()` é `None`,
  levantar `ValueError` com o slot, o tipo antigo e o novo, e as saídas possíveis (instalar o slicer, definir
  `CONVERSOR3MF_SLICER` ou salvar um molde novo com o filamento no slot).
- Testes em `tests/test_conversao.py`:
  - sem perfis (`CONVERSOR3MF_SLICER=nenhum`): `alterar_slot(1, tipo="PETG")` e `converter` levanta `ValueError` e
    não deixa arquivo de saída;
  - com perfis falsos (um `filament/*.json` com `filament_type` e `nozzle_temperature`): o slot 1 sai com
    `filament_type` `PETG` e `nozzle_temperature` `240`, copiados do slot PETG do molde sintético.

**Critério:** testes verdes; com os perfis reais, `_chaves_de_filamento()` tem as 128 chaves da pesquisa.

### Fase 4 — Documentação de uso
- Uma linha sobre Linux nos requisitos de `README.md`, `README.pt-BR.md` e `README.es.md` (instalação em
  `/opt/AnycubicSlicerNext` ou `CONVERSOR3MF_SLICER`).

**Critério:** os três READMEs dizem a mesma coisa, sem mexer no resto do texto do autor.

### Fase 5 — Validação final e PR
- Suíte inteira, `git diff --check origin/main`, teste manual da fase 2 e conferência da fase 3 com perfis reais.
- Commits: código e testes (`fix: …`) separados de `thoughts/` (`docs: …`), para o cherry-pick ao upstream.
- PR no fork com `Closes #2`.

**Critério:** PR aberto com as validações registradas; Windows e macOS sem mudança de comportamento (revisão do
diff: nenhum ramo `win32`/`darwin` alterado).

## Progresso

| Fase | Estado | Notas |
|---|---|---|
| 1 | concluída | `tests/test_config.py` (4 testes); 26 testes verdes. Instalação real: `pasta_slicer()` → `/opt/AnycubicSlicerNext`, `executavel_slicer()` → `.../bin/AnycubicSlicerNext`, `pasta_perfis()` → `.../resources/profiles/Anycubic`. |
| 2 | concluída | `ambiente_slicer` + `env=` no `verificar`; 2 testes; 28 verdes. Teste manual com `panda_bookmark.3mf` (1 placa, salvo pelo Anycubic Slicer Next): caminho absoluto → `ok: true`, `conferido_no_slicer: true` em 0,5 s, sem processo do slicer sobrando. **Desvio:** com caminho relativo a conferência falha (defeito antigo, independente do Linux) → Issue #6, fora deste escopo. |
| 3 | concluída | Recusa em `aplicar_slots`; 2 testes em `TestTrocaDeTipo`; 30 verdes. Prova negativa: sem a mudança do `ace.py` o teste de recusa falha ("ValueError not raised"); sem a do `config.py` o teste com perfis falha (perfis não achados). Perfis reais: 128 chaves. |
| 4 | concluída | Linha de Linux nos requisitos dos três READMEs. |
| 5 | concluída | PR [#7](https://github.com/Thiagobhmg/conversor-3mf/pull/7) aberto. Suíte inteira verde (30), `git diff --check` ok, ramos `win32`/`darwin` intocados no diff. **Desvio:** o `--help` da pesquisa, rodado na raiz do worktree, deixou um `result.json` do slicer ali; removido e registrado na pesquisa. |
