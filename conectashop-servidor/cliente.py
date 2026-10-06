import requests
import grpc
import time
import uuid
import datetime
import argparse
import shipping_pb2
import shipping_pb2_grpc

CLIENT_TEAM = "C02"

def log_client(protocol, server_team, req_id, operation, target, status, duration_ms, result):
    agora = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    msg = f"[{agora}] protocol={protocol} client={CLIENT_TEAM} server={server_team} requestId={req_id} operation={operation} target={target} status={status} durationMs={duration_ms} result={result}"
    print(msg)
    with open("client_logs.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def run_rest_tests(base_url):
    print("\n--- INICIANDO TESTES REST ---")
    server_team = "S??" 
    
    def do_request(method, endpoint, json_body=None):
        req_id = f"req-{uuid.uuid4().hex[:6]}"
        headers = {"X-Client-Team": CLIENT_TEAM, "X-Request-ID": req_id}
        target = f"{base_url}{endpoint}"
        
        start_time = time.perf_counter()
        if method == "GET":
            response = requests.get(target, headers=headers)
        else:
            response = requests.post(target, headers=headers, json=json_body)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        return response, req_id, target, duration_ms

    # R1: GET KB-100 
    resp, req_id, target, dur = do_request("GET", "/api/v1/products/KB-100")
    passou = resp.status_code == 200 and resp.json().get("unitPriceCents") == 25990
    log_client("REST", server_team, req_id, "R1_GET_KB-100", target, resp.status_code, dur, "PASS" if passou else "FAIL")

    # R2: GET XX-999 (Esperado: 404)
    resp, req_id, target, dur = do_request("GET", "/api/v1/products/XX-999")
    passou = resp.status_code == 404 and resp.json().get("code") == "PRODUCT_NOT_FOUND"
    log_client("REST", server_team, req_id, "R2_GET_XX-999", target, resp.status_code, dur, "PASS" if passou else "FAIL")

    # R3: POST quote 2x KB-100 + 1x MS-200 
    payload_r3 = {"items": [{"sku": "KB-100", "quantity": 2}, {"sku": "MS-200", "quantity": 1}]}
    resp, req_id, target, dur = do_request("POST", "/api/v1/quotes", payload_r3)
    passou = resp.status_code == 200 and resp.json().get("totalCents") == 61722
    log_client("REST", server_team, req_id, "R3_POST_QUOTE_1", target, resp.status_code, dur, "PASS" if passou else "FAIL")

    # R4: POST quote 1x MN-400 
    payload_r4 = {"items": [{"sku": "MN-400", "quantity": 1}]}
    resp, req_id, target, dur = do_request("POST", "/api/v1/quotes", payload_r4)
    passou = resp.status_code == 200 and resp.json().get("totalCents") == 107991 and resp.json().get("discountPercent") == 10
    log_client("REST", server_team, req_id, "R4_POST_QUOTE_2", target, resp.status_code, dur, "PASS" if passou else "FAIL")

    # R5: POST quote com SKU inexistente 
    payload_r5 = {"items": [{"sku": "FAKE-99", "quantity": 1}]}
    resp, req_id, target, dur = do_request("POST", "/api/v1/quotes", payload_r5)
    passou = resp.status_code == 422 and resp.json().get("code") == "INVALID_PRODUCT"
    log_client("REST", server_team, req_id, "R5_POST_INVALID_SKU", target, resp.status_code, dur, "PASS" if passou else "FAIL")

def run_grpc_tests(target_address):
    print("\n--- INICIANDO TESTES GRPC ---")
    channel = grpc.insecure_channel(target_address)
    stub = shipping_pb2_grpc.ShippingServiceStub(channel)
    metadata = (('x-client-team', CLIENT_TEAM),)
    server_team = "UNKNOWN"

    def measure_call(func, request):
        req_id = f"req-{uuid.uuid4().hex[:6]}"
        if hasattr(request, 'request_id'):
            request.request_id = req_id
            
        start_time = time.perf_counter()
        try:
            response = func(request, metadata=metadata)
            status_code = "OK"
        except grpc.RpcError as e:
            response = None
            status_code = e.code().name
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return response, req_id, status_code, duration_ms

    # G1: Health 
    resp, req_id, status, dur = measure_call(stub.Health, shipping_pb2.HealthRequest())
    passou = status == "OK" and resp.status == "SERVING"
    if passou:
        server_team = resp.server_team
    log_client("GRPC", server_team, req_id, "G1_HEALTH", target_address, status, dur, "PASS" if passou else "FAIL")

    # G2: 1500g, LOCAL, STANDARD 
    req = shipping_pb2.ShippingRequest(weight_grams=1500, zone=shipping_pb2.LOCAL, mode=shipping_pb2.STANDARD)
    resp, req_id, status, dur = measure_call(stub.CalculateShipping, req)
    passou = status == "OK" and resp.price_cents == 1800 and resp.estimated_days == 2
    log_client("GRPC", server_team, req_id, "G2_CALC_LOCAL_STD", target_address, status, dur, "PASS" if passou else "FAIL")

    # G3: 2500g, REGIONAL, EXPRESS 
    req = shipping_pb2.ShippingRequest(weight_grams=2500, zone=shipping_pb2.REGIONAL, mode=shipping_pb2.EXPRESS)
    resp, req_id, status, dur = measure_call(stub.CalculateShipping, req)
    passou = status == "OK" and resp.price_cents == 4600 and resp.estimated_days == 2
    log_client("GRPC", server_team, req_id, "G3_CALC_REG_EXP", target_address, status, dur, "PASS" if passou else "FAIL")

    # G4: 1000g, NATIONAL, STANDARD 
    req = shipping_pb2.ShippingRequest(weight_grams=1000, zone=shipping_pb2.NATIONAL, mode=shipping_pb2.STANDARD)
    resp, req_id, status, dur = measure_call(stub.CalculateShipping, req)
    passou = status == "OK" and resp.price_cents == 3400 and resp.estimated_days == 7
    log_client("GRPC", server_team, req_id, "G4_CALC_NAT_STD", target_address, status, dur, "PASS" if passou else "FAIL")

    # G5: weight_grams = 0
    req = shipping_pb2.ShippingRequest(weight_grams=0, zone=shipping_pb2.LOCAL, mode=shipping_pb2.STANDARD)
    resp, req_id, status, dur = measure_call(stub.CalculateShipping, req)
    passou = status == "INVALID_ARGUMENT"
    log_client("GRPC", server_team, req_id, "G5_CALC_INVALID_WEIGHT", target_address, status, dur, "PASS" if passou else "FAIL")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente ConectaShop")
    parser.add_argument("--rest", default="http://127.0.0.1:8080", help="URL base do servidor REST")
    parser.add_argument("--grpc", default="127.0.0.1:50051", help="Host:Porta do servidor gRPC")
    args = parser.parse_args()

    run_rest_tests(args.rest)
    run_grpc_tests(args.grpc)
    print("\nTestes concluídos. Verifique o arquivo client_logs.txt")