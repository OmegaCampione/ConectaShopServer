# 1. Preparando o ambiente

Rode no terminal, um comando por vez:

python -m venv venv
.\venv\Scripts\activate
pip install fastapi uvicorn grpcio grpcio-tools pydantic requests

# 2. Subindo os servidores

Abra dois terminais na pasta do projeto. Lembre de ativar o ambiente virtual em ambos (.\venv\Scripts\activate) antes de rodar:

No Terminal 1 (REST):

uvicorn rest_server:app --host 0.0.0.0 --port 8080
No Terminal 2 (gRPC):

python grpc_server.py

(Aviso: Se o firewall do Windows abrir um pop-up, clique em Permitir para liberar as portas na rede local).

# 3. Testando a integração (Cliente)

Com os servidores rodando, abra um terceiro terminal, ative o venv e execute:

python cliente.py --rest http://127.0.0.1:8080 --grpc 127.0.0.1:50051
