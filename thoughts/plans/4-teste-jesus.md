# Plan — #4 Teste real com `jesus+makerworld.3mf`

Issue: [#4](https://github.com/Thiagobhmg/conversor-3mf/issues/4).
Pesquisa: [thoughts/research/4-teste-jesus.md](../research/4-teste-jesus.md).
Branch: `improve/4-teste-jesus`, worktree `.claude/worktrees/4-teste-jesus/`. **Depende de #7 e #8**: a branch parte
de `fix/2-suporte-linux` com `improve/3-estilo-qualidade` unida por merge; depois que os dois entrarem na `main`,
rebase sobre a `main` (sobram só `thoughts/` e o relatório).

## Decisões

- Tudo grava dentro do worktree: `CONVERSOR3MF_DADOS=.local/dados`, saídas em `.local/artifacts/`, temporários em
  `.local/tmp/`. O original só é lido.
- Molde gerado pela linha de comando do Anycubic Slicer Next com perfis de sistema e as cores lidas do ACE (pesquisa
  §3), em vez de esperar um molde salvo pela interface.
- Conversão com o plano automático; o mapa manual (qual cor junta com qual) é decisão do usuário.
- OrcaSlicer só numa instância isolada, nunca na compartilhada (13130). Nada é enviado à impressora.

## Fases

| Fase | Critério de sucesso |
|---|---|
| 1. Molde de 4 slots | `ace definir` aceita; 4 slots PETG com as cores do ACE. |
| 2. Inspecionar e planejar | 6 cores → 4 slots, avisos de PLA → PETG e de cores juntadas. |
| 3. Converter | Arquivo em `.local/artifacts/`, processo High Quality, chaves do designer mantidas, pintura e peças batendo com a inspeção, original intacto. |
| 4. Abrir no OrcaSlicer pelo MCP (instância isolada) | 3 placas, Kobra X, cores nos slots; fatiar cada placa sem erro; conferir escolhas do designer no G-code. |
| 5. Relatório e Issues | Resultado no PR; Issues para o que for encontrado. |

## Progresso

| Fase | Estado | Notas |
|---|---|---|
| 1 | concluída | Molde `molde-cores.3mf` gerado pela CLI do slicer com 4 cópias do JSON de PETG (uma cor por slot). PETG de fábrica a 230 °C. |
| 2 | concluída | Plano automático deixa o slot 4 (bege) sem uso; amarelo e preto com qualidade "ruim". |
| 3 | concluída | 10 s; `0.16mm High Quality @Anycubic Kobra X 0.4 nozzle`; 4 chaves do designer mantidas; pintura 12.792/1.365, peças 32/29/5; original intacto. Conferência pela CLI pulada (3 placas); a CLI do slicer cai com falha de segmentação também no original. |
| 4 | **bloqueada** | Falta uma instância isolada do OrcaSlicer com MCP nesta sessão (registro feito pelo usuário). |
| 5 | em andamento | |
