from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mercadopago
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import urllib.parse

# Cargar variables de entorno (.env)
load_dotenv()

# Inicializar la app FastAPI
app = FastAPI()

# Permitir llamadas desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ro-lorenzo-nutricionista.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el SDK de Mercado Pago
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

# Leer FRONT_URL desde .env
FRONT_URL = os.getenv("FRONT_URL", "http://localhost:3000")

# Modelo del turno
class TurnoRequest(BaseModel):
    nombre: str
    apellido: str
    motivo: str
    modalidad: str
    fecha: str
    hora: str
    duracion: str
    costo: float
    ubicacion: str

# Crear preferencia de pago
@app.post("/crear-preferencia")
def crear_preferencia(turno: TurnoRequest):
    print("\n--- [INFO] Endpoint /crear-preferencia alcanzado. ---")

    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        turnos = []

    turno_id = str(uuid.uuid4())
    token_cancelacion = str(uuid.uuid4())
    turno_data = {
        "id": turno_id,
        "estado": "pendiente_de_pago",
        "nombre": turno.nombre,
        "apellido": turno.apellido,
        "motivo": turno.motivo,
        "modalidad": turno.modalidad,
        "fecha": turno.fecha,
        "hora": turno.hora,
        "duracion": turno.duracion,
        "costo": turno.costo,
        "ubicacion": turno.ubicacion,
        "token_cancelacion": token_cancelacion,
        "fecha_creacion": datetime.now().isoformat()
    }
    with open("turnos.json", "w", encoding="utf-8") as f:
        turnos.append(turno_data)
        json.dump(turnos, f, indent=2, ensure_ascii=False)

    print("[INFO] Turno guardado localmente. Preparando datos para Mercado Pago...")

    params_para_url = {
        "nombre": turno.nombre,
        "apellido": turno.apellido,
        "motivo": turno.motivo,
        "modalidad": turno.modalidad,
        "fecha": turno.fecha,
        "hora": turno.hora,
        "ubicacion": turno.ubicacion,
    }
    query_string = urllib.parse.urlencode(params_para_url)

    preference_data = {
        "items": [
            {
                "title": f"Turno - {turno.motivo}",
                "quantity": 1,
                "unit_price": float(turno.costo),
                "currency_id": "ARS"
            }
        ],
        "external_reference": turno_id,
        "notification_url": "https://tu-backend.com/webhook",  # aún no implementado
        "back_urls": {
            "success": f"{FRONT_URL}/gracias?{query_string}",
            "failure": f"{FRONT_URL}/error",
            "pending": f"{FRONT_URL}/pending"
        },
        "auto_return": "approved"
    }

    try:
        print("[INFO] Enviando solicitud a la API de Mercado Pago...")
        preference_response = sdk.preference().create(preference_data)
        print("[SUCCESS] Respuesta recibida de Mercado Pago:")
        print(preference_response)
        init_point = preference_response["response"]["init_point"]
        return {"pago_url": init_point}

    except Exception as e:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!! [ERROR] Ocurrió una excepción al llamar a Mercado Pago: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        raise HTTPException(status_code=500, detail="Error al crear preferencia de pago en Mercado Pago.")

# Endpoint para turnos ocupados
@app.get("/turnos-ocupados")
def turnos_ocupados(modalidad: str = Query(...), fecha: str = Query(...)):
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        turnos = []

    horarios_ocupados = [
        turno["hora"]
        for turno in turnos
        if turno["modalidad"] == modalidad and turno["fecha"] == fecha and turno["estado"] in ["pendiente_de_pago", "confirmado"]
    ]

    return horarios_ocupados

# 🟩 BLOQUE CLAVE PARA RENDER
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render asigna PORT en runtime
    uvicorn.run("main:app", host="0.0.0.0", port=port)
