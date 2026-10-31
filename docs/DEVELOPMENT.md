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
├── thoughts/research/  plans/        RPI: pesquisa e plano de cada Issue (AGENTS.md §2)
└── .github/                          modelos de Issue e PR; workflows do autor
```

## Requisitos

- `git` e `gh` autenticado com acesso ao fork.
- `uv` (recomendado) ou Python 3.10+ com `venv`. O pacote depende de `mcp`, `numpy` e `pillow`.
- **OrcaSlicer** (alvo do fork): a build do MCP em `~/Apps/orcaslicer-mcp/current`, para os perfis da Kobra X, o
  molde e a conferência pela linha de comando; e uma instância **isolada** dela com servidor MCP, para abrir e fatiar o
  resultado.
- Opcional: **Anycubic Slicer Next** (alvo do upstream). No Linux, o pacote AUR `anycubicslicernext-bin` em
  `/opt/AnycubicSlicerNext` é achado sozinho.

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

Outras variáveis do conversor: `CONVERSOR3MF_SLICER` (pasta ou executável do slicer; `nenhum` finge que não há slicer,
como nos testes) e `CONVERSOR3MF_IDIOMA` (`pt`, `en` ou `es`). No fork, aponte para o OrcaSlicer do MCP:

```bash
export CONVERSOR3MF_SLICER="$HOME/Apps/orcaslicer-mcp/current"
```

Com o OrcaSlicer, a conferência pela linha de comando usa `--datadir` temporário (nunca a pasta de uma instância) e
`--allow-newer-file` (a linha de comando 2.4.2 recusa a versão `BambuStudio-02.06…` que o próprio Orca grava).

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
.venv/bin/conversor3mf ace definir .local/tmp/molde/molde-orca.3mf   # uma vez por pasta de dados (abaixo)
.venv/bin/conversor3mf planejar caminho/modelo.3mf
mkdir -p .local/artifacts
.venv/bin/conversor3mf converter caminho/modelo.3mf --saida "$PWD/.local/artifacts/modelo_KobraX.3mf"
```

Use caminho absoluto na saída: com caminho relativo a conferência falha (Issue #6).

### Molde pelo OrcaSlicer

Até a automação (Issue #10), o molde é gerado pela linha de comando do OrcaSlicer, numa pasta de dados vazia:

1. Leia os slots do ACE (só leitura): `curl -s http://127.0.0.1:7125/kx/filament/slots`.
2. Monte, em `.local/tmp/molde/`, JSON **achatados** (herança resolvida, `inherits` vazio) a partir de
   `resources/profiles/Anycubic` da build: a máquina `Anycubic Kobra X 0.4 nozzle` com
   `retraction_distances_when_cut = ["18"]` (a linha de comando recusa o 0 do perfil de sistema; a função está
   desligada), um processo da Kobra X e um `Generic PETG @Anycubic Kobra X 0.4 nozzle` por slot, com o padrão local de
   PETG (bico 236 °C também na 1ª camada, mesa 80 °C PEI / 75 °C Cool Plate) e `filament_colour` = cor do slot.
3. Rode, de dentro de `.local/tmp/molde/` (a linha de comando grava um `result.json` na pasta atual), com um STL
   qualquer (ex.: um cubo):

   ```bash
   ~/Apps/orcaslicer-mcp/current/AppRun --datadir "$PWD/dados" \
     --load-settings "maquina.json;processo.json" \
     --load-filaments "petg-slot1.json;petg-slot2.json;petg-slot3.json;petg-slot4.json" \
     --export-3mf molde-orca.3mf cubo.stl
   ```

O resultado esperado: impressora `Anycubic Kobra X 0.4 nozzle`, 4 × `Generic PETG`, `different_settings_to_system`
vazio e nenhum perfil embutido. Detalhes em `thoughts/research/11-orcaslicer.md`.

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

Os workflows do autor (`testes.yml`, em Windows e Ubuntu) **não rodam no fork**: o GitHub os deixa desligados em
forks até alguém ligá-los na aba Actions (conferido no PR #7, sem checks). A validação é local; ligar os workflows
é decisão do usuário e daria uma conferência no Windows que não temos aqui.

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
