"""
Punto de Entrada Principal (Entrypoint)
Software de Gestión Comercial - Glow Up Cosméticos S.R.L.
Trabajo Práctico Integrador
"""

import sys
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database import init_db
from routes.api import router as api_router
from routes.views import router as views_router
from config import EMPRESA

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización de la base de datos y datos semilla
    print("\n" + "="*60)
    print("✨ INICIANDO SISTEMA DE GESTIÓN COMERCIAL - GLOW UP COSMÉTICOS ✨")
    print(f"🏢 Empresa: {EMPRESA['razon_social']} (CUIT: {EMPRESA['cuit']})")
    print(f"📋 Condición IVA: {EMPRESA['condicion_iva']}")
    print("🛠️ Inicializando base de datos SQLite y verificando tablas...")
    init_db()
    print("✅ Base de datos lista con datos de prueba cargados.")
    print("🌐 Servidor Web disponible en: http://127.0.0.1:8000")
    print("📖 Documentación Swagger API en: http://127.0.0.1:8000/docs")
    print("="*60 + "\n")
    yield

app = FastAPI(
    title="Glow Up Cosméticos - Gestión Comercial",
    description="Sistema de gestión comercial, inventario y facturación electrónica (Factura A / B) adaptado a normativa tributaria argentina.",
    version="1.0.0",
    lifespan=lifespan
)

# Servir archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Registrar enrutadores
app.include_router(views_router)
app.include_router(api_router)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
