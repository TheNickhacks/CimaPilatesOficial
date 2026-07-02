# Cima Pilates - Plataforma Web

Base inicial del sistema en Django para landing, agenda y operación interna.

## Stack

- Django 5.x + Python 3.12+
- Neon DB (PostgreSQL serverless) vía ORM de Django
- Tailwind CSS + HTMX + Alpine.js (via CDN en esta fase)

## Módulos implementados en esta fase

- IAM base:
  - Registro autónomo de alumnas
  - Login/Logout
  - Roles RBAC (`admin`, `reception`, `student`)
  - Redirección por dashboard según rol
- Modelo de fidelización:
  - Antigüedad total (`A = fecha_actual - fecha_registro`)
  - Insignias por continuidad de plan: 6m y 12m
- Datos core iniciales:
  - Planes
  - Suscripciones de planes
  - Tickets de soporte

## Puesta en marcha local

```powershell
Set-Location "c:\Users\nnava\Desktop\CimaPilates Oficial"
Copy-Item .env.example .env
& "c:/Users/nnava/Desktop/CimaPilates Oficial/.venv/Scripts/python.exe" manage.py makemigrations
& "c:/Users/nnava/Desktop/CimaPilates Oficial/.venv/Scripts/python.exe" manage.py migrate
& "c:/Users/nnava/Desktop/CimaPilates Oficial/.venv/Scripts/python.exe" manage.py createsuperuser
& "c:/Users/nnava/Desktop/CimaPilates Oficial/.venv/Scripts/python.exe" manage.py runserver
```

## Docker

El proyecto ya incluye contenedores separados para backend Django, frontend Next.js y una base Postgres local para desarrollo o despliegue inicial.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Servicios expuestos:

- Backend Django: http://localhost:8000
- Frontend Next.js: http://localhost:3000

Si vas a desplegar en Neon u otro Postgres administrado, solo cambia `DATABASE_URL` y deja `DATABASE_SSL_REQUIRE=True` cuando el proveedor lo requiera.

## Siguientes hitos recomendados

1. Agenda de clases (sesiones, cupos, reservas, cancelaciones)
2. Registro de asistencia de recepcionista
3. Historial de compras y caja local
4. Flujo formal de cambios de plan (solicitud y aprobación)
5. Centro de tickets con SLA y trazabilidad
