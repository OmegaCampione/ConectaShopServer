import grpc
from concurrent import futures
import math
import datetime
import shipping_pb2
import shipping_pb2_grpc

SERVER_TEAM = "S04" # Alterar para o código da equipe no dia

# Tabelas de preço conforme contrato
TARIFAS = {
    shipping_pb2.LOCAL: {shipping_pb2.STANDARD: 1000, shipping_pb2.EXPRESS: 1600},
    shipping_pb2.REGIONAL: {shipping_pb2.STANDARD: 1800, shipping_pb2.EXPRESS: 2800},
    shipping_pb2.NATIONAL: {shipping_pb2.STANDARD: 3000, shipping_pb2.EXPRESS: 4500},
}
ADICIONAL = {shipping_pb2.STANDARD: 400, shipping_pb2.EXPRESS: 600}
PRAZO = {
    shipping_pb2.LOCAL: {shipping_pb2.STANDARD: 2, shipping_pb2.EXPRESS: 1},
    shipping_pb2.REGIONAL: {shipping_pb2.STANDARD: 4, shipping_pb2.EXPRESS: 2},
    shipping_pb2.NATIONAL: {shipping_pb2.STANDARD: 7, shipping_pb2.EXPRESS: 3},
}

def log_grpc(client, req_id, operation, input_data, status, result):
    agora = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    mensagem = f"[{agora}] protocol=GRPC server=S04 client={client} requestId={req_id} operation={operation} input={input_data} status={status} result={result}\n"
    print(mensagem, end="")
    with open("integration_logs.txt", "a", encoding="utf-8") as f:
        f.write(mensagem)
class ShippingService(shipping_pb2_grpc.ShippingServiceServicer):
    
    def get_client_team(self, context):
        metadata = dict(context.invocation_metadata())
        team = metadata.get("x-client-team")
        if not team:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "MISSING_CLIENT_TEAM")
        return team

    def Health(self, request, context):
        client = self.get_client_team(context)
        log_grpc(client, "N/A", "Health", "N/A", "OK", "SERVING")
        return shipping_pb2.HealthResponse(status="SERVING", server_team=SERVER_TEAM)

    def CalculateShipping(self, request, context):
        client = self.get_client_team(context)
        
        # Validações
        if not request.request_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "MISSING_REQUEST_ID")
        if request.weight_grams < 1 or request.weight_grams > 30000:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "INVALID_WEIGHT")
        if request.zone == shipping_pb2.SHIPPING_ZONE_UNSPECIFIED:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "INVALID_ZONE")
        if request.mode == shipping_pb2.SHIPPING_MODE_UNSPECIFIED:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "INVALID_MODE")

        # Cálculos
        kg_cobrados = math.ceil(request.weight_grams / 1000)
        tarifa_base = TARIFAS[request.zone][request.mode]
        valor_adicional = ADICIONAL[request.mode] * kg_cobrados
        price_cents = tarifa_base + valor_adicional
        dias = PRAZO[request.zone][request.mode]

        log_grpc(client, request.request_id, "CalculateShipping", f"{request.weight_grams}g", "OK", price_cents)

        return shipping_pb2.ShippingResponse(
            request_id=request.request_id,
            price_cents=price_cents,
            estimated_days=dias,
            server_team=SERVER_TEAM
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    shipping_pb2_grpc.add_ShippingServiceServicer_to_server(ShippingService(), server)
    server.add_insecure_port('[::]:50051') # Escuta em 0.0.0.0
    print("Servidor gRPC rodando na porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()