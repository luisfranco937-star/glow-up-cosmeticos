"""
Configuración general de la aplicación y parámetros fiscales del emisor
Glow Up Cosméticos S.R.L.
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

if os.environ.get("VERCEL"):
    TEMP_DB = Path("/tmp") / "glow_up.db"
    ORIGINAL_DB = BASE_DIR / "glow_up.db"
    if not TEMP_DB.exists() and ORIGINAL_DB.exists():
        shutil.copy2(ORIGINAL_DB, TEMP_DB)
    DB_PATH = TEMP_DB
else:
    DB_PATH = BASE_DIR / "glow_up.db"

# Datos Fiscales de la Empresa Emisora (Responsable Inscripto)
EMPRESA = {
    "nombre_fantasia": "Glow Up Cosméticos",
    "razon_social": "Glow Up Cosméticos S.R.L.",
    "cuit": "30-71829347-9",
    "condicion_iva": "IVA Responsable Inscripto",
    "punto_venta": 1,
    "domicilio": "Av. Santa Fe 2450, Piso 3, CABA",
    "ingresos_brutos": "30-71829347-9 (CM)",
    "inicio_actividades": "01/03/2022",
    "telefono": "+54 11 4821-9988",
    "email": "ventas@glowupcosmeticos.com.ar",
    "web": "www.glowupcosmeticos.com.ar"
}

# Tipos de comprobante según codificación AFIP / ARCA
COMPROBANTES_AFIP = {
    "A": {
        "codigo": "01",
        "descripcion": "FACTURA A",
        "letra": "A",
        "requiere_cuit": True,
        "condicion_receptor_permitida": ["IVA Responsable Inscripto"],
        "discrimina_iva": True
    },
    "B": {
        "codigo": "06",
        "descripcion": "FACTURA B",
        "letra": "B",
        "requiere_cuit": False,
        "condicion_receptor_permitida": ["Consumidor Final", "Monotributo", "Exento"],
        "discrimina_iva": False
    }
}
