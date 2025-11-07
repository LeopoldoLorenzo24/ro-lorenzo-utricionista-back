"""
Test de reserva REAL de turno - Antropometría
Fecha: 13 de noviembre de 2025
Hora: 17:15
"""
import requests
import json
import time

BACKEND_URL = "https://ro-lorenzo-nutricionista-back.onrender.com"

print("=" * 70)
print("🧪 TEST DE RESERVA REAL - ANTROPOMETRÍA")
print("=" * 70)

# Datos del turno a reservar
turno_data = {
    "nombre": "Leonardo",
    "apellido": "Lorenzo",
    "telefono": "351-1234567",
    "motivo": "Antropometría",
    "modalidad": "presencial",
    "fecha": "2025-11-13",
    "hora": "17:15",
    "duracion": "30 minutos",
    "costo": 15000.0,
    "ubicacion": "GOOD LIFE CENTER"
}

print("\n📋 Datos del turno a reservar:")
print(f"   Paciente: {turno_data['nombre']} {turno_data['apellido']}")
print(f"   Teléfono: {turno_data['telefono']}")
print(f"   Motivo: {turno_data['motivo']}")
print(f"   Modalidad: {turno_data['modalidad']}")
print(f"   Fecha: {turno_data['fecha']}")
print(f"   Hora: {turno_data['hora']}")
print(f"   Duración: {turno_data['duracion']}")
print(f"   Costo: ${turno_data['costo']}")
print(f"   Ubicación: {turno_data['ubicacion']}")

# 1. Verificar horarios ocupados ANTES de la reserva
print("\n" + "=" * 70)
print("1️⃣ VERIFICANDO HORARIOS OCUPADOS ANTES DE LA RESERVA")
print("=" * 70)

try:
    response = requests.get(
        f"{BACKEND_URL}/turnos-ocupados",
        params={
            "modalidad": turno_data['modalidad'],
            "fecha": turno_data['fecha']
        },
        timeout=10
    )
    
    if response.status_code == 200:
        horarios_ocupados_antes = response.json()
        print(f"✅ Horarios ocupados antes: {horarios_ocupados_antes}")
        
        if turno_data['hora'] in horarios_ocupados_antes:
            print(f"⚠️  ADVERTENCIA: El horario {turno_data['hora']} ya está ocupado!")
            print("   Se intentará reservar de todas formas (debería fallar)")
        else:
            print(f"✅ El horario {turno_data['hora']} está DISPONIBLE")
    else:
        print(f"❌ Error al verificar horarios: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# 2. Crear preferencia de pago (reservar turno)
print("\n" + "=" * 70)
print("2️⃣ CREANDO PREFERENCIA DE PAGO (RESERVANDO TURNO)")
print("=" * 70)

try:
    response = requests.post(
        f"{BACKEND_URL}/crear-preferencia",
        json=turno_data,
        timeout=15
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Turno reservado exitosamente!")
        print(f"\n📌 Datos de la reserva:")
        print(f"   Turno ID: {data.get('turno_id')}")
        print(f"   URL de pago: {data.get('pago_url')[:80]}...")
        
        turno_id = data.get('turno_id')
        pago_url = data.get('pago_url')
        
        print(f"\n💳 Link de pago de MercadoPago:")
        print(f"   {pago_url}")
        
    elif response.status_code == 409:
        print(f"❌ El horario ya está ocupado (esperado si ya estaba reservado)")
        print(f"   Detalle: {response.json().get('detail')}")
        turno_id = None
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        turno_id = None
        
except Exception as e:
    print(f"❌ Error al crear preferencia: {e}")
    turno_id = None

# 3. Verificar horarios ocupados DESPUÉS de la reserva
if turno_id:
    print("\n" + "=" * 70)
    print("3️⃣ VERIFICANDO HORARIOS OCUPADOS DESPUÉS DE LA RESERVA")
    print("=" * 70)
    
    time.sleep(2)  # Esperar un poco para que se guarde en la BD
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/turnos-ocupados",
            params={
                "modalidad": turno_data['modalidad'],
                "fecha": turno_data['fecha']
            },
            timeout=10
        )
        
        if response.status_code == 200:
            horarios_ocupados_despues = response.json()
            print(f"✅ Horarios ocupados después: {horarios_ocupados_despues}")
            
            if turno_data['hora'] in horarios_ocupados_despues:
                print(f"✅ CORRECTO: El horario {turno_data['hora']} ahora aparece como OCUPADO")
            else:
                print(f"❌ ERROR: El horario {turno_data['hora']} NO aparece como ocupado")
        else:
            print(f"❌ Error al verificar horarios: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 4. Verificar estado del turno
    print("\n" + "=" * 70)
    print("4️⃣ VERIFICANDO ESTADO DEL TURNO")
    print("=" * 70)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/estado-turno",
            params={"id": turno_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estado del turno: {data.get('estado')}")
            print(f"   Segundos restantes para pagar: {data.get('segundos_restantes')}")
            
            if data.get('estado') == 'pendiente_de_pago':
                minutos = data.get('segundos_restantes') // 60
                segundos = data.get('segundos_restantes') % 60
                print(f"   ⏰ Tiempo restante: {minutos}m {segundos}s")
        else:
            print(f"❌ Error al verificar estado: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 5. Ver todos los turnos
    print("\n" + "=" * 70)
    print("5️⃣ VIENDO TODOS LOS TURNOS EN LA BASE DE DATOS")
    print("=" * 70)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/ver-turnos",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            turnos = data.get('turnos', [])
            print(f"✅ Total de turnos en la BD: {len(turnos)}")
            
            # Mostrar solo el turno recién creado
            for turno in turnos:
                if turno.get('id') == turno_id:
                    print(f"\n📋 Turno recién creado:")
                    print(f"   ID: {turno.get('id')}")
                    print(f"   Estado: {turno.get('estado')}")
                    print(f"   Paciente: {turno.get('nombre')} {turno.get('apellido')}")
                    print(f"   Fecha/Hora: {turno.get('fecha')} {turno.get('hora')}")
                    print(f"   Modalidad: {turno.get('modalidad')}")
                    print(f"   Costo: ${turno.get('costo')}")
        else:
            print(f"❌ Error al ver turnos: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETADO")
print("=" * 70)

if turno_id:
    print("\n📧 NOTA: Se debería haber enviado un email a licrosariomlorenzo@gmail.com")
    print("   con los detalles de la reserva. ¡Revisá la casilla!")
    print("\n💳 Para completar el pago, abrí el link de MercadoPago mostrado arriba")
    print("   (El turno expira en 2 minutos si no se paga)")
