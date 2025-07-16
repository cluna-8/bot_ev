"""
Chatbot Web con Azure OpenAI
"""
import os
import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from openai import AsyncAzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    SYSTEM_PROMPT,
    MAX_TOKENS,
    TEMPERATURE
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(title="Chatbot Web Evidenze")

# HTML para la interfaz
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot Evidenze</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f2f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .chat-container { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; background: #fafafa; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #007bff; color: white; text-align: right; }
        .bot-message { background: #e9ecef; color: #333; }
        .input-container { display: flex; gap: 10px; }
        .input-container input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-container button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .input-container button:hover { background: #0056b3; }
        .loading { text-align: center; color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Chatbot Evidenze</h1>
            <p>Asistente de IA para empleados</p>
        </div>
        
        <div id="chat-container" class="chat-container">
            <div class="message bot-message">
                ¡Hola! 👋 Soy el asistente de IA de Evidenze. ¿En qué puedo ayudarte?
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="message-input" placeholder="Escribe tu mensaje..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Mostrar mensaje del usuario
            addMessage(message, 'user-message');
            input.value = '';
            
            // Mostrar indicador de carga
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = '🤔 Procesando...';
            document.getElementById('chat-container').appendChild(loadingDiv);
            
            try {
                // Enviar mensaje al backend
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Remover indicador de carga
                loadingDiv.remove();
                
                if (data.response) {
                    addMessage(data.response, 'bot-message');
                } else {
                    addMessage('Error: No se pudo procesar tu mensaje', 'bot-message');
                }
            } catch (error) {
                loadingDiv.remove();
                addMessage('Error: Problema de conexión', 'bot-message');
            }
        }
        
        function addMessage(text, className) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${className}`;
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal del chatbot"""
    return HTML_TEMPLATE

@app.post("/chat")
async def chat(request: Request):
    """Endpoint para procesar mensajes del chat"""
    try:
        # Obtener mensaje del usuario
        body = await request.json()
        user_message = body.get("message", "").strip()
        
        if not user_message:
            return JSONResponse({"error": "Mensaje vacío"}, status_code=400)
        
        # Crear cliente OpenAI
        client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            default_headers={"User-Agent": "WebChat/1.0"}
        )
        
        # Llamar a OpenAI
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        # Extraer respuesta
        ai_response = response.choices[0].message.content
        
        # Log para monitoreo
        logger.info(f"Chat - Usuario: {user_message[:50]}... | Tokens: {response.usage.total_tokens}")
        
        return JSONResponse({"response": ai_response})
        
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return JSONResponse({"error": "Error procesando mensaje"}, status_code=500)

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "chatbot-web"}