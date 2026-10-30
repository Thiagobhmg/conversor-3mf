# conversor3mf

[![testes](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml/badge.svg)](https://github.com/JohnnyTrindade/conversor-3mf/actions/workflows/testes.yml)

**Imprima modelos multicoloridos do MakerWorld na Anycubic Kobra X sem recolorir nada.**
[English](README.md)

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
- **Nunca sobrescreve nada.** Grava `<nome>_KobraX.3mf` ao lado do original.

## Requisitos

- Windows com o **Anycubic Slicer Next** instalado. Ele é detectado sozinho; se não for,
  defina `CONVERSOR3MF_SLICER` com a pasta dele.
- **Python 3.10 ou mais novo**.
- Uma **Kobra X** com ACE. Outras impressoras Anycubic podem funcionar, mas não foram
  testadas (veja [Limitações](#limitações)).

## Instalação

```bash
pip install git+https://github.com/JohnnyTrindade/conversor-3mf
```

### Usando pelo Claude (MCP)

```bash
claude mcp add conversor3mf --scope user -- conversor3mf-mcp
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

## Linha de comando

```bash
conversor3mf planejar  modelo.3mf               # mostra em qual slot cada cor vai sair
conversor3mf converter modelo.3mf --mapa 1=3    # converte; força o filamento 1 no slot 3
conversor3mf ilhas     modelo_KobraX.3mf --vista cima   # mapa numerado das regiões de cor
conversor3mf repintar  modelo_KobraX.3mf 32=4,3=3       # repinta as ilhas 32 e 3
conversor3mf verificar modelo_KobraX.3mf        # reabre no slicer e compara
```

## Como funciona

- **Formato das cores.** O 3MF da Bambu e do Orca guarda números de filamento, não cores.
  A pintura de cada triângulo é uma árvore de subdivisões codificada em hexadecimal, com o
  número do filamento em cada folha. O conversor decodifica essa árvore, troca os números
  e codifica de novo. O resto do arquivo não é alterado.
- **Configurações da impressora.** Vêm de um projeto salvo pelo seu próprio Anycubic
  Slicer Next, então o pacote não distribui perfis da Anycubic.
- **Ilhas.** São triângulos ligados entre si com a mesma cor, depois de juntar vértices
  repetidos. Em triângulos com várias cores, a repintura só muda as partes da cor da ilha,
  inclusive na borda.

## Limitações

- **Conferência de projetos de várias placas.** O Anycubic Slicer Next 2.0.0.3 trava pela
  linha de comando com qualquer projeto de mais de uma placa. Esses projetos só são
  conferidos internamente; abra no slicer antes de fatiar.
- **Espaçamento entre placas.** Foi medido só na Kobra X (314,4 × 328,8 mm). Nas outras
  impressoras, o conversor usa 1,2 × o tamanho da mesa.
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
