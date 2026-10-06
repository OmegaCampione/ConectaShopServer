# ConectaShop Server

Projeto do grupo Servidor para o laboratorio de interoperabilidade REST e gRPC.

## 1. Preparando o ambiente

No terminal, na pasta raiz do projeto:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install fastapi uvicorn grpcio grpcio-tools pydantic requests
```

Os arquivos Python do servidor ficam em `conectashop-servidor`. Antes de subir servidores ou rodar o cliente, entre nessa pasta:

```powershell
cd conectashop-servidor
```

## 2. Subindo os servidores

Abra dois terminais. Nos dois, ative o ambiente virtual e entre na pasta `conectashop-servidor`.

Terminal 1, servidor REST:

```powershell
..\venv\Scripts\activate
uvicorn rest_server:app --host 0.0.0.0 --port 8080
```

Terminal 2, servidor gRPC:

```powershell
..\venv\Scripts\activate
python grpc_server.py
```

Portas usadas:

- REST: `8080`
- gRPC: `50051`

Para testes em outra maquina da mesma rede, informe o IP da maquina que esta rodando os servidores:

- REST_BASE_URL: `http://SEU_IP:8080`
- GRPC_TARGET: `SEU_IP:50051`

Exemplo local:

- REST_BASE_URL: `http://127.0.0.1:8080`
- GRPC_TARGET: `127.0.0.1:50051`

Se o Windows mostrar aviso de firewall, permita o acesso para que outras maquinas consigam chamar os servidores.

## 3. Como o cliente chama nosso servidor

O cliente REST deve enviar:

- Base URL: `http://IP_DO_SERVIDOR:8080`
- Header obrigatorio: `X-Client-Team`
- Header obrigatorio: `X-Request-ID`
- Content-Type em chamadas com body: `application/json`

Endpoints REST:

- `GET /api/v1/products/{sku}`
- `POST /api/v1/quotes`

O cliente gRPC deve usar:

- Target: `IP_DO_SERVIDOR:50051`
- Metadata obrigatoria: `x-client-team`
- Service: `shipping.v1.ShippingService`
- RPCs: `Health` e `CalculateShipping`

## 4. Testando a integracao com o cliente do projeto

Com REST e gRPC rodando, abra um terceiro terminal, ative o ambiente virtual e entre em `conectashop-servidor`:

```powershell
..\venv\Scripts\activate
python cliente.py --rest http://127.0.0.1:8080 --grpc 127.0.0.1:50051
```

Para testar contra outra maquina, troque `127.0.0.1` pelo IP do servidor:

```powershell
python cliente.py --rest http://SEU_IP:8080 --grpc SEU_IP:50051
```

O cliente executa os testes obrigatorios do PDF:

- REST: R1, R2, R3, R4 e R5
- gRPC: G1, G2, G3, G4 e G5

Os logs ficam em:

- `client_logs.txt`
- `integration_logs.txt`
