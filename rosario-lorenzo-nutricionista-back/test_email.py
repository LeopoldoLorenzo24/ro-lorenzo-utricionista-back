"""
Test de diagnóstico de EMAIL con Resend
"""
import requests

BACKEND_URL = "https://ro-lorenzo-nutricionista-back.onrender.com"

print("=" * 60)
print("🧪 TEST DE EMAIL CON RESEND")
print("=" * 60)

# 1. Verificar configuración de email
print("\n1️⃣ Verificando configuración de EMAIL...")
try:
    response = requests.get(f"{BACKEND_URL}/debug-email", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print("✅ Endpoint /debug-email alcanzado")
        print(f"   - EMAIL_PASSWORD configurado: {data.get('email_password_configured')}")
        print(f"   - SMTP Server: {data.get('smtp_server')}")
        print(f"   - SMTP Port: {data.get('smtp_port')}")
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"❌ Error conectando al backend: {e}")

# 2. Enviar email de prueba
print("\n2️⃣ Enviando email de prueba a licrosariomlorenzo@gmail.com...")
print("   (Una vez que configures la nueva API key de la cuenta de Rosario)")
try:
    response = requests.get(
        f"{BACKEND_URL}/send-test-email",
        params={"to_email": "licrosariomlorenzo@gmail.com"},
        timeout=15
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        print(f"   Email ID: {data.get('email_id')}")
        print("\n🎉 ¡EMAIL ENVIADO EXITOSAMENTE!")
        print("📧 Revisá la casilla de licrosariomlorenzo@gmail.com")
        print("   (No olvides revisar SPAM si no lo ves)")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Error al enviar email: {e}")

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)
