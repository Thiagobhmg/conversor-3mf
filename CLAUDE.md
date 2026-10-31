# CLAUDE.md

@AGENTS.md

## Notas específicas do Claude Code

- As regras do `AGENTS.md` valem integralmente; não há exceção para mudanças "pequenas".
- Termine commits com o trailer `Co-Authored-By` do modelo em uso e PRs com a linha de geração do Claude Code.
- Subagentes que **editam** arquivos rodam com `isolation: "worktree"` (um worktree por agente). Subagentes só de
  leitura dispensam. Repasse a eles as regras do `AGENTS.md`, principalmente §3 e §6.
- OrcaSlicer: use as ferramentas da instância isolada (`mcp__orcaslicer-<n>__…`), nunca `load_model` ou
  `select_preset` na `mcp__orcaslicer__…` compartilhada. Registrar um servidor MCP é configuração do Claude Code:
  o usuário faz (`claude mcp add …` e depois `/mcp`); o agente não altera essa configuração sozinho.
