"""
Bot Handler para Teams con Azure OpenAI
"""
import logging
from typing import List
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, ActivityTypes
from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME
)

logger = logging.getLogger(__name__)

class TeamsOpenAIBot(ActivityHandler):
    """
    Bot que maneja mensajes de Teams y los procesa con Azure OpenAI
    """
    
    def __init__(self):
        super().__init__()
        self.openai_client = None
        self._initialize_openai_client()
        
    def _initialize_openai_client(self):
        """
        Inicializa el cliente de Azure OpenAI usando Managed Identity
        """
        try:
            # Crear credential usando Managed Identity
            credential = DefaultAzureCredential()
            
            # Función para obtener token que se refresca automáticamente
            def get_azure_ad_token():
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                return token.token

            # Crear cliente async de Azure OpenAI con token provider
            self.openai_client = AsyncAzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_ad_token_provider=get_azure_ad_token,
                default_headers={"User-Agent": "Teams-Bot/1.0"}
)
            
            logger.info("✅ Cliente de Azure OpenAI inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente de Azure OpenAI: {e}")
            self.openai_client = None

    def is_initialized(self) -> bool:
        """
        Verifica si el bot está correctamente inicializado
        """
        return self.openai_client is not None
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Se ejecuta cuando el bot recibe un mensaje de texto
        """
        user_message = turn_context.activity.text.strip()
        user_name = turn_context.activity.from_property.name or "Usuario"
        
        logger.info(f"👤 Mensaje de {user_name}: {user_message}")
        
        # Verificar si el cliente está inicializado
        if not self.openai_client:
            await turn_context.send_activity(
                "❌ Lo siento, el servicio de IA no está disponible en este momento. "
                "Por favor, contacta al administrador del sistema."
            )
            return
        
        # Respuesta rápida para saludos
        if user_message.lower() in ["hola", "hi", "hello", "buenos días", "buenas tardes"]:
            await turn_context.send_activity(
                f"¡Hola {user_name}! 👋 Soy tu asistente interno de IA. "
                "¿En qué puedo ayudarte hoy?"
            )
            return
        
        # Comando de ayuda
        if user_message.lower() in ["ayuda", "help", "?"]:
            await self._send_help_message(turn_context)
            return
        
        # Procesar mensaje con Azure OpenAI
        if user_message:
            await self._process_with_openai(turn_context, user_message, user_name)
    
    async def _process_with_openai(self, turn_context: TurnContext, user_message: str, user_name: str):
        """
        Procesa el mensaje del usuario con Azure OpenAI
        """
        try:
            # Enviar indicador de que el bot está "escribiendo"
            await turn_context.send_activity("🤔 Procesando tu consulta...")
            
            # Preparar mensajes para la API
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente interno de la empresa Evidenze, amable, útil y profesional. "
                        "Tu objetivo es ayudar a los empleados con consultas relacionadas con el trabajo, "
                        "procesos internos, preguntas técnicas generales y tareas corporativas. "
                        "Mantén tus respuestas concisas pero completas. "
                        "Si no puedes ayudar con algo específico, explica por qué y sugiere alternativas. "
                        "Usa emojis ocasionalmente para hacer la conversación más amigable."
                    )
                },
                {
                    "role": "user",
                    "content": f"Usuario: {user_name}\nConsulta: {user_message}"
                }
            ]
            
            # Llamar a Azure OpenAI
            response = await self.openai_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                max_tokens=500,  # Límite de tokens para la respuesta
                temperature=0.7,  # Creatividad moderada
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Extraer la respuesta
            ai_response = response.choices[0].message.content
            
            # Log del uso de tokens (para monitoreo de costos)
            usage = response.usage
            logger.info(
                f"💰 Uso de tokens - Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, "
                f"Total: {usage.total_tokens}"
            )
            
            # Enviar respuesta al usuario
            await turn_context.send_activity(ai_response)
            
        except Exception as e:
            logger.error(f"❌ Error procesando con OpenAI: {e}")
            await turn_context.send_activity(
                "😔 Lo siento, no pude procesar tu consulta en este momento. "
                "Por favor, inténtalo de nuevo más tarde o contacta al equipo de soporte."
            )
    
    async def _send_help_message(self, turn_context: TurnContext):
        """
        Envía mensaje de ayuda al usuario
        """
        help_message = (
            "🤖 **Asistente IA de Evidenze**\n\n"
            "Puedo ayudarte con:\n"
            "• Consultas generales sobre procesos de trabajo\n"
            "• Preguntas técnicas\n"
            "• Información sobre herramientas y sistemas\n"
            "• Resolución de problemas comunes\n\n"
            "💡 **Consejos:**\n"
            "• Sé específico en tus preguntas\n"
            "• Incluye contexto relevante\n"
            "• Pregunta una cosa a la vez\n\n"
            "📧 Para soporte técnico avanzado, contacta al equipo de IT."
        )
        
        await turn_context.send_activity(help_message)
    
    async def on_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ):
        """
        Se ejecuta cuando se agregan nuevos miembros al chat
        """
        for member in members_added:
            # No saludar al mismo bot
            if member.id != turn_context.activity.recipient.id:
                welcome_message = (
                    f"¡Bienvenido al asistente IA de Evidenze, {member.name}! 👋\n\n"
                    "🤖 Soy tu asistente interno de inteligencia artificial. "
                    "Estoy aquí para ayudarte con consultas relacionadas con el trabajo, "
                    "procesos internos y preguntas técnicas generales.\n\n"
                    "💡 Escribe 'ayuda' para ver qué puedo hacer por ti."
                )
                
                await turn_context.send_activity(welcome_message)
    
    async def on_activity(self, turn_context: TurnContext):
        """
        Maneja todos los tipos de actividad
        """
        logger.info(f"📨 Actividad recibida: {turn_context.activity.type}")
        
        # Llamar al handler padre
        await super().on_activity(turn_context)