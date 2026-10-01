# ✨ Glow Up Cosméticos S.R.L. - Sistema de Gestión Comercial

Software de gestión comercial, control de stock y facturación electrónica adaptado a la normativa fiscal argentina (ARCA / AFIP), con foco específico en la emisión y validación de **Factura "A"** con discriminación de alícuotas de IVA (21% y 10.5%).

---

## 🎯 Objetivo del Trabajo Práctico

Desarrollar un sistema de gestión comercial básico, modular y funcional para la empresa ficticia **Glow Up Cosméticos S.R.L.** (distribuidora y tienda de productos de cosmética, skincare, maquillaje y fragancias), implementando:
1. **Punto de Venta (POS) Interactivo** con opciones de venta y cálculo automático de **Factura A** vs **Factura B**.
2. **Validación Impositiva AFIP**: Reglas de negocio para impedir la emisión indebida de Factura A a Consumidores Finales, y validación estricta de CUIT mediante el algoritmo ponderado **Módulo 11**.
3. **Comprobante Fiscal Reglamentario**: Generación del modelo oficial de Factura A para impresión / PDF con código de autorización electrónica (CAE), vencimiento, código de barras y QR oficial.
4. **Gestión de Inventario y Stock**: Control de existencias de cosméticos, alertas automáticas de reposición (stock crítico) y actualización de inventario en tiempo real.
5. **Reportes Contables**: Generación del **Libro IVA Ventas** con desglose de Neto Gravado y Débito Fiscal, exportable a planilla de cálculo (CSV).

---

## 🏗️ Arquitectura y Tecnologías

- **Backend**: Python 3.12 + FastAPI (Arquitectura en capas: Rutas, Servicios, Modelos, Base de Datos).
- **Persistencia**: SQLite3 con integridad referencial (claves foráneas) y transacciones ACID.
- **Frontend**: HTML5 semántico, Jinja2 Templates, CSS3 moderno (con paleta estética cosmética y diseño responsive), JavaScript vanilla.
- **Servidor Web**: Uvicorn ASGI.
- **Documentación de API**: OpenAPI / Swagger interactivo generado automáticamente.

---

## 🚀 Puesta en Marcha Rápida

### 1. Iniciar la Aplicación

Puedes ejecutar el archivo por lotes en Windows:
```cmd
run.bat
```
O directamente desde la consola con Python:
```bash
python main.py
```

### 2. Acceder al Sistema

- 🖥️ **Panel Principal (Dashboard)**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 🛒 **Terminal POS & Facturación A**: [http://127.0.0.1:8000/pos](http://127.0.0.1:8000/pos)
- 💄 **Catálogo & Control de Stock**: [http://127.0.0.1:8000/productos](http://127.0.0.1:8000/productos)
- 👥 **Padrón de Clientes & CUITs**: [http://127.0.0.1:8000/clientes](http://127.0.0.1:8000/clientes)
- 🧾 **Historial de Facturas Emitidas**: [http://127.0.0.1:8000/ventas](http://127.0.0.1:8000/ventas)
- 📊 **Libro IVA Ventas**: [http://127.0.0.1:8000/libro-iva](http://127.0.0.1:8000/libro-iva)
- 📖 **Documentación Swagger API**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye una suite de pruebas unitarias e integrales que validan la matemática impositiva, el algoritmo de CUIT y la integridad del stock:

```bash
python tests/test_core.py
```

---

## 📋 Estructura del Código

```
glow_up_cosmeticos/
│
├── main.py                     # Punto de entrada y configuración del servidor FastAPI
├── config.py                   # Parámetros fiscales de la empresa y códigos AFIP
├── database.py                 # Esquema relacional SQLite y precarga de datos semilla
├── models.py                   # Esquemas de datos Pydantic
│
├── services/                   # Capa de Lógica de Negocio
│   ├── billing_service.py      # Motor de cálculo fiscal, CUIT Módulo 11, CAE y QR
│   └── inventory_service.py    # Gestión de inventario, stock crítico y métricas KPI
│
├── routes/                     # Capa de Controladores / Endpoints
│   ├── api.py                  # API RESTful (Productos, Clientes, Ventas, Reportes)
│   └── views.py                # Enrutador de plantillas Jinja2
│
├── templates/                  # Interfaz de Usuario Web
│   ├── base.html               # Layout base y barra de navegación
│   ├── dashboard.html          # Panel principal con KPIs
│   ├── pos.html                # Terminal de venta y facturación A
│   ├── comprobante.html        # Formato de factura reglamentaria AFIP (imprimible)
│   ├── productos.html          # Catálogo e inventario
│   ├── clientes.html           # Directorio de clientes con validador de CUIT
│   ├── ventas.html             # Registro histórico de comprobantes
│   └── libro_iva.html          # Reporte contable Libro IVA Ventas
│
├── static/                     # Recursos Estáticos
│   ├── css/style.css           # Estilos visuales temáticos y modo impresión
│   └── js/app.js               # Carrito dinámico, llamadas API y validaciones
│
├── tests/
│   └── test_core.py            # Batería de pruebas automatizadas
│
├── run.bat                     # Ejecutable por lotes para Windows
├── README.md                   # Instrucciones del proyecto
└── DOCUMENTACION_TRABAJO_PRACTICO.md # Informe académico completo del TP
```
