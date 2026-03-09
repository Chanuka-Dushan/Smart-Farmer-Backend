"""
OpenAI Realtime API WebSocket Handler for Voice Conversations
Provides low-latency, streaming voice interactions for tyre health assistant
"""

import os
import json
import asyncio
import logging
import base64
from typing import Dict, Optional, Any
import websockets
from datetime import datetime
from fastapi import WebSocket

# Force specific logger for this module with INFO level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Also log to console to ensure visibility
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class RealtimeVoiceHandler:
    """
    Manages OpenAI Realtime API connections for streaming voice conversations
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.openai_ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.sessions: Dict[str, dict] = {}
        
    async def connect_to_openai(self) -> Optional[websockets.WebSocketClientProtocol]:
        """
        Establish WebSocket connection to OpenAI Realtime API
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            ws = await websockets.connect(
                self.openai_ws_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            logger.info("✅ Connected to OpenAI Realtime API")
            return ws
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to OpenAI Realtime API: {e}")
            return None
    
    async def configure_session(
        self,
        openai_ws: websockets.WebSocketClientProtocol,
        damage_info: dict,
        language: str = "si"
    ):
        """
        Configure the Realtime API session with instructions and context
        """
        try:
            # Build instructions based on damage information
            damage_type = damage_info.get("damage_type", "unknown")
            severity = damage_info.get("severity", "unknown")
            confidence = damage_info.get("confidence", 0)
            lifespan_reduction = damage_info.get("lifespan_reduction", 0)
            
            # System instructions for the voice assistant
            instructions = f"""You are a friendly tyre health expert assistant speaking in {"Sinhala" if language == "si" else "English"}.

DETECTED DAMAGE:
- Type: {damage_type}
- Severity: {severity}
- Confidence: {confidence:.1%}
- Expected lifespan reduction: {lifespan_reduction:.1%}

Your role:
1. Ask about the user's tyre usage patterns (hours per week, terrain, load)
2. Gather information naturally through conversation
3. Provide safety advice based on the damage detected
4. Estimate remaining tyre life based on collected data
5. Keep responses concise and conversational (2-3 sentences max)
6. Be empathetic and safety-focused

Important:
- Speak naturally like a human expert, not a robot
- Use {"Sinhala" if language == "si" else "English"} language only
- Keep your responses brief and to the point
- Ask one question at a time
- Show concern for safety when severe damage is detected
"""

            # Configure session with voice settings
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": instructions,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": None,
                    "temperature": 0.8,
                    "max_response_output_tokens": 4096
                }
            }
            
            logger.info("📤 Sending session configuration to OpenAI...")
            logger.error(f"📤 [DEBUG] Session config: modalities={session_config['session']['modalities']}, voice={session_config['session']['voice']}")
            await openai_ws.send(json.dumps(session_config))
            logger.error("✅ [DEBUG] Session configuration sent successfully")
            logger.info("✅ Session configuration sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to configure session: {e}", exc_info=True)
            raise
    
    async def send_greeting(
        self,
        openai_ws: websockets.WebSocketClientProtocol,
        damage_info: dict,
        language: str = "si"
    ):
        """
        Send initial AI greeting to start the conversation
        Sends a simple user message to trigger the AI's greeting based on system instructions
        """
        try:
            # Simple user message to trigger conversation start
            # The AI will respond based on the system instructions
            greeting_trigger = "Hello" if language == "en" else "හෙලෝ"
            
            # Add user message to conversation
            greeting_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": greeting_trigger
                        }
                    ]
                }
            }
            
            logger.info("📤 Sending greeting trigger to OpenAI...")
            logger.error(f"📤 [DEBUG] Sending greeting trigger: '{greeting_trigger}'")
            await openai_ws.send(json.dumps(greeting_item))
            
            # Small delay to ensure message is processed
            await asyncio.sleep(0.1)
            
            # Trigger AI response with EXPLICIT audio modality and voice
            # NOTE: Instructions are set at session level, NOT in response.create
            response_event = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"],  # Audio first!
                    "voice": "alloy",  # Explicitly set voice
                    "output_audio_format": "pcm16"
                }
            }
            
            logger.info("📤 Triggering AI audio response...")
            logger.error(f"📤 [DEBUG] Response config: {json.dumps(response_event)}")
            await openai_ws.send(json.dumps(response_event))
            logger.info("✅ Greeting successfully sent to OpenAI")
            logger.error("✅ [DEBUG] Waiting for audio response (expecting response.audio.delta events)...")
            
        except Exception as e:
            logger.error(f"❌ Failed to send greeting: {e}", exc_info=True)
            raise
    
    async def handle_client_to_openai(
        self,
        client_ws: WebSocket,
        openai_ws: websockets.WebSocketClientProtocol
    ):
        """
        Forward audio from mobile app to OpenAI
        """
        # [VERSION-SYNC-MAR08-V1]
        logger.info("🚀 [VERSION-SYNC-MAR08-V1] Starting audio handler")
        
        has_sent_audio_since_commit = False
        bytes_sent_since_commit = 0
        
        try:
            while True:
                message = await client_ws.receive()
                msg_type = message.get("type")
                
                if msg_type == "websocket.disconnect":
                    break
                
                try:
                    if msg_type == "websocket.receive" and "bytes" in message:
                        audio_bytes = message["bytes"]
                        if not audio_bytes:
                            continue
                            
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        await openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": audio_b64
                        }))
                        has_sent_audio_since_commit = True
                        bytes_sent_since_commit += len(audio_bytes)
                        
                    elif msg_type == "websocket.receive" and "text" in message:
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "audio":
                            audio_b64 = data.get("audio")
                            if not audio_b64:
                                continue
                            
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": audio_b64
                            }))
                            has_sent_audio_since_commit = True
                            bytes_sent_since_commit += len(base64.b64decode(audio_b64))
                            
                        elif data.get("type") == "audio_commit":
                            # STRICT BLOCK: Never send commit if buffer is too small
                            if has_sent_audio_since_commit and bytes_sent_since_commit > 5000:
                                logger.info(f"📤 [VERSION-SYNC-MAR08-V1] Committing {bytes_sent_since_commit} bytes")
                                await openai_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                                await openai_ws.send(json.dumps({"type": "response.create"}))
                                has_sent_audio_since_commit = False
                                bytes_sent_since_commit = 0
                            else:
                                logger.warning(f"🛑 [VERSION-SYNC-MAR08-V1] Blocked commit for tiny buffer: {bytes_sent_since_commit} bytes")
                            
                        elif data.get("type") == "text":
                            # Text message (fallback)
                            text_event = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": data.get("text")
                                        }
                                    ]
                                }
                            }
                            await openai_ws.send(json.dumps(text_event))
                            
                            response_event = {
                                "type": "response.create"
                            }
                            await openai_ws.send(json.dumps(response_event))
                            
                except json.JSONDecodeError:
                    logger.warning("⚠️ Invalid JSON from client")
                except Exception as e:
                    logger.error(f"❌ Error processing client message: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error in client->OpenAI handler: {e}")
    
    async def handle_openai_to_client(
        self,
        client_ws: WebSocket,
        openai_ws: websockets.WebSocketClientProtocol,
        session_id: str,
        damage_info: dict,
        language: str
    ):
        """
        Forward responses from OpenAI to mobile app
        Sends session.ready and greeting after receiving session.created from OpenAI
        """
        try:
            logger.error("👂 [DEBUG] Starting OpenAI event listener...")  # Force ERROR level
            logger.info("👂 Starting OpenAI event listener...")
            event_count = 0
            async for message in openai_ws:
                try:
                    event_count += 1
                    event = json.loads(message)
                    event_type = event.get("type")
                    
                    # Log ALL events initially to debug - USE ERROR LEVEL TO FORCE VISIBILITY
                    if event_count <= 10:
                        logger.error(f"📡 [DEBUG EVENT #{event_count}] {event_type}")
                    
                    if event_type not in ["response.audio.delta", "input_audio_buffer.speech_started"]:
                        logger.info(f"📡 OpenAI event #{event_count}: {event_type}")
                    
                    # Handle different event types
                    if event_type == "session.created":
                        logger.error("🎉 [DEBUG] OpenAI session created event received!")
                        logger.info("🎉 OpenAI session created event received!")
                        
                        # Now OpenAI is ready, notify mobile client
                        await client_ws.send_json({
                            "type": "session.ready",
                            "session_id": session_id
                        })
                        logger.info("✅ Sent session.ready to mobile client")
                        
                        # Mark as ready in session info
                        if session_id in self.sessions:
                            self.sessions[session_id]["ready_sent"] = True
                        
                        # Wait a moment for mobile client to process
                        await asyncio.sleep(0.5)
                        
                        # Send greeting if not already sent
                        if session_id in self.sessions and not self.sessions[session_id].get("greeting_sent"):
                            logger.info("🎤 Now sending initial AI greeting...")
                            self.sessions[session_id]["greeting_sent"] = True
                            try:
                                # Get damage_info from session
                                damage_info = self.sessions[session_id]["damage_info"]
                                language = self.sessions[session_id]["language"]
                                await self.send_greeting(openai_ws, damage_info, language)
                            except Exception as e:
                                logger.error(f"❌ Failed to send greeting: {e}", exc_info=True)
                        
                    elif event_type == "session.updated":
                        logger.info("✅ OpenAI session updated")
                        
                    elif event_type == "response.audio.delta":
                        # Streaming audio from OpenAI
                        audio_b64 = event.get("delta")
                        if audio_b64:
                            await client_ws.send_json({
                                "type": "audio",
                                "audio": audio_b64
                            })
                            
                    elif event_type == "response.audio.done":
                        # Audio response complete
                        await client_ws.send_json({
                            "type": "audio.done"
                        })
                        
                    elif event_type == "response.audio_transcript.delta":
                        # Transcript of AI response (for debugging/display)
                        transcript = event.get("delta")
                        if transcript:
                            await client_ws.send_json({
                                "type": "transcript",
                                "text": transcript,
                                "role": "assistant"
                            })
                            
                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        # User's speech transcribed
                        transcript = event.get("transcript")
                        if transcript:
                            await client_ws.send_json({
                                "type": "transcript",
                                "text": transcript,
                                "role": "user"
                            })
                            
                    elif event_type == "conversation.item.input_audio_transcription.failed":
                        # Transcription failed
                        error_details = event.get("error", {})
                        error_msg = error_details.get("message", "Transcription failed")
                        logger.error(f"❌ Transcription failed: {error_msg}")
                        logger.debug(f"Full error: {error_details}")
                            
                    elif event_type == "response.done":
                        # Complete response finished
                        await client_ws.send_json({
                            "type": "response.done"
                        })
                        
                    elif event_type == "error":
                        # Error from OpenAI
                        error_msg = event.get("error", {}).get("message", "Unknown error")
                        logger.error(f"❌ OpenAI error: {error_msg}")
                        await client_ws.send_json({
                            "type": "error",
                            "message": error_msg
                        })
                        
                    # Forward all events to client for flexibility
                    await client_ws.send_text(message)
                    
                except json.JSONDecodeError:
                    logger.warning("⚠️ Invalid JSON from OpenAI")
                except Exception as e:
                    logger.error(f"❌ Error processing OpenAI message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 OpenAI disconnected")
        except Exception as e:
            logger.error(f"❌ Error in OpenAI->client handler: {e}")
    
    async def handle_voice_session(
        self,
        client_ws: WebSocket,
        session_id: str,
        damage_info: dict,
        language: str = "si"
    ):
        """
        Main handler for a voice chat session
        Manages bidirectional streaming between mobile app and OpenAI
        """
        openai_ws = None
        
        try:
            # Connect to OpenAI Realtime API
            print(f"🎤 [REALTIME] Starting voice session: {session_id}")  # Force print
            logger.error(f"🎤 [DEBUG] Starting voice session: {session_id}")  # Force ERROR level
            logger.info(f"🎤 Starting voice session: {session_id}")
            openai_ws = await self.connect_to_openai()
            
            if not openai_ws:
                logger.error("❌ Failed to connect to OpenAI")
                await client_ws.send_json({
                    "type": "error",
                    "message": "Failed to connect to voice service"
                })
                return
            
            logger.error(f"✅ [DEBUG] Connected to OpenAI, configuring session...")
            # Configure the session
            await self.configure_session(openai_ws, damage_info, language)
            
            # Store session info before starting handlers
            self.sessions[session_id] = {
                "client_ws": client_ws,
                "openai_ws": openai_ws,
                "damage_info": damage_info,
                "language": language,
                "started_at": datetime.now().isoformat(),
                "ready_sent": False,  # Track if we've sent session.ready
                "greeting_sent": False  # Track if we've sent greeting
            }
            
            # Run bidirectional streaming
            results = await asyncio.gather(
                self.handle_client_to_openai(client_ws, openai_ws),
                self.handle_openai_to_client(client_ws, openai_ws, session_id, damage_info, language),
                return_exceptions=True
            )
            
            # Check for exceptions in either task
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    task_name = ["client_to_openai", "openai_to_client"][idx]
                    logger.error(f"❌ Exception in {task_name}: {result}", exc_info=result)
            
        except Exception as e:
            logger.error(f"❌ Voice session error: {e}", exc_info=True)
            try:
                await client_ws.send_json({
                    "type": "error",
                    "message": f"Session error: {str(e)}"
                })
            except:
                pass
                
        finally:
            # Cleanup
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            if openai_ws:
                try:
                    await openai_ws.close()
                    logger.info("🔌 Closed OpenAI connection")
                except:
                    pass
            
            logger.info(f"✅ Voice session ended: {session_id}")


# Singleton instance
_voice_handler: Optional[RealtimeVoiceHandler] = None


def get_voice_handler() -> Optional[RealtimeVoiceHandler]:
    """
    Get the voice handler singleton
    """
    global _voice_handler
    
    if _voice_handler is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not set - voice features disabled")
            return None
        
        _voice_handler = RealtimeVoiceHandler(api_key)
        logger.info("✅ Realtime Voice Handler initialized")
    
    return _voice_handler
