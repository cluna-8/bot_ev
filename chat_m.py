"""
Chatbot Web con Azure OpenAI - Evidenze con Memoria de Sesión
"""
import os
import logging
from fastapi import FastAPI, Request
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
app = FastAPI(title="Evidenze AI Chatbot")

# HTML para la interfaz con diseño Evidenze
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Asistente de IA Evidenze</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a2332 0%, #2d3748 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-wrapper {
            width: 100%;
            max-width: 900px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
        }
        
        .header { 
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            padding: 25px 30px;
            text-align: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }
        
        .logo img {
            height: 35px;
            width: auto;
        }
        
        .tagline {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .security-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            margin-top: 8px;
        }
        
        .controls {
            background: white;
            padding: 15px 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .message-count {
            color: #64748b;
            font-size: 12px;
        }
        
        .clear-btn {
            background: transparent;
            color: #64748b;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .clear-btn:hover {
            background: #fee2e2;
            color: #dc2626;
            border-color: #fecaca;
        }
        
        .chat-container { 
            height: 450px; 
            overflow-y: auto; 
            background: white;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .message { 
            padding: 15px 18px;
            border-radius: 18px;
            max-width: 80%;
            animation: fadeInUp 0.3s ease;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message { 
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        
        .bot-message { 
            background: #f8fafc;
            color: #1e293b;
            align-self: flex-start;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .input-section {
            background: white;
            padding: 20px;
        }
        
        .input-container { 
            display: flex; 
            gap: 12px;
            align-items: center;
        }
        
        .input-container input { 
            flex: 1; 
            padding: 15px 18px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 14px;
            font-family: inherit;
        }
        
        .input-container input:focus {
            outline: none;
            border-color: #2563eb;
        }
        
        .send-btn { 
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 15px 24px;
            cursor: pointer;
            font-weight: 600;
            min-width: 80px;
        }
        
        .send-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.4);
        }
        
        .loading { 
            text-align: center; 
            color: #64748b;
            font-style: italic;
            padding: 15px;
        }
        
        @media (max-width: 768px) {
            body { padding: 10px; }
            .chat-container { height: 350px; }
            .message { max-width: 90%; }
        }
    </style>
</head>
<body>
    <div class="chat-wrapper">
        <div class="header">
            <div class="logo">
                <img src="https://evidenze.com/assets/front/img/logos/logoEvidenze_blanco.png" 
                     alt="Evidenze" 
                     onerror="this.style.display='none'; this.parentElement.innerHTML='EVIDENZE AI';">
            </div>
            <div class="tagline">
                Bot prueba con seguridad GDPR Evidenze
            </div>
            <div class="security-badge">
                ● Memoria temporal por sesión para pruebas
            </div>
        </div>
        
        <div class="controls">
            <div class="message-count">
                <span id="message-count">0</span> mensajes en esta sesión
            </div>
            <button class="clear-btn" onclick="clearConversation()">
                ↻ Limpiar historial
            </button>
        </div>
        
        <div id="chat-container" class="chat-container">
            <div class="message bot-message">
                <strong>Bienvenido al Asistente de IA de Evidenze</strong><br>
                Soy tu asistente inteligente especializado en investigación clínica y servicios farmacéuticos.<br>
                Puedo ayudarte con consultas profesionales y recordaré nuestra conversación durante esta sesión.<br>
                ¿En qué puedo asistirte hoy?
            </div>
        </div>
        
        <div class="input-section">
            <div class="input-container">
                <input type="text" id="message-input" placeholder="Escribe tu mensaje aquí..." onkeypress="handleKeyPress(event)">
                <button class="send-btn" onclick="sendMessage()">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        // Memoria de conversación - EXACTAMENTE como tu código que funcionaba, pero con historial
        var conversationHistory = [
            {
                "role": "system",
                "content": "Eres un asistente de IA profesional de Evidenze, una empresa CRO especializada en investigación clínica y servicios farmacéuticos. Proporciona respuestas útiles, profesionales y precisas."
            }
        ];
        
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Mostrar mensaje del usuario (IGUAL que tu versión)
            addMessage(message, 'user-message');
            input.value = '';
            
            // Agregar al historial
            conversationHistory.push({
                "role": "user",
                "content": message
            });
            
            updateMessageCount();
            
            // Mostrar indicador de carga (IGUAL que tu versión)
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = 'Procesando tu consulta...';
            document.getElementById('chat-container').appendChild(loadingDiv);
            
            try {
                // Enviar historial completo al backend
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: conversationHistory })
                });
                
                const data = await response.json();
                
                // Remover indicador de carga
                loadingDiv.remove();
                
                if (data.response) {
                    addMessage(data.response, 'bot-message');
                    
                    // Agregar respuesta al historial
                    conversationHistory.push({
                        "role": "assistant",
                        "content": data.response
                    });
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
            messageDiv.className = 'message ' + className;
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function updateMessageCount() {
            var userMessages = 0;
            for (var i = 0; i < conversationHistory.length; i++) {
                if (conversationHistory[i].role === 'user') {
                    userMessages++;
                }
            }
            document.getElementById('message-count').textContent = userMessages;
        }
        
        function clearConversation() {
            if (confirm('¿Estás seguro de que quieres limpiar el historial de la conversación?')) {
                conversationHistory = [conversationHistory[0]]; // Mantener solo system prompt
                
                const chatContainer = document.getElementById('chat-container');
                chatContainer.innerHTML = '<div class="message bot-message"><strong>Bienvenido al Asistente de IA de Evidenze</strong><br>Soy tu asistente inteligente especializado en investigación clínica y servicios farmacéuticos.<br>Puedo ayudarte con consultas profesionales y recordaré nuestra conversación durante esta sesión.<br>¿En qué puedo asistirte hoy?</div>';
                
                updateMessageCount();
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal del chatbot Evidenze"""
    return HTML_TEMPLATE

@app.post("/chat")
async def chat(request: Request):
    """Endpoint para procesar mensajes del chat con memoria"""
    try:
        # Obtener historial de conversación
        body = await request.json()
        messages = body.get("messages", [])
        
        if not messages or len(messages) < 2:
            return JSONResponse({"error": "Historial de conversación inválido"}, status_code=400)
        
        # Crear cliente OpenAI
        client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            default_headers={"User-Agent": "EvidenzeChat/1.0"}
        )
        
        # Llamar a OpenAI con el historial completo
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        # Extraer respuesta
        ai_response = response.choices[0].message.content
        
        # Log para monitoreo
        user_message = messages[-1]["content"]
        logger.info(f"Evidenze Chat - Usuario: {user_message[:50]}... | Historial: {len(messages)} msgs | Tokens: {response.usage.total_tokens}")
        
        return JSONResponse({"response": ai_response})
        
    except Exception as e:
        logger.error(f"Error en chat de Evidenze: {e}")
        return JSONResponse({"error": "Error procesando mensaje"}, status_code=500)

@app.get("/health")
async def health():
    """Health check para Evidenze chatbot"""
    return {
        "status": "healthy", 
        "service": "evidenze-chatbot",
        "features": ["session_memory", "gdpr_compliant", "azure_openai"]
    }