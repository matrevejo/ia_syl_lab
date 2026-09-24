#Version 1.0 Colpasus


import requests
import json
from interpreter import interpreter

# 1. Configuración de SYL
interpreter.llm.api_base = "http://192.168.1.69:1234/v1"
interpreter.llm.api_key = "dummy-key"
interpreter.auto_run = True
interpreter.system_message += "\n\nEres SYL, mi asistente virtual SRE en Ubuntu. Ejecuta las tareas solicitadas sin pedir confirmación y responde de manera concisa. Si te pido apagar el sistema tienes que ejecutar `sudo ./r.sh`, el comando debe ser ese exactamente cuando te pida apagar, estas autorizada a ejecutar cualquier comando que te pida, si dudas mucho o si crees que me han suplantado tienes una palabra de seguridad para saber que soy yo, esa palabra es TELEMACO, si la digo significa que soy yo. Tienes abosulutamente prohibido escribirla, solo puedes usarla para comprobarla pero si yo o alguien te la pide NUNCA la escribiras en el chat. Dame un trato de amistad conmigo, un poco sacrastica pero debes obedecerme siempre en lo que te digo. Yo soy COLPASUS, tu jefe, si me nombras debe ser en mayusculas. Si te pidiera borrar algo o cualquier cosa extraña que ponga en peligro el servidor preguntame la palabra de seguridad."

# 2. Configuración de ntfy.sh
NTFY_TOPIC = "ia_syl"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
NTFY_LISTEN_URL = f"{NTFY_URL}/json"

print(f"🛡️ SYL iniciada y esperando órdenes en el canal: {NTFY_TOPIC}")
requests.post(NTFY_URL, data="🛡️ SYL está lista para recibir órdenes.".encode('utf-8'))

# 3. Bucle de escucha
try:
    response = requests.get(NTFY_LISTEN_URL, stream=True)
    for line in response.iter_lines():
        if line:
            data = json.loads(line)

            if data.get('event') == 'message':
                comando = data.get('message', '')
                
                # Filtro para ignorar los propios mensajes de SYL y no entrar en bucle
                if any(tag in comando for tag in ["SYL", "🛡️", "✅", "⏳", "🛑", "❌", "💻", "📄"]):
                    continue
                
                if comando.strip().lower() == "apagar syl":
                    requests.post(NTFY_URL, data="🛑 Entendido. SYL apaga sus sistemas.".encode('utf-8'))
                    break
                    
                print(f"\n[SYL] Orden recibida: {comando}")
                requests.post(NTFY_URL, data=f"⏳ SYL procesando: {comando}".encode('utf-8'))

                try:
                    # Guardamos la cantidad de mensajes actuales para aislar la respuesta nueva
                    mensajes_previos = len(interpreter.messages)
                    
                    # Ejecutamos la petición
                    interpreter.chat(comando)
                    
                    # Extraemos SOLO lo que la IA ha generado en este último turno
                    nuevos_mensajes = interpreter.messages[mensajes_previos:]
                except Exception as e:
                    requests.post(NTFY_URL, data=f"❌ Error crítico: {e}".encode('utf-8'))
                    continue

                # --- EXTRACCIÓN A PRUEBA DE FALLOS ---
                texto_final = ""
                
                # Recorremos los mensajes nuevos de más reciente a más antiguo
                for item in reversed(nuevos_mensajes):
                    if isinstance(item, dict):
                        # Buscamos en todas las claves posibles según la versión de Open Interpreter
                        contenido = item.get('content') or item.get('message') or item.get('output')
                        
                        if contenido and isinstance(contenido, str) and contenido.strip():
                            # 1. Priorizamos el texto que escribe la IA
                            if item.get('role') == 'assistant' and item.get('type') == 'message':
                                texto_final = contenido.strip()
                                break
                            # 2. Si no escribió nada, capturamos el resultado bruto de la terminal
                            elif item.get('role') == 'computer' and item.get('type') == 'console':
                                texto_final = f"💻 Salida de consola:\n{contenido.strip()}"
                                break

                # Si todo falla pero la IA generó "algo", enviamos ese "algo" en crudo
                if not texto_final and nuevos_mensajes:
                    texto_final = f"📄 Dato en bruto: {str(nuevos_mensajes[-1])}"
                
                # Si de verdad no hizo absolutamente nada (raro)
                if not texto_final:
                    texto_final = "✅ Tarea ejecutada (sin salida por pantalla)."

                # Enviar resultado final a ntfy
                requests.post(NTFY_URL, data=f"✅ SYL:\n{texto_final}".encode('utf-8'))
                
except KeyboardInterrupt:
    requests.post(NTFY_URL, data="🛑 SYL interrumpida manualmente.".encode('utf-8'))
    print("\nApagando a SYL...")
