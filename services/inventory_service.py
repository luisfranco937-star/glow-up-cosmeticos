"""
Servicio de Inventario, Gestión de Clientes y Métricas de Negocio.
Glow Up Cosméticos S.R.L.
"""

from typing import List, Dict, Any, Optional
from database import get_db_connection
from services.billing_service import validar_cuit, formatear_cuit

def obtener_metricas_dashboard() -> Dict[str, Any]:
    """Recopila KPIs principales para la pantalla principal."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total facturado general (ventas no anuladas)
    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE estado = 'EMITIDA'")
    total_facturado = cursor.fetchone()[0]

    # Total Facturado en Facturas A
    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE tipo_comprobante = 'A' AND estado = 'EMITIDA'")
    total_factura_a = cursor.fetchone()[0]

    # Total Facturado en Facturas B
    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE tipo_comprobante = 'B' AND estado = 'EMITIDA'")
    total_factura_b = cursor.fetchone()[0]

    # Cantidad total de comprobantes emitidos
    cursor.execute("SELECT COUNT(*) FROM ventas WHERE estado = 'EMITIDA'")
    cantidad_ventas = cursor.fetchone()[0]

    # Productos totales
    cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
    total_productos = cursor.fetchone()[0]

    # Productos con stock bajo
    cursor.execute("""
        SELECT COUNT(*) FROM productos 
        WHERE stock_actual <= stock_minimo AND activo = 1
    """)
    stock_critico_count = cursor.fetchone()[0]

    # Lista de productos con stock crítico
    cursor.execute("""
        SELECT id, codigo, nombre, marca, categoria, stock_actual, stock_minimo 
        FROM productos 
        WHERE stock_actual <= stock_minimo AND activo = 1
        ORDER BY stock_actual ASC
        LIMIT 5
    """)
    productos_bajo_stock = [dict(row) for row in cursor.fetchall()]

    # Últimas 5 ventas
    cursor.execute("""
        SELECT id, tipo_comprobante, punto_venta, numero_comprobante, fecha, 
               cliente_nombre, total, metodo_pago, estado
        FROM ventas 
        ORDER BY id DESC 
        LIMIT 5
    """)
    ultimas_ventas = [dict(row) for row in cursor.fetchall()]

    # Top 5 productos más vendidos
    cursor.execute("""
        SELECT vi.producto_nombre, SUM(vi.cantidad) as total_unidades, SUM(vi.subtotal_total) as total_recaudado
        FROM venta_items vi
        JOIN ventas v ON vi.venta_id = v.id
        WHERE v.estado = 'EMITIDA'
        GROUP BY vi.producto_id
        ORDER BY total_unidades DESC
        LIMIT 5
    """)
    top_vendidos = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_facturado": round(total_facturado, 2),
        "total_factura_a": round(total_factura_a, 2),
        "total_factura_b": round(total_factura_b, 2),
        "cantidad_ventas": cantidad_ventas,
        "total_productos": total_productos,
        "stock_critico_count": stock_critico_count,
        "productos_bajo_stock": productos_bajo_stock,
        "ultimas_ventas": ultimas_ventas,
        "top_vendidos": top_vendidos
    }

def obtener_libro_iva_ventas(mes: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Genera el reporte fiscal 'Libro IVA Ventas' requerido por la normativa AFIP/ARCA.
    Contiene: Fecha, Tipo Comp., N° Comprobante, Cliente, CUIT, Cond. IVA, Neto Gravado, Débito Fiscal IVA, Total.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            id,
            fecha,
            tipo_comprobante,
            punto_venta,
            numero_comprobante,
            cliente_nombre,
            cliente_cuit,
            cliente_condicion_iva,
            subtotal_neto,
            iva_total,
            total,
            cae,
            estado
        FROM ventas
        WHERE estado = 'EMITIDA'
    """
    params = []
    if mes:
        query += " AND strftime('%Y-%m', fecha) = ?"
        params.append(mes)

    query += " ORDER BY fecha ASC, numero_comprobante ASC"

    cursor.execute(query, params)
    filas = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Formatear números de comprobante
    for f in filas:
        f["numero_formateado"] = f"{f['tipo_comprobante']} {f['punto_venta']:04d}-{f['numero_comprobante']:08d}"

    return filas
