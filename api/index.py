import sys
from pathlib import Path

# Agregar directorio raíz a sys.path para importación correcta en Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import app

