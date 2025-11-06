from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import mercadopago
import os
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import urllib.parse
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importar database y models
from database import engine, get_db, Base
from models import Turno

load_dotenv()

# Crear las tablas en la base de datos al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🔧 Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ro-lorenzo-nutricionista.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
FRONT_URL = os.getenv("FRONT_URL", "https://ro-lorenzo-nutricionista.vercel.app")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ro-lorenzo-nutricionista-back.onrender.com/webhook")

RESERVA_MINUTOS = 2

def es_pendiente_vigente(turno: Turno):
    """Verifica si un turno pendiente aún está vigente (< 2 minutos)"""
    if turno.estado != "pendiente_de_pago":
        return False
    try:
        ahora = datetime.now(timezone.utc)
        # Asegurar que fecha_creacion sea aware
        fecha_creacion = turno.fecha_creacion
        if fecha_creacion.tzinfo is None:
            fecha_creacion = fecha_creacion.replace(tzinfo=timezone.utc)
        return (ahora - fecha_creacion) < timedelta(minutes=RESERVA_MINUTOS)
    except Exception as e:
        print(f"[ERROR] en es_pendiente_vigente: {e}")
        return False

def limpiar_turnos_vencidos(db: Session):
    """Elimina turnos pendientes que hayan expirado (> 2 minutos)"""
    ahora = datetime.now(timezone.utc)
    limite = ahora - timedelta(minutes=RESERVA_MINUTOS)
    
    # Eliminar turnos pendientes expirados
    turnos_eliminados = db.query(Turno).filter(
        Turno.estado == "pendiente_de_pago",
        Turno.fecha_creacion < limite
    ).delete()
    
    if turnos_eliminados > 0:
        db.commit()
        print(f"[INFO] Eliminados {turnos_eliminados} turnos expirados")
    
    return turnos_eliminados

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

# Function to send email
def send_email(to_email: str, subject: str, body: str):
    """
    Envía un email usando Gmail SMTP
    """
    from_email = "rosariomlorenzo365@gmail.com"
    password = os.getenv("EMAIL_PASSWORD")

    if not password:
        print("[ERROR] EMAIL_PASSWORD no configurado en variables de entorno")
        return False

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        print(f"[INFO] Email enviado exitosamente a {to_email}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo enviar email: {e}")
        return False

@app.post("/crear-preferencia")
def crear_preferencia(turno: TurnoRequest, db: Session = Depends(get_db)):
    """
    Crea una preferencia de pago en MercadoPago y guarda el turno en la BD
    """
    print("\n--- [INFO] Endpoint /crear-preferencia alcanzado. ---")

    # Limpiar turnos vencidos
    limpiar_turnos_vencidos(db)

    # Bloquear creación si el horario ya está reservado o confirmado
    turno_existente = db.query(Turno).filter(
        Turno.modalidad == turno.modalidad.lower(),
        Turno.fecha == turno.fecha,
        Turno.hora == turno.hora
    ).first()

    if turno_existente:
        if turno_existente.estado == "confirmado" or es_pendiente_vigente(turno_existente):
            raise HTTPException(
                status_code=409,
                detail="El horario seleccionado ya no está disponible. Por favor elegí otro."
            )

    turno_id = str(uuid.uuid4())
    token_cancelacion = str(uuid.uuid4())

    # Crear objeto Turno para la base de datos
    nuevo_turno = Turno(
        id=turno_id,
        estado="pendiente_de_pago",
        nombre=turno.nombre,
        apellido=turno.apellido,
        telefono=turno.telefono,
        motivo=turno.motivo,
        modalidad=turno.modalidad.lower(),
        fecha=turno.fecha,
        hora=turno.hora,
        duracion=turno.duracion,
        costo=turno.costo,
        ubicacion=turno.ubicacion,
        token_cancelacion=token_cancelacion
    )

    # Guardar en la base de datos
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)
    
    print(f"[INFO] Turno guardado en BD: {turno_id}")

    # Enviar correo al CLIENTE (no a Rosario)
    email_body = f"""Hola {turno.nombre} {turno.apellido},

Gracias por agendar tu turno con Lic. Rosario Lorenzo.

📋 Detalles de tu turno:
- Motivo: {turno.motivo}
- Modalidad: {turno.modalidad}
- Fecha: {turno.fecha}
- Hora: {turno.hora}
- Duración: {turno.duracion}
- Costo: ${turno.costo}
- Ubicación: {turno.ubicacion}

Por favor, completa el pago para confirmar tu turno.
El enlace de pago expira en {RESERVA_MINUTOS} minutos.

¡Te esperamos!

---
Lic. Rosario Lorenzo
Nutricionista
"""
    
    # Enviar email al cliente (turno.telefono podría tener email, pero usamos campo separado)
    # NOTA: Aquí deberías tener el email del cliente, por ahora solo enviamos a Rosario
    send_email("licrosariomlorenzo@gmail.com", f"Nueva reserva de turno - {turno.nombre} {turno.apellido}", email_body)

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

    # Ventana de expiración de preferencia
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
        "expires": True,
        "expiration_date_from": ahora_utc.isoformat().replace("+00:00", "Z"),
        "expiration_date_to": expira_utc.isoformat().replace("+00:00", "Z")
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        if "init_point" not in preference_response["response"]:
            raise ValueError("init_point no recibido de Mercado Pago")
        init_point = preference_response["response"]["init_point"]
        
        print(f"[INFO] Preferencia creada: {init_point[:50]}...")
        
        return {
            "pago_url": init_point,
            "turno_id": turno_id
        }
    except Exception as e:
        print(f"[ERROR] al crear preferencia: {e}")
        # Si falla MercadoPago, eliminar el turno de la BD
        db.delete(nuevo_turno)
        db.commit()
        raise HTTPException(status_code=500, detail="Error al crear preferencia de pago.")

@app.post("/webhook")
async def recibir_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook de MercadoPago para confirmar pagos
    """
    try:
        body = await request.json()
        print(f"[INFO] Webhook recibido: {body}")
        
        if body.get("type") != "payment":
            return {"status": "ignorado"}

        payment_id = body.get("data", {}).get("id")
        if not payment_id:
            return {"status": "sin id de pago"}

        payment_info = sdk.payment().get(payment_id)
        status = payment_info["response"].get("status")
        external_reference = payment_info["response"].get("external_reference")

        print(f"[INFO] Pago {payment_id}: status={status}, turno_id={external_reference}")

        if status == "approved":
            # Buscar el turno en la BD
            turno = db.query(Turno).filter(Turno.id == external_reference).first()
            
            if turno:
                turno.estado = "confirmado"
                db.commit()
                print(f"[INFO] Turno {external_reference} confirmado")
                
                # Enviar email de confirmación a Rosario
                email_confirmacion = f"""¡Nuevo turno confirmado!

Cliente: {turno.nombre} {turno.apellido}
Teléfono: {turno.telefono}
Motivo: {turno.motivo}
Modalidad: {turno.modalidad}
Fecha: {turno.fecha}
Hora: {turno.hora}
Ubicación: {turno.ubicacion}

Pago confirmado por MercadoPago.
"""
                send_email(
                    "licrosariomlorenzo@gmail.com",
                    f"✅ Turno confirmado - {turno.nombre} {turno.apellido}",
                    email_confirmacion
                )
            else:
                print(f"[WARNING] Turno {external_reference} no encontrado en BD")
        
        return {"status": "ok"}

    except Exception as e:
        print(f"[ERROR] en webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/turnos-ocupados")
def turnos_ocupados(
    modalidad: str = Query(...),
    fecha: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Devuelve los horarios ocupados para una modalidad y fecha específica
    """
    # Limpiar turnos vencidos primero
    limpiar_turnos_vencidos(db)

    # Buscar turnos ocupados (confirmados o pendientes vigentes)
    turnos = db.query(Turno).filter(
        Turno.modalidad == modalidad.lower(),
        Turno.fecha == fecha
    ).all()

    horarios_ocupados = []
    for t in turnos:
        if t.estado == "confirmado" or es_pendiente_vigente(t):
            horarios_ocupados.append(t.hora)

    print(f"[INFO] Horarios ocupados para {modalidad}/{fecha}: {horarios_ocupados}")
    return horarios_ocupados

@app.delete("/cancelar-turno")
def cancelar_turno(id: str, db: Session = Depends(get_db)):
    """
    Cancela (elimina) un turno por su ID
    """
    try:
        turno = db.query(Turno).filter(Turno.id == id).first()
        
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        
        db.delete(turno)
        db.commit()
        
        print(f"[INFO] Turno {id} cancelado")
        return {"status": "turno cancelado"}
    except Exception as e:
        print(f"[ERROR] No se pudo cancelar el turno: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cancelar el turno")

@app.get("/ver-turnos")
def ver_turnos(estado: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Devuelve todos los turnos, opcionalmente filtrados por estado
    """
    try:
        # Limpiar turnos vencidos
        limpiar_turnos_vencidos(db)

        # Consultar turnos
        query = db.query(Turno)
        
        if estado:
            query = query.filter(Turno.estado == estado)
        
        turnos = query.order_by(Turno.fecha_creacion.desc()).all()
        
        # Convertir a diccionarios
        turnos_dict = [t.to_dict() for t in turnos]
        
        print(f"[INFO] Devolviendo {len(turnos_dict)} turnos")
        return {"turnos": turnos_dict}

    except Exception as e:
        print(f"[ERROR] No se pudieron leer los turnos: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron leer los turnos")

@app.get("/estado-turno")
def estado_turno(id: str = Query(...), db: Session = Depends(get_db)):
    """
    Devuelve el estado de un turno específico y los segundos restantes si está pendiente
    """
    try:
        # Limpiar turnos vencidos
        limpiar_turnos_vencidos(db)

        turno = db.query(Turno).filter(Turno.id == id).first()
        
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        
        segundos_restantes = 0
        if turno.estado == "pendiente_de_pago":
            try:
                ahora = datetime.now(timezone.utc)
                fecha_creacion = turno.fecha_creacion
                if fecha_creacion.tzinfo is None:
                    fecha_creacion = fecha_creacion.replace(tzinfo=timezone.utc)
                restante = (timedelta(minutes=RESERVA_MINUTOS) - (ahora - fecha_creacion)).total_seconds()
                segundos_restantes = max(0, int(restante))
            except Exception as e:
                print(f"[ERROR] calculando segundos restantes: {e}")
                segundos_restantes = 0
        
        return {
            "estado": turno.estado,
            "segundos_restantes": segundos_restantes
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] en estado_turno: {e}")
        raise HTTPException(status_code=500, detail="Error al consultar estado del turno")

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    """Endpoint raíz"""
    return {"message": "Servidor funcionando correctamente con PostgreSQL"}

@app.get("/debug-db")
def debug_db():
    """Debug: Muestra información de la configuración de DB"""
    import sys
    db_url = os.getenv("DATABASE_URL", "NO CONFIGURADO")
    
    # Ocultar password en la respuesta
    db_url_safe = db_url.replace(db_url.split(":")[2].split("@")[0] if "@" in db_url else "", "***") if db_url != "NO CONFIGURADO" else db_url
    
    return {
        "database_url_configured": db_url != "NO CONFIGURADO",
        "database_url": db_url_safe,
        "python_version": sys.version,
        "database_module_imported": "database" in sys.modules,
        "models_module_imported": "models" in sys.modules,
        "engine_url": str(engine.url) if hasattr(engine, 'url') else "N/A"
    }

@app.get("/debug-email")
def debug_email():
    """Debug: Verifica configuración de EMAIL"""
    email_password = os.getenv("EMAIL_PASSWORD")
    mp_token = os.getenv("MP_ACCESS_TOKEN")
    
    return {
        "email_password_configured": email_password is not None and email_password != "",
        "email_password_length": len(email_password) if email_password else 0,
        "from_email": "rosariomlorenzo365@gmail.com",
        "to_email": "licrosariomlorenzo@gmail.com",
        "mp_access_token_configured": mp_token is not None and mp_token != "",
        "front_url": os.getenv("FRONT_URL", "NO CONFIGURADO"),
        "webhook_url": os.getenv("WEBHOOK_URL", "NO CONFIGURADO")
    }
    
    @app.post("/send-test-email")
    def send_test_email(to_email: str):
        """Envía un email de prueba al correo indicado y devuelve resultado detallado."""
        print(f"[DEBUG] Enviando email de prueba a: {to_email}")

        ok = send_email(to_email, "Prueba de correo - Nutricionista", "Este es un correo de prueba enviado desde el backend.")

        if ok:
            return {"status": "ok", "message": f"Email enviado a {to_email}"}
        else:
            raise HTTPException(status_code=500, detail="No se pudo enviar el email. Revisá EMAIL_PASSWORD en variables de entorno y logs.")

@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Verificar conexión a la BD
        db.execute(text("SELECT 1"))
        db_status = "✅ Conectado"
    except Exception as e:
        db_status = f"❌ Error: {str(e)}"
    
    return {
        "status": "ok",
        "message": "Backend funcionando correctamente",
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
