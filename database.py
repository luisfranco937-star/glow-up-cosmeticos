"""
Módulo de Base de Datos SQLite para Glow Up Cosméticos.
Manejo de conexión, esquema relacional y carga de datos iniciales (Seed).
"""

import sqlite3
from datetime import datetime, timedelta
import random
from config import DB_PATH, EMPRESA

def get_db_connection():
    """Retorna una conexión a la base de datos con row_factory para acceso por nombre de columna."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Crea las tablas de la base de datos si no existen y precarga datos iniciales."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        razon_social TEXT NOT NULL,
        cuit TEXT UNIQUE,
        condicion_iva TEXT NOT NULL,
        domicilio TEXT,
        telefono TEXT,
        email TEXT,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabla de Productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        marca TEXT,
        categoria TEXT NOT NULL,
        descripcion TEXT,
        precio_costo REAL NOT NULL,
        precio_neto REAL NOT NULL,
        alicuota_iva REAL DEFAULT 21.0,
        stock_actual INTEGER NOT NULL DEFAULT 0,
        stock_minimo INTEGER NOT NULL DEFAULT 5,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabla de Ventas / Facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_comprobante TEXT NOT NULL, -- 'A' o 'B'
        punto_venta INTEGER NOT NULL DEFAULT 1,
        numero_comprobante INTEGER NOT NULL,
        fecha TIMESTAMP NOT NULL,
        cliente_id INTEGER,
        cliente_nombre TEXT NOT NULL,
        cliente_cuit TEXT,
        cliente_condicion_iva TEXT NOT NULL,
        cliente_domicilio TEXT,
        subtotal_neto REAL NOT NULL,
        iva_total REAL NOT NULL,
        total REAL NOT NULL,
        metodo_pago TEXT NOT NULL,
        cae TEXT NOT NULL,
        cae_vto TEXT NOT NULL,
        observaciones TEXT,
        estado TEXT DEFAULT 'EMITIDA',
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    );
    """)

    # Tabla de Ítems de la Venta
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venta_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        producto_codigo TEXT NOT NULL,
        producto_nombre TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario_neto REAL NOT NULL,
        alicuota_iva REAL NOT NULL,
        subtotal_neto REAL NOT NULL,
        subtotal_iva REAL NOT NULL,
        subtotal_total REAL NOT NULL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );
    """)

    conn.commit()

    # Verificar si ya existen productos para sembrar datos
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    """Carga datos iniciales de demostración para el Trabajo Práctico."""
    cursor = conn.cursor()

    # 1. Clientes semilla (con foco en Responsables Inscriptos para Factura A)
    clientes_iniciales = [
        ("Perfumerías Rouge S.A.", "30-65489123-7", "IVA Responsable Inscripto", "Av. Cabildo 2140, CABA", "011-4788-1234", "compras@perfumeriasrouge.com.ar"),
        ("Estética Bella & Spa S.R.L.", "33-71234567-0", "IVA Responsable Inscripto", "Calle Florida 890, CABA", "011-4322-9988", "administracion@esteticabella.com"),
        ("Distribuidora Cosmética del Sur S.A.", "30-70894562-1", "IVA Responsable Inscripto", "Calle 12 N° 450, La Plata", "0221-489-3321", "contacto@cosmeticasur.com.ar"),
        ("Dra. Valeria Gómez (Dermatología)", "27-28945612-6", "Monotributo", "Av. Corrientes 3420, CABA", "011-5544-2211", "valeriagomez@gmail.com"),
        ("Mariana Belén Fernández", "27-35612874-0", "Consumidor Final", "Billinghurst 1540, CABA", "011-6677-8899", "mariana.fernandez@hotmail.com"),
        ("Consumidor Final Anónimo", None, "Consumidor Final", "Mostrador", "-", "-")
    ]

    cursor.executemany("""
    INSERT INTO clientes (razon_social, cuit, condicion_iva, domicilio, telefono, email)
    VALUES (?, ?, ?, ?, ?, ?);
    """, clientes_iniciales)

    # 2. Productos cosméticos semilla
    # (codigo, nombre, marca, categoria, descripcion, costo, neto, iva, stock, stock_min)
    productos_iniciales = [
        ("SKU-001", "Serum Ácido Hialurónico + Vitamina C 30ml", "L'Éclat Paris", "Skincare", "Serum concentrado antioxidante e hidratación profunda", 4200.0, 8500.0, 21.0, 35, 10),
        ("SKU-002", "Crema Facial Antiedad con Colágeno 50g", "Glow Up Pro", "Skincare", "Crema reafirmante de noche con efecto tensor", 5500.0, 11200.0, 21.0, 24, 8),
        ("SKU-003", "Protector Solar Facial Toque Seco FPS 50+ 50ml", "SunShield Derm", "Skincare", "Alta protección UVA/UVB no comedogénico acabado mate", 6800.0, 13900.0, 21.0, 40, 15),
        ("SKU-004", "Agua Micelar Desmaquillante Termal 250ml", "Pure Cleanse", "Skincare", "Limpia, desmaquilla e hidrata pieles sensibles", 2100.0, 4600.0, 21.0, 50, 10),
        ("SKU-005", "Labial Líquido Mate Velvet Red 5ml", "Rouge Luxe", "Make-Up", "Color intenso hasta por 16 horas sin transferir", 2900.0, 6200.0, 21.0, 45, 12),
        ("SKU-006", "Base Fluida Cobertura Luminosa Tono 02 30ml", "Silk Skin", "Make-Up", "Fórmula liviana con ácido hialurónico acabado glow", 5900.0, 12500.0, 21.0, 18, 8),
        ("SKU-007", "Máscara de Pestañas Efecto Pestañas Postizas", "Lash Queen", "Make-Up", "Volumen extremo a prueba de agua con cepillo curvo", 3100.0, 6900.0, 21.0, 30, 10),
        ("SKU-008", "Paleta de Sombras Nude & Glow 12 Tonos", "Palette Studio", "Make-Up", "Sombras ultra pigmentadas mates y satinadas", 7800.0, 16800.0, 21.0, 15, 5),
        ("SKU-009", "Perfume Eau de Parfum Rose Mystère 100ml", "Maison de Parfum", "Fragancias", "Fragancia floral ambarada de fijación prolongada", 14500.0, 29900.0, 21.0, 12, 4),
        ("SKU-010", "Perfume Eau de Toilette Citrus Breeze 100ml", "Maison de Parfum", "Fragancias", "Notas frescas de bergamota, té verde y cedro", 11200.0, 23500.0, 21.0, 16, 5),
        ("SKU-011", "Shampoo Reparación Molecular y Keratina 400ml", "HairBotox Pro", "Cuidado Capilar", "Reconstruye la fibra capilar dañada por calor y coloración", 3400.0, 7200.0, 21.0, 28, 10),
        ("SKU-012", "Aceite Capilar Oro Líquido Argán & Macadamia 60ml", "HairBotox Pro", "Cuidado Capilar", "Nutrición instantánea, brillo espejo y antifrizz", 4100.0, 8900.0, 21.0, 22, 6),
        ("SKU-013", "Set de Brochas Profesionales x 10 Piezas", "ProTools Studio", "Accesorios", "Cerdas sintéticas ultrasuaves con estuche de cuero ecológico", 8900.0, 18500.0, 21.0, 8, 3)
    ]

    cursor.executemany("""
    INSERT INTO productos (codigo, nombre, marca, categoria, descripcion, precio_costo, precio_neto, alicuota_iva, stock_actual, stock_minimo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, productos_iniciales)

    # 3. Registrar un par de ventas iniciales de prueba (Factura A y Factura B) para enriquecer el dashboard
    # Venta 1: Factura A a Perfumerías Rouge S.A.
    fecha_venta1 = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    cae_1 = "74128956321458"
    vto_cae_1 = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    
    # Ítems: 5 Serums ($8.500 c/u = $42.500 neto) + 3 Bases ($12.500 c/u = $37.500 neto) -> Neto: $80.000, IVA 21%: $16.800, Total: $96.800
    cursor.execute("""
    INSERT INTO ventas (tipo_comprobante, punto_venta, numero_comprobante, fecha, cliente_id, cliente_nombre, cliente_cuit, cliente_condicion_iva, cliente_domicilio, subtotal_neto, iva_total, total, metodo_pago, cae, cae_vto, observaciones, estado)
    VALUES ('A', 1, 1, ?, 1, 'Perfumerías Rouge S.A.', '30-65489123-7', 'IVA Responsable Inscripto', 'Av. Cabildo 2140, CABA', 80000.0, 16800.0, 96800.0, 'Transferencia Bancaria', ?, ?, 'Venta mayorista apertura de cuenta', 'EMITIDA');
    """, (fecha_venta1, cae_1, vto_cae_1))
    venta1_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO venta_items (venta_id, producto_id, producto_codigo, producto_nombre, cantidad, precio_unitario_neto, alicuota_iva, subtotal_neto, subtotal_iva, subtotal_total)
    VALUES 
    (?, 1, 'SKU-001', 'Serum Ácido Hialurónico + Vitamina C 30ml', 5, 8500.0, 21.0, 42500.0, 8925.0, 51425.0),
    (?, 6, 'SKU-006', 'Base Fluida Cobertura Luminosa Tono 02 30ml', 3, 12500.0, 21.0, 37500.0, 7875.0, 45375.0);
    """, (venta1_id, venta1_id))

    # Venta 2: Factura A a Estética Bella & Spa S.R.L.
    fecha_venta2 = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    cae_2 = "74128956321459"
    vto_cae_2 = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    
    # Ítems: 4 Cremas ($11.200 = $44.800) + 2 Fragancias Rose ($29.900 = $59.800) -> Neto: $104.600, IVA 21%: $21.966, Total: $126.566
    cursor.execute("""
    INSERT INTO ventas (tipo_comprobante, punto_venta, numero_comprobante, fecha, cliente_id, cliente_nombre, cliente_cuit, cliente_condicion_iva, cliente_domicilio, subtotal_neto, iva_total, total, metodo_pago, cae, cae_vto, observaciones, estado)
    VALUES ('A', 1, 2, ?, 2, 'Estética Bella & Spa S.R.L.', '33-71234567-0', 'IVA Responsable Inscripto', 'Calle Florida 890, CABA', 104600.0, 21966.0, 126566.0, 'Tarjeta de Crédito', ?, ?, 'Pedido productos para cabina estética', 'EMITIDA');
    """, (fecha_venta2, cae_2, vto_cae_2))
    venta2_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO venta_items (venta_id, producto_id, producto_codigo, producto_nombre, cantidad, precio_unitario_neto, alicuota_iva, subtotal_neto, subtotal_iva, subtotal_total)
    VALUES 
    (?, 2, 'SKU-002', 'Crema Facial Antiedad con Colágeno 50g', 4, 11200.0, 21.0, 44800.0, 9408.0, 54208.0),
    (?, 9, 'SKU-009', 'Perfume Eau de Parfum Rose Mystère 100ml', 2, 29900.0, 21.0, 59800.0, 12558.0, 72358.0);
    """, (venta2_id, venta2_id))

    # Venta 3: Factura B a Consumidor Final
    fecha_venta3 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cae_3 = "74128956321460"
    vto_cae_3 = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    
    # 1 Labial ($6.200 neto + $1.302 IVA = $7.502 total)
    cursor.execute("""
    INSERT INTO ventas (tipo_comprobante, punto_venta, numero_comprobante, fecha, cliente_id, cliente_nombre, cliente_cuit, cliente_condicion_iva, cliente_domicilio, subtotal_neto, iva_total, total, metodo_pago, cae, cae_vto, observaciones, estado)
    VALUES ('B', 1, 1, ?, 5, 'Mariana Belén Fernández', '27-35612874-0', 'Consumidor Final', 'Billinghurst 1540, CABA', 6200.0, 1302.0, 7502.0, 'Efectivo', ?, ?, 'Venta en local', 'EMITIDA');
    """, (fecha_venta3, cae_3, vto_cae_3))
    venta3_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO venta_items (venta_id, producto_id, producto_codigo, producto_nombre, cantidad, precio_unitario_neto, alicuota_iva, subtotal_neto, subtotal_iva, subtotal_total)
    VALUES (?, 5, 'SKU-005', 'Labial Líquido Mate Velvet Red 5ml', 1, 6200.0, 21.0, 6200.0, 1302.0, 7502.0);
    """, (venta3_id,))

    conn.commit()
