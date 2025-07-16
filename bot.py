"""
Bot Handler para Teams con Azure OpenAI
"""
import logging
from typing import List
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    SYSTEM_PROMPT,
    MAX_TOKENS,
    TEMPERATURE
)

logger = logging.getLogger(__name__)

class TeamsOpenAIBot(ActivityHandler):
    """Bot que procesa mensajes de Teams con Azure OpenAI"""
    
    def __init__(self):
        super().__init__()
        logger.info("✅ Bot inicializado correctamente")
    
    def is_ready(self) -> bool:
        """El bot siempre está listo (crea cliente bajo demanda)"""
        return True
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Procesa mensajes de texto"""
        user_message = turn_context.activity.text.strip()
        user_name = turn_context.activity.from_property.name or "Usuario"
        
        logger.info(f"👤 {user_name}: {user_message}")
        
        # Respuesta rápida para saludos
        if user_message.lower() in ["hola", "hi", "hello"]:
            await turn_context.send_activity(f"¡Hola {user_name}! 👋 ¿En qué puedo ayudarte?")
            return
        
        # Procesar con OpenAI
        await self._process_message(turn_context, user_message, user_name)
    
    async def _process_message(self, turn_context: TurnContext, message: str, user_name: str):
        """Procesa el mensaje con OpenAI (crea cliente cada vez)"""
        try:
            await turn_context.send_activity("🤔 Procesando...")
            
            # Usar exactamente la misma lógica que funciona en el endpoint
            credential = DefaultAzureCredential(
                managed_identity_client_id="a5787cf8-15b6-4980-ba9d-2b9b76884a3a"
            )
            
            # Obtener token
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            
            # Crear cliente (como en el endpoint que funciona)
            client = AsyncAzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_ad_token_provider=lambda: token.token,
                default_headers={"User-Agent": "Teams-Bot/1.0"}
            )
            
            # Llamar a OpenAI
            response = await client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Usuario: {user_name}\nConsulta: {message}"}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            # Enviar respuesta
            ai_response = response.choices[0].message.content
            await turn_context.send_activity(ai_response)
            
            # Log de tokens
            usage = response.usage
            logger.info(f"💰 Tokens: {usage.total_tokens}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            logger.error(f"❌ Tipo: {type(e).__name__}")
            await turn_context.send_activity("😔 No pude procesar tu consulta. Intenta de nuevo.")
    
    async def on_members_added_activity(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        """Saluda a nuevos miembros"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(f"¡Bienvenido {member.name}! 👋 Soy el asistente IA de Evidenze.")