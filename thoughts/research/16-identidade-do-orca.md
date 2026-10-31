# Research — #16 Convertido aberto como "projeto do Bambu Studio" no OrcaSlicer

Issue: [#16](https://github.com/Thiagobhmg/conversor-3mf/issues/16). Base: `fix/12-escolhas-do-designer` (#14, sobre #13).
Documento descritivo (2026-10-30).

## 1. O que foi observado

Jesus convertido (molde do OrcaSlicer, opção A, `--mapa 5=3`) aberto como projeto na 5ª instância do OrcaSlicer
(2.4.2-mcp.13), iniciando-a com o arquivo:

- aviso modal "O arquivo 3MF foi criado pelo Bambu Studio. Algumas configurações podem ser diferentes do OrcaSlicer."
  (precisou de clique humano);
- depois do OK: 3 placas com os nomes do designer, presets certos por nome (`Anycubic Kobra X 0.4 nozzle`,
  `0.16mm High Quality @Anycubic Kobra X`, 4 × `Generic PETG`), cores dos slots certas;
- **valores do arquivo descartados**: `nozzle_temperature` 230 (arquivo: 236), `textured_plate_temp` 75 (80),
  `cool_plate_temp` 70 (75), `retraction_distances_when_cut` 0 (18); `get_status.modified` vazio.
- `load_model` do MCP, com a instância vazia, importou o mesmo arquivo **só como geometria**: 1 placa, objetos fora
  dela, presets inalterados.

## 2. Marcas de identidade

| | `3D/3dmodel.model` | `Metadata/slice_info.config` (header) |
|---|---|---|
| Molde gravado pelo OrcaSlicer | `Application = BambuStudio-02.06.00.51`, **`OrcaSlicer = 2.4.2`** | `X-BBL-Client-Type`, `X-BBL-Client-Version`, **`OrcaSlicer-Version`** |
| Molde gravado pelo Anycubic Slicer Next | `Application = BambuStudio-2.0.0.5` | `X-ACNext-Client-Type`, `X-ACNext-Client-Version` |
| Convertido hoje | `Application` do molde; demais metadados do **original** (Bambu) | `X-ACNext-Client-Type`, `X-ACNext-Client-Version` (= `version` do config), `X-Conversor3mf` |

## 2b. Experimentos depois da primeira correção (marcas de identidade)

- Convertido **com** as marcas do OrcaSlicer, aberto ao iniciar a 5ª instância: carregou sozinho (porta em 15 s,
  projeto e 3 placas prontos pelo MCP), mas os valores de filamento **continuaram** os do preset (230/75/70) e
  `modified` vazio. As marcas não eram a causa disso.
- Cópia do mesmo arquivo com `different_settings_to_system[1..4]` =
  `cool_plate_temp;cool_plate_temp_initial_layer;nozzle_temperature;nozzle_temperature_initial_layer;textured_plate_temp;textured_plate_temp_initial_layer`:
  o OrcaSlicer aplicou 236/236 °C, 80 e 75 °C, marcou os 6 campos como alterados e criou presets de projeto
  (`Generic PETG @Anycubic Kobra X 0.4 nozzle(<arquivo>)`) para os slots 2–4.
- Conclusão: ao abrir um projeto, o OrcaSlicer parte dos presets pelo nome e só mantém do arquivo as chaves listadas em
  `different_settings_to_system`. O molde gerado pela linha de comando tem essa lista vazia (a CLI tratou os JSON
  carregados como os próprios presets), e o conversor só preenche a posição 0 (processo).

## 3. Código

- `ace.definir_molde` guarda só `_aplicativo` (o `Application` do molde) no molde salvo.
- `conversor._montar_config` tira `_aplicativo` do config antes de gravar o `project_settings.config`.
- `conversor._ajustar_principal` troca o `Application` do `3dmodel.model`; não mexe em outros metadados.
- `conversor.converter` descarta o `slice_info.config` original (regex `DESCARTAR`) e grava um novo, sempre no formato
  do Anycubic Slicer Next.
- `purga.aprender` só aprende de arquivos com `X-ACNext` e sem `X-Conversor3mf`.
- Testes: o molde sintético (`criar_molde_anycubic`) não tem `slice_info.config` nem a marca `OrcaSlicer`.
