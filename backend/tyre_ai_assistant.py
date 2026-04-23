"""
Tyre Health Conversational AI Assistant
Sinhala-speaking AI assistant for collecting tyre usage information
and providing recommendations
"""
import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    logger.info("✓ OpenAI library available (v1.0+)")
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None
    logger.warning("⚠ OpenAI library not available")


class ConversationState(Enum):
    """States in the conversation flow"""
    INITIAL = "initial"
    COLLECTING_USAGE = "collecting_usage"
    COLLECTING_MONTHS = "collecting_months"
    EXPLAINING_DAMAGE = "explaining_damage"
    PROVIDING_RECOMMENDATION = "providing_recommendation"
    COMPLETE = "complete"


class TyreHealthAssistant:
    """Conversational AI assistant for tyre health assessment"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the assistant
        
        Args:
            openai_api_key: OpenAI API key
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠ OpenAI API key not found - using simulation mode")
            self.enabled = False
        else:
            self.enabled = OPENAI_AVAILABLE
            if OPENAI_AVAILABLE:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI client configured (v1.0+)")
        
        # Conversation context storage (in production, use database)
        self.conversations = {}
    
    def start_conversation(
        self, 
        session_id: str,
        damage_info: Dict,
        language: str = "si"  # si for Sinhala, en for English
    ) -> Dict:
        """
        Start a new conversation about tyre health
        
        Args:
            session_id: Unique session identifier
            damage_info: Damage detection results
            language: Language code
        
        Returns:
            Initial AI response
        """
        # Initialize conversation context
        self.conversations[session_id] = {
            "state": ConversationState.INITIAL.value,
            "damage_info": damage_info,
            "language": language,
            "usage_hours_per_week": None,
            "months_used": None,
            "messages": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Generate initial greeting based on damage
        damage_type = damage_info.get("damage_type", "unknown")
        confidence = damage_info.get("confidence", 0.0)
        
        if language == "si":
            initial_message = self._get_sinhala_greeting(damage_type, confidence)
        else:
            initial_message = self._get_english_greeting(damage_type, confidence)
        
        # Update state
        self.conversations[session_id]["state"] = ConversationState.COLLECTING_USAGE.value
        self.conversations[session_id]["messages"].append({
            "role": "assistant",
            "content": initial_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "message": initial_message,
            "state": ConversationState.COLLECTING_USAGE.value
        }
    
    def continue_conversation(
        self, 
        session_id: str,
        user_message: str
    ) -> Dict:
        """
        Continue an existing conversation
        
        Args:
            session_id: Session identifier
            user_message: User's message (from speech-to-text)
        
        Returns:
            AI response
        """
        if session_id not in self.conversations:
            return {
                "error": "Session not found",
                "message": "කරුණාකර නැවත පටන් ගන්න / Please start again"
            }
        
        context = self.conversations[session_id]
        
        # Add user message to history
        context["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Process based on current state
        if context["state"] == ConversationState.COLLECTING_USAGE.value:
            return self._handle_usage_collection(session_id, user_message, context)
        
        elif context["state"] == ConversationState.COLLECTING_MONTHS.value:
            return self._handle_months_collection(session_id, user_message, context)
        
        elif context["state"] == ConversationState.EXPLAINING_DAMAGE.value:
            return self._handle_damage_explanation(session_id, user_message, context)
        
        else:
            # Use OpenAI for general conversation
            return self._handle_general_conversation(session_id, user_message, context)
    
    def _handle_usage_collection(self, session_id: str, user_message: str, context: Dict) -> Dict:
        """Handle collection of weekly usage hours"""
        # Extract number from user message
        usage_hours = self._extract_number(user_message)
        
        if usage_hours is not None:
            context["usage_hours_per_week"] = usage_hours
            context["state"] = ConversationState.COLLECTING_MONTHS.value
            
            # Ask about months used
            if context["language"] == "si":
                response = f"හොඳයි! සතියකට පැය {usage_hours}. දැන් කියන්න, ඔබ මේ ටයර් එක මාස කීයක් භාවිතා කරනවාද?"
            else:
                response = f"Good! {usage_hours} hours per week. Now tell me, how many months have you been using this tyre?"
        else:
            # Ask again
            if context["language"] == "si":
                response = "සමාවන්න, මට තේරුණේ නැහැ. කරුණාකර සංඛ්‍යාවක් කියන්න. උදාහරණයක් ලෙස: 'පැය 40' හෝ 'හතළිස්'"
            else:
                response = "Sorry, I didn't understand. Please provide a number. For example: '40 hours' or 'forty'"
        
        context["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "message": response,
            "state": context["state"]
        }
    
    def _handle_months_collection(self, session_id: str, user_message: str, context: Dict) -> Dict:
        """Handle collection of months used"""
        # Extract number from user message
        months_used = self._extract_number(user_message)
        
        if months_used is not None:
            context["months_used"] = months_used
            context["state"] = ConversationState.PROVIDING_RECOMMENDATION.value
            
            # Calculate remaining life
            prediction = self._calculate_remaining_life(context)
            
            # Generate recommendation
            if context["language"] == "si":
                response = self._generate_sinhala_recommendation(prediction, context)
            else:
                response = self._generate_english_recommendation(prediction, context)
            
            # Store prediction in context
            context["prediction"] = prediction
        else:
            # Ask again
            if context["language"] == "si":
                response = "කරුණාකර මාස සංඛ්‍යාව කියන්න. උදාහරණයක් ලෙස: 'මාස 6' හෝ 'හයක්'"
            else:
                response = "Please provide the number of months. For example: '6 months' or 'six'"
        
        context["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "message": response,
            "state": context["state"],
            "prediction": context.get("prediction")
        }
    
    def _handle_damage_explanation(self, session_id: str, user_message: str, context: Dict) -> Dict:
        """Handle questions about damage"""
        # Use OpenAI to explain damage in context
        if self.enabled:
            response = self._get_ai_explanation(user_message, context)
        else:
            response = self._get_simulated_explanation(context)
        
        context["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "message": response,
            "state": context["state"]
        }
    
    def _handle_general_conversation(self, session_id: str, user_message: str, context: Dict) -> Dict:
        """Handle general follow-up questions using OpenAI"""
        if self.enabled:
            try:
                # Prepare context for OpenAI
                messages = [
                    {
                        "role": "system",
                        "content": self._get_system_prompt(context)
                    }
                ]
                
                # Add conversation history (last 5 messages)
                for msg in context["messages"][-5:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                # Get AI response
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=300
                )
                
                ai_message = response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"❌ OpenAI API error: {e}")
                if context["language"] == "si":
                    ai_message = "සමාවන්න, දැන් මට උත්තර දෙන්න බැහැ. පසුව නැවත උත්සහ කරන්න."
                else:
                    ai_message = "Sorry, I can't respond right now. Please try again later."
        else:
            ai_message = self._get_simulated_response(context)
        
        context["messages"].append({
            "role": "assistant",
            "content": ai_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "message": ai_message,
            "state": context["state"]
        }
    
    def _calculate_remaining_life(self, context: Dict) -> Dict:
        """Calculate remaining tyre life based on collected information"""
        damage_info = context["damage_info"]
        usage_hours = context["usage_hours_per_week"] or 40
        months_used = context["months_used"] or 0
        
        # Normal tyre life: 3-5 years (36-60 months)
        base_life_months = 36
        
        # Get damage severity
        lifespan_reduction = damage_info.get("lifespan_reduction", 0.3)
        
        # Calculate usage intensity factor
        # High usage (>40 hrs/week) reduces life faster
        usage_factor = 1.0
        if usage_hours > 40:
            usage_factor = 1.0 + (usage_hours - 40) / 80  # Max 1.5x for 120 hrs/week
        
        # Calculate effective age
        effective_age = months_used * usage_factor
        
        # Calculate remaining life
        reduced_life = base_life_months * (1 - lifespan_reduction)
        remaining_months = max(0, reduced_life - effective_age)
        
        # Determine status
        if remaining_months < 3 or lifespan_reduction > 0.6:
            status = "critical"
            recommendation = "immediate_replacement"
        elif remaining_months < 6 or lifespan_reduction > 0.4:
            status = "warning"
            recommendation = "replace_soon"
        else:
            status = "good"
            recommendation = "continue_monitoring"
        
        return {
            "damage_type": damage_info.get("damage_type", "unknown"),
            "confidence": damage_info.get("confidence", 0.0),
            "severity": damage_info.get("severity", "unknown"),
            "usage_hours_per_week": usage_hours,
            "months_used": months_used,
            "remaining_life_months": round(remaining_months, 1),
            "status": status,
            "recommendation": recommendation,
            "lifespan_reduction_factor": lifespan_reduction
        }
    
    def _get_sinhala_greeting(self, damage_type: str, confidence: float) -> str:
        """Get Sinhala greeting based on damage type"""
        greetings = {
            "crack_1": f"ආයුබෝවන්! මම ඔබේ ටයර් එක පරීක්ෂා කළා. සුළු ඉරිතැලීම් ({int(confidence*100)}% විශ්වාසනීයත්වය) හමු වී ඇත. ඔබ මේ ටයර් එක සතියකට පැය කීයක් භාවිතා කරනවාද?",
            "crack_2": f"ආයුබෝවන්! අවවාදයයි - ඔබේ ටයර් එකේ මධ්‍යස්ථ හා ඉහළ මට්ටමේ ඉරිතැලීම් ({int(confidence*100)}% විශ්වාසනීයත්වය) හමු වී ඇත. වැඩි විස්තර සඳහා, ඔබ මේ ටයර් එක සතියකට පැය කීයක් භාවිතා කරනවාද?",
            "treadwear_1": f"ආයුබෝවන්! මම ඔබේ ටයර් එක පරීක්ෂා කළා. සුළු ක්ෂයවීමක් ({int(confidence*100)}% විශ්වාසනීයත්වය) හමු වී ඇත. ඔබ මේ ටයර් එක සතියකට පැය කීයක් භාවිතා කරනවාද?",
            "treadwear_2": f"ආයුබෝවන්! ඔබේ ටයර් එකේ මධ්‍යස්ථ ක්ෂයවීමක් ({int(confidence*100)}% විශ්වාසනීයත්වය) හමු වී ඇත. ටිකක් විස්තර අවශ්‍යයි. ඔබ මේ ටයර් එක සතියකට පැය කීයක් භාවිතා කරනවාද?",
        }
        
        return greetings.get(
            damage_type,
            f"ආයුබෝවන්! මම ඔබේ ටයර් එක පරීක්ෂා කළා. ටිකක් තොරතුරු අවශ්‍යයි. ඔබ මේ ටයර් එක සතියකට පැය කීයක් භාවිතා කරනවාද?"
        )
    
    def _get_english_greeting(self, damage_type: str, confidence: float) -> str:
        """Get English greeting based on damage type"""
        greetings = {
            "crack_1": f"Hello! I've analyzed your tyre. Small cracks detected ({int(confidence*100)}% confidence). How many hours per week do you use this tyre?",
            "crack_2": f"Hello! Warning - medium to high level cracks detected ({int(confidence*100)}% confidence). For more details, how many hours per week do you use this tyre?",
            "treadwear_1": f"Hello! I've analyzed your tyre. Minor wear detected ({int(confidence*100)}% confidence). How many hours per week do you use this tyre?",
            "treadwear_2": f"Hello! Moderate wear detected on your tyre ({int(confidence*100)}% confidence). I need some details. How many hours per week do you use this tyre?",
        }
        
        return greetings.get(
            damage_type,
            f"Hello! I've analyzed your tyre. I need some information. How many hours per week do you use this tyre?"
        )
    
    def _generate_sinhala_recommendation(self, prediction: Dict, context: Dict) -> str:
        """Generate Sinhala recommendation"""
        remaining = prediction["remaining_life_months"]
        damage = prediction["damage_type"]
        status = prediction["status"]
        
        if status == "critical":
            return (
                f"විශ්ලේෂණය සම්පූර්ණයි! ඔබේ ටයර් එකේ {damage} හමු වී ඇත. "
                f"භාවිතය සහ හානිය මත පදනම්ව, ඔබට තව මාස {remaining} පමණ පමණක් ඉතිරිව ඇත. "
                f"🚨 නිර්දේශය: වහාම ටයර් එක ප්‍රතිස්ථාපනය කරන්න. මෙය ආරක්ෂිත අවදානමක්!"
            )
        elif status == "warning":
            return (
                f"විශ්ලේෂණය සම්පූර්ණයි! ඔබේ ටයර් එකේ {damage} හමු වී ඇත. "
                f"භාවිතය සහ හානිය මත පදනම්ව, ඔබට තව මාස {remaining} පමණ ඉතිරිව ඇත. "
                f"⚠️ නිර්දේශය: ඉදිරි මාස 2-3 තුළ ටයර් එක ප්‍රතිස්ථාපනය කිරීම සලකා බලන්න."
            )
        else:
            return (
                f"සුභ පුවතක්! ඔබේ ටයර් එක තවමත් හොඳ තත්ත්වයේ. "
                f"භාවිතය මත පදනම්ව, ඔබට තව මාස {remaining} පමණ ඉතිරිව ඇත. "
                f"✅ නිර්දේශය: නිතිපතා පරීක්ෂා කරන්න සහ සාමාන්‍ය භාවිතය දිගටම කරගෙන යන්න."
            )
    
    def _generate_english_recommendation(self, prediction: Dict, context: Dict) -> str:
        """Generate English recommendation"""
        remaining = prediction["remaining_life_months"]
        damage = prediction["damage_type"]
        status = prediction["status"]
        
        if status == "critical":
            return (
                f"Analysis complete! {damage} detected on your tyre. "
                f"Based on usage and damage, you have approximately {remaining} months remaining. "
                f"🚨 Recommendation: Replace the tyre immediately. This is a safety risk!"
            )
        elif status == "warning":
            return (
                f"Analysis complete! {damage} detected on your tyre. "
                f"Based on usage and damage, you have approximately {remaining} months remaining. "
                f"⚠️ Recommendation: Consider replacing the tyre within the next 2-3 months."
            )
        else:
            return (
                f"Good news! Your tyre is still in good condition. "
                f"Based on usage, you have approximately {remaining} months remaining. "
                f"✅ Recommendation: Continue regular monitoring and normal use."
            )
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text (supports English and Sinhala number words)"""
        import re
        
        # Try to find digits
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])
        
        # Try Sinhala/English number words
        number_words = {
            "එක": 1, "දෙක": 2, "තුන": 3, "හතර": 4, "පහ": 5,
            "හය": 6, "හත": 7, "අට": 8, "නවය": 9, "දහය": 10,
            "විස්ස": 20, "තිහ": 30, "හතළිස්": 40, "පනස්": 50, "හැට": 60,
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60
        }
        
        text_lower = text.lower()
        for word, num in number_words.items():
            if word in text_lower:
                return float(num)
        
        return None
    
    def _get_system_prompt(self, context: Dict) -> str:
        """Get system prompt for OpenAI"""
        language = context["language"]
        
        if language == "si":
            return (
                "ඔබ ටයර් සෞඛ්‍ය සහායකයෙකි. ඔබගේ කාර්යය වන්නේ සිංහලෙන් පරිශීලකයාට "
                "ටයර් හානිය සහ නඩත්තුව පිළිබඳව උදව් කිරීමයි. "
                "සරල, මිත්‍රශීලී සහ ප්‍රයෝජනවත් විය යුතුය."
            )
        else:
            return (
                "You are a tyre health assistant. Your job is to help users understand "
                "tyre damage and maintenance. Be simple, friendly, and helpful."
            )
    
    def _get_simulated_response(self, context: Dict) -> str:
        """Get simulated response when OpenAI is not available"""
        if context["language"] == "si":
            return "ස්තූතියි! තව ප්‍රශ්න තිබේද?"
        else:
            return "Thank you! Do you have any other questions?"
    
    def _get_simulated_explanation(self, context: Dict) -> str:
        """Get simulated damage explanation"""
        damage_type = context["damage_info"].get("damage_type", "unknown")
        
        if context["language"] == "si":
            return f"{damage_type} යනු ටයර් එකේ ක්ෂයවීමේ වර්ගයකි. මෙය ආරක්ෂිතතාවට බලපෑ හැකිය."
        else:
            return f"{damage_type} is a type of tyre wear. This can affect safety."
    
    def get_conversation_summary(self, session_id: str) -> Optional[Dict]:
        """Get summary of a conversation"""
        if session_id not in self.conversations:
            return None
        
        return self.conversations[session_id]
    
    def text_to_speech(self, text: str, language: str = "si") -> bytes:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text: Text to convert
            language: Language code (si for Sinhala, en for English)
        
        Returns:
            Audio bytes (MP3 format)
        """
        if not self.enabled:
            logger.warning("⚠ OpenAI TTS not available - returning empty audio")
            return b""
        
        try:
            # OpenAI TTS supports multiple voices
            # Use 'nova' for female voice, 'onyx' for male voice
            voice = "nova"  # Good for both English and other languages
            
            response = self.client.audio.speech.create(
                model="tts-1",  # Use tts-1-hd for higher quality
                voice=voice,
                input=text,
                speed=0.9  # Slightly slower for clarity
            )
            
            audio_bytes = response.content
            logger.info(f"✅ Generated speech audio: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return b""
    
    def speech_to_text(self, audio_file) -> str:
        """
        Convert speech to text using OpenAI Whisper
        
        Args:
            audio_file: Audio file object (bytes or file-like)
        
        Returns:
            Transcribed text
        """
        if not self.enabled:
            logger.warning("⚠ OpenAI Whisper not available")
            return ""
        
        try:
            # OpenAI Whisper API automatically detects language
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="si"  # Hint: Sinhala (also supports auto-detection)
            )
            
            text = transcription.text
            logger.info(f"✅ Transcribed audio: {text[:50]}...")
            return text
            
        except Exception as e:
            logger.error(f"❌ Speech-to-text error: {e}")
            return ""


# Initialize global assistant instance
_assistant_instance = None

def get_assistant() -> TyreHealthAssistant:
    """Get or create assistant singleton"""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = TyreHealthAssistant()
    return _assistant_instance
