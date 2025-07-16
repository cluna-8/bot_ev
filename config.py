"""
Configuración para el Bot de Teams con Azure OpenAI
"""
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN DE AZURE OPENAI ===
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

# === CONFIGURACIÓN DEL BOT FRAMEWORK ===
BOT_APP_ID = os.environ.get("MicrosoftAppId", "")
BOT_APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

# === CONFIGURACIÓN DE AZURE OPENAI ===
MAX_TOKENS = 500
TEMPERATURE = 0.7

# === SYSTEM PROMPT ===
SYSTEM_PROMPT = """
Eres un asistente interno de la empresa Evidenze, amable, útil y profesional. 
Ayuda a los empleados con consultas relacionadas con el trabajo, procesos internos y preguntas técnicas generales.
Mantén tus respuestas concisas pero completas.
Usa emojis ocasionalmente para hacer la conversación más amigable.
Siempre responde en español.
"""

# === VALIDACIÓN ===
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT es requerido")
if not AZURE_OPENAI_DEPLOYMENT_NAME:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME es requerido")

logger.info("✅ Configuración cargada correctamente")