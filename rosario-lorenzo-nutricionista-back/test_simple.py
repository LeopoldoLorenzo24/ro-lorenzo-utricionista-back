"""
Test simple para verificar creación de turno
"""
import requests
import json
from datetime import datetime, timedelta

BACKEND_URL = "https://ro-lorenzo-nutricionista-back.onrender.com"

print("🧪 Test de creación de turno\n")

# Datos del turno
fecha_turno = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

turno_data = {
    "nombre": "TEST",
    "apellido": "PRUEBA",
    "telefono": "+54 9 11 9999-9999",
    "motivo": "Antropometría",
    "modalidad": "presencial",
    "fecha": fecha_turno,
    "hora": "14:00",
    "duracion": "30 minutos",
    "costo": 15000.0,
    "ubicacion": "Test Location"
}

print("📝 Creando turno...")
print(f"   Fecha: {fecha_turno} 14:00")
print(f"   Cliente: TEST PRUEBA")
print()

try:
    response = requests.post(
        f"{BACKEND_URL}/crear-preferencia",
        json=turno_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📄 Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("Ahora verificando si se guardó en la BD...")
print("="*60 + "\n")

try:
    response = requests.get(f"{BACKEND_URL}/ver-turnos")
    turnos = response.json()["turnos"]
    
    print(f"Total turnos en BD: {len(turnos)}")
    
    if turnos:
        print("\nÚltimo turno:")
        print(json.dumps(turnos[0], indent=2, ensure_ascii=False))
    else:
        print("❌ No hay turnos en la base de datos")
        
except Exception as e:
    print(f"❌ Error: {e}")
