# ✅ BACKEND ACTUALIZADO Y VERIFICADO

## 📅 Fecha: 6 de Noviembre 2025

---

## 🎯 CAMBIOS REALIZADOS

### 1. ✅ Endpoint `/crear-preferencia` - ACTUALIZADO

**Cambio:** Ahora devuelve tanto `pago_url` como `turno_id`

**Antes:**
```python
return {"pago_url": init_point}
```

**Después:**
```python
return {
    "pago_url": init_point,
    "turno_id": turno_id
}
```

**Razón:** El frontend necesita el `turno_id` para poder trackear el estado del pago y actualizar la UI.

---

### 2. ✅ Endpoint `/turnos-ocupados` - YA ESTABA CORRECTO

**Funcionalidad verificada:**
- ✅ Incluye turnos con estado `confirmado`
- ✅ Incluye turnos con estado `pendiente_de_pago` que no hayan expirado (< 2 minutos)
- ✅ Filtra por `modalidad` y `fecha`
- ✅ Limpia automáticamente turnos expirados antes de devolver resultados

**Código clave:**
```python
if t["estado"] == "confirmado" or es_pendiente_vigente(t):
    horarios_ocupados.append(t["hora"])
```

---

### 3. ✅ Sistema de Expiración - YA ESTABA CORRECTO

**Configuración:**
- Tiempo de reserva: **2 minutos** (`RESERVA_MINUTOS = 2`)
- Los turnos `pendiente_de_pago` expiran automáticamente después de 2 minutos
- Los turnos `confirmado` nunca expiran

**Funciones clave:**

1. **`es_pendiente_vigente(turno)`**
   - Verifica si un turno pendiente tiene menos de 2 minutos de antigüedad
   - Retorna `True` si está vigente, `False` si expiró

2. **`limpiar_turnos_vencidos(turnos)`**
   - Elimina turnos pendientes con más de 2 minutos
   - Mantiene todos los turnos confirmados
   - Se ejecuta automáticamente en cada consulta de turnos ocupados

---

## 🔄 FLUJO COMPLETO VERIFICADO

### Paso 1: Usuario reserva un turno
```
Frontend → POST /crear-preferencia
```
**Respuesta:**
```json
{
  "pago_url": "https://www.mercadopago.com.ar/...",
  "turno_id": "uuid-generado"
}
```

**Backend guarda en `turnos.json`:**
```json
{
  "id": "uuid-generado",
  "estado": "pendiente_de_pago",
  "nombre": "Juan",
  "apellido": "Pérez",
  "telefono": "351-123456",
  "fecha": "2025-11-20",
  "hora": "10:00",
  "fecha_creacion": "2025-11-06T10:00:00",
  ...
}
```

### Paso 2: El horario queda bloqueado
```
Frontend → GET /turnos-ocupados?modalidad=presencial&fecha=2025-11-20
```
**Respuesta:** `["10:00"]` ← El horario aparece ocupado por 2 minutos

### Paso 3A: Usuario paga exitosamente
```
MercadoPago → POST /webhook
```
**Backend actualiza:**
```json
{
  "id": "uuid-generado",
  "estado": "confirmado",  ← Cambió de pendiente a confirmado
  ...
}
```
El horario queda ocupado permanentemente ✅

### Paso 3B: Usuario NO paga (expira)
- Después de 2 minutos, el turno se elimina automáticamente
- El horario queda disponible nuevamente ✅

---

## 📊 ESTRUCTURA DE DATOS

### Turno guardado en `turnos.json`:
```json
{
  "id": "uuid-v4",
  "estado": "pendiente_de_pago" | "confirmado",
  "nombre": "string",
  "apellido": "string",
  "telefono": "string",
  "motivo": "string",
  "modalidad": "presencial" | "virtual",
  "fecha": "YYYY-MM-DD",
  "hora": "HH:MM",
  "duracion": "string",
  "costo": number,
  "ubicacion": "string",
  "token_cancelacion": "uuid-v4",
  "fecha_creacion": "ISO8601 datetime"
}
```

---

## 🧪 PRUEBAS REALIZADAS

✅ **Prueba 1:** Creación de turno pendiente
- Se crea correctamente con estado `pendiente_de_pago`
- Se guarda en `turnos.json`
- Incluye campo `telefono`

✅ **Prueba 2:** Verificación de horarios ocupados
- Turnos pendientes (< 2 min) aparecen como ocupados
- Turnos confirmados aparecen como ocupados
- Turnos expirados (> 2 min) NO aparecen

✅ **Prueba 3:** Confirmación de pago
- El estado cambia de `pendiente_de_pago` a `confirmado`
- El turno permanece en `turnos.json`

✅ **Prueba 4:** Expiración automática
- Turnos pendientes > 2 minutos se eliminan
- Turnos confirmados nunca se eliminan

---

## 🚀 ENDPOINTS DISPONIBLES

### 1. POST `/crear-preferencia`
**Request:**
```json
{
  "nombre": "string",
  "apellido": "string",
  "telefono": "string",
  "motivo": "string",
  "modalidad": "presencial" | "virtual",
  "fecha": "YYYY-MM-DD",
  "hora": "HH:MM",
  "duracion": "string",
  "costo": number,
  "ubicacion": "string"
}
```

**Response:**
```json
{
  "pago_url": "string",
  "turno_id": "string"
}
```

**Errores:**
- `409 Conflict`: Horario ya ocupado
- `500 Internal Server Error`: Error al crear preferencia de pago

---

### 2. GET `/turnos-ocupados`
**Parámetros:**
- `modalidad`: "presencial" | "virtual"
- `fecha`: "YYYY-MM-DD"

**Response:**
```json
["09:00", "10:00", "15:30"]
```

---

### 3. POST `/webhook`
**Uso:** Recibe notificaciones de MercadoPago
- Actualiza el estado del turno a `confirmado` cuando el pago es aprobado
- Es llamado automáticamente por MercadoPago

---

### 4. GET `/ver-turnos`
**Parámetros opcionales:**
- `estado`: "pendiente_de_pago" | "confirmado"

**Response:**
```json
{
  "turnos": [...]
}
```

---

### 5. DELETE `/cancelar-turno`
**Parámetros:**
- `id`: string (turno_id)

**Response:**
```json
{
  "status": "turno cancelado"
}
```

---

### 6. GET `/estado-turno`
**Parámetros:**
- `id`: string (turno_id)

**Response:**
```json
{
  "estado": "pendiente_de_pago" | "confirmado",
  "segundos_restantes": number
}
```

---

## 🔐 CONFIGURACIÓN REQUERIDA

### Variables de entorno (.env):
```bash
MP_ACCESS_TOKEN=your_mercadopago_access_token
FRONT_URL=https://ro-lorenzo-nutricionista.vercel.app
WEBHOOK_URL=https://ro-lorenzo-nutricionista-back.onrender.com/webhook
EMAIL_PASSWORD=your_gmail_app_password
```

---

## ✅ ESTADO FINAL

**Backend:** ✅ Funcionando correctamente
**Guardado de turnos:** ✅ Implementado y verificado
**Campo teléfono:** ✅ Se guarda correctamente
**Expiración:** ✅ Funciona (2 minutos)
**Integración con Frontend:** ✅ Compatible

---

## 📝 NOTAS IMPORTANTES

1. **Persistencia de datos:**
   - Actualmente se usa un archivo JSON local (`turnos.json`)
   - Para producción se recomienda migrar a una base de datos (PostgreSQL, MongoDB, etc.)

2. **Concurrencia:**
   - El archivo JSON no es ideal para múltiples requests simultáneos
   - Considerar usar una base de datos con transacciones para producción

3. **Limpieza automática:**
   - Los turnos expirados se limpian automáticamente en cada request a `/turnos-ocupados`
   - Considerar un job/cron para limpiar periódicamente

4. **Tiempo de reserva:**
   - Actualmente: 2 minutos (`RESERVA_MINUTOS = 2`)
   - Se puede ajustar según necesidad
   - También se configura en MercadoPago (`expiration_date_to`)

---

## 🎉 CONCLUSIÓN

El backend está **100% funcional** y listo para integrarse con el frontend.

Todos los requerimientos del frontend están implementados:
- ✅ Devuelve `turno_id` en la respuesta
- ✅ Bloquea horarios por 2 minutos
- ✅ Guarda el campo `telefono`
- ✅ Actualiza estado con webhook
- ✅ Limpia turnos expirados automáticamente
