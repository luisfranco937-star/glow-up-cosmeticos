"""
Modelos de Datos y Esquemas Pydantic para Validación.
Glow Up Cosméticos S.R.L.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class CondicionIVAEnum(str, Enum):
    RESPONSABLE_INSCRIPTO = "IVA Responsable Inscripto"
    MONOTRIBUTO = "Monotributo"
    CONSUMIDOR_FINAL = "Consumidor Final"
    EXENTO = "Exento"

class TipoComprobanteEnum(str, Enum):
    FACTURA_A = "A"
    FACTURA_B = "B"

class MetodoPagoEnum(str, Enum):
    EFECTIVO = "Efectivo"
    TRANSFERENCIA = "Transferencia Bancaria"
    DEBITO = "Tarjeta de Débito"
    CREDITO = "Tarjeta de Crédito"
    CUENTA_CORRIENTE = "Cuenta Corriente"

# ----------------- CLIENTES -----------------
class ClienteBase(BaseModel):
    razon_social: str = Field(..., min_length=2, max_length=150, description="Nombre o Razón Social del cliente")
    cuit: Optional[str] = Field(None, description="CUIT o CUIL (formato XX-XXXXXXXX-X o 11 dígitos)")
    condicion_iva: CondicionIVAEnum = Field(..., description="Condición tributaria frente al IVA")
    domicilio: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id: int
    activo: int
    created_at: str

# ----------------- PRODUCTOS -----------------
class ProductoBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=30, description="Código de barras o SKU")
    nombre: str = Field(..., min_length=2, max_length=150, description="Nombre comercial del producto")
    marca: Optional[str] = Field(None, max_length=100)
    categoria: str = Field(..., max_length=100, description="Skincare, Make-Up, Fragancias, etc.")
    descripcion: Optional[str] = Field(None, max_length=300)
    precio_costo: float = Field(..., ge=0, description="Costo de adquisición")
    precio_neto: float = Field(..., ge=0, description="Precio unitario neto sin IVA")
    alicuota_iva: float = Field(default=21.0, description="Alícuota IVA porcentual (21% o 10.5%)")
    stock_actual: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=5, ge=0)

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    precio_costo: Optional[float] = None
    precio_neto: Optional[float] = None
    alicuota_iva: Optional[float] = None
    stock_actual: Optional[int] = None
    stock_minimo: Optional[int] = None

class ProductoResponse(ProductoBase):
    id: int
    activo: int
    created_at: str

# ----------------- VENTAS Y FACTURACIÓN -----------------
class ItemVentaCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0, description="Cantidad a vender")

class VentaCreate(BaseModel):
    cliente_id: Optional[int] = None
    # Si es cliente ocasional no registrado o se ingresa directo:
    cliente_nombre: Optional[str] = None
    cliente_cuit: Optional[str] = None
    cliente_condicion_iva: Optional[CondicionIVAEnum] = None
    cliente_domicilio: Optional[str] = None
    
    tipo_comprobante: TipoComprobanteEnum = Field(..., description="'A' para Factura A, 'B' para Factura B")
    metodo_pago: MetodoPagoEnum
    observaciones: Optional[str] = None
    items: List[ItemVentaCreate] = Field(..., min_items=1, description="Lista de artículos a facturar")

class ItemVentaResponse(BaseModel):
    id: int
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    cantidad: int
    precio_unitario_neto: float
    alicuota_iva: float
    subtotal_neto: float
    subtotal_iva: float
    subtotal_total: float

class VentaResponse(BaseModel):
    id: int
    tipo_comprobante: str
    punto_venta: int
    numero_comprobante: int
    fecha: str
    cliente_id: Optional[int]
    cliente_nombre: str
    cliente_cuit: Optional[str]
    cliente_condicion_iva: str
    cliente_domicilio: Optional[str]
    subtotal_neto: float
    iva_total: float
    total: float
    metodo_pago: str
    cae: str
    cae_vto: str
    observaciones: Optional[str]
    estado: str
    items: Optional[List[ItemVentaResponse]] = None
