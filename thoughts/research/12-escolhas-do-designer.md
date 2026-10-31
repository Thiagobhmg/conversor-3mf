# Research — #12 O que conta como escolha do designer

Issue: [#12](https://github.com/Thiagobhmg/conversor-3mf/issues/12). Base: `feat/11-orcaslicer` (`3717e97`), porque
mexe na mesma função que a #11. Documento descritivo, sem propor mudanças.

## 1. Como as "escolhas do modelo" entram hoje

Em `_montar_config` ([conversor.py](../../conversor3mf/conversor.py)), depois de aplicar o perfil de processo da Kobra X:

- para cada chave de `CHAVES_DO_MODELO` (estrutura, suportes, borda, costura, ironing, compensações…), se ela existe no
  original e no config, com o mesmo tipo, e o valor **difere**, o valor do original é copiado e entra em `alteradas`;
- `CHAVES_FUNCAO` (filamento de parede, preenchimento, suporte) é remapeada à parte, pelos slots;
- `different_settings_to_system[0]` do convertido recebe as chaves de `alteradas`;
- `alteradas` aparece no resumo como `configuracoes_mantidas_do_modelo`.

O código não olha o que o designer mudou: qualquer diferença entre o perfil de origem e o da Kobra X é copiada,
inclusive padrões de fábrica da outra impressora.

## 2. Onde o projeto registra o que o designer mudou

`project_settings.config` → `different_settings_to_system`: lista com `1 + n_filamentos + 1` textos (processo, cada
filamento, impressora), cada um com as chaves alteradas em relação ao perfil de sistema, separadas por `;`. Projetos
sem essa chave existem (o projeto sintético dos testes não a tem).

## 3. Caso real (Jesus, MakerWorld)

- `print_settings_id = "0.16mm High Quality @BBL A1"`;
  `different_settings_to_system = ["prime_tower_rib_wall", "", "", "", "", "", "", ""]`: o designer mudou só
  `prime_tower_rib_wall` (que não está em `CHAVES_DO_MODELO`).
- Mesmo assim, a conversão levou `support_on_build_plate_only=0`, `support_interface_bottom_layers=2`,
  `tree_support_wall_count=-1` e `elefant_foot_compensation=0.075`, padrões do perfil da A1.
- `tree_support_wall_count=-1` fica fora da faixa do OrcaSlicer (0–2): a linha de comando do Orca recusa o arquivo.

## 4. Testes existentes

`test_converter` usa o projeto sintético (sem `different_settings_to_system`) e espera `layer_height = 0.16` e
`wall_loops = 3` levados do original. O molde sintético tem `layer_height` e `wall_loops`, mas não
`elefant_foot_compensation` nem `tree_support_wall_count`.

## 5. Decisão do usuário (2026-10-30)

Opção **A**: só o que o designer mudou no perfil dele; o resto vem do perfil equivalente da Kobra X.
