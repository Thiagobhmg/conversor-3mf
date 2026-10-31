# Research — #3 Manter o estilo de qualidade do processo original

Issue: [#3](https://github.com/Thiagobhmg/conversor-3mf/issues/3). Base: `a82d05f`. Documento descritivo, sem propor
mudanças.

## 1. Como o processo da Kobra X é escolhido hoje

`_escolher_processo(config, fonte)` ([conversor.py:254](../../conversor3mf/conversor.py#L254)):

- `config` é o molde já ajustado aos slots; `fonte` é o `project_settings.config` do arquivo original.
- Altura: `fonte["layer_height"]`, senão a do molde, senão 0,2 (valor que não vira número também cai em 0,2).
- Tenta, nesta ordem, `"{altura:.2f}mm {estilo} @{printer_settings_id do molde}"` com os estilos `Standard`,
  `High Quality`, `Draft`, `Extra Draft`, e devolve `(perfil, nome)` do primeiro que `perfil_de_processo` achar.
- Sem nenhum: `(None, print_settings_id do molde)`.
- **Não lê o nome do processo original** (`fonte["print_settings_id"]`).

Chamador único: `_montar_config` ([conversor.py:268](../../conversor3mf/conversor.py#L268), chamada na L275). Com
perfil, copia para o config todas as chaves do perfil que já existem no config (menos `CHAVES_META`) e grava
`print_settings_id = nome`. Depois aplica `CHAVES_DO_MODELO` do original (altura, paredes, preenchimento,
suportes…), que **não** inclui velocidades nem acelerações. `_montar_config` tem um chamador, `converter`
([L403](../../conversor3mf/conversor.py#L403)), que monta os `avisos` ([L405](../../conversor3mf/conversor.py#L405))
e devolve o nome em `Resultado.processo` (`"perfil_de_processo"` no resumo da CLI e do MCP). Nenhum aviso fala da
escolha do processo.

## 2. Nomes de processo da Bambu (perfis BBL do OrcaSlicer 2.4.2, A1)

| Processo | Altura | Parede externa | Acel. parede | Acel. geral |
|---|---|---|---|---|
| 0.08mm Extra Fine | 0,08 | — | — | — |
| 0.08mm High Quality | 0,08 | — | — | — |
| 0.12mm Fine | 0,12 | 200 | 5000 | 6000 |
| 0.12mm High Quality | 0,12 | — | — | — |
| 0.16mm Optimal | 0,16 | 200 | 5000 | 6000 |
| 0.16mm High Quality | 0,16 | 60 | 2000 | 4000 |
| 0.20mm Standard | 0,20 | 200 | 5000 | 6000 |
| 0.20mm Strength | 0,20 | — | — | — |
| 0.24mm Draft / 0.28mm Extra Draft | 0,24 / 0,28 | — | — | — |

(— = não conferido.) `Extra Fine`, `Fine`, `Optimal`, `Standard`, `Draft` e `Extra Draft` nomeiam a altura de camada
com as mesmas velocidades; `High Quality` é a variante lenta. Usuários podem salvar cópias com sufixo (ex.:
`… - Copy`), mantendo o nome-base.

## 3. Processos da Kobra X 0.4 no Anycubic Slicer Next 2.0.0.5

`Standard`: 0,08, 0,12, 0,16, 0,20, 0,24, 0,28. `High Quality`: 0,12, 0,16, 0,20. Não há `Draft` nem `Extra Draft`.
Arquivos sem `inherits`.

## 4. Caso real que motivou

`jesus+makerworld.3mf` (MakerWorld): `print_settings_id = "0.16mm High Quality @BBL A1"`, `layer_height = 0.16`,
`different_settings_to_system[0] = "prime_tower_rib_wall"`. Hoje sairia com `0.16mm Standard @Anycubic Kobra X 0.4
nozzle` (Standard é tentado primeiro e existe).

## 5. Testes existentes

Nenhum teste passa por `_escolher_processo` com perfil: a classe `Base` usa `CONVERSOR3MF_SLICER=nenhum`. O projeto
sintético não tem `print_settings_id` e usa `layer_height` `"0.16"`; o molde sintético tem
`printer_settings_id = "Anycubic Kobra X 0.4 nozzle"`, `sparse_infill_speed = "200"` e não tem velocidades de parede.
Uma instalação falsa no layout do Windows (`AnycubicSlicerNext.exe` + `resources/profiles/Anycubic`) é achada por
`CONVERSOR3MF_SLICER` em qualquer sistema com o código desta base.
