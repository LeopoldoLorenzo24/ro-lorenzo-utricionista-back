"""
Script de prueba para simular una reserva desde el frontend
"""
import requests
import json
from datetime import datetime, timedelta

# URL del backend
BACKEND_URL = "https://ro-lorenzo-nutricionista-back.onrender.com"
# Para pruebas locales usar: "http://localhost:8000"

def test_crear_reserva():
    """Simula la petición que hace el frontend"""
    
    # Datos de ejemplo que enviaría el frontend
    turno_data = {
        "nombre": "Maria",
        "apellido": "Gonzalez",
        "telefono": "351-9876543",
        "motivo": "1ra Consulta",
        "modalidad": "presencial",
        "fecha": "2025-11-20",
        "hora": "10:00",
        "duracion": "45-60 minutos",
        "costo": 27500,
        "ubicacion": "GOOD LIFE CENTER (San Luis 145, Nueva Córdoba)"
    }
    
    print("=" * 60)
    print("PRUEBA DE RESERVA DE TURNO")
    print("=" * 60)
    print("\n📤 Datos a enviar:")
    print(json.dumps(turno_data, indent=2, ensure_ascii=False))
    
    try:
        print("\n🔄 Enviando petición POST a /crear-preferencia...")
        response = requests.post(
            f"{BACKEND_URL}/crear-preferencia",
            json=turno_data,
            timeout=10
        )
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ÉXITO - La reserva se creó correctamente")
            data = response.json()
            print(f"\n💳 URL de pago recibida:")
            print(f"   {data.get('pago_url', 'NO SE RECIBIÓ')[:80]}...")
            
            # Verificar que se guardó en turnos.json
            print("\n📁 Verificando si se guardó en turnos.json...")
            with open("turnos.json", "r", encoding="utf-8") as f:
                turnos = json.load(f)
            
            print(f"   Total de turnos guardados: {len(turnos)}")
            
            # Buscar el turno recién creado
            turno_encontrado = None
            for t in turnos:
                if (t.get("nombre") == turno_data["nombre"] and 
                    t.get("apellido") == turno_data["apellido"] and
                    t.get("fecha") == turno_data["fecha"]):
                    turno_encontrado = t
                    break
            
            if turno_encontrado:
                print("   ✅ Turno encontrado en el archivo:")
                print(f"      - ID: {turno_encontrado['id']}")
                print(f"      - Estado: {turno_encontrado['estado']}")
                print(f"      - Teléfono: {turno_encontrado.get('telefono', 'NO GUARDADO')}")
            else:
                print("   ❌ No se encontró el turno en el archivo")
                
        elif response.status_code == 409:
            print("⚠️ CONFLICTO - El horario ya está reservado")
            print(f"   Respuesta: {response.json()}")
            
        else:
            print(f"❌ ERROR - Código {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR DE CONEXIÓN")
        print("   No se pudo conectar al servidor.")
        print("   ¿Está el backend corriendo?")
        
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT")
        print("   El servidor tardó demasiado en responder")
        
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
    
    print("\n" + "=" * 60)

def test_ver_turnos():
    """Verifica cuántos turnos hay guardados"""
    print("\n📋 VERIFICANDO TURNOS GUARDADOS...")
    
    try:
        with open("turnos.json", "r", encoding="utf-8") as f:
            turnos = json.load(f)
        
        print(f"\nTotal: {len(turnos)} turno(s)")
        
        for i, turno in enumerate(turnos, 1):
            print(f"\nTurno {i}:")
            print(f"  Nombre: {turno.get('nombre')} {turno.get('apellido')}")
            print(f"  Fecha: {turno.get('fecha')} {turno.get('hora')}")
            print(f"  Estado: {turno.get('estado')}")
            print(f"  Teléfono: {turno.get('telefono', 'NO TIENE')}")
            
    except FileNotFoundError:
        print("❌ No existe el archivo turnos.json")
    except json.JSONDecodeError:
        print("❌ Error al leer turnos.json - formato inválido")

if __name__ == "__main__":
    # Primero ver estado actual
    test_ver_turnos()
    
    # Luego hacer prueba de reserva
    # DESCOMENTA LA SIGUIENTE LÍNEA PARA HACER LA PRUEBA REAL:
    # test_crear_reserva()
    
    print("\n💡 Para probar la reserva real, descomenta la línea 'test_crear_reserva()'")
