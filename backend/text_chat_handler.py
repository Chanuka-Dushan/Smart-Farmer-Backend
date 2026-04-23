"""
Structured Text Chat Handler for Tyre Usage Data Collection
Provides Q&A flow in Sinhala when voice chat is unavailable
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class TextChatHandler:
    """
    Manages structured text Q&A sessions for collecting tyre usage data
    """
    
    # Question states
    STATE_GREETING = "greeting"
    STATE_HOURS_PER_DAY = "hours_per_day"
    STATE_DAYS_PER_WEEK = "days_per_week"
    STATE_TERRAIN = "terrain"
    STATE_LOAD = "load"
    STATE_COMPLETE = "complete"
    
    # Questions in Sinhala
    QUESTIONS = {
        STATE_GREETING: "ආයුබෝවන්! ඔබගේ ටයර් භාවිතය ගැන ප්‍රශ්න කිහිපයක් ඇසීමට අවශ්‍යයි. මෙය ටයර් ජීවිත කාලය තක්සේරු කිරීමට උපකාරී වේ.",
        STATE_HOURS_PER_DAY: "දිනකට සාමාන්‍යයෙන් පැය කීයක් වැඩ කරනවාද? (සංඛ්‍යාවක් ඇතුළත් කරන්න: 1-24)",
        STATE_DAYS_PER_WEEK: "සතියකට දින කීයක් වැඩ කරනවාද? (සංඛ්‍යාවක් ඇතුළත් කරන්න: 1-7)",
        STATE_TERRAIN: """භූමි වර්ගය තෝරන්න:
1 - මාර්ගය (සුමට)
2 - ගොවිපල (සාමාන්‍ය)
3 - කඳුකර (රළු)
4 - අධික රළු භූමිය
(1-4 අතර සංඛ්‍යාවක් ඇතුළත් කරන්න)""",
        STATE_LOAD: """බර මට්ටම තෝරන්න:
1 - සැහැල්ලු බර
2 - සාමාන්‍ය බර
3 - අධික බර
4 - ඉතා අධික බර
(1-4 අතර සංඛ්‍යාවක් ඇතුළත් කරන්න)"""
    }
    
    # Error messages in Sinhala
    ERROR_MESSAGES = {
        "invalid_number": "කරුණාකර වලංගු සංඛ්‍යාවක් ඇතුළත් කරන්න.",
        "out_of_range": "කරුණාකර නිවැරදි පරාසයක සංඛ්‍යාවක් ඇතුළත් කරන්න.",
        "hours_range": "පැය 1-24 අතර විය යුතුය.",
        "days_range": "දින 1-7 අතර විය යුතුය.",
        "terrain_range": "1-4 අතර සංඛ්‍යාවක් ඇතුළත් කරන්න.",
        "load_range": "1-4 අතර සංඛ්‍යාවක් ඇතුළත් කරන්න."
    }
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, session_id: str, damage_info: dict) -> dict:
        """
        Create a new chat session
        """
        session = {
            "id": session_id,
            "state": self.STATE_GREETING,
            "damage_info": damage_info,
            "data": {},
            "created_at": datetime.utcnow().isoformat()
        }
        self.sessions[session_id] = session
        return session
    
    def get_current_question(self, session_id: str) -> Optional[str]:
        """
        Get the current question for the session
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        state = session["state"]
        return self.QUESTIONS.get(state)
    
    def validate_and_store_answer(
        self,
        session_id: str,
        answer: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate answer and store if valid
        Returns (is_valid, error_message)
        """
        session = self.sessions.get(session_id)
        if not session:
            return False, "Session not found"
        
        state = session["state"]
        
        # Greeting doesn't need validation
        if state == self.STATE_GREETING:
            return True, None
        
        # Try to parse as number
        try:
            value = float(answer.strip())
        except ValueError:
            return False, self.ERROR_MESSAGES["invalid_number"]
        
        # Validate based on current state
        if state == self.STATE_HOURS_PER_DAY:
            if not (1 <= value <= 24):
                return False, self.ERROR_MESSAGES["hours_range"]
            session["data"]["hours_per_day"] = value
            
        elif state == self.STATE_DAYS_PER_WEEK:
            if not (1 <= value <= 7):
                return False, self.ERROR_MESSAGES["days_range"]
            session["data"]["days_per_week"] = value
            
        elif state == self.STATE_TERRAIN:
            if value not in [1, 2, 3, 4]:
                return False, self.ERROR_MESSAGES["terrain_range"]
            # Map to terrain type
            terrain_map = {
                1: "road",
                2: "farm",
                3: "mountain",
                4: "extreme"
            }
            session["data"]["terrain"] = terrain_map[int(value)]
            
        elif state == self.STATE_LOAD:
            if value not in [1, 2, 3, 4]:
                return False, self.ERROR_MESSAGES["load_range"]
            # Map to load level
            load_map = {
                1: "light",
                2: "normal",
                3: "heavy",
                4: "extreme"
            }
            session["data"]["load"] = load_map[int(value)]
        
        return True, None
    
    def advance_to_next_state(self, session_id: str) -> bool:
        """
        Move to next question state
        Returns True if there are more questions, False if complete
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        state = session["state"]
        
        # State transitions
        transitions = {
            self.STATE_GREETING: self.STATE_HOURS_PER_DAY,
            self.STATE_HOURS_PER_DAY: self.STATE_DAYS_PER_WEEK,
            self.STATE_DAYS_PER_WEEK: self.STATE_TERRAIN,
            self.STATE_TERRAIN: self.STATE_LOAD,
            self.STATE_LOAD: self.STATE_COMPLETE
        }
        
        next_state = transitions.get(state)
        if next_state:
            session["state"] = next_state
            return next_state != self.STATE_COMPLETE
        
        return False
    
    def calculate_lifespan_estimate(self, session_id: str) -> Optional[dict]:
        """
        Calculate tyre lifespan based on collected data and damage info
        """
        session = self.sessions.get(session_id)
        if not session or session["state"] != self.STATE_COMPLETE:
            return None
        
        data = session["data"]
        damage_info = session["damage_info"]
        
        # Base lifespan (months) for a new tyre
        base_lifespan = 36
        
        # Get damage reduction factor
        damage_reduction = damage_info.get("lifespan_reduction", 0)
        severity = damage_info.get("severity", "unknown")
        
        # Calculate usage intensity factor
        hours_per_day = data.get("hours_per_day", 8)
        days_per_week = data.get("days_per_week", 5)
        hours_per_week = hours_per_day * days_per_week
        
        # Usage factor (higher usage = faster wear)
        # Normal usage: 40 hours/week → factor 1.0
        usage_factor = hours_per_week / 40.0
        
        # Terrain factor
        terrain_factors = {
            "road": 1.0,      # Best conditions
            "farm": 1.3,      # Moderate wear
            "mountain": 1.6,  # High wear
            "extreme": 2.0    # Very high wear
        }
        terrain = data.get("terrain", "farm")
        terrain_factor = terrain_factors.get(terrain, 1.3)
        
        # Load factor
        load_factors = {
            "light": 1.0,
            "normal": 1.2,
            "heavy": 1.5,
            "extreme": 1.8
        }
        load = data.get("load", "normal")
        load_factor = load_factors.get(load, 1.2)
        
        # Calculate adjusted lifespan
        # Formula: base × (1 - damage) / (usage × terrain × load)
        adjusted_lifespan = base_lifespan * (1 - damage_reduction) / (
            usage_factor * terrain_factor * load_factor
        )
        
        # Round to 1 decimal place
        adjusted_lifespan = round(adjusted_lifespan, 1)
        
        # Generate safety message in Sinhala
        if severity == "severe":
            safety_message = "⚠️ දැඩි හානිය හඳුනාගෙන ඇත. වහාම ටයර් මාරු කරන්න."
        elif severity == "moderate":
            safety_message = "⚠️ මධ්‍යම හානිය හඳුනාගෙන ඇත. නිතර පරීක්ෂා කරන්න."
        else:
            safety_message = "✅ සුළු හානිය පමණි. නමුත් නිතර පරීක්ෂා කරන්න."
        
        # Build result message in Sinhala
        result_message = f"""
📊 ටයර් ජීවිත කාල තක්සේරුව:

🔍 හඳුනාගත් හානිය: {damage_info.get('damage_type', 'unknown')}
📉 බරපතලකම: {severity}
⏱️ ඇස්තමේන්තුගත ඉතිරි ජීවිත කාලය: {adjusted_lifespan} මාස

{safety_message}

📋 ඔබගේ භාවිත රටාව:
• දිනකට පැය: {hours_per_day}
• සතියකට දින: {days_per_week}
• භූමි වර්ගය: {terrain}
• බර මට්ටම: {load}

💡 නිර්දේශය:
- නිතර පීඩනය පරීක්ෂා කරන්න
- හානිය නිරීක්ෂණය කරන්න
- අධික වේගයෙන් ධාවනය නොකරන්න
- අධික බර උචිත පීඩනය සමඟ පමණක් යොදාගන්න

ස්තූතියි! ආරක්ෂාවෙන් ධාවනය කරන්න! 🚜
"""
        
        return {
            "adjusted_lifespan_months": adjusted_lifespan,
            "message": result_message.strip(),
            "data": data,
            "damage_info": damage_info,
            "factors": {
                "usage_factor": round(usage_factor, 2),
                "terrain_factor": terrain_factor,
                "load_factor": load_factor,
                "damage_reduction": damage_reduction
            }
        }
    
    async def handle_text_chat_session(
        self,
        websocket: WebSocket,
        session_id: str,
        damage_info: dict
    ):
        """
        Handle a complete text chat session
        """
        try:
            # Create session
            session = self.create_session(session_id, damage_info)
            logger.info(f"💬 Text chat session started: {session_id}")
            
            # Send greeting
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": self.get_current_question(session_id)
            })
            
            # Advance from greeting to first question
            self.advance_to_next_state(session_id)
            
            # Send first question
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": self.get_current_question(session_id)
            })
            
            # Process messages
            while True:
                # Receive message from client
                message = await websocket.receive_json()
                
                if message.get("type") != "message":
                    continue
                
                user_answer = message.get("content", "").strip()
                if not user_answer:
                    continue
                
                # Validate and store answer
                is_valid, error_message = self.validate_and_store_answer(
                    session_id,
                    user_answer
                )
                
                if not is_valid:
                    # Send error message
                    await websocket.send_json({
                        "type": "error",
                        "content": error_message
                    })
                    # Re-send current question
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": self.get_current_question(session_id)
                    })
                    continue
                
                # Move to next state
                has_more = self.advance_to_next_state(session_id)
                
                if not has_more:
                    # Calculate and send final result
                    result = self.calculate_lifespan_estimate(session_id)
                    if result:
                        await websocket.send_json({
                            "type": "result",
                            "content": result["message"],
                            "lifespan_months": result["adjusted_lifespan_months"],
                            "data": result["data"],
                            "factors": result["factors"]
                        })
                    
                    # Clean up session
                    if session_id in self.sessions:
                        del self.sessions[session_id]
                    
                    break
                else:
                    # Send next question
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": self.get_current_question(session_id)
                    })
            
            logger.info(f"✅ Text chat session completed: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Text chat session error: {e}", exc_info=True)
            raise


# Global handler instance
_text_chat_handler: Optional[TextChatHandler] = None


def get_text_chat_handler() -> Optional[TextChatHandler]:
    """Get or create the text chat handler"""
    global _text_chat_handler
    if _text_chat_handler is None:
        _text_chat_handler = TextChatHandler()
    return _text_chat_handler
