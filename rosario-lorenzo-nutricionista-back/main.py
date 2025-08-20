from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mercadopago
import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import urllib.parse
from typing import Optional 

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
FRONT_URL = os.getenv("FRONT_URL", "https://ro-lorenzo-nutricionista-4k9y.onrender.com")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ro-lorenzo-nutricionista-back.onrender.com/webhook")


RESERVA_MINUTOS = 2


def es_pendiente_vigente(turno):
    if turno["estado"] != "pendiente_de_pago":
        return False
    try:
        fecha_creacion = datetime.fromisoformat(turno["fecha_creacion"])  # puede venir con tz o sin tz
    except Exception:
        return False
    ahora = datetime.now(fecha_creacion.tzinfo) if fecha_creacion.tzinfo else datetime.now()
    return (ahora - fecha_creacion) < timedelta(minutes=RESERVA_MINUTOS)


def limpiar_turnos_vencidos(turnos):
    ahora = datetime.now()
    filtrados = []
    for turno in turnos:
        if turno["estado"] == "pendiente_de_pago":
            fecha_creacion = datetime.fromisoformat(turno["fecha_creacion"])
            if ahora - fecha_creacion < timedelta(minutes=RESERVA_MINUTOS):
                filtrados.append(turno)
        else:
            filtrados.append(turno)
    return filtrados


class TurnoRequest(BaseModel):
    nombre: str
    apellido: str
    telefono: str
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

    # Bloquear creación si el horario ya está reservado o confirmado
    for t in turnos:
        mismo_horario = (
            t["modalidad"].lower() == turno.modalidad.lower()
            and t["fecha"] == turno.fecha
            and t["hora"] == turno.hora
        )
        if not mismo_horario:
            continue
        if t["estado"] == "confirmado" or es_pendiente_vigente(t):
            raise HTTPException(status_code=409, detail="El horario seleccionado ya no está disponible. Por favor elegí otro.")

    turno_id = str(uuid.uuid4())
    token_cancelacion = str(uuid.uuid4())

    turno_data = {
        "id": turno_id,
        "estado": "pendiente_de_pago",
        "nombre": turno.nombre,
        "apellido": turno.apellido,
        "telefono": turno.telefono,
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

    query_string = urllib.parse.urlencode({
        "nombre": turno.nombre,
        "apellido": turno.apellido,
        "telefono": turno.telefono,
        "motivo": turno.motivo,
        "modalidad": turno.modalidad,
        "fecha": turno.fecha,
        "hora": turno.hora,
        "ubicacion": turno.ubicacion,
    })

    # Ventana de expiración de preferencia (2 minutos)
    ahora_utc = datetime.now(timezone.utc)
    expira_utc = ahora_utc + timedelta(minutes=RESERVA_MINUTOS)

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
            # Permitir solo tarjeta (crédito/débito/prepaga) o billetera Mercado Pago (account_money)
            # Excluir efectivo/cupones (ticket), transferencia/depósitos (bank_transfer) y cajero (atm)
            "excluded_payment_types": [
                {"id": "ticket"},
                {"id": "bank_transfer"},
                {"id": "atm"}
            ],
            "installments": 1
        },
        "back_urls": {
            "success": f"{FRONT_URL}/gracias?{query_string}",
            "failure": f"{FRONT_URL}/error?id={turno_id}",
            "pending": f"{FRONT_URL}/pending"
        },
        "auto_return": "approved",
        # Expiración del checkout para desalojar inactividad
        "expires": True,
        "expiration_date_from": ahora_utc.isoformat().replace("+00:00", "Z"),
        "expiration_date_to": expira_utc.isoformat().replace("+00:00", "Z")
    }

    try:
        preference_response = sdk.preference().create(preference_data)
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

    horarios_ocupados = []
    for t in turnos:
        if t["modalidad"].lower() != modalidad.lower() or t["fecha"] != fecha:
            continue
        if t["estado"] == "confirmado" or es_pendiente_vigente(t):
            horarios_ocupados.append(t["hora"])
    return horarios_ocupados


@app.delete("/cancelar-turno")
def cancelar_turno(id: str):
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
        nuevos_turnos = [t for t in turnos if t["id"] != id]
        with open("turnos.json", "w", encoding="utf-8") as f:
            json.dump(nuevos_turnos, f, indent=2, ensure_ascii=False)
        return {"status": "turno cancelado"}
    except Exception as e:
        print(f"[ERROR] No se pudo cancelar el turno: {e}")
        raise HTTPException(500, "No se pudo cancelar el turno")

@app.get("/ver-turnos")
def ver_turnos(estado: Optional[str] = Query(None)):
    """
    Devuelve todos los turnos.
    Si se pasa ?estado=confirmado o ?estado=pendiente_de_pago, los filtra.
    """
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)

        # Aplicar limpieza de vencidos
        turnos = limpiar_turnos_vencidos(turnos)

        if estado:
            turnos = [t for t in turnos if t["estado"] == estado]

        return {"turnos": turnos}

    except Exception as e:
        print(f"[ERROR] No se pudieron leer los turnos: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron leer los turnos")


@app.get("/estado-turno")
def estado_turno(id: str = Query(...)):
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        turnos = []

    turnos = limpiar_turnos_vencidos(turnos)

    with open("turnos.json", "w", encoding="utf-8") as f:
        json.dump(turnos, f, indent=2, ensure_ascii=False)

    for t in turnos:
        if t["id"] == id:
            if t["estado"] == "pendiente_de_pago":
                try:
                    fecha_creacion = datetime.fromisoformat(t["fecha_creacion"])
                    ahora = datetime.now(fecha_creacion.tzinfo) if fecha_creacion.tzinfo else datetime.now()
                    restante = (timedelta(minutes=RESERVA_MINUTOS) - (ahora - fecha_creacion)).total_seconds()
                    restante = max(0, int(restante))
                except Exception:
                    restante = 0
                return {"estado": t["estado"], "segundos_restantes": restante}
            return {"estado": t["estado"], "segundos_restantes": 0}
    raise HTTPException(status_code=404, detail="Turno no encontrado")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
