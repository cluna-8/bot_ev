"""
Configuración para el Bot de Teams con Azure OpenAI
"""
import os
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno (opcional para desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Variables de entorno cargadas desde .env")
except ImportError:
    logger.info("📝 python-dotenv no disponible, usando variables de entorno del sistema")

# === CONFIGURACIÓN DE AZURE OPENAI ===

AZURE_OPENAI_ENDPOINT: Optional[str] = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION: Optional[str] = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

# Validar configuración de Azure OpenAI
if not AZURE_OPENAI_ENDPOINT:
    logger.error("❌ AZURE_OPENAI_ENDPOINT no configurado")
    raise ValueError("AZURE_OPENAI_ENDPOINT es requerido")

if not AZURE_OPENAI_DEPLOYMENT_NAME:
    logger.error("❌ AZURE_OPENAI_DEPLOYMENT_NAME no configurado")
    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME es requerido")

logger.info(f"🔧 Azure OpenAI configurado - Endpoint: {AZURE_OPENAI_ENDPOINT}")
logger.info(f"🔧 Deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")

# === CONFIGURACIÓN DEL BOT FRAMEWORK ===

# ID de la aplicación del bot (obtenido de Azure Bot Service)
BOT_APP_ID: str = os.environ.get("MicrosoftAppId", "")

# Password de la aplicación (generalmente vacío con Managed Identity)
BOT_APP_PASSWORD: str = os.environ.get("MicrosoftAppPassword", "")

# Validar configuración del bot
if not BOT_APP_ID:
    logger.warning("⚠️ MicrosoftAppId no configurado, usando cadena vacía")
    
logger.info(f"🤖 Bot Framework configurado - App ID: {BOT_APP_ID[:10]}...")

# === CONFIGURACIÓN DE LA APLICACIÓN ===

# Configuración de logging
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configuración del servidor
PORT: int = int(os.environ.get("PORT", 8000))
HOST: str = os.environ.get("HOST", "0.0.0.0")

# Configuración de desarrollo
DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"

# === CONFIGURACIÓN DE AZURE OPENAI ADICIONAL ===

# Configuración de tokens
MAX_TOKENS: int = int(os.environ.get("MAX_TOKENS", "500"))
TEMPERATURE: float = float(os.environ.get("TEMPERATURE", "0.7"))

# Configuración de timeouts
OPENAI_TIMEOUT: int = int(os.environ.get("OPENAI_TIMEOUT", "30"))

logger.info(f"🚀 Configuración completa - Puerto: {PORT}, Debug: {DEBUG}")

# === MENSAJES DEL SISTEMA ===

SYSTEM_PROMPT = """
Eres un asistente interno de la empresa Evidenze, amable, útil y profesional. 
Tu objetivo es ayudar a los empleados con:

1. Consultas relacionadas con el trabajo
2. Procesos internos de la empresa
3. Preguntas técnicas generales
4. Tareas corporativas y administrativas

INSTRUCCIONES:
- Mantén tus respuestas concisas pero completas
- Usa un tono profesional pero amigable
- Si no puedes ayudar con algo específico, explica por qué y sugiere alternativas
- Usa emojis ocasionalmente para hacer la conversación más amigable
- Siempre responde en español
- No proporciones información confidencial o sensible

LIMITACIONES:
- No puedes acceder a sistemas internos específicos
- No puedes realizar acciones en nombre de los usuarios
- No puedes proporcionar información financiera detallada
- Para soporte técnico avanzado, dirige al equipo de IT
"""

# === VALIDACIÓN FINAL ===

def validate_config():
    """
    Valida que todas las configuraciones necesarias estén presentes
    """
    required_vars = [
        ("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_DEPLOYMENT_NAME", AZURE_OPENAI_DEPLOYMENT_NAME),
    ]
    
    missing_vars = []
    for var_name, var_value in required_vars:
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        error_msg = f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✅ Configuración validada correctamente")

# Ejecutar validación al importar
validate_config()