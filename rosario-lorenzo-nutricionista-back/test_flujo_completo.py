"""
Script de prueba para verificar el flujo completo del sistema de turnos
"""
import json
from datetime import datetime, timedelta
import time

def test_flujo_completo():
    """Prueba el flujo completo de reserva de turnos"""
    
    print("=" * 70)
    print("PRUEBA DE FLUJO COMPLETO - SISTEMA DE TURNOS")
    print("=" * 70)
    
    # 1. Limpiar turnos de prueba antiguos
    print("\n[1/6] Limpiando turnos de prueba antiguos...")
    with open("turnos.json", "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)
    print("✅ Archivo turnos.json limpiado")
    
    # 2. Simular creación de turno (lo que hace crear-preferencia)
    print("\n[2/6] Simulando creación de turno pendiente...")
    turno_nuevo = {
        "id": "test-123-abc",
        "estado": "pendiente_de_pago",
        "nombre": "Test",
        "apellido": "Usuario",
        "telefono": "351-123456",
        "motivo": "1ra Consulta",
        "modalidad": "presencial",
        "fecha": "2025-11-20",
        "hora": "10:00",
        "duracion": "45 minutos",
        "costo": 27500,
        "ubicacion": "GOOD LIFE CENTER",
        "token_cancelacion": "test-token",
        "fecha_creacion": datetime.now().isoformat()
    }
    
    with open("turnos.json", "r+", encoding="utf-8") as f:
        turnos = json.load(f)
        turnos.append(turno_nuevo)
        f.seek(0)
        json.dump(turnos, f, indent=2, ensure_ascii=False)
        f.truncate()
    
    print(f"✅ Turno creado:")
    print(f"   - ID: {turno_nuevo['id']}")
    print(f"   - Estado: {turno_nuevo['estado']}")
    print(f"   - Fecha/Hora: {turno_nuevo['fecha']} {turno_nuevo['hora']}")
    print(f"   - Creado: {turno_nuevo['fecha_creacion']}")
    
    # 3. Verificar que aparece como ocupado
    print("\n[3/6] Verificando que el horario aparece como ocupado...")
    with open("turnos.json", "r", encoding="utf-8") as f:
        turnos = json.load(f)
    
    # Simular lógica de turnos-ocupados
    horarios_ocupados = []
    for t in turnos:
        if t["modalidad"] == "presencial" and t["fecha"] == "2025-11-20":
            # Verificar si es pendiente vigente
            if t["estado"] == "pendiente_de_pago":
                fecha_creacion = datetime.fromisoformat(t["fecha_creacion"])
                ahora = datetime.now()
                es_vigente = (ahora - fecha_creacion) < timedelta(minutes=2)
                if es_vigente:
                    horarios_ocupados.append(t["hora"])
            elif t["estado"] == "confirmado":
                horarios_ocupados.append(t["hora"])
    
    if "10:00" in horarios_ocupados:
        print("✅ El horario 10:00 SÍ aparece como ocupado")
    else:
        print("❌ ERROR: El horario NO aparece como ocupado")
    
    # 4. Simular pago aprobado (webhook)
    print("\n[4/6] Simulando pago aprobado (webhook de MercadoPago)...")
    with open("turnos.json", "r+", encoding="utf-8") as f:
        turnos = json.load(f)
        for turno in turnos:
            if turno["id"] == "test-123-abc":
                turno["estado"] = "confirmado"
                break
        f.seek(0)
        json.dump(turnos, f, indent=2, ensure_ascii=False)
        f.truncate()
    
    print("✅ Estado del turno actualizado a 'confirmado'")
    
    # 5. Verificar que sigue ocupado aunque sea confirmado
    print("\n[5/6] Verificando que sigue ocupado como confirmado...")
    with open("turnos.json", "r", encoding="utf-8") as f:
        turnos = json.load(f)
    
    horarios_ocupados = []
    for t in turnos:
        if t["modalidad"] == "presencial" and t["fecha"] == "2025-11-20":
            if t["estado"] == "confirmado":
                horarios_ocupados.append(t["hora"])
    
    if "10:00" in horarios_ocupados:
        print("✅ El horario 10:00 sigue ocupado como confirmado")
    else:
        print("❌ ERROR: El horario confirmado NO aparece como ocupado")
    
    # 6. Prueba de expiración
    print("\n[6/6] Probando lógica de expiración...")
    turno_viejo = {
        "id": "test-viejo-456",
        "estado": "pendiente_de_pago",
        "nombre": "Viejo",
        "apellido": "Test",
        "telefono": "351-999999",
        "motivo": "Test",
        "modalidad": "virtual",
        "fecha": "2025-11-20",
        "hora": "14:00",
        "duracion": "45 minutos",
        "costo": 1,
        "ubicacion": "Online",
        "token_cancelacion": "test-token-2",
        "fecha_creacion": (datetime.now() - timedelta(minutes=5)).isoformat()
    }
    
    with open("turnos.json", "r+", encoding="utf-8") as f:
        turnos = json.load(f)
        turnos.append(turno_viejo)
        f.seek(0)
        json.dump(turnos, f, indent=2, ensure_ascii=False)
        f.truncate()
    
    # Limpiar turnos vencidos
    with open("turnos.json", "r", encoding="utf-8") as f:
        turnos = json.load(f)
    
    ahora = datetime.now()
    filtrados = []
    for turno in turnos:
        if turno["estado"] == "pendiente_de_pago":
            fecha_creacion = datetime.fromisoformat(turno["fecha_creacion"])
            if ahora - fecha_creacion < timedelta(minutes=2):
                filtrados.append(turno)
        else:
            filtrados.append(turno)
    
    with open("turnos.json", "w", encoding="utf-8") as f:
        json.dump(filtrados, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Turnos antes de limpiar: 2")
    print(f"✅ Turnos después de limpiar: {len(filtrados)}")
    
    if len(filtrados) == 1:
        print("✅ Se eliminó correctamente el turno expirado (> 2 min)")
    else:
        print("❌ ERROR: No se eliminó el turno expirado")
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN DEL ESTADO FINAL")
    print("=" * 70)
    
    with open("turnos.json", "r", encoding="utf-8") as f:
        turnos = json.load(f)
    
    print(f"\nTotal de turnos guardados: {len(turnos)}")
    for i, t in enumerate(turnos, 1):
        print(f"\nTurno {i}:")
        print(f"  ID: {t['id']}")
        print(f"  Estado: {t['estado']}")
        print(f"  Paciente: {t['nombre']} {t['apellido']}")
        print(f"  Teléfono: {t['telefono']}")
        print(f"  Fecha/Hora: {t['fecha']} a las {t['hora']}")
        print(f"  Modalidad: {t['modalidad']}")
        
        fecha_creacion = datetime.fromisoformat(t['fecha_creacion'])
        edad = (datetime.now() - fecha_creacion).total_seconds()
        print(f"  Antigüedad: {int(edad)} segundos")
    
    print("\n" + "=" * 70)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    test_flujo_completo()
