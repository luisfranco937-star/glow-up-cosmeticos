# 📖 Manual de Procedimiento Técnico y Despliegue
## ✨ Glow Up Cosméticos S.R.L. - Sistema de Gestión Comercial y Facturación AFIP

Este documento registra de manera detallada todo el procedimiento técnico ejecutado para preparar, probar, transportar y desplegar el sistema **Glow Up Cosméticos S.R.L.** tanto en entornos locales (vía USB) como en la nube (servidor público 24/7 gratuito).

---

## 📌 1. Información General y Enlaces Oficiales

- **Repositorio Oficial de Código (GitHub):**  
  [https://github.com/luisfranco937-star/glow-up-cosmeticos](https://github.com/luisfranco937-star/glow-up-cosmeticos)
- **Servidor Web Activo 24/7 en Producción:**  
  [https://glow-up-cosmeticos.onrender.com](https://glow-up-cosmeticos.onrender.com)
- **Documentación Interactiva de APIs (Swagger):**  
  [https://glow-up-cosmeticos.onrender.com/docs](https://glow-up-cosmeticos.onrender.com/docs)
- **Stack Tecnológico:**
  - **Backend:** Python 3.12 + FastAPI + Uvicorn ASGI.
  - **Base de Datos:** SQLite3 relacional con claves foráneas activas y transacciones ACID.
  - **Frontend:** Jinja2 Templates, HTML5 semántico, CSS3 temático responsive, JavaScript Vanilla.
  - **Lógica Impositiva:** AFIP/ARCA, discriminación de IVA (21% y 10.5%), algoritmo Módulo 11 para CUIT, emisión de Factura A y B, asignación de CAE y generación de QR fiscal.

---

## 💻 2. Procedimiento: Portabilidad y Ejecución Local (USB)

Para garantizar que el sistema funcione en cualquier computadora sin necesidad de conexión a Internet permanente:

### A. Preparación del USB (Unidad `D:\`)
1. Se descargó el instalador oficial de Python para Windows de 64 bits:
   - Archivo: `D:\Instalador_Python_Windows.exe` (Python 3.12.6).
2. Se copió íntegramente la carpeta del proyecto a la unidad extraíble:
   - Carpeta: `D:\glow_up_cosmeticos\`
3. Se integraron scripts de automatización:
   - `requirements.txt`: Lista de dependencias (`fastapi`, `uvicorn`, `jinja2`, `pydantic`).
   - `instalar.bat`: Script de instalación rápida de librerías.
   - `run.bat`: Lanzador inteligente con comando `cd /d "%~dp0"` para ejecución autónoma y detección automática de paquetes faltantes.

### B. Pasos para abrir en otra computadora:
1. Conectar el pendrive USB.
2. Ejecutar `Instalador_Python_Windows.exe`.
   > **REQUISITO INDISPENSABLE:** Marcar la casilla **`☑ Add python.exe to PATH`** antes de dar clic en *Install Now*.
3. Entrar a `glow_up_cosmeticos` y hacer doble clic en **`run.bat`**.
4. Abrir en el navegador: `http://127.0.0.1:8000`.

---

## ☁️ 3. Procedimiento: Despliegue en la Nube 24/7 (Render.com + GitHub)

Para permitir que el sistema esté disponible permanentemente en Internet sin depender de que la computadora local esté encendida:

### Paso 1: Configuración de la Aplicación para la Nube
1. **Puerto dinámico:** Se adaptó `main.py` para leer la variable de entorno `PORT` proporcionada por el proveedor de la nube (`os.environ.get("PORT", 8000)` y escucha en host `0.0.0.0`).
2. **Plano de Despliegue (Blueprint):** Se creó el archivo `render.yaml`:
   ```yaml
   services:
     - type: web
       name: glow-up-cosmeticos
       runtime: python
       plan: free
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Paso 2: Control de Versiones con Git y GitHub
1. Se inicializó el repositorio local:
   ```bash
   git init
   git branch -M main
   ```
2. Se creó el repositorio remoto en GitHub:
   - Nombre: `glow-up-cosmeticos`
   - Propietario: `luisfranco937-star`
   - URL: `https://github.com/luisfranco937-star/glow-up-cosmeticos.git`
3. **Resolución de Conflicto de Credenciales:**
   - La máquina tenía guardada la sesión de un usuario previo (`yanu937`).
   - Se instaló la herramienta oficial **GitHub CLI (`gh`)**.
   - Se completó la autenticación segura por dispositivo (`gh auth login --web` con código de dispositivo).
   - Se configuró el helper de Git para el nuevo usuario: `gh auth setup-git`.
4. Se subieron los archivos a la rama principal:
   ```bash
   git add .
   git commit -m "feat: complete glow up cosmeticos project ready for cloud deployment"
   git push -u origin main
   ```

### Paso 3: Configuración del Web Service en Render
1. Se vinculó la cuenta de GitHub `luisfranco937-star` en [Render.com](https://render.com).
2. Se seleccionó el repositorio `glow-up-cosmeticos`.
3. Se configuraron los parámetros del servicio:
   - **Environment / Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free ($0/month)`
4. Se inició el despliegue automático. Render completó la construcción en contenedor Linux y asignó el dominio con certificado SSL:
   - 🌐 **https://glow-up-cosmeticos.onrender.com**

---

## 🧪 4. Verificación y Suite de Pruebas Automatizadas

El proyecto incluye pruebas integrales para validar que la matemática tributaria y la integridad del stock cumplan con la normativa:

Comando para ejecutar pruebas:
```bash
python tests/test_core.py
```

### Casos de prueba validados:
1. **Algoritmo Módulo 11 de CUIT:** Verificación del dígito verificador para CUITs válidos e inválidos.
2. **Restricción Fiscal AFIP:** Bloqueo automático para evitar que se emita Factura A a Consumidores Finales.
3. **Emisión de Factura A a Responsable Inscripto:** Cálculo correcto de Netos Gravados, alícuotas discriminadas (21% y 10.5%), totales, CAE y QR.
4. **Anulación y Reintegro de Inventario:** Cancelación de facturas con reposición automática del stock al inventario.

---

## 🔄 5. ¿Cómo Aplicar Cambios Futuros al Proyecto?

Si en el futuro deseas modificar algún texto, producto, estilo o funcionalidad:

1. Realiza las modificaciones en los archivos de la carpeta local:  
   `C:\Users\joa\.gemini\antigravity\scratch\glow_up_cosmeticos`
2. Abre la terminal en esa carpeta y ejecuta:
   ```bash
   git add .
   git commit -m "Descripción de los cambios realizados"
   git push origin main
   ```
3. **¡Listo!** Render detectará automáticamente el cambio en GitHub y actualizará la página web en vivo en menos de 2 minutos sin que tengas que hacer nada más.
