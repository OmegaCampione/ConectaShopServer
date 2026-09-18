from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
import datetime

app = FastAPI()

# Catálogo em memória conforme o contrato
CATALOGO = {
    "KB-100": {"name": "Teclado Mecânico", "unitPriceCents": 25990, "available": True},
    "MS-200": {"name": "Mouse Sem Fio", "unitPriceCents": 12990, "available": True},
    "HD-300": {"name": "Headset USB", "unitPriceCents": 19990, "available": True},
    "MN-400": {"name": "Monitor 27", "unitPriceCents": 119990, "available": True}
}

# Função de log padrão
def log_rest(client, req_id, operation, input_data, http_status, result):
    agora = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print(f"[{agora}] protocol=REST server=S01 client={client} requestId={req_id} operation={operation} input={input_data} status={http_status} result={result}")

# Middleware para exigir os headers obrigatórios
@app.middleware("http")
async def check_headers(request: Request, call_next):
    client_team = request.headers.get("x-client-team")
    req_id = request.headers.get("x-request-id")
    
    if not client_team or not req_id:
        return JSONResponse(
            status_code=400,
            content={"code": "MISSING_REQUIRED_HEADER", "message": "Headers obrigatórios ausentes"}
        )
        
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id # Devolver o request-id
    return response

# Endpoint 1: Consultar Produto
@app.get("/api/v1/products/{sku}")
def get_product(sku: str, request: Request):
    client = request.headers.get("x-client-team")
    req_id = request.headers.get("x-request-id")
    
    if sku not in CATALOGO:
        log_rest(client, req_id, "GET_PRODUCT", sku, 404, "PRODUCT_NOT_FOUND")
        return JSONResponse(
            status_code=404,
            content={"code": "PRODUCT_NOT_FOUND", "message": "Product not found", "requestId": req_id}
        )
    
    produto = CATALOGO[sku].copy()
    produto["sku"] = sku
    log_rest(client, req_id, "GET_PRODUCT", sku, 200, "OK")
    return produto

# Modelos para Cotação
class QuoteItem(BaseModel):
    sku: str
    quantity: int = Field(ge=1, le=10) # Quantidade entre 1 e 10

class QuoteRequest(BaseModel):
    items: List[QuoteItem] = Field(min_length=1, max_length=5) # 1 a 5 itens

# Endpoint 2: Cotação
@app.post("/api/v1/quotes")
def calculate_quote(quote: QuoteRequest, request: Request):
    client = request.headers.get("x-client-team")
    req_id = request.headers.get("x-request-id")
    
    skus_vistos = set()
    subtotal_cents = 0
    
    # Validações e soma
    for item in quote.items:
        if item.sku in skus_vistos:
            log_rest(client, req_id, "POST_QUOTE", item.sku, 422, "INVALID_QUANTITY_OR_ITEMS")
            return JSONResponse(status_code=422, content={"code": "INVALID_QUANTITY_OR_ITEMS", "message": "SKU duplicado", "requestId": req_id})
        
        if item.sku not in CATALOGO:
            log_rest(client, req_id, "POST_QUOTE", item.sku, 422, "INVALID_PRODUCT")
            return JSONResponse(status_code=422, content={"code": "INVALID_PRODUCT", "message": "SKU inválido", "requestId": req_id})
            
        skus_vistos.add(item.sku)
        subtotal_cents += CATALOGO[item.sku]["unitPriceCents"] * item.quantity
        
    # Regra de desconto
    discount_percent = 0
    if subtotal_cents >= 100000:
        discount_percent = 10
    elif subtotal_cents >= 50000:
        discount_percent = 5
        
    discount_cents = int(subtotal_cents * discount_percent / 100)
    total_cents = subtotal_cents - discount_cents
    
def log_rest(client, req_id, operation, input_data, http_status, result):
    agora = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    mensagem = f"[{agora}] protocol=REST server=S01 client={client} requestId={req_id} operation={operation} input={input_data} status={http_status} result={result}\n"
    print(mensagem, end="")
    with open("integration_logs.txt", "a", encoding="utf-8") as f:
        f.write(mensagem)

# Para rodar (execute isso em um terminal separado):
# uvicorn rest_server:app --host 0.0.0.0 --port 8080