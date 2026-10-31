# conversor3mf

[![testes](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml/badge.svg)](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml)

**Imprima modelos multicoloridos do MakerWorld na Anycubic Kobra X sem recolorir nada.**
[English](README.md) · [Español](README.es.md)

A maioria dos 3MF multicoloridos do MakerWorld é feita para impressoras Bambu Lab. No
Anycubic Slicer Next, as cores entram na ordem dos filamentos do arquivo, e não na ordem
dos carretéis do seu ACE. Depois de sincronizar o ACE, elas ficam trocadas. Em modelos
pintados é pior: o menu do objeto mostra uma cor só, e você acaba repintando à mão.

O conversor3mf reescreve o projeto para que **cada cor do modelo vá para o slot do ACE
onde aquele carretel já está**. Ele também vem com um servidor MCP, então dá para pedir
ao Claude que faça isso por você.

> Projeto independente, sem vínculo com a Anycubic ou a Bambu Lab. As marcas pertencem
> aos seus donos. Respeite a licença de cada modelo: a ferramenta só converte arquivos
> que você baixou para uso próprio e não redistribui nada.

## O que ele faz

- **Reordena as cores.** Reescreve a pintura de cada triângulo, o filamento de cada peça
  e as trocas de filamento por camada para a ordem dos seus slots. Escolhe a cor mais
  parecida (CIEDE2000) e junta cores repetidas.
- **Abre como projeto da Kobra X.** Sem o diálogo "Printer parameter switching" e sem
  carregar só a geometria.
- **Mantém as escolhas do designer.** Altura de camada, paredes, preenchimento, suportes,
  borda, passar ferro e fuzzy skin. Velocidades e temperaturas vêm do perfil de fábrica.
- **Centraliza as placas.** As peças de cada placa ficam centralizadas na mesa de 260 mm.
- **Avisa os problemas.** Mostra quando não há carretel de cor parecida, quando o modelo
  tem mais cores que o ACE e quando a impressão mistura PLA e PETG.
- **Repinta regiões inteiras ("ilhas").** Por exemplo, todas as folhas de azevinho em
  verde ou todas as estrelas em vermelho, inclusive as laterais de detalhes em relevo,
  sem usar o pincel.
- **Ajusta a purga para cada par de cores.** A tabela de purga (quanto filamento é descartado em cada
  troca de cor) é recalculada para os carretéis que estão de fato no seu ACE, e você pode calibrar cada
  par: "o branco saiu acinzentado depois do preto" → mais purga só de preto → branco.
- **Nunca sobrescreve nada.** Grava `<nome>_KobraX.3mf` ao lado do original.

## Requisitos

- Windows com o **Anycubic Slicer Next** instalado. Ele é detectado sozinho; se não for,
  defina `CONVERSOR3MF_SLICER` com a pasta dele.
- No Linux, o pacote do Anycubic Slicer Next do AUR (`anycubicslicernext-bin`), em
  `/opt/AnycubicSlicerNext`, também é detectado; em outro lugar, defina `CONVERSOR3MF_SLICER`.
  Testado no Manjaro com o Anycubic Slicer Next 2.0.0.5.
- **Python 3.10 ou mais novo**.
- Uma **Kobra X** com ACE. Outras impressoras Anycubic podem funcionar, mas não foram
  testadas (veja [Limitações](#limitações)).

**Testado com:** firmware 2.0.2.8 da Kobra X e Anycubic Slicer Next 2.0.0.3. Se você usa outras
versões e algo se comportar diferente, abra uma issue informando as suas versões.

## Instalação

```bash
pip install conversor3mf
```

### Usando pelo Claude (MCP)

```bash
claude mcp add conversor3mf --scope user -- conversor3mf-mcp
```

Se você usa o [uv](https://docs.astral.sh/uv/), dá para pular o `pip install`:
`claude mcp add conversor3mf --scope user -- uvx --from conversor3mf conversor3mf-mcp`

**Claude Desktop (app de conversa):** abra Configurações → Desenvolvedor → Editar configuração,
adicione o servidor ao `claude_desktop_config.json` e reinicie o app:

```json
{
  "mcpServers": {
    "conversor3mf": { "command": "python", "args": ["-m", "conversor3mf.servidor_mcp"] }
  }
}
```

Depois é só pedir:

> "Converte o C:\Downloads\porta-copos.3mf para a minha Kobra X"
>
> "Troquei o slot 4 por um PLA amarelo"
>
> "No porta-copos, deixa as folhas de azevinho verdes e as estrelas vermelhas"

O Claude mostra em qual slot cada cor vai sair antes de converter. Para repintar, ele olha
um mapa numerado do modelo.

## Primeira configuração: diga o que está no seu ACE

1. No Anycubic Slicer Next, escolha a Kobra X, sincronize o ACE e salve qualquer projeto.
2. Rode o comando abaixo, ou peça ao Claude "configura meu ACE a partir desse projeto":

   ```bash
   conversor3mf ace definir "C:\caminho\do\projeto_salvo.3mf"
   ```

Isso guarda o perfil da impressora e a cor e o material de cada slot. Se você só trocar a
cor de um carretel, atualize assim:

```bash
conversor3mf ace slot 4 --cor "#FFD700" --tipo PLA
```

Para um material que ainda não está em nenhum slot (ABS, TPU…), salve um projeto novo com
ele e rode `ace definir` de novo.

Os dados ficam em `%APPDATA%\conversor3mf`. Dá para mudar o local com `CONVERSOR3MF_DADOS`.

## Passo a passo: conversando com o Claude

Escreva na sua língua, do jeito que pediria a um amigo. Estes são os pedidos que funcionam
melhor, na ordem em que você costuma precisar deles.

**1. Primeira vez: mostre o seu ACE ao Claude**

Sincronize o ACE no Anycubic Slicer Next, salve qualquer projeto e peça:

> "Configura meu ACE usando o projeto C:\Users\eu\Documents\qualquer_projeto.3mf"

O Claude lê os slots e mostra a lista. Confira se as cores e os materiais batem com os
carretéis que estão de fato na impressora.

**2. Sempre que trocar um carretel**

> "Troquei o slot 4 por um PLA amarelo"
>
> "O que tem no meu ACE agora?"

Para um material que ainda não está em nenhum slot (ABS, TPU…), repita o passo 1 com um
projeto que use esse material.

**3. Convertendo um arquivo**

Informe sempre o **caminho completo** do arquivo, ou a pasta e o nome dele:

> "Converte o C:\Downloads\porta-copos.3mf para a minha Kobra X"

Primeiro o Claude mostra **em qual slot cada cor vai sair** e avisa dos problemas. Depois:

- Se estiver tudo certo: "pode converter".
- Se alguma cor não tiver carretel parecido, troque o carretel e avise o Claude ("coloquei
  um PLA verde no slot 4") ou force um slot: "põe o laranja (filamento 3) no slot 3".
- Se o modelo tiver mais cores que slots, diga quais juntar: "usa o slot do preto para o
  preto e para o cinza-escuro".

**4. Vários arquivos de uma vez**

> "Lista os 3MF da pasta C:\Downloads e converte os que forem para impressoras Bambu"

**5. Repintando partes do modelo ("ilhas")**

Use o arquivo já convertido (`..._KobraX.3mf`) e diga **o quê** e **qual cor**:

> "No C:\Downloads\porta-copos_KobraX.3mf, deixa as folhas de azevinho verdes e as estrelas
> vermelhas"

O Claude desenha um mapa numerado de cada região de mesma cor, escolhe os números e mostra
uma prévia do resultado. Dicas:

- Descreva a parte pela **forma, posição ou cor atual**: "as estrelinhas brancas", "as
  folhas em volta da borda", "as bolinhas vermelhas do gorro".
- Em figuras 3D, peça **outra vista**: "olha de frente" (ou de trás, da esquerda, da
  direita, de baixo).
- Se os números estiverem amontoados, peça **zoom**: "dá um zoom no canto superior esquerdo".
- Corrija usando os números do mapa: "a ilha 42 não, era a 32".
- Nada é sobrescrito: cada repintura cria um arquivo novo `..._repintado.3mf`.

**6. Conferindo antes de imprimir**

> "Confere o C:\Downloads\porta-copos_KobraX.3mf no slicer"

Em projetos com mais de uma placa, abra também o arquivo no Anycubic Slicer Next e dê uma
olhada (veja [Limitações](#limitações)).

**7. Calibrando a purga (cor manchada ou desperdício demais)**

Cada troca de cor descarta um pouco de filamento. Pouco demais e a cor anterior mancha a nova; demais
desperdiça filamento. Depois de uma impressão, conte ao Claude o que você viu:

> "O branco saiu acinzentado logo depois do preto"
>
> "Mostra quanto cada troca de cor purga"
>
> "Quero economizar filamento, usa a purga no nível economia"

O Claude aumenta (ou diminui) só aquele par, 20% por vez, e lembra disso nas próximas conversões.
Para valer num arquivo já convertido: "aplica a purga nova no porta-copos_KobraX.3mf" (grava
`..._purga.3mf`). Dica: "aprende a purga dos meus projetos em C:\Impressoes" ensina os valores que o
Anycubic Slicer Next calculou para as suas cores.

**O que o Claude não faz:** iniciar a impressão, mudar configurações dentro do slicer ou
baixar modelos do MakerWorld. Baixe o 3MF você mesmo e depois peça.

## Linha de comando

```bash
conversor3mf planejar  modelo.3mf               # mostra em qual slot cada cor vai sair
conversor3mf converter modelo.3mf --mapa 1=3    # converte; força o filamento 1 no slot 3
conversor3mf ilhas     modelo_KobraX.3mf --vista cima   # mapa numerado das regiões de cor
conversor3mf repintar  modelo_KobraX.3mf 32=4,3=3       # repinta as ilhas 32 e 3
conversor3mf verificar modelo_KobraX.3mf        # reabre no slicer e compara
```

Todos os comandos e opções também funcionam em **inglês e espanhol**: use o que for mais
natural para você. A ajuda e as mensagens de erro saem na língua em que você digitou o
comando, ou na língua do sistema:

| Português | English | Español |
|---|---|---|
| `inspecionar` | `inspect` | `inspeccionar` |
| `planejar` | `plan` | `planificar` |
| `converter` | `convert` | `convertir` |
| `verificar` | `verify` | `verificar` |
| `ilhas` | `islands` | `islas` |
| `repintar` | `repaint` | `repintar` |
| `ace mostrar` / `definir` / `slot` | `ace show` / `setup` / `slot` | `ace mostrar` / `configurar` / `ranura` |
| `--mapa` `--saida` `--sem-verificar` | `--map` `--output` `--no-verify` | `--mapa` `--salida` `--sin-verificar` |
| `--vista cima/baixo/frente/tras/esquerda/direita` | `--view top/bottom/front/back/left/right` | `--vista arriba/abajo/frente/atras/izquierda/derecha` |
| `--cor` `--tipo` `--nome` | `--color` `--type` `--name` | `--color` `--tipo` `--nombre` |
| `purga mostrar` / `ajustar 2 1 mais` / `nivel economia` / `aprender` / `aplicar` | `purge show` / `adjust 2 1 more` / `level economy` / `learn` / `apply` | `purga mostrar` / `ajustar 2 1 más` / `nivel economía` / `aprender` / `aplicar` |

Para forçar uma língua, use `--idioma pt` (ou `en`, `es`) ou a variável
`CONVERSOR3MF_IDIOMA`. Rode `conversor3mf --help` para ver tudo.

## Como funciona

- **Formato das cores.** O 3MF da Bambu e do Orca guarda números de filamento, não cores.
  A pintura de cada triângulo é uma árvore de subdivisões codificada em hexadecimal, com o
  número do filamento em cada folha. O conversor decodifica essa árvore, troca os números
  e codifica de novo. O resto do arquivo não é alterado.
- **Configurações da impressora.** Vêm de um projeto salvo pelo seu próprio Anycubic
  Slicer Next, então o pacote não distribui perfis da Anycubic.
- **Purga.** O firmware da Kobra X lê a tabela de purga (`flush_volumes_matrix`) do cabeçalho do
  G-code e faz a purga sozinho; a purga real é tabela × `flush_multiplier` (0,7). Cada par usa o valor
  que o Anycubic Slicer Next calculou para ele nos seus projetos salvos, ou a fórmula do OrcaSlicer
  mais o volume do bico, vezes a sua calibração.
- **Ilhas.** São triângulos ligados entre si com a mesma cor, depois de juntar vértices
  repetidos. Em triângulos com várias cores, a repintura só muda as partes da cor da ilha,
  inclusive na borda.

## Limitações

- **Conferência de projetos de várias placas.** O Anycubic Slicer Next 2.0.0.3 trava pela
  linha de comando com qualquer projeto de mais de uma placa. Esses projetos só são
  conferidos internamente; abra no slicer antes de fatiar.
- **Distância entre as placas no slicer.** Em projetos de várias placas, o slicer desenha
  as placas lado a lado, com um vão entre elas. A mesa em si tem 260 × 260 mm; a distância
  de uma placa até a seguinte (314,4 mm para o lado e 328,8 mm para baixo) foi medida em
  projetos salvos pelo Anycubic Slicer Next 2.0.0.3 para a Kobra X. Nas outras impressoras,
  o conversor usa 1,2 × o tamanho da mesa, que é o que o Bambu Studio usa.
- **Mais cores que slots.** Cores parecidas são juntadas. Em projetos de várias placas, dá
  para imprimir placa por placa e usar `--mapa`.
- **3MF só com malha.** Arquivos sem projeto do slicer dentro não têm cores para converter.

## Desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\python -m unittest discover -s tests
```

Os testes usam 3MFs sintéticos montados em `tests/fixtures.py` e não precisam do slicer.
`ferramentas/testar_na_interface.ps1` abre um arquivo na interface do slicer, tira uma
captura de tela e fecha o programa.

## Licença

MIT
