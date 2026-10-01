"""
Servicio de Facturación y Reglas Impositivas (ARCA / AFIP).
Lógica de negocio para Factura A y Factura B.
Glow Up Cosméticos S.R.L.
"""

from datetime import datetime, timedelta
import random
import json
import base64
import re
from typing import Dict, Any, List
from config import EMPRESA, COMPROBANTES_AFIP
from database import get_db_connection

class BillingException(Exception):
    """Excepción específica para errores de validación fiscal o facturación."""
    pass

def validar_cuit(cuit_str: str) -> bool:
    """
    Valida un número de CUIT/CUIL según el algoritmo oficial de AFIP (Módulo 11).
    Acepta formato con o sin guiones (ej: 30-71829341-9 o 30718293419).
    """
    if not cuit_str:
        return False
    
    # Extraer solo dígitos
    digits = re.sub(r'\D', '', cuit_str)
    if len(digits) != 11:
        return False
    
    # Prefijos válidos: 20, 23, 24, 27, 30, 33, 34
    prefijo = digits[:2]
    if prefijo not in ['20', '23', '24', '27', '30', '33', '34']:
        return False
    
    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(digits[i]) * multiplicadores[i] for i in range(10))
    resto = suma % 11
    
    if resto == 0:
        dv_esperado = 0
    elif resto == 1:
        # Casos especiales de AFIP
        dv_esperado = 9 if prefijo in ['20', '27'] else 4
    else:
        dv_esperado = 11 - resto
        
    return int(digits[10]) == dv_esperado

def formatear_cuit(cuit_str: str) -> str:
    """Retorna el CUIT con guiones (XX-XXXXXXXX-X)."""
    if not cuit_str:
        return ""
    digits = re.sub(r'\D', '', cuit_str)
    if len(digits) == 11:
        return f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
    return cuit_str

def obtener_siguiente_numero_comprobante(tipo_comprobante: str, punto_venta: int = 1) -> int:
    """
    Obtiene el siguiente número correlativo para el tipo de comprobante y punto de venta.
    La numeración de Factura A es independiente de Factura B.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(MAX(numero_comprobante), 0) + 1 
        FROM ventas 
        WHERE tipo_comprobante = ? AND punto_venta = ?
    """, (tipo_comprobante, punto_venta))
    siguiente = cursor.fetchone()[0]
    conn.close()
    return siguiente

def generar_cae_simulado() -> tuple[str, str]:
    """
    Genera un Código de Autorización Electrónico (CAE) de 14 dígitos y fecha de vencimiento (+10 días).
    """
    prefijo = "74" + datetime.now().strftime("%y%m")
    aleatorio = "".join([str(random.randint(0, 9)) for _ in range(8)])
    cae = f"{prefijo}{aleatorio}"[:14]
    
    fecha_vto = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    return cae, fecha_vto

def generar_qr_afip_url(venta_data: Dict[str, Any]) -> str:
    """
    Genera la URL con los datos del comprobante para el Código QR oficial de AFIP / ARCA.
    """
    cuit_emisor_digits = int(re.sub(r'\D', '', EMPRESA['cuit']))
    cuit_receptor_digits = int(re.sub(r'\D', '', venta_data.get('cliente_cuit', '0') or '0'))
    
    tipo_cmp = 1 if venta_data['tipo_comprobante'] == 'A' else 6
    tipo_doc_rec = 80 if cuit_receptor_digits > 0 else 99 # 80: CUIT, 99: Doc del Consumidor Final
    
    qr_dict = {
        "ver": 1,
        "fecha": venta_data['fecha'][:10],
        "cuit": cuit_emisor_digits,
        "ptoVta": venta_data['punto_venta'],
        "tipoCmp": tipo_cmp,
        "nroCmp": venta_data['numero_comprobante'],
        "importe": round(venta_data['total'], 2),
        "moneda": "ARS",
        "ctz": 1.0,
        "tipoDocRec": tipo_doc_rec,
        "nroDocRec": cuit_receptor_digits,
        "tipoCodAut": "E",
        "codAut": int(venta_data['cae'])
    }
    
    json_bytes = json.dumps(qr_dict).encode('utf-8')
    b64_str = base64.b64encode(json_bytes).decode('utf-8')
    return f"https://www.afip.gob.ar/fe/qr/?p={b64_str}"

def validar_y_procesar_factura(
    cliente_info: Dict[str, Any],
    tipo_comprobante: str,
    items_pedidos: List[Dict[str, Any]],
    metodo_pago: str,
    observaciones: str = ""
) -> Dict[str, Any]:
    """
    Ejecuta el control fiscal y cálculo comercial de la venta:
    1. Valida correspondencia fiscal para Factura A (Receptor Responsable Inscripto con CUIT).
    2. Valida stock y disponibilidad de productos.
    3. Calcula Neto Gravado, IVA 21% desglosado y Total.
    4. Decrementa stock.
    5. Asigna CAE y numeración correlativa.
    6. Persiste en base de datos de manera atómica (Transacción ACID).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # --- 1. REGLAS FISCALES FACTURA A ---
        condicion_iva_receptor = cliente_info.get("condicion_iva", "").strip()
        cuit_receptor = cliente_info.get("cuit", "")
        
        if tipo_comprobante == "A":
            if condicion_iva_receptor not in ["IVA Responsable Inscripto", "Responsable Inscripto"]:
                raise BillingException(
                    f"Incompatibilidad Fiscal AFIP: La FACTURA 'A' solo puede emitirse a clientes "
                    f"con condición 'IVA Responsable Inscripto'. El cliente actual es '{condicion_iva_receptor}'."
                )
            
            if not cuit_receptor:
                raise BillingException(
                    "Error Fiscal AFIP: La FACTURA 'A' requiere obligatoriamente un número de CUIT del receptor."
                )
            
            if not validar_cuit(cuit_receptor):
                raise BillingException(
                    f"El CUIT ingresado '{cuit_receptor}' no es válido según el algoritmo de control de AFIP (Módulo 11)."
                )
        
        elif tipo_comprobante == "B":
            # Factura B para Consumidor Final, Monotributo o Exento
            pass
        else:
            raise BillingException(f"Tipo de comprobante '{tipo_comprobante}' no soportado en esta versión.")

        # --- 2. VALIDAR PRODUCTOS Y STOCK ---
        if not items_pedidos:
            raise BillingException("La venta debe contener al menos un producto.")

        items_calculados = []
        subtotal_neto_acumulado = 0.0
        iva_total_acumulado = 0.0

        for item in items_pedidos:
            prod_id = item["producto_id"]
            cantidad = item["cantidad"]

            if cantidad <= 0:
                raise BillingException(f"La cantidad solicitada debe ser mayor a 0.")

            cursor.execute("SELECT * FROM productos WHERE id = ? AND activo = 1", (prod_id,))
            producto = cursor.fetchone()

            if not producto:
                raise BillingException(f"El producto ID {prod_id} no existe o no está activo.")

            if producto["stock_actual"] < cantidad:
                raise BillingException(
                    f"Stock insuficiente para '{producto['nombre']}'. "
                    f"Disponible: {producto['stock_actual']}, Solicitado: {cantidad}"
                )

            # Cálculos de línea
            precio_neto = float(producto["precio_neto"])
            alicuota_iva = float(producto["alicuota_iva"]) # Por defecto 21.0
            
            linea_neto = round(precio_neto * cantidad, 2)
            linea_iva = round(linea_neto * (alicuota_iva / 100.0), 2)
            linea_total = round(linea_neto + linea_iva, 2)

            subtotal_neto_acumulado += linea_neto
            iva_total_acumulado += linea_iva

            items_calculados.append({
                "producto_id": prod_id,
                "producto_codigo": producto["codigo"],
                "producto_nombre": producto["nombre"],
                "cantidad": cantidad,
                "precio_unitario_neto": precio_neto,
                "alicuota_iva": alicuota_iva,
                "subtotal_neto": linea_neto,
                "subtotal_iva": linea_iva,
                "subtotal_total": linea_total
            })

        total_facturado = round(subtotal_neto_acumulado + iva_total_acumulado, 2)

        # --- 3. NUMERACIÓN FISCAL Y CAE ---
        pto_vta = EMPRESA["punto_venta"]
        cursor.execute("""
            SELECT COALESCE(MAX(numero_comprobante), 0) + 1 
            FROM ventas 
            WHERE tipo_comprobante = ? AND punto_venta = ?
        """, (tipo_comprobante, pto_vta))
        nro_comprobante = cursor.fetchone()[0]

        cae, cae_vto = generar_cae_simulado()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- 4. PERSISTIR VENTA ---
        cursor.execute("""
            INSERT INTO ventas (
                tipo_comprobante, punto_venta, numero_comprobante, fecha,
                cliente_id, cliente_nombre, cliente_cuit, cliente_condicion_iva, cliente_domicilio,
                subtotal_neto, iva_total, total, metodo_pago, cae, cae_vto, observaciones, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EMITIDA')
        """, (
            tipo_comprobante, pto_vta, nro_comprobante, fecha_actual,
            cliente_info.get("id"),
            cliente_info.get("razon_social") or "Consumidor Final",
            formatear_cuit(cuit_receptor) if cuit_receptor else None,
            condicion_iva_receptor or "Consumidor Final",
            cliente_info.get("domicilio") or "",
            subtotal_neto_acumulado,
            iva_total_acumulado,
            total_facturado,
            metodo_pago,
            cae,
            cae_vto,
            observaciones
        ))
        venta_id = cursor.lastrowid

        # --- 5. PERSISTIR ITEMS Y DECREMENTAR STOCK ---
        for item in items_calculados:
            cursor.execute("""
                INSERT INTO venta_items (
                    venta_id, producto_id, producto_codigo, producto_nombre,
                    cantidad, precio_unitario_neto, alicuota_iva,
                    subtotal_neto, subtotal_iva, subtotal_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venta_id, item["producto_id"], item["producto_codigo"], item["producto_nombre"],
                item["cantidad"], item["precio_unitario_neto"], item["alicuota_iva"],
                item["subtotal_neto"], item["subtotal_iva"], item["subtotal_total"]
            ))

            # Actualizar stock físico en inventario
            cursor.execute("""
                UPDATE productos 
                SET stock_actual = stock_actual - ? 
                WHERE id = ?
            """, (item["cantidad"], item["producto_id"]))

        conn.commit()

        # Armar respuesta completa
        resultado_venta = {
            "id": venta_id,
            "tipo_comprobante": tipo_comprobante,
            "letra": tipo_comprobante,
            "codigo_afip": COMPROBANTES_AFIP[tipo_comprobante]["codigo"],
            "punto_venta": pto_vta,
            "numero_comprobante": nro_comprobante,
            "numero_formateado": f"{pto_vta:04d}-{nro_comprobante:08d}",
            "fecha": fecha_actual,
            "cliente_nombre": cliente_info.get("razon_social") or "Consumidor Final",
            "cliente_cuit": formatear_cuit(cuit_receptor),
            "cliente_condicion_iva": condicion_iva_receptor,
            "cliente_domicilio": cliente_info.get("domicilio") or "",
            "subtotal_neto": subtotal_neto_acumulado,
            "iva_total": iva_total_acumulado,
            "total": total_facturado,
            "metodo_pago": metodo_pago,
            "cae": cae,
            "cae_vto": cae_vto,
            "observaciones": observaciones,
            "estado": "EMITIDA",
            "items": items_calculados
        }

        # Generar QR
        resultado_venta["qr_url"] = generar_qr_afip_url(resultado_venta)

        return resultado_venta

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def anular_factura(venta_id: int) -> bool:
    """
    Anula una venta y restituye el stock al inventario.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado FROM ventas WHERE id = ?", (venta_id,))
        venta = cursor.fetchone()
        if not venta:
            raise BillingException("Comprobante no encontrado.")
        if venta["estado"] == "ANULADA":
            raise BillingException("El comprobante ya fue anulado previamente.")

        # Obtener los items para devolver stock
        cursor.execute("SELECT producto_id, cantidad FROM venta_items WHERE venta_id = ?", (venta_id,))
        items = cursor.fetchall()
        for item in items:
            cursor.execute("""
                UPDATE productos 
                SET stock_actual = stock_actual + ? 
                WHERE id = ?
            """, (item["cantidad"], item["producto_id"]))

        cursor.execute("UPDATE ventas SET estado = 'ANULADA' WHERE id = ?", (venta_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
