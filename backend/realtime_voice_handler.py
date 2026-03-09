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

logger = logging.getLogger(__name__)


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
                "voice": "alloy",  # Options: alloy, echo, shimmer
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": None, # Disable VAD to prevent auto-commit errors
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
        
        await openai_ws.send(json.dumps(session_config))
        logger.info("✅ Sent OpenAI session config (VAD disabled)")
        
        # Small delay to ensure session is ready
        await asyncio.sleep(0.1)
    
    async def send_greeting(
        self,
        openai_ws: websockets.WebSocketClientProtocol,
        damage_info: dict,
        language: str = "si"
    ):
        """
        Send initial AI greeting to start the conversation
        """
        try:
            language_name = "Sinhala" if language == "si" else "English"
            damage_type_clean = damage_info['damage_type'].replace('_', ' ').replace('1', '').replace('2', '').strip()
            damage_details = f"{damage_type_clean} with {damage_info['severity']} severity"
            
            greeting_text = (
                f"Greet the user warmly in {language_name}. "
                f"Tell them you have analyzed the tyre and detected {damage_details}. "
                f"Ask them how many hours per week they typically use the tractor so you can estimate the remaining life. "
                f"Keep it very brief and conversational (max 2 sentences). Respond ONLY in {language_name}."
            )
            
            # Add greeting message to conversation
            greeting_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": greeting_text
                        }
                    ]
                }
            }
            
            logger.info("📤 Sending greeting conversation item...")
            await openai_ws.send(json.dumps(greeting_item))
            
            # Trigger AI response with audio
            response_event = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"]
                }
            }
            
            logger.info("📤 Triggering AI response with audio...")
            await openai_ws.send(json.dumps(response_event))
            logger.info("✅ Greeting successfully sent to OpenAI")
            
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
        Note: Greeting is sent proactively in handle_voice_session, not here
        """
        try:
            async for message in openai_ws:
                try:
                    event = json.loads(message)
                    event_type = event.get("type")
                    
                    # Log interesting events
                    if event_type not in ["response.audio.delta", "input_audio_buffer.speech_started"]:
                        logger.debug(f"📡 OpenAI event: {event_type}")
                    
                    # Handle different event types
                    if event_type == "session.created":
                        logger.info("✅ OpenAI session created")
                        await client_ws.send_json({
                            "type": "session.ready",
                            "session_id": session_id
                        })
                        # Greeting is sent proactively - no need to trigger here
                        
                    elif event_type == "session.updated":
                        logger.info("✅ OpenAI session updated")
                        # Greeting already sent proactively
                        
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
            logger.info(f"🎤 Starting voice session: {session_id}")
            openai_ws = await self.connect_to_openai()
            
            if not openai_ws:
                await client_ws.send_json({
                    "type": "error",
                    "message": "Failed to connect to voice service"
                })
                return
            
            # Configure the session
            await self.configure_session(openai_ws, damage_info, language)
            
            # Notify client that session is ready FIRST
            await client_ws.send_json({
                "type": "session.ready",
                "session_id": session_id
            })
            logger.info(f"✅ Sent session.ready to client: {session_id}")
            
            # Wait a moment for mobile client to fully process and set up listeners
            logger.info("⏳ Waiting for client to be ready...")
            await asyncio.sleep(0.5)
            
            # Send initial greeting
            logger.info("🎤 Sending initial AI greeting...")
            await self.send_greeting(openai_ws, damage_info, language)
            
            # Store session info
            self.sessions[session_id] = {
                "client_ws": client_ws,
                "openai_ws": openai_ws,
                "damage_info": damage_info,
                "language": language,
                "started_at": datetime.now().isoformat()
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
