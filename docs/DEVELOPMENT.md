# Desenvolvimento

Procedimentos operacionais do fork. As regras (Issues, worktrees, PRs, upstream, segurança) ficam no
[AGENTS.md](../AGENTS.md); aqui ficam os comandos.

## Estrutura de diretórios

```
conversor-3mf/                        raiz fixa: checkout principal, sempre na main
├── .git/
├── .claude/worktrees/<n>-<slug>/     um worktree por tarefa (ignorado pelo Git)
│   ├── .venv/                        ambiente virtual do worktree
│   └── .local/                       auxiliares da tarefa (ignorado), criados quando usados
│       ├── tmp/  logs/  artifacts/  backups/  cache/
│       └── dados/                    CONVERSOR3MF_DADOS: molde, slots e purga usados nos testes manuais
├── conversor3mf/                     pacote
├── tests/                            unittest com 3MF sintéticos
├── ferramentas/                      script de teste na interface (Windows)
├── docs/                             este arquivo
└── .github/                          modelos de Issue e PR; workflows do autor
```

## Requisitos

- `git` e `gh` autenticado com acesso ao fork.
- `uv` (recomendado) ou Python 3.10+ com `venv`. O pacote depende de `mcp`, `numpy` e `pillow`.
- Opcional: **Anycubic Slicer Next**, para ler os perfis de sistema da Kobra X e conferir o arquivo convertido
  pela linha de comando. No Windows e no macOS o conversor acha a instalação sozinho; no Linux (pacote AUR
  `anycubicslicernext-bin`, em `/opt/AnycubicSlicerNext`) depende da Issue
  [#2](https://github.com/Thiagobhmg/conversor-3mf/issues/2).
- Opcional: uma instância **isolada** do OrcaSlicer com servidor MCP, para abrir e fatiar o resultado.

## Iniciar uma tarefa em worktree

Na raiz (checkout principal):

```bash
git fetch origin upstream
gh issue list -R Thiagobhmg/conversor-3mf          # já existe Issue para isto?
gh pr list -R Thiagobhmg/conversor-3mf             # já existe PR?

N=2; SLUG=suporte-linux; TIPO=fix                  # TIPO: fix | improve | feat
git worktree add -b "$TIPO/$N-$SLUG" ".claude/worktrees/$N-$SLUG" origin/main
cd ".claude/worktrees/$N-$SLUG"
git branch --show-current                          # confira antes de operar
```

## Preparar o ambiente do worktree

Cada worktree tem o próprio ambiente; nada é copiado de outro worktree. O projeto **não usa `.env`**: as variáveis
abaixo são opcionais e definidas na sessão.

```bash
export UV_CACHE_DIR="$PWD/.local/cache/uv"         # cache do uv dentro do worktree
export TMPDIR="$PWD/.local/tmp"                    # os testes usam tempfile: ficam aqui, não em /tmp
export CONVERSOR3MF_DADOS="$PWD/.local/dados"      # molde, slots e purga de teste (não usa ~/.config)
mkdir -p "$TMPDIR"

uv venv .venv
uv pip install --python .venv/bin/python -e .
```

Sem `uv`: `python3 -m venv .venv`, `export PIP_CACHE_DIR="$PWD/.local/cache/pip"` e
`.venv/bin/pip install -e .`.

Outras variáveis do conversor: `CONVERSOR3MF_SLICER` (pasta ou executável do Anycubic Slicer Next; `nenhum` finge que
não está instalado, como nos testes) e `CONVERSOR3MF_IDIOMA` (`pt`, `en` ou `es`).

## Validar

```bash
.venv/bin/python -m unittest discover -s tests -v  # a suíte inteira; não precisa do slicer
git diff --check origin/main                       # espaços sobrando e marcas de conflito
```

Os testes forçam `CONVERSOR3MF_SLICER=nenhum` e usam 3MF sintéticos de `tests/fixtures.py`. Mudança que dependa do
slicer instalado ou de um 3MF real precisa também de um teste manual, registrado no PR (comando, arquivo e
resultado).

### Teste manual com um 3MF real

Leia o arquivo de onde ele estiver, mas grave a saída no worktree; o original nunca é sobrescrito.

```bash
.venv/bin/conversor3mf inspecionar caminho/modelo.3mf
.venv/bin/conversor3mf ace definir caminho/molde-salvo-no-anycubic.3mf   # uma vez por pasta de dados
.venv/bin/conversor3mf planejar caminho/modelo.3mf
mkdir -p .local/artifacts
.venv/bin/conversor3mf converter caminho/modelo.3mf --saida .local/artifacts/modelo_KobraX.3mf
```

## Recursos compartilhados

Worktrees isolam arquivos, não recursos da máquina.

| Recurso | Como isolar |
|---|---|
| Pasta de dados do conversor | `CONVERSOR3MF_DADOS` dentro do worktree, um por tarefa. |
| Anycubic Slicer Next | Instalação única. A conferência pela linha de comando grava logs na pasta de configuração do próprio slicer (limitação conhecida). Projetos com várias placas pulam essa conferência. |
| OrcaSlicer | A instância principal (porta 13130, MCP `orcaslicer`) é compartilhada: não carregue projetos nem troque presets nela. Use uma instância isolada por agente (portas 13131, 13132…), registrada pelo usuário no Claude Code. |
| Impressoras e ponte KX | Só leitura (por exemplo, os slots do ACE). Nada é enviado para impressão a partir deste repositório. |
| Portas | O servidor MCP do conversor fala por stdio e não abre porta; não há serviços para separar. |

## Abrir o PR

Num fork, o `gh pr create` aponta para o upstream se o repositório não for indicado:

```bash
git push -u origin HEAD
gh pr create -R Thiagobhmg/conversor-3mf --base main --draft \
  --title "fix: …" --body-file .local/artifacts/pr.md   # modelo: .github/PULL_REQUEST_TEMPLATE.md
gh pr ready <N> -R Thiagobhmg/conversor-3mf             # quando estiver completo
```

O GitHub Actions do fork pode rodar o `testes.yml` do autor (Windows e Ubuntu) nos pushes. Esse resultado
complementa a validação local, mas não a substitui.

Merge em *squash*, com o OK do usuário. Depois do merge, na raiz:

```bash
git switch main && git pull --ff-only
git worktree remove ".claude/worktrees/$N-$SLUG"   # só sem trabalho pendente
git branch -d "$TIPO/$N-$SLUG"
```

## Sincronizar com o upstream

Numa Issue própria (`improve/<n>-sincronizar-upstream`), traga a `upstream/main` por PR:

```bash
git fetch upstream
git merge upstream/main          # dentro do worktree da tarefa; resolva conflitos e rode os testes
```

## Contribuir com o upstream

Só com o OK explícito do usuário (é ação externa). Depois que a mudança foi mesclada no fork:

```bash
git fetch upstream
git worktree add -b "contrib/$N-$SLUG" ".claude/worktrees/$N-contrib-$SLUG" upstream/main
cd ".claude/worktrees/$N-contrib-$SLUG"
git cherry-pick <commits de código e testes>      # nunca os arquivos de organização do fork
.venv/bin/python -m unittest discover -s tests -v  # prepare o ambiente como acima antes
git push -u origin HEAD
gh pr create -R JohnnyTrindade/conversor-3mf --base main --head "Thiagobhmg:contrib/$N-$SLUG"
```

Siga o estilo do autor no PR e nas mensagens (frases curtas em português, sem Conventional Commits) e explique o caso
real que motivou a mudança.

## Instalação para uso (deploy)

Ainda não definida. O fork não publica no PyPI (sem tags `v*`). A forma de instalar a versão do fork para uso no
fluxo de impressão (e onde guardar a pasta de dados real) será decidida numa Issue própria.
