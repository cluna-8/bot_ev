"""
FastAPI App para el Bot de Teams con Azure OpenAI
"""
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from pydantic import BaseModel
from bot import TeamsOpenAIBot
from config import BOT_APP_ID, BOT_APP_PASSWORD

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Teams OpenAI Bot",
    description="Bot interno para Teams con Azure OpenAI",
    version="1.0.0"
)

# Configuración del Bot Framework Adapter para UserAssignedMSI
bot_settings = BotFrameworkAdapterSettings(
    app_id=BOT_APP_ID,
    app_password=""  # Vacío para Managed Identity
)
adapter = BotFrameworkAdapter(bot_settings)

# Crear instancia del bot
bot = TeamsOpenAIBot()

# Modelo para el request (opcional, para validación)
class ActivityRequest(BaseModel):
    """Modelo para validar el request de Teams"""
    class Config:
        extra = "allow"  # Permite campos adicionales

@app.get("/")
async def root():
    """Endpoint raíz para verificar que el bot está funcionando"""
    return {
        "message": "Teams OpenAI Bot está funcionando",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/test-connection")
async def test_connection():
    """Test de conexión a Azure OpenAI"""
    try:
        from azure.identity import DefaultAzureCredential
        from openai import AsyncAzureOpenAI
        from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME
        
        result = {}
        
        # Paso 1: Verificar variables de entorno
        result["config"] = {
            "endpoint": AZURE_OPENAI_ENDPOINT,
            "api_version": AZURE_OPENAI_API_VERSION,
            "deployment": AZURE_OPENAI_DEPLOYMENT_NAME
        }
        
        # Paso 2: Probar obtener token
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        result["token"] = {
            "obtained": True,
            "expires_on": str(token.expires_on)
        }
        
        # Paso 3: Probar crear cliente
        client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_ad_token_provider=lambda: token.token,
            default_headers={"User-Agent": "Teams-Bot/1.0"}
        )
        result["client"] = {"created": True}
        
        # Paso 4: Probar llamada real a Azure OpenAI
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=50
        )
        result["api_call"] = {
            "success": True,
            "response": response.choices[0].message.content
        }
        
        return {"status": "success", "details": result}
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        }

@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "bot_initialized": bot.is_initialized(),
        "timestamp": "2025-07-08T08:00:00Z"
    }

@app.post("/api/messages")
async def handle_messages(request: Request):
    """
    Endpoint principal que recibe mensajes de Teams
    Azure Bot Service enviará requests POST aquí
    """
    try:
        # Verificar que el content-type sea JSON
        if not request.headers.get("content-type", "").startswith("application/json"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content-Type debe ser application/json"
            )
        
        # Obtener el body del request
        body = await request.json()
        logger.info(f"Mensaje recibido: {body}")
        
        # Deserializar la actividad del Bot Framework
        activity = Activity().deserialize(body)
        
        # Obtener el header de autorización
        auth_header = request.headers.get("Authorization", "")
        
        # Procesar la actividad con el adapter
        response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        
        # Retornar la respuesta
        if response:
            return JSONResponse(
                content=response.body,
                status_code=response.status,
                headers={"Content-Type": "application/json"}
            )
        
        return JSONResponse(content={}, status_code=200)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )

# Para desarrollo local
if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app:app",  # Cambiado de "main:app" a "app:app"
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True  # Solo para desarrollo
    )