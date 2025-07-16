"""
FastAPI App para el Bot de Teams con Azure OpenAI
"""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from bot import TeamsOpenAIBot
from config import BOT_APP_ID, BOT_APP_PASSWORD

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Teams OpenAI Bot",
    description="Bot interno para Teams con Azure OpenAI",
    version="2.0.0"
)

# Configurar Bot Framework Adapter (sin app_type)
bot_settings = BotFrameworkAdapterSettings(
    app_id=BOT_APP_ID,
    app_password=BOT_APP_PASSWORD
)

adapter = BotFrameworkAdapter(bot_settings)

# Crear instancia del bot
bot = TeamsOpenAIBot()

@app.get("/")
async def root():
    """Endpoint principal"""
    return {
        "message": "Teams OpenAI Bot v2.0",
        "status": "online",
        "bot_ready": bot.is_ready()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "bot_ready": bot.is_ready()
    }

@app.post("/api/messages")
async def messages(request: Request):
    """Endpoint para mensajes del Bot Framework"""
    try:
        # Obtener el body del request
        body = await request.json()
        
        # Deserializar la actividad
        activity = Activity().deserialize(body)
        
        # Obtener header de autorización
        auth_header = request.headers.get("Authorization", "")
        
        # Procesar la actividad
        response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        
        # Retornar respuesta
        if response:
            return JSONResponse(
                content=response.body,
                status_code=response.status
            )
        
        return JSONResponse(content={}, status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Error en /api/messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones"""
    logger.error(f"❌ Error global: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor"}
    )