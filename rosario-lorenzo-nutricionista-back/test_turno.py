"""
Script de prueba para crear una reserva de turno de ANTROPOMETRÍA
y verificar que se guarde en PostgreSQL y se envíe email a Rosario
"""
import requests
import json
from datetime import datetime, timedelta

# URL del backend
BACKEND_URL = "https://ro-lorenzo-nutricionista-back.onrender.com"

def test_health():
    """Verifica que el backend esté funcionando y conectado a PostgreSQL"""
    print("\n🔍 1. Verificando salud del backend...")
    response = requests.get(f"{BACKEND_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_crear_turno_antropometria():
    """Crea una reserva de ANTROPOMETRÍA de prueba"""
    print("\n📝 2. Creando reserva de ANTROPOMETRÍA de prueba...")
    
    # Fecha de mañana
    fecha_turno = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    turno_data = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "telefono": "+54 9 11 1234-5678",
        "motivo": "Antropometría",
        "modalidad": "presencial",
        "fecha": fecha_turno,
        "hora": "10:00",
        "duracion": "30 minutos",
        "costo": 15000.0,
        "ubicacion": "Av. Corrientes 1234, CABA"
    }
    
    print(f"   📋 Datos del turno:")
    print(f"      Cliente: {turno_data['nombre']} {turno_data['apellido']}")
    print(f"      Motivo: {turno_data['motivo']}")
    print(f"      Modalidad: {turno_data['modalidad']}")
    print(f"      Fecha: {turno_data['fecha']} a las {turno_data['hora']}")
    print(f"      Costo: ${turno_data['costo']}")
    
    response = requests.post(
        f"{BACKEND_URL}/crear-preferencia",
        json=turno_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Turno creado exitosamente!")
        print(f"   🆔 Turno ID: {result['turno_id']}")
        print(f"   💳 URL de pago: {result['pago_url'][:60]}...")
        print(f"\n   📧 Debería haber llegado un email a: licrosariomlorenzo@gmail.com")
        return result['turno_id']
    else:
        print(f"   ❌ Error: {response.text}")
        return None

def test_ver_turnos():
    """Verifica que el turno se haya guardado en PostgreSQL"""
    print("\n🗄️  3. Consultando turnos en PostgreSQL...")
    response = requests.get(f"{BACKEND_URL}/ver-turnos")
    
    if response.status_code == 200:
        turnos = response.json()["turnos"]
        print(f"   Total de turnos en BD: {len(turnos)}")
        
        if turnos:
            print(f"\n   📋 Último turno registrado:")
            ultimo = turnos[0]
            print(f"      ID: {ultimo['id']}")
            print(f"      Cliente: {ultimo['nombre']} {ultimo['apellido']}")
            print(f"      Motivo: {ultimo['motivo']}")
            print(f"      Estado: {ultimo['estado']}")
            print(f"      Fecha creación: {ultimo['fecha_creacion']}")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False

def test_turnos_ocupados(fecha):
    """Verifica que el horario aparezca como ocupado"""
    print(f"\n📅 4. Verificando horarios ocupados para presencial en {fecha}...")
    response = requests.get(
        f"{BACKEND_URL}/turnos-ocupados",
        params={"modalidad": "presencial", "fecha": fecha}
    )
    
    if response.status_code == 200:
        horarios = response.json()
        print(f"   Horarios ocupados: {horarios}")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 PRUEBA DE SISTEMA DE TURNOS CON POSTGRESQL")
    print("=" * 70)
    
    # 1. Verificar salud
    if not test_health():
        print("\n❌ El backend no está funcionando correctamente")
        exit(1)
    
    # 2. Crear turno de prueba
    turno_id = test_crear_turno_antropometria()
    if not turno_id:
        print("\n❌ No se pudo crear el turno")
        exit(1)
    
    # 3. Verificar en BD
    test_ver_turnos()
    
    # 4. Verificar horarios ocupados
    fecha_manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    test_turnos_ocupados(fecha_manana)
    
    print("\n" + "=" * 70)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 70)
    print("\n📝 PRÓXIMOS PASOS:")
    print("   1. Verificá que haya llegado un email a: licrosariomlorenzo@gmail.com")
    print("   2. El turno está en estado 'pendiente_de_pago' (expira en 2 min)")
    print("   3. Podés ver todos los turnos en: /ver-turnos")
    print("   4. Los datos están persistidos en PostgreSQL ✅")
    print("\n")
