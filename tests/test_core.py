"""
Batería de Pruebas Automatizadas (Unit Tests & Integration Tests).
Valida las reglas impositivas de Factura A, cálculo de IVA 21%, CUIT Módulo 11 y stock.
Glow Up Cosméticos S.R.L.
"""

import sys
from pathlib import Path

# Configurar stdout en UTF-8 para compatibilidad con Windows cp1252
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar directorio raíz al path para importar módulos
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from database import init_db, get_db_connection
from services.billing_service import (
    validar_cuit, formatear_cuit, validar_y_procesar_factura,
    anular_factura, BillingException
)

def run_all_tests():
    print("\n" + "="*50)
    print("🧪 INICIANDO SUITE DE PRUEBAS - GLOW UP COSMÉTICOS")
    print("="*50)

    # Inicializar base de datos de prueba
    init_db()

    # --- Test 1: Validación de CUIT (Módulo 11) ---
    print("\n[TEST 1] Verificación del Algoritmo Módulo 11 de CUIT...")
    cuit_valido_1 = "30-71829347-9"
    cuit_valido_2 = "30654891237"
    cuit_invalido_dv = "30-71829347-2" # Dígito verificador erróneo
    cuit_invalido_longitud = "30-7182934-9" # Longitud incorrecta

    assert validar_cuit(cuit_valido_1) is True, f"Error: {cuit_valido_1} debería ser válido"
    assert validar_cuit(cuit_valido_2) is True, f"Error: {cuit_valido_2} debería ser válido"
    assert validar_cuit(cuit_invalido_dv) is False, f"Error: {cuit_invalido_dv} no debería ser válido"
    assert validar_cuit(cuit_invalido_longitud) is False, f"Error: {cuit_invalido_longitud} no debería ser válido"
    print("✅ Test 1 PASÓ: Algoritmo Módulo 11 validó CUITs correctamente.")

    # --- Test 2: Rechazo de Factura A a Consumidor Final ---
    print("\n[TEST 2] Restricción impositiva: Rechazar Factura A a Consumidor Final...")
    cliente_cf = {
        "id": 5,
        "razon_social": "Consumidor Ocasional",
        "cuit": None,
        "condicion_iva": "Consumidor Final"
    }
    items_prueba = [{"producto_id": 1, "cantidad": 2}]

    rechazado = False
    try:
        validar_y_procesar_factura(
            cliente_info=cliente_cf,
            tipo_comprobante="A", # Factura A a Consumidor Final DEBE FALLAR
            items_pedidos=items_prueba,
            metodo_pago="Efectivo"
        )
    except BillingException as be:
        rechazado = True
        print(f"  Detalle de rechazo fiscal esperado: {be}")

    assert rechazado is True, "ERROR GRAVE: El sistema permitió emitir Factura A a un Consumidor Final!"
    print("✅ Test 2 PASÓ: El sistema bloqueó correctamente la Factura A improcedente.")

    # --- Test 3: Emisión exitosa de Factura A a Responsable Inscripto con discriminación de IVA ---
    print("\n[TEST 3] Emisión de Factura A a Responsable Inscripto...")
    conn = get_db_connection()
    # Tomar stock inicial del producto 1
    prod = conn.execute("SELECT stock_actual, precio_neto, alicuota_iva FROM productos WHERE id = 1").fetchone()
    stock_antes = prod["stock_actual"]
    precio_neto = prod["precio_neto"]
    alicuota = prod["alicuota_iva"]
    conn.close()

    cliente_ri = {
        "id": 1,
        "razon_social": "Perfumerías Rouge S.A.",
        "cuit": "30-65489123-7",
        "condicion_iva": "IVA Responsable Inscripto",
        "domicilio": "Av. Cabildo 2140, CABA"
    }

    cantidad_compra = 2
    factura_a = validar_y_procesar_factura(
        cliente_info=cliente_ri,
        tipo_comprobante="A",
        items_pedidos=[{"producto_id": 1, "cantidad": cantidad_compra}],
        metodo_pago="Transferencia Bancaria",
        observaciones="Test automatizado de Factura A"
    )

    # Validar importes
    neto_esperado = round(precio_neto * cantidad_compra, 2)
    iva_esperado = round(neto_esperado * (alicuota / 100.0), 2)
    total_esperado = round(neto_esperado + iva_esperado, 2)

    assert factura_a["tipo_comprobante"] == "A", "El tipo de comprobante debe ser A"
    assert factura_a["subtotal_neto"] == neto_esperado, f"Neto esperado {neto_esperado}, obtenido {factura_a['subtotal_neto']}"
    assert factura_a["iva_total"] == iva_esperado, f"IVA esperado {iva_esperado}, obtenido {factura_a['iva_total']}"
    assert factura_a["total"] == total_esperado, f"Total esperado {total_esperado}, obtenido {factura_a['total']}"
    assert len(factura_a["cae"]) == 14, f"CAE debe tener 14 dígitos ({factura_a['cae']})"
    assert "https://www.afip.gob.ar/fe/qr/?p=" in factura_a["qr_url"], "Debe generar URL de QR AFIP"

    # Validar descuento de stock
    conn = get_db_connection()
    prod_despues = conn.execute("SELECT stock_actual FROM productos WHERE id = 1").fetchone()
    conn.close()
    assert prod_despues["stock_actual"] == stock_antes - cantidad_compra, "El stock no se descontó correctamente"

    print(f"  Comprobante A N°: {factura_a['numero_formateado']}")
    print(f"  Neto Gravado: ${factura_a['subtotal_neto']}")
    print(f"  IVA 21%: ${factura_a['iva_total']}")
    print(f"  Total Facturado: ${factura_a['total']}")
    print(f"  CAE asignado: {factura_a['cae']} (Vto: {factura_a['cae_vto']})")
    print("✅ Test 3 PASÓ: Factura A calculada y emitida con total precisión.")

    # --- Test 4: Anulación y Reintegro de Stock ---
    print("\n[TEST 4] Anulación de comprobante y reintegro al inventario...")
    venta_id = factura_a["id"]
    anular_factura(venta_id)

    conn = get_db_connection()
    prod_reintegrado = conn.execute("SELECT stock_actual FROM productos WHERE id = 1").fetchone()
    venta_estado = conn.execute("SELECT estado FROM ventas WHERE id = ?", (venta_id,)).fetchone()["estado"]
    conn.close()

    assert venta_estado == "ANULADA", "El estado de la venta debe ser ANULADA"
    assert prod_reintegrado["stock_actual"] == stock_antes, "El stock reintegrado no coincide con el stock original"
    print("✅ Test 4 PASÓ: Anulación correcta y stock reintegrado.")

    print("\n" + "="*50)
    print("🎉 TODAS LAS PRUEBAS UNITARIAS E INTEGRACIÓN PASARON EXITOSAMENTE!")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_all_tests()
