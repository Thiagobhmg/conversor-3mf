# Research — #4 Teste real com `jesus+makerworld.3mf`

Issue: [#4](https://github.com/Thiagobhmg/conversor-3mf/issues/4). Código: `fix/2-suporte-linux` (#7) +
`improve/3-estilo-qualidade` (#8), unidos neste worktree. Registro do que existe e do que foi observado em
2026-10-30, sem propor mudanças.

## 1. O arquivo original

"Jesus with Heart – Mini Flexi Articulated Figure" (designer `helder.bernardo`, MakerWorld), lido em
`~/Projetos/ser/impressao3d/bonecos/Jesus/` e nunca alterado (sha256 conferido antes e depois).

- `BambuStudio-02.05.00.64`, Bambu Lab A1, `0.16mm High Quality @BBL A1`, 3 placas, não fatiado.
- 6 filamentos PLA: 1 branco `#FFFFFF`, 2 rosa `#D4B1DD`, 3 vermelho `#F72323`, 4 marrom `#7C4B00`,
  5 amarelo `#FFFF00` (Silk), 6 preto `#000000`. Todos usados (pintura e peças).
- 33 MB compactado; malhas de 133 MB e 48 MB descompactadas. Sem `custom_gcode_per_layer.xml`.
- Ajuste do designer sobre o sistema: só `prime_tower_rib_wall`.

## 2. ACE da Kobra X (ponte KX, só leitura)

Slots 1–4: PETG `#EFF0F1` branco, `#7C4D3A` marrom, `#E10600` vermelho, `#DEB79D` bege.

## 3. Molde

- Nenhum projeto existente servia: os válidos (Anycubic Slicer Next, Kobra X sem alterações, sem perfis embutidos)
  têm no máximo 2 filamentos.
- A linha de comando do Anycubic Slicer Next 2.0.0.5 gera um projeto com os perfis de sistema
  (`--load-settings "<machine>;<process>" --load-filaments "<f1>;…;<f4>" --export-3mf … cubo.stl`). Com os 4 JSON de
  sistema do PETG, `filament_colour` sai com **uma** cor (as demais listas saem com 4). Com cópias do JSON contendo
  `filament_colour` = cor de cada slot, sai com as 4 cores, `different_settings_to_system` vazio, sem perfis
  embutidos e com a assinatura `X-ACNext`. Esse projeto foi aceito por `ace definir`.
- O PETG do molde é o de fábrica: 230 °C (o padrão local de impressão é 236 °C).

## 4. Inspeção e plano (CLI do conversor)

- `inspecionar`: 6 filamentos usados; amarelo só na placa 1, preto nas placas 1 e 2.
- `planejar` automático (mais cores que slots, cada cor vai para o slot mais parecido):

| Filamento | → Slot | ΔE | Qualidade |
|---|---|---|---|
| 1 branco | 1 branco | 3,1 | boa |
| 2 rosa | 1 branco | 22,1 | aproximada |
| 3 vermelho | 3 vermelho | 6,7 | boa |
| 4 marrom | 2 marrom | 13,6 | aproximada |
| 5 amarelo | 1 branco | 31,4 | ruim |
| 6 preto | 2 marrom | 31,8 | ruim |

O **slot 4 (bege) fica sem uso**. Diferenças para o bege: branco 21,3, rosa 26,0, vermelho 30,7, marrom 39,1,
amarelo 32,4, preto 68,4.

## 5. Conversão

`converter --saida <worktree>/.local/artifacts/jesus_KobraX.3mf` (caminho absoluto, por causa da #6): 10 s, saída 0.

- Processo `0.16mm High Quality @Anycubic Kobra X 0.4 nozzle` (com a #3; sem ela seria Standard).
- Mantidas do designer, além do que já coincide com o perfil: `support_on_build_plate_only` 0,
  `support_interface_bottom_layers` 2, `tree_support_wall_count` -1, `elefant_foot_compensation` 0.075.
- Coincidem com o original: camada 0,16, 2 paredes, 15 %, topo `monotonicline`, sem suporte, sem saia, parede externa
  60 mm/s e aceleração 2000.
- Filamentos: 4 × PETG a 230 °C, cores do ACE. `post_process` vazio, G-code de início do molde.
- Pintura: slot 1 = 12.792 triângulos (1.010 branco + 11.782 rosa), slot 2 = 1.365 (marrom). Peças: slot 1 = 32,
  slot 2 = 29, slot 3 = 5. Batem com a inspeção.
- Descartado do original: só `Metadata/filament_sequence.json`. 3 placas mantidas.

## 6. Conferência pelo slicer em projetos de várias placas

O conversor pula a conferência pela linha de comando com mais de uma placa (o autor relata travamento no Windows,
2.0.0.3). No Linux (2.0.0.5), `--export-3mf` **fecha com falha de segmentação** (saída 139, ~10 s) tanto no arquivo
convertido quanto no **original** do MakerWorld: a falha é da linha de comando do slicer, não da conversão.

## 7. OrcaSlicer

- Quatro instâncias rodando (portas 13130–13133). Nesta sessão só há o MCP `orcaslicer` (13130), compartilhado:
  tinha 6 objetos de outra sessão e 41 chaves de processo alteradas sem salvar. `load_model` de um projeto ou
  `select_preset` ali arriscam o trabalho dessa sessão.
- Instâncias isoladas documentadas em `Thiagobhmg/impressao-3d: ia/mcp/instancias-paralelas.md`: a 2ª
  (`orcaslicer-2`) está registrada só para `~/Projetos/ser/impressao3d`; a 3ª (13132, `orcaslicer-mcp-server-3`)
  roda sem MCP registrado. Registrar servidor MCP é configuração do Claude Code (o usuário faz).
- Presets do Orca para a Kobra X têm nomes diferentes dos do Anycubic Slicer Next (ex.: processo
  `0.20mm Standard @Anycubic Kobra X` sem "0.4 nozzle"); o comportamento ao abrir o 3MF convertido não foi observado.
