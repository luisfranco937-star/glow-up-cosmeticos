"""
Rutas de Vistas Web (Frontend Jinja2) para Glow Up Cosméticos.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from config import EMPRESA, COMPROBANTES_AFIP
from database import get_db_connection
from services.inventory_service import obtener_metricas_dashboard, obtener_libro_iva_ventas
from services.billing_service import generar_qr_afip_url

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)

@router.get("/", response_class=HTMLResponse)
def view_dashboard(request: Request):
    metricas = obtener_metricas_dashboard()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"empresa": EMPRESA, "metricas": metricas, "active_page": "dashboard"}
    )

@router.get("/pos", response_class=HTMLResponse)
def view_pos(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE activo = 1 ORDER BY categoria, nombre")
    productos = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM clientes WHERE activo = 1 ORDER BY razon_social")
    clientes = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="pos.html",
        context={
            "empresa": EMPRESA,
            "productos": productos,
            "clientes": clientes,
            "active_page": "pos"
        }
    )

@router.get("/productos", response_class=HTMLResponse)
def view_productos(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE activo = 1 ORDER BY categoria, nombre")
    productos = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT categoria FROM productos WHERE activo = 1 ORDER BY categoria")
    categorias = [r[0] for r in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={
            "empresa": EMPRESA,
            "productos": productos,
            "categorias": categorias,
            "active_page": "productos"
        }
    )

@router.get("/clientes", response_class=HTMLResponse)
def view_clientes(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE activo = 1 ORDER BY razon_social")
    clientes = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context={
            "empresa": EMPRESA,
            "clientes": clientes,
            "active_page": "clientes"
        }
    )

@router.get("/ventas", response_class=HTMLResponse)
def view_ventas(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventas ORDER BY id DESC")
    ventas = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for v in ventas:
        v["numero_formateado"] = f"{v['tipo_comprobante']} {v['punto_venta']:04d}-{v['numero_comprobante']:08d}"

    return templates.TemplateResponse(
        request=request,
        name="ventas.html",
        context={
            "empresa": EMPRESA,
            "ventas": ventas,
            "active_page": "ventas"
        }
    )

@router.get("/comprobante/{venta_id}", response_class=HTMLResponse)
def view_comprobante(request: Request, venta_id: int):
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
    venta["descripcion_afip"] = COMPROBANTES_AFIP.get(venta["tipo_comprobante"], {}).get("descripcion", "FACTURA")

    return templates.TemplateResponse(
        request=request,
        name="comprobante.html",
        context={
            "empresa": EMPRESA,
            "venta": venta,
            "items": venta["items"],
            "active_page": "ventas"
        }
    )

@router.get("/libro-iva", response_class=HTMLResponse)
def view_libro_iva(request: Request):
    filas = obtener_libro_iva_ventas()
    totales = {
        "neto": sum(f["subtotal_neto"] for f in filas),
        "iva": sum(f["iva_total"] for f in filas),
        "total": sum(f["total"] for f in filas)
    }

    return templates.TemplateResponse(
        request=request,
        name="libro_iva.html",
        context={
            "empresa": EMPRESA,
            "filas": filas,
            "totales": totales,
            "active_page": "libro_iva"
        }
    )
