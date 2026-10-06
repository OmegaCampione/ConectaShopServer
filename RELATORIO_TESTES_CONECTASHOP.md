# Relatorio de testes ConectaShop

Data/hora local: 2026-10-06 18:16

## Ambiente usado

- PDF analisado: `DOC-20260909-WA0048.pdf`
- README seguido: `README.md`
- Codigo testado: `conectashop-servidor`
- REST: `http://127.0.0.1:8080`
- gRPC: `127.0.0.1:50051`
- Comando do cliente:
  `python cliente.py --rest http://127.0.0.1:8080 --grpc 127.0.0.1:50051`

## Testes obrigatorios do PDF

Todos os testes obrigatorios passaram usando `cliente.py` depois dos ajustes nas respostas REST de erro.

| Teste | Resultado observado |
| --- | --- |
| R1 GET KB-100 | PASS: HTTP 200, `unitPriceCents=25990` |
| R2 GET XX-999 | PASS: HTTP 404, `code=PRODUCT_NOT_FOUND` |
| R3 POST quote 2x KB-100 + 1x MS-200 | PASS: HTTP 200, `totalCents=61722` |
| R4 POST quote 1x MN-400 | PASS: HTTP 200, `discountPercent=10`, `totalCents=107991` |
| R5 POST quote com SKU inexistente | PASS: HTTP 422, `code=INVALID_PRODUCT` |
| G1 Health | PASS: `status=SERVING`, `server_team=S01` |
| G2 1500g LOCAL STANDARD | PASS: `price_cents=1800`, `estimated_days=2` |
| G3 2500g REGIONAL EXPRESS | PASS: `price_cents=4600`, `estimated_days=2` |
| G4 1000g NATIONAL STANDARD | PASS: `price_cents=3400`, `estimated_days=7` |
| G5 weight_grams=0 | PASS: `INVALID_ARGUMENT` |

Evidencias geradas:

- `conectashop-servidor/client_logs.txt`
- `conectashop-servidor/integration_logs.txt`

## Verificacoes extras de conformidade

O gRPC respondeu corretamente aos erros adicionais verificados:

| Caso | Resultado observado |
| --- | --- |
| Metadata `x-client-team` ausente | `INVALID_ARGUMENT`, `MISSING_CLIENT_TEAM` |
| `request_id` vazio | `INVALID_ARGUMENT`, `MISSING_REQUEST_ID` |
| `zone` UNSPECIFIED | `INVALID_ARGUMENT`, `INVALID_ZONE` |
| `mode` UNSPECIFIED | `INVALID_ARGUMENT`, `INVALID_MODE` |

## Validacoes REST corrigidas

As validacoes REST abaixo foram testadas novamente e agora seguem o formato/codigo definido no PDF.

| Caso | Resultado observado |
| --- | --- |
| JSON invalido em `POST /api/v1/quotes` | HTTP 400, `code=INVALID_REQUEST`, com `requestId` |
| Campo obrigatorio ausente em `POST /api/v1/quotes` | HTTP 400, `code=INVALID_REQUEST`, com `requestId` |
| Quantidade fora do intervalo, exemplo `quantity=0` | HTTP 422, `code=INVALID_QUANTITY_OR_ITEMS`, com `requestId` |
| Header obrigatorio ausente, com `X-Request-ID` enviado | HTTP 400, `code=MISSING_REQUIRED_HEADER`, com `requestId` |

## Conclusao

O projeto esta funcional para os testes obrigatorios R1-R5 e G1-G5 pedidos no PDF. A parte gRPC passou nas verificacoes extras de erro e os principais erros REST verificados agora seguem o formato/codigo definido no contrato.
