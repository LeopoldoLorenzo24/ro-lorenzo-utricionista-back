from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mercadopago
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib.parse

# Cargar variables de entorno (.env)
load_dotenv()

# Inicializar la app FastAPI
app = FastAPI()

# Permitir llamadas desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ro-lorenzo-nutricionista.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el SDK de Mercado Pago
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

# Leer URLs desde .env o usar por defecto las URL desplegadas
FRONT_URL = os.getenv("FRONT_URL", "https://ro-lorenzo-nutricionista.onrender.com")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ro-lorenzo-nutricionista-back.onrender.com/webhook")


def limpiar_turnos_vencidos(turnos):
    ahora = datetime.now()
    filtrados = []
    for turno in turnos:
        if turno["estado"] == "pendiente_de_pago":
            fecha_creacion = datetime.fromisoformat(turno["fecha_creacion"])
            if ahora - fecha_creacion < timedelta(minutes=1):  # ahora 12h para pagos en efectivo
                filtrados.append(turno)
        else:
            filtrados.append(turno)
    return filtrados


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


@app.post("/crear-preferencia")
def crear_preferencia(turno: TurnoRequest):
    print("\n--- [INFO] Endpoint /crear-preferencia alcanzado. ---")

    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        turnos = []

    turnos = limpiar_turnos_vencidos(turnos)

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

    turnos.append(turno_data)
    with open("turnos.json", "w", encoding="utf-8") as f:
        json.dump(turnos, f, indent=2, ensure_ascii=False)

    print("[INFO] Turno guardado. Preparando preferencia...")

    if not FRONT_URL or not FRONT_URL.startswith("http"):
        raise HTTPException(status_code=500, detail="FRONT_URL no está definido correctamente.")

    query_string = urllib.parse.urlencode({
        "nombre": turno.nombre,
        "apellido": turno.apellido,
        "motivo": turno.motivo,
        "modalidad": turno.modalidad,
        "fecha": turno.fecha,
        "hora": turno.hora,
        "ubicacion": turno.ubicacion,
    })

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
        "notification_url": WEBHOOK_URL,
        "payment_methods": {
            "excluded_payment_types": [{"id": "atm"}],
            "installments": 1
        },
        "back_urls": {
            "success": f"{FRONT_URL}/gracias?{query_string}",
            "failure": f"{FRONT_URL}/error?id={turno_id}",
            "pending": f"{FRONT_URL}/pending"
        },
        "auto_return": "approved"
    }

    try:
        print("[INFO] Enviando solicitud a la API de Mercado Pago...")
        preference_response = sdk.preference().create(preference_data)
        print("[SUCCESS] Preferencia creada:", preference_response)

        if "init_point" not in preference_response["response"]:
            raise ValueError("init_point no recibido de Mercado Pago")

        init_point = preference_response["response"]["init_point"]
        return {"pago_url": init_point}

    except Exception as e:
        print("[ERROR] al crear preferencia:", e)
        raise HTTPException(status_code=500, detail="Error al crear preferencia de pago.")


@app.post("/webhook")
async def recibir_webhook(request: Request):
    try:
        body = await request.json()
        print("[INFO] Webhook recibido:", body)

        if body.get("type") != "payment":
            return {"status": "ignorado"}

        payment_id = body.get("data", {}).get("id")
        if not payment_id:
            return {"status": "sin id de pago"}

        payment_info = sdk.payment().get(payment_id)
        status = payment_info["response"].get("status")
        external_reference = payment_info["response"].get("external_reference")

        if status == "approved":
            with open("turnos.json", "r+", encoding="utf-8") as f:
                turnos = json.load(f)
                for turno in turnos:
                    if turno["id"] == external_reference:
                        turno["estado"] = "confirmado"
                        break
                f.seek(0)
                json.dump(turnos, f, indent=2, ensure_ascii=False)
                f.truncate()
            print(f"[INFO] Turno {external_reference} marcado como confirmado.")
        return {"status": "ok"}

    except Exception as e:
        print(f"[ERROR] en webhook: {e}")
        return {"status": "error"}


@app.get("/turnos-ocupados")
def turnos_ocupados(modalidad: str = Query(...), fecha: str = Query(...)):
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        turnos = []

    turnos = limpiar_turnos_vencidos(turnos)
    with open("turnos.json", "w", encoding="utf-8") as f:
        json.dump(turnos, f, indent=2, ensure_ascii=False)

    horarios_ocupados = [
        turno["hora"]
        for turno in turnos
        if turno["modalidad"].lower() == modalidad.lower() and turno["fecha"] == fecha and turno["estado"] == "confirmado"
    ]
    return horarios_ocupados


@app.delete("/cancelar-turno")
def cancelar_turno(id: str):
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
        nuevos_turnos = [t for t in turnos if t["id"] != id]
        with open("turnos.json", "w", encoding="utf-8") as f:
            json.dump(nuevos_turnos, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Turno cancelado manualmente: {id}")
        return {"status": "turno cancelado"}
    except Exception as e:
        print(f"[ERROR] No se pudo cancelar el turno: {e}")
        raise HTTPException(500, "No se pudo cancelar el turno")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
