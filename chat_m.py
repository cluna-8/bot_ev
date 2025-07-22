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
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
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
            position: relative;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
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
        
        .chat-container { 
            height: 450px; 
            overflow-y: auto; 
            background: white;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .chat-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-container::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        
        .chat-container::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        
        .message { 
            padding: 15px 18px;
            border-radius: 18px;
            max-width: 80%;
            position: relative;
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
            border-top: 1px solid #e2e8f0;
        }
        
        .input-container { 
            display: flex; 
            gap: 12px;
            align-items: end;
        }
        
        .input-container textarea { 
            flex: 1; 
            padding: 15px 18px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 14px;
            resize: none;
            min-height: 50px;
            max-height: 120px;
            font-family: inherit;
            transition: border-color 0.2s ease;
        }
        
        .input-container textarea:focus {
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
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            min-width: 80px;
        }
        
        .send-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.4);
        }
        
        .send-btn:disabled {
            background: #94a3b8;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .clear-btn {
            background: transparent;
            color: #64748b;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s ease;
        }
        
        .clear-btn:hover {
            background: #fee2e2;
            color: #dc2626;
            border-color: #fecaca;
        }
        
        .message-count {
            color: #64748b;
            font-size: 12px;
        }
        
        .loading { 
            text-align: center; 
            color: #64748b;
            font-style: italic;
            padding: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .loading::before {
            content: '';
            width: 16px;
            height: 16px;
            border: 2px solid #e2e8f0;
            border-top: 2px solid #2563eb;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error-message {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            body { padding: 10px; }
            .chat-wrapper { border-radius: 15px; }
            .header { padding: 20px; }
            .logo { font-size: 20px; }
            .chat-container { height: 350px; padding: 15px; }
            .message { max-width: 90%; }
            .input-section { padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="chat-wrapper">
        <div class="header">
            <div class="logo">
                <img src="https://evidenze.com/assets/front/img/logos/logoEvidenze_blanco.png" alt="Evidenze" onerror="this.style.display='none'; this.parentElement.innerHTML='EVIDENZE AI';">
            </div>
            <div class="tagline">
                Bot prueba con seguridad GDPR Evidenze
            </div>
            <div class="security-badge">
                ● Memoria temporal por sesión para pruebas
            </div>
        </div>
        
        <div class="input-section">
            <div class="controls">
                <div class="message-count">
                    <span id="message-count">0</span> mensajes en esta sesión
                </div>
                <button class="clear-btn" onclick="clearConversation()">
                    ↻ Limpiar historial
                </button>
            </div>
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
                <textarea id="message-input" 
                         placeholder="Escribe tu mensaje aquí..." 
                         onkeydown="handleKeyDown(event)"
                         rows="1"></textarea>
                <button id="send-btn" class="send-btn" onclick="sendMessage()">
                    Enviar
                </button>
            </div>
        </div>
    </div>

    <script>
        // Almacén de conversación en memoria de sesión
        let conversationHistory = [
            {
                "role": "system",
                "content": "Eres un asistente de IA profesional de Evidenze, una empresa CRO especializada en investigación clínica y servicios farmacéuticos. Proporciona respuestas útiles, profesionales y precisas."
            }
        ];
        
        let messageCount = 0;
        
        // Función para enviar mensaje
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const sendBtn = document.getElementById('send-btn');
            const message = input.value.trim();
            
            if (!message) return;
            
            console.log('Enviando mensaje:', message);
            
            // Deshabilitar input
            sendBtn.disabled = true;
            sendBtn.textContent = 'Enviando...';
            
            // Mostrar mensaje del usuario
            addMessage(message, 'user-message');
            input.value = '';
            input.style.height = 'auto';
            
            // Agregar al historial
            conversationHistory.push({
                "role": "user",
                "content": message
            });
            
            updateMessageCount();
            
            // Mostrar indicador de carga
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = 'Procesando tu consulta...';
            document.getElementById('chat-container').appendChild(loadingDiv);
            scrollToBottom();
            
            try {
                console.log('Enviando request a /chat');
                
                // Enviar historial completo al backend
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ 
                        messages: conversationHistory 
                    })
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Response data:', data);
                
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
                    addMessage('❌ Error: No se pudo procesar tu mensaje', 'bot-message error-message');
                }
                
            } catch (error) {
                console.error('Error:', error);
                loadingDiv.remove();
                addMessage('❌ Error: Problema de conexión con el servidor', 'bot-message error-message');
            }
            
            // Reactivar input
            sendBtn.disabled = false;
            sendBtn.textContent = 'Enviar';
            input.focus();
        }
        
        // Función para agregar mensaje
        function addMessage(text, className) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${className}`;
            messageDiv.innerHTML = text.replace(/\n/g, '<br>');
            chatContainer.appendChild(messageDiv);
            scrollToBottom();
        }
        
        // Función para scroll
        function scrollToBottom() {
            const chatContainer = document.getElementById('chat-container');
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Función para actualizar contador
        function updateMessageCount() {
            const userMessages = conversationHistory.filter(msg => msg.role === 'user').length;
            document.getElementById('message-count').textContent = userMessages;
        }
        
        // Función para limpiar conversación
        function clearConversation() {
            if (confirm('¿Estás seguro de que quieres limpiar el historial de la conversación?')) {
                conversationHistory = [conversationHistory[0]];
                
                const chatContainer = document.getElementById('chat-container');
                chatContainer.innerHTML = `
                    <div class="message bot-message">
                        <strong>Bienvenido al Asistente de IA de Evidenze</strong><br>
                        Soy tu asistente inteligente especializado en investigación clínica y servicios farmacéuticos.<br>
                        Puedo ayudarte con consultas profesionales y recordaré nuestra conversación durante esta sesión.<br>
                        ¿En qué puedo asistirte hoy?
                    </div>
                `;
                
                updateMessageCount();
            }
        }
        
        // Función para manejar teclas
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        // Auto-resize del textarea
        function setupTextarea() {
            const textarea = document.getElementById('message-input');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        }
        
        // Inicialización cuando se carga la página
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM cargado, inicializando...');
            
            // Setup del textarea
            setupTextarea();
            
            // Focus inicial
            document.getElementById('message-input').focus();
            
            // Event listener de respaldo para el botón
            document.getElementById('send-btn').addEventListener('click', sendMessage);
        });
        
        // Hacer funciones globales (por si acaso)
        window.sendMessage = sendMessage;
        window.clearConversation = clearConversation;
        window.handleKeyDown = handleKeyDown;
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
        
        # Validar que el último mensaje sea del usuario
        if messages[-1]["role"] != "user":
            return JSONResponse({"error": "El último mensaje debe ser del usuario"}, status_code=400)
        
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