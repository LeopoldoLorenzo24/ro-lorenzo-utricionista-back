# 🚀 DEPLOYMENT - INSTRUCCIONES

## ⚠️ IMPORTANTE: Solo hay UN cambio que deployar

### Cambio realizado:
El endpoint `/crear-preferencia` ahora devuelve:
```python
return {
    "pago_url": init_point,
    "turno_id": turno_id  # ← NUEVO
}
```

---

## 📋 PASOS PARA DEPLOYAR EN RENDER

### Opción 1: Deploy Automático (Recomendado)

1. **Hacer commit del cambio:**
```bash
git add main.py
git commit -m "feat: agregar turno_id en respuesta de /crear-preferencia"
git push origin main
```

2. **Render detectará automáticamente el cambio y redesplegará**
   - Si tienes auto-deploy habilitado, Render hará el deploy automáticamente
   - Sino, ve al dashboard de Render y haz click en "Manual Deploy"

---

### Opción 2: Deploy Manual (Si no funciona automático)

1. **Ve a Render Dashboard:**
   https://dashboard.render.com

2. **Selecciona tu servicio:**
   `rosario-lorenzo-nutricionista-back`

3. **Click en "Manual Deploy"**
   - Selecciona la rama `main`
   - Click en "Deploy latest commit"

4. **Espera a que termine el deploy** (1-3 minutos)

---

## ✅ VERIFICAR QUE EL DEPLOY FUNCIONÓ

### Prueba 1: Health Check
```bash
curl https://ro-lorenzo-nutricionista-back.onrender.com/health
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "message": "Backend funcionando correctamente"
}
```

---

### Prueba 2: Verificar el nuevo cambio

**Usando PowerShell:**
```powershell
$body = @{
    nombre = "Test"
    apellido = "Deploy"
    telefono = "351-123456"
    motivo = "1ra Consulta"
    modalidad = "presencial"
    fecha = "2025-11-20"
    hora = "14:00"
    duracion = "45 minutos"
    costo = 1
    ubicacion = "Test"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "https://ro-lorenzo-nutricionista-back.onrender.com/crear-preferencia" -Method POST -Body $body -ContentType "application/json"

Write-Host "Pago URL: $($response.pago_url)"
Write-Host "Turno ID: $($response.turno_id)"  # ← DEBE APARECER
```

**Respuesta esperada:**
```
Pago URL: https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=...
Turno ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

✅ Si ves el `Turno ID`, el deploy fue exitoso.

---

## 🔧 TROUBLESHOOTING

### Problema: "No se devuelve turno_id"

**Solución:**
1. Verifica que el código en Render sea el último:
   - Ve a Render Dashboard → tu servicio → "Logs"
   - Busca la línea que dice: `Building...`
   - Asegúrate que esté usando el último commit

2. Si no está actualizado:
   ```bash
   git push origin main --force
   ```

---

### Problema: "Error 500 en /crear-preferencia"

**Diagnóstico:**
1. Ve a Render Dashboard → tu servicio → "Logs"
2. Busca el error exacto
3. Probablemente falta una variable de entorno

**Variables de entorno requeridas:**
- `MP_ACCESS_TOKEN` ← MercadoPago Access Token
- `FRONT_URL` ← https://ro-lorenzo-nutricionista.vercel.app
- `WEBHOOK_URL` ← https://ro-lorenzo-nutricionista-back.onrender.com/webhook
- `EMAIL_PASSWORD` ← Gmail App Password

---

### Problema: "El archivo turnos.json se borra al hacer deploy"

**Explicación:**
- Render usa contenedores efímeros
- Cada deploy crea un nuevo contenedor
- Los archivos NO persisten entre deploys

**Solución temporal:**
- El archivo `turnos.json` se crea automáticamente al hacer la primera reserva
- Los turnos de prueba se perderán en cada deploy

**Solución definitiva (FUTURO):**
- Migrar a una base de datos (PostgreSQL, MongoDB)
- Render ofrece PostgreSQL gratuito

---

## 📊 MONITOREO POST-DEPLOY

### 1. Ver logs en tiempo real:
```bash
# Instalar Render CLI (opcional)
npm install -g render-cli

# Ver logs
render logs rosario-lorenzo-nutricionista-back --tail
```

### 2. Monitorear requests:
- Ve a Render Dashboard
- Click en tu servicio
- Ve a la pestaña "Metrics"
- Verás:
  - CPU usage
  - Memory usage
  - Request count
  - Response times

---

## 🎯 CHECKLIST POST-DEPLOY

- [ ] Health check responde OK
- [ ] `/crear-preferencia` devuelve `turno_id`
- [ ] Frontend puede crear reservas
- [ ] MercadoPago redirecciona correctamente
- [ ] Webhook actualiza turnos a "confirmado"
- [ ] Turnos expirados se limpian correctamente

---

## 📞 SI ALGO FALLA

1. **Revisa los logs en Render**
2. **Verifica las variables de entorno**
3. **Prueba localmente primero:**
   ```bash
   cd rosario-lorenzo-nutricionista-back
   uvicorn main:app --reload
   ```
4. **Compara respuesta local vs producción**

---

## ✅ CONFIRMACIÓN FINAL

Una vez deployado, envía esta prueba al frontend:

```
Backend actualizado y deployado ✅

Cambio: El endpoint /crear-preferencia ahora devuelve:
{
  "pago_url": "...",
  "turno_id": "..."
}

Por favor probá:
1. Hacer una reserva desde el frontend
2. Verificar que recibís el turno_id en la respuesta
3. Confirmar que el horario se bloquea correctamente

URL del backend: https://ro-lorenzo-nutricionista-back.onrender.com
```
