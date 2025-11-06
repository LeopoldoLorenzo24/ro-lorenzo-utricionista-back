# 🚀 GUÍA DE MIGRACIÓN A POSTGRESQL

## ✅ Cambios Realizados

### Archivos Nuevos:
- ✅ `database.py` - Configuración de PostgreSQL con SQLAlchemy
- ✅ `models.py` - Modelo Turno para la base de datos
- ✅ `init_db.py` - Script para inicializar la BD
- ✅ `main.py` - **ACTUALIZADO** para usar PostgreSQL en lugar de JSON

### Archivos Modificados:
- ✅ `requirements.txt` - Agregadas dependencias: `sqlalchemy` y `psycopg2-binary`

### Archivos de Backup:
- 📄 `main_old.py` - Versión antigua (con JSON)

---

## 📋 PASOS PARA DEPLOYAR EN RENDER

### 1. Crear Base de Datos PostgreSQL en Render (GRATIS)

1. **Ve a Render Dashboard:**
   https://dashboard.render.com

2. **Clic en "New +"** → **"PostgreSQL"**

3. **Configurar:**
   - **Name:** `rosario-lorenzo-nutricionista-db`
   - **Database:** `turnos_db`
   - **User:** (se genera automáticamente)
   - **Region:** `Oregon` (o el que prefieras)
   - **PostgreSQL Version:** `15` (o la más reciente)
   - **Plan:** **Free** ✅

4. **Clic en "Create Database"**

5. **Espera 2-3 minutos** mientras se crea la base de datos

---

### 2. Conectar el Backend con la Base de Datos

1. **En el dashboard de PostgreSQL**, copia la **Internal Database URL**
   - Se ve así: `postgres://user:password@dpg-xxxxx/dbname`

2. **Ve a tu servicio web** (rosario-lorenzo-nutricionista-back)
   - Clic en el servicio
   - Ve a **"Environment"**

3. **Agregar variable de entorno:**
   - Key: `DATABASE_URL`
   - Value: **Pega la Internal Database URL**
   - Clic en **"Save Changes"**

---

### 3. Deploy del Nuevo Código

#### Opción A: Git Push (Recomendado)

```bash
cd "c:\Users\Usuario\Desktop\Paginas Web\Proyecto Nutricionista\Nutricionista Back\ro-lorenzo-utricionista-back\rosario-lorenzo-nutricionista-back"

# Agregar cambios
git add .

# Commit
git commit -m "feat: migrar de JSON a PostgreSQL + fix email"

# Push
git push origin main
```

Render detectará el cambio y redesplegará automáticamente.

#### Opción B: Manual Deploy

1. Ve a Render Dashboard → tu servicio
2. Clic en **"Manual Deploy"** → **"Deploy latest commit"**

---

### 4. Verificar el Deploy

Una vez que termine el deploy (3-5 minutos):

#### Test 1: Health Check
```powershell
Invoke-RestMethod -Uri "https://ro-lorenzo-nutricionista-back.onrender.com/health"
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "message": "Backend funcionando correctamente",
  "database": "✅ Conectado"
}
```

#### Test 2: Ver Turnos (debería estar vacío)
```powershell
Invoke-RestMethod -Uri "https://ro-lorenzo-nutricionista-back.onrender.com/ver-turnos"
```

**Respuesta esperada:**
```json
{
  "turnos": []
}
```

#### Test 3: Crear una Reserva de Prueba
```powershell
$body = @{
    nombre = "Test"
    apellido = "PostgreSQL"
    telefono = "351-123456"
    motivo = "1ra Consulta"
    modalidad = "presencial"
    fecha = "2025-11-20"
    hora = "14:00"
    duracion = "45 minutos"
    costo = 1
    ubicacion = "Test"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://ro-lorenzo-nutricionista-back.onrender.com/crear-preferencia" -Method POST -Body $body -ContentType "application/json"
```

**Respuesta esperada:**
```json
{
  "pago_url": "https://www.mercadopago.com.ar/...",
  "turno_id": "uuid-generado"
}
```

#### Test 4: Verificar que se Guardó
```powershell
Invoke-RestMethod -Uri "https://ro-lorenzo-nutricionista-back.onrender.com/ver-turnos"
```

**Debería mostrar el turno de prueba** ✅

---

## 🔐 Variables de Entorno Requeridas

Asegúrate de tener TODAS estas variables en Render:

```bash
DATABASE_URL=postgres://user:password@host/database  # ← NUEVO
MP_ACCESS_TOKEN=your_mercadopago_access_token
FRONT_URL=https://ro-lorenzo-nutricionista.vercel.app
WEBHOOK_URL=https://ro-lorenzo-nutricionista-back.onrender.com/webhook
EMAIL_PASSWORD=your_gmail_app_password
```

---

## 🎯 VENTAJAS DE POSTGRESQL

### ✅ Antes (JSON):
- ❌ Se perdían datos al reiniciar
- ❌ No escalable
- ❌ Problemas de concurrencia
- ❌ Sin backups

### ✅ Ahora (PostgreSQL):
- ✅ **Persistencia garantizada** - Los datos NUNCA se pierden
- ✅ **Gratis en Render** - Plan Free
- ✅ **Backups automáticos** - Render hace backups diarios
- ✅ **Escalable** - Soporta miles de usuarios
- ✅ **Profesional** - Estándar de la industria

---

## 🔧 TROUBLESHOOTING

### Problema: "database" en health check muestra error

**Solución:**
1. Verifica que la variable `DATABASE_URL` esté configurada correctamente
2. Asegúrate de usar la **Internal Database URL** (no la External)
3. Verifica que la base de datos PostgreSQL esté corriendo en Render

### Problema: "Error connecting to database"

**Solución:**
1. Ve al dashboard de PostgreSQL en Render
2. Verifica que el estado sea **"Available"**
3. Si está detenido, inícialo
4. Espera 1-2 minutos y vuelve a intentar

### Problema: Las tablas no se crean

**Solución:**
- Las tablas se crean automáticamente al iniciar el servidor
- Verifica los logs en Render para ver si hay errores
- La línea `Base.metadata.create_all(bind=engine)` en `main.py` crea las tablas

### Problema: Los turnos no se guardan

**Diagnóstico:**
```python
# Ver logs en Render Dashboard → tu servicio → Logs
# Busca líneas como:
# [INFO] Turno guardado en BD: uuid-xxx
```

---

## 📊 MIGRACIÓN DE DATOS (Si tenías turnos en JSON)

Si tenías turnos importantes en `turnos.json` que quieres migrar:

```python
# Script de migración (ejecutar localmente)
import json
from database import SessionLocal
from models import Turno
from datetime import datetime

# Leer turnos del JSON
with open("turnos.json", "r", encoding="utf-8") as f:
    turnos_json = json.load(f)

# Conectar a la BD
db = SessionLocal()

# Migrar cada turno
for turno_data in turnos_json:
    turno = Turno(
        id=turno_data["id"],
        estado=turno_data["estado"],
        nombre=turno_data["nombre"],
        apellido=turno_data["apellido"],
        telefono=turno_data.get("telefono", ""),
        motivo=turno_data["motivo"],
        modalidad=turno_data["modalidad"],
        fecha=turno_data["fecha"],
        hora=turno_data["hora"],
        duracion=turno_data["duracion"],
        costo=turno_data["costo"],
        ubicacion=turno_data["ubicacion"],
        token_cancelacion=turno_data["token_cancelacion"],
        fecha_creacion=datetime.fromisoformat(turno_data["fecha_creacion"])
    )
    db.add(turno)

db.commit()
print(f"✅ Migrados {len(turnos_json)} turnos")
```

---

## 🔄 ROLLBACK (Si algo sale mal)

Si necesitas volver a la versión con JSON:

```bash
# 1. Revertir main.py
cd "c:\Users\Usuario\Desktop\Paginas Web\Proyecto Nutricionista\Nutricionista Back\ro-lorenzo-utricionista-back\rosario-lorenzo-nutricionista-back"
Copy-Item main_old.py main.py -Force

# 2. Commit y push
git add main.py
git commit -m "rollback: volver a JSON temporalmente"
git push origin main
```

---

## ✨ NUEVO COMPORTAMIENTO

### Al crear una reserva:
1. ✅ Se guarda en PostgreSQL (persistente)
2. ✅ Se envía email a Rosario
3. ✅ Se crea link de pago en MercadoPago
4. ✅ El horario se bloquea por 2 minutos

### Al confirmar el pago:
1. ✅ Webhook de MercadoPago actualiza el turno a "confirmado"
2. ✅ Se envía email de confirmación a Rosario
3. ✅ El horario queda ocupado permanentemente

### Limpieza automática:
- ✅ Turnos pendientes > 2 minutos se eliminan automáticamente
- ✅ Turnos confirmados permanecen para siempre

---

## 📞 SOPORTE

Si tenés problemas durante el deploy:

1. **Revisa los logs en Render:**
   - Dashboard → tu servicio → Logs
   - Busca líneas con `[ERROR]` o `[WARNING]`

2. **Verifica la conexión a la BD:**
   - Llama al endpoint `/health`
   - Debe mostrar "database": "✅ Conectado"

3. **Prueba localmente primero:**
   ```bash
   # Instalar dependencias
   pip install -r requirements.txt
   
   # Ejecutar servidor
   uvicorn main:app --reload
   ```

---

## 🎉 ¡LISTO!

Una vez completados todos los pasos:
- ✅ PostgreSQL configurado
- ✅ Datos persistentes garantizados
- ✅ Emails funcionando
- ✅ Sistema 100% operativo

¡Ahora sí podés recibir reservas reales sin perder datos! 🚀
