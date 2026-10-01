"""
Endpoints REST API para el Software de Gestión Comercial Glow Up Cosméticos.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from database import get_db_connection
from models import (
    ClienteCreate, ClienteResponse,
    ProductoCreate, ProductoUpdate, ProductoResponse,
    VentaCreate, VentaResponse
)
from services.billing_service import (
    validar_y_procesar_factura, anular_factura,
    validar_cuit, formatear_cuit, BillingException,
    generar_qr_afip_url
)
from services.inventory_service import (
    obtener_metricas_dashboard, obtener_libro_iva_ventas
)
from config import EMPRESA, COMPROBANTES_AFIP

router = APIRouter(prefix="/api", tags=["API Comercial"])

# ==================== PRODUCTOS ====================

@router.get("/productos", response_model=List[ProductoResponse])
def listar_productos(q: Optional[str] = None, categoria: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM productos WHERE activo = 1"
    params = []

    if categoria and categoria != "Todas":
        query += " AND categoria = ?"
        params.append(categoria)
    if q:
        query += " AND (nombre LIKE ? OR codigo LIKE ? OR marca LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term])

    query += " ORDER BY nombre ASC"
    cursor.execute(query, params)
    productos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return productos

@router.post("/productos", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(prod: ProductoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO productos (codigo, nombre, marca, categoria, descripcion, precio_costo, precio_neto, alicuota_iva, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prod.codigo.strip().upper(), prod.nombre.strip(), prod.marca, prod.categoria,
            prod.descripcion, prod.precio_costo, prod.precio_neto, prod.alicuota_iva,
            prod.stock_actual, prod.stock_minimo
        ))
        conn.commit()
        prod_id = cursor.lastrowid
        cursor.execute("SELECT * FROM productos WHERE id = ?", (prod_id,))
        nuevo = dict(cursor.fetchone())
        return nuevo
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear producto (verifique SKU único): {str(e)}")
    finally:
        conn.close()

@router.put("/productos/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(producto_id: int, prod: ProductoUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ? AND activo = 1", (producto_id,))
    existente = cursor.fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    update_fields = []
    params = []
    for k, v in prod.model_dump(exclude_unset=True).items():
        if v is not None:
            update_fields.append(f"{k} = ?")
            params.append(v)

    if update_fields:
        params.append(producto_id)
        cursor.execute(f"UPDATE productos SET {', '.join(update_fields)} WHERE id = ?", params)
        conn.commit()

    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    actualizado = dict(cursor.fetchone())
    conn.close()
    return actualizado

@router.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()
    return {"message": "Producto desactivado correctamente"}

# ==================== CLIENTES ====================

@router.get("/clientes", response_model=List[ClienteResponse])
def listar_clientes(q: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM clientes WHERE activo = 1"
    params = []
    if q:
        query += " AND (razon_social LIKE ? OR cuit LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term])
    query += " ORDER BY razon_social ASC"
    cursor.execute(query, params)
    clientes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return clientes

@router.post("/clientes", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(cliente: ClienteCreate):
    cuit_formateado = None
    if cliente.cuit:
        cuit_limpio = cliente.cuit.replace("-", "").strip()
        if not validar_cuit(cuit_limpio):
            raise HTTPException(status_code=400, detail="El CUIT ingresado no es válido según algoritmo Módulo 11 de AFIP.")
        cuit_formateado = formatear_cuit(cuit_limpio)

    if cliente.condicion_iva == "IVA Responsable Inscripto" and not cuit_formateado:
        raise HTTPException(status_code=400, detail="Un cliente 'IVA Responsable Inscripto' debe poseer CUIT de manera obligatoria.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (razon_social, cuit, condicion_iva, domicilio, telefono, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cliente.razon_social.strip(), cuit_formateado, cliente.condicion_iva.value,
            cliente.domicilio, cliente.telefono, cliente.email
        ))
        conn.commit()
        nuevo_id = cursor.lastrowid
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (nuevo_id,))
        nuevo = dict(cursor.fetchone())
        return nuevo
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al registrar cliente: {str(e)}")
    finally:
        conn.close()

@router.get("/clientes/validar-cuit")
def check_cuit(cuit: str = Query(...)):
    valido = validar_cuit(cuit)
    return {
        "cuit_ingresado": cuit,
        "valido": valido,
        "formateado": formatear_cuit(cuit) if valido else ""
    }

# ==================== FACTURACIÓN Y VENTAS ====================

@router.post("/ventas")
def procesar_venta(venta_req: VentaCreate):
    """
    Emite una venta/factura con las validaciones tributarias correspondientes.
    Especialmente para Factura A valida condición del cliente y genera desglose de IVA.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Resolver datos del cliente
    cliente_info = {}
    if venta_req.cliente_id:
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (venta_req.cliente_id,))
        row = cursor.fetchone()
        if row:
            cliente_info = dict(row)
        else:
            conn.close()
            raise HTTPException(status_code=404, detail="Cliente especificado no existe.")
    else:
        # Datos proporcionados al vuelo
        cliente_info = {
            "id": None,
            "razon_social": venta_req.cliente_nombre or "Consumidor Final",
            "cuit": venta_req.cliente_cuit or "",
            "condicion_iva": venta_req.cliente_condicion_iva.value if venta_req.cliente_condicion_iva else "Consumidor Final",
            "domicilio": venta_req.cliente_domicilio or ""
        }
    conn.close()

    try:
        items_payload = [{"producto_id": item.producto_id, "cantidad": item.cantidad} for item in venta_req.items]
        resultado = validar_y_procesar_factura(
            cliente_info=cliente_info,
            tipo_comprobante=venta_req.tipo_comprobante.value,
            items_pedidos=items_payload,
            metodo_pago=venta_req.metodo_pago.value,
            observaciones=venta_req.observaciones or ""
        )
        return resultado
    except BillingException as be:
        raise HTTPException(status_code=422, detail=str(be))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado al emitir factura: {str(e)}")

@router.get("/ventas")
def listar_ventas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tipo_comprobante, punto_venta, numero_comprobante, fecha,
               cliente_nombre, cliente_cuit, cliente_condicion_iva,
               subtotal_neto, iva_total, total, metodo_pago, cae, estado
        FROM ventas
        ORDER BY id DESC
    """)
    ventas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for v in ventas:
        v["numero_formateado"] = f"{v['tipo_comprobante']} {v['punto_venta']:04d}-{v['numero_comprobante']:08d}"
    return ventas

@router.get("/ventas/{venta_id}")
def obtener_detalle_venta(venta_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")

    venta = dict(row)
    cursor.execute("SELECT * FROM venta_items WHERE venta_id = ?", (venta_id,))
    venta["items"] = [dict(r) for r in cursor.fetchall()]
    conn.close()

    venta["empresa"] = EMPRESA
    venta["qr_url"] = generar_qr_afip_url(venta)
    venta["numero_formateado"] = f"{venta['punto_venta']:04d}-{venta['numero_comprobante']:08d}"
    venta["letra"] = venta["tipo_comprobante"]
    venta["codigo_afip"] = COMPROBANTES_AFIP.get(venta["tipo_comprobante"], {}).get("codigo", "01")
    return venta

@router.post("/ventas/{venta_id}/anular")
def cancelar_venta(venta_id: int):
    try:
        anular_factura(venta_id)
        return {"message": "Comprobante anulado correctamente y stock reintegrado."}
    except BillingException as be:
        raise HTTPException(status_code=400, detail=str(be))

# ==================== REPORTES Y DASHBOARD ====================

@router.get("/dashboard")
def get_dashboard():
    return obtener_metricas_dashboard()

@router.get("/libro-iva")
def get_libro_iva(mes: Optional[str] = None):
    return obtener_libro_iva_ventas(mes)
