# 1.0 Arquitectura de Datos y Flujos de Trabajo

## 1.1 Matriz de interacción de actores y datos

### Alumna
- Canal: Interfaz Web Externa.
- Operación:
  - Visualiza catálogo de clases.
  - Gestiona reservas y cancelaciones.
  - Solicita cambio de plan (asíncrono).
  - Crea tickets de soporte y consulta historial de compras.
- Entidades relacionadas:
  - Perfil de usuario, reservas, tickets, planes contratados, transacciones.

### Recepcionista
- Canal: Panel Interno de Administración.
- Operación:
  - Registra asistencia en grilla horaria.
  - Ingresa transacciones locales.
  - Valida cambios de plan con checklist.
  - Registra asistentes temporales.
- Entidades relacionadas:
  - Transacciones, sesiones, planes, asistencias.

### Administrador
- Canal: Consola Central de Control.
- Operación:
  - Configuración global.
  - Estadísticas operativas y reportes.
  - Gestión centralizada de tickets.
  - Borrado/anonimización y carga de deslindes.
- Entidades relacionadas:
  - Todos los registros de la plataforma.

# 2.0 IAM (Identidad, Accesos y Roles)

## 2.1 Gestión de roles

- RFS-IAM-01: Registro autónomo de alumnas habilitado en `/cuentas/registro/`.
- RFS-IAM-02: Roles jerárquicos definidos (`admin`, `reception`, `student`) con vistas restringidas por RBAC.
- RFS-IAM-03: Indicador de antigüedad y fidelización:
  - Fórmula base: `A = Fecha actual - Fecha registro`
  - Fidelización por continuidad de planes:
    - `A >= 6 meses`: `LOYALTY_6M`
    - `A >= 12 meses`: `LOYALTY_12M`

## Modelado inicial ligado a IAM

- `accounts.User`: rol, teléfono, antigüedad, badge de fidelización.
- `core.Plan`: catálogo comercial.
- `core.PlanSubscription`: plan contratado por alumna, periodos y estado.
- `core.SupportTicket`: atención al cliente.
