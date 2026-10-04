# STONKS - Control Permanente de Cuenta Corriente y Crédito Comercial de Barrio

> **Universidad Peruana de Ciencias Aplicadas (UPC)**  
> **Curso:** SI642 - Finanzas e Ingeniería Económica  
> **Ciclo Académico:** 2026-20  
> **Grupo:** 2 &bull; Sección: 7691  

---

## Descripción del Proyecto

**Stonks** es una solución web empresarial y multiplataforma concebida para reemplazar el cuaderno tradicional de notas en pequeños comercios de barrio (bodegas, panaderías, carnicerías, boticas, fruterías, bazares, peluquerías, spas, entre otros). Permite llevar de forma automatizada, transparente y matemáticamente rigurosa el control de la cuenta corriente de créditos otorgados a clientes de su zona de influencia.

La plataforma opera bajo una arquitectura **multitienda y multirol**, permitiendo que diversos comercios de giros distintos operen de manera independiente sobre la misma base tecnológica.

---

## Convenciones Financieras y Normativas (Anexo A del Enunciado)

El motor financiero ([`financial_engine.py`](file:///C:/Users/Frank/Documents/antigravity/happy-carson/stonks/financial_engine.py)) implementa estrictamente las directrices del curso:

1. **Base Anual:** 360 días (año comercial).
2. **Mes Comercial:** 30 días para todos los cálculos de cuotas y cronogramas.
3. **Conversión Explícita de Tasas:** Fórmulas exactas entre Tasas Efectivas (TEA, TEM, TED) y Nominales (TNA con capitalización diaria o mensual).
4. **Método Francés Vencido Simple Ordinario:** Cuotas constantes mensuales ($C$) calculadas con:
   $$C = P_{\text{cap}} \times \frac{\text{TEM} \cdot (1 + \text{TEM})^N}{(1 + \text{TEM})^N - 1}$$
5. **Capitalización de Período de Gracia Total:** Si una compra en cuotas se realiza antes de la fecha de corte, los días transcurridos hasta la primera fecha de pago pactada constituyen un período de gracia total. Los intereses devengados se capitalizan a la deuda inicial antes de computar las cuotas mensuales:
   $$P_{\text{cap}} = P_0 \times (1 + \text{TED})^{d_{\text{gracia}}}$$
6. **Compras a Fin de Mes (Pago Único):**
   - Compras realizadas hasta la fecha y hora de corte se cobran en la fecha de pago pactada del ciclo, computando intereses por los días transcurridos.
   - Compras realizadas **después de la fecha de corte** difieren automáticamente su obligación de pago al ciclo inmediatamente posterior ($M+1$).
7. **Control Estricto de Límite de Crédito:** El sistema deniega cualquier compra cuyo importe sumado a la deuda actual exceda el límite máximo autorizado al cliente.
8. **Prohibición de Pagos Parciales:** En la fecha de pago se exige la cancelación de la deuda líquida total exigible.
9. **Intereses por Mora Diferenciados:** Si el cliente cancela después de la fecha pactada, el listado de pago desglosa un ítem independiente rotulado **"Intereses por mora"** aplicado sobre el saldo exigible por los días de atraso.
10. **Orden Legal de Imputación (Prelación de Pagos):**
    $$\text{1° Intereses por Mora} \longrightarrow \text{2° Interés Compensatorio} \longrightarrow \text{3° Capital}$$
11. **Indicadores Financieros para el Comercio:** Cálculo automatizado de la **TIR** (Tasa Interna de Retorno anualizada obtenida por el comerciante prestamista), el **VAN** (Valor Actual Neto descontado a la tasa COK de oportunidad del negocio) y la **TCEA**.
12. **Precisión de Redondeo:** Expresiones monetarias con 2 decimales y tasas internas con al menos 7 decimales.

---

## Roles y Flujo del Sistema

| Rol | Pantallas y Funcionalidades |
|---|---|
| **Administrador del Sistema** | Gestión global de tiendas (altas y bajas), monitoreo de clientes atendidos, volumen consolidado de crédito. |
| **Administrador de Tienda (Dueño/Cajero)** | Dashboard financiero con gráficos, catálogo de productos con precio contado vs lista (crédito) y modalidades permitidas, gestión de clientes y asignación de límites de crédito, punto de venta (POS) a crédito con validación en vivo, emisión de listados de corte y caja de cobranzas con prelación de pagos. |
| **Cliente Particular** | Portal móvil adaptativo para consultar deuda actual, saldo de línea disponible, detalle cronológico de consumos y cronograma de cuotas francesas. |
| **Público / Todos** | Simulador financiero interactivo y conversor de tasas. |

---

## Credenciales Demo de Acceso Rápido

La pantalla de inicio de sesión incluye botones de acceso con 1-click para evaluar de inmediato cada perfil:

| Perfil | Usuario | Contraseña | Rol / Descripción |
|---|---|---|---|
| **Admin Sistema** | `admin` | `admin123` | Administrador general de la plataforma |
| **Admin Tienda** | `bodega_don_pepe` | `tienda123` | Dueño de "Bodega Don Pepe" (Giro: Bodega) |
| **Admin Tienda 2** | `panaderia_espiga` | `espiga123` | Dueño de "Panadería La Espiga" (Giro: Panadería) |
| **Cliente** | `cliente_juan` | `cliente123` | Juan Pérez (Cliente particular con línea de crédito) |

---

## Guía de Instalación y Ejecución Local

### Prerrequisitos
- Python 3.10 o superior instalado.
- Navegador web moderno (Chrome, Edge, Firefox).

### Opción 1: Ejecución Inmediata en Windows (1-Click)
Hacer doble clic en el archivo:
```bat
run.bat
```

### Opción 2: Línea de Comandos
1. Abrir terminal en la carpeta del proyecto:
   ```powershell
   cd C:\Users\Frank\Documents\antigravity\happy-carson\stonks
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicializar la base de datos y cargar datos de prueba:
   ```bash
   python seed_data.py
   ```
4. Iniciar el servidor web:
   ```bash
   python app.py
   ```
5. Abrir en el navegador:
   ```
   http://localhost:5000
   ```

---

## Pruebas Unitarias Automatizadas

El proyecto incluye dos suites completas de pruebas unitarias que validan la matemática financiera y las rutas web:

```bash
# Probar el motor financiero (Reglas del Anexo A, Gracia, Francés, Mora, Prelación)
python -m unittest tests/test_financial.py

# Probar la aplicación web (Login, Roles, POS, Liquidaciones, APIs)
python -m unittest tests/test_webapp.py
```

---

## Estructura del Repositorio

```text
stonks/
├── app.py                     # Controlador web Flask y endpoints REST
├── financial_engine.py        # Motor de matemática financiera estricta (Base 360, Francés, Mora, TIR, VAN)
├── database.py                # Definición de tablas SQLite y conexión relacional
├── seed_data.py               # Generador de datos iniciales y escenarios del enunciado
├── run.bat                    # Script ejecutable de un clic para Windows
├── requirements.txt           # Dependencias mínimas del proyecto
├── README.md                  # Manual técnico y de usuario
│
├── templates/                 # Vistas HTML5 con Tailwind CSS y componentes responsivos
│   ├── base.html              # Layout base con navbar y notificaciones
│   ├── login.html             # Inicio de sesión y registro de tienda / cliente
│   ├── admin_system.html      # Panel del Administrador del Sistema (Altas/bajas tiendas)
│   ├── store_dashboard.html   # Panel del Comercio (KPIs, gráficos Chart.js, cobranzas)
│   ├── products.html          # Catálogo de productos (Precios contado vs lista, modalidades)
│   ├── customers.html         # Políticas de crédito (Límites, TEA/TNA, plazos, corte, pago)
│   ├── pos_credit.html        # Punto de Venta a crédito con validación en tiempo real
│   ├── settlement.html        # Gestión de listados de corte mensuales
│   ├── settlement_detail.html # Detalle imprimible de listado de pago con compras y mora
│   ├── payment.html           # Caja y cobranzas con orden de prelación legal
│   ├── customer_portal.html   # Portal móvil para el cliente particular
│   └── simulator.html         # Simulador financiero y conversor de tasas
│
└── tests/
    ├── test_financial.py      # Pruebas matemáticas rigurosas del Anexo A
    └── test_webapp.py         # Pruebas de integración de la aplicación web
```
