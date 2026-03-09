"""
Tyre Remaining Life Prediction Module
Calculates remaining useful life of tyres based on damage detection and usage patterns
"""
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TyreLifePredictor:
    """Predicts remaining useful life of tyres"""
    
    # Base tyre lifespan in months (varies by type)
    BASE_LIFESPAN = {
        "car": 36,          # 3 years
        "truck": 48,        # 4 years
        "bus": 60,          # 5 years
        "motorcycle": 24,   # 2 years
        "tractor": 36,      # 3 years
        "default": 36       # Default to car tyres
    }
    
    # Usage intensity thresholds (hours per week)
    USAGE_THRESHOLDS = {
        "light": 20,      # < 20 hrs/week
        "moderate": 40,   # 20-40 hrs/week
        "heavy": 60,      # 40-60 hrs/week
        "extreme": 80     # > 60 hrs/week
    }
    
    # Damage severity multipliers
    DAMAGE_MULTIPLIERS = {
        "good": 1.0,
        "minor": 0.9,
        "moderate": 0.75,
        "severe": 0.5,
        "critical": 0.2
    }
    
    def __init__(self):
        """Initialize the predictor"""
        logger.info("✅ Tyre Life Predictor initialized")
    
    def predict_remaining_life(
        self,
        damage_type: str,
        damage_severity: str,
        lifespan_reduction: float,
        usage_hours_per_week: float,
        months_used: float,
        tyre_type: str = "default",
        confidence: float = 0.8
    ) -> Dict:
        """
        Predict remaining tyre life
        
        Args:
            damage_type: Type of damage detected
            damage_severity: Severity level (good, minor, moderate, severe, critical)
            lifespan_reduction: Reduction factor from damage detection (0.0-1.0)
            usage_hours_per_week: Average hours of use per week
            months_used: Number of months the tyre has been in use
            tyre_type: Type of vehicle/tyre (car, truck, etc.)
            confidence: Confidence level of damage detection
        
        Returns:
            Dictionary with prediction results
        """
        try:
            logger.info(
                f"🔮 Predicting tyre life - Damage: {damage_type}, "
                f"Usage: {usage_hours_per_week}h/week, Age: {months_used} months"
            )
            
            # Get base lifespan for tyre type
            base_life_months = self.BASE_LIFESPAN.get(tyre_type, self.BASE_LIFESPAN["default"])
            
            # Calculate usage intensity factor
            usage_factor = self._calculate_usage_factor(usage_hours_per_week)
            
            # Calculate damage impact
            damage_factor = self.DAMAGE_MULTIPLIERS.get(damage_severity, 0.7)
            
            # Alternative: use lifespan_reduction directly if more accurate
            if lifespan_reduction > 0:
                damage_factor = 1.0 - lifespan_reduction
            
            # Calculate effective age (accelerated by heavy usage)
            effective_age = months_used * usage_factor
            
            # Calculate adjusted lifespan considering damage
            adjusted_lifespan = base_life_months * damage_factor
            
            # Calculate remaining months
            remaining_months = max(0, adjusted_lifespan - effective_age)
            
            # Calculate percentage of life remaining
            life_remaining_percentage = (remaining_months / base_life_months) * 100 if base_life_months > 0 else 0
            
            # Determine status
            status, color_code = self._determine_status(
                remaining_months, 
                life_remaining_percentage,
                damage_severity,
                confidence
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                status,
                remaining_months,
                damage_type,
                damage_severity,
                usage_hours_per_week
            )
            
            # Calculate replacement urgency score (0-100)
            urgency_score = self._calculate_urgency_score(
                remaining_months,
                damage_severity,
                usage_hours_per_week,
                confidence
            )
            
            # Prepare detailed result
            result = {
                "success": True,
                "tyre_info": {
                    "type": tyre_type,
                    "base_lifespan_months": base_life_months,
                    "months_used": months_used,
                    "usage_hours_per_week": usage_hours_per_week
                },
                "damage_analysis": {
                    "damage_type": damage_type,
                    "severity": damage_severity,
                    "confidence": round(confidence, 3),
                    "lifespan_reduction_factor": round(lifespan_reduction, 3)
                },
                "prediction": {
                    "remaining_life_months": round(remaining_months, 1),
                    "remaining_life_percentage": round(life_remaining_percentage, 1),
                    "effective_age_months": round(effective_age, 1),
                    "adjusted_lifespan_months": round(adjusted_lifespan, 1),
                    "status": status,
                    "color_code": color_code,
                    "urgency_score": urgency_score
                },
                "recommendation": recommendation,
                "factors": {
                    "usage_intensity": self._get_usage_category(usage_hours_per_week),
                    "usage_factor": round(usage_factor, 2),
                    "damage_factor": round(damage_factor, 2)
                },
                "metadata": {
                    "prediction_time": datetime.utcnow().isoformat(),
                    "model_version": "v1.0"
                }
            }
            
            logger.info(
                f"✅ Prediction complete: {remaining_months:.1f} months remaining "
                f"({status}) - Urgency: {urgency_score}/100"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_usage_factor(self, hours_per_week: float) -> float:
        """
        Calculate usage intensity factor
        Higher usage = faster aging
        
        Args:
            hours_per_week: Weekly usage hours
        
        Returns:
            Usage factor (1.0 = normal, >1.0 = accelerated aging)
        """
        # Base factor at moderate usage (40 hrs/week)
        base_hours = 40
        
        if hours_per_week <= 20:
            # Light usage - slower aging
            return 0.7 + (hours_per_week / 20) * 0.3  # 0.7 to 1.0
        elif hours_per_week <= 40:
            # Moderate usage - normal aging
            return 1.0
        elif hours_per_week <= 60:
            # Heavy usage - accelerated aging
            return 1.0 + (hours_per_week - 40) / 40 * 0.5  # 1.0 to 1.5
        else:
            # Extreme usage - rapid aging
            return 1.5 + (hours_per_week - 60) / 60 * 0.5  # 1.5 to 2.0 (capped)
    
    def _get_usage_category(self, hours_per_week: float) -> str:
        """Get usage intensity category"""
        if hours_per_week < 20:
            return "light"
        elif hours_per_week < 40:
            return "moderate"
        elif hours_per_week < 60:
            return "heavy"
        else:
            return "extreme"
    
    def _determine_status(
        self,
        remaining_months: float,
        life_percentage: float,
        damage_severity: str,
        confidence: float
    ) -> tuple:
        """
        Determine tyre status and color code
        
        Returns:
            Tuple of (status_string, color_code)
        """
        # Critical conditions
        if remaining_months < 2 or life_percentage < 5 or damage_severity == "critical":
            return ("CRITICAL - REPLACE IMMEDIATELY", "#FF0000")
        
        # Severe warning
        if remaining_months < 3 or life_percentage < 10 or damage_severity == "severe":
            return ("URGENT - REPLACE SOON", "#FF4500")
        
        # Warning
        if remaining_months < 6 or life_percentage < 20 or damage_severity == "moderate":
            return ("WARNING - MONITOR CLOSELY", "#FFA500")
        
        # Caution
        if remaining_months < 12 or life_percentage < 40 or damage_severity == "minor":
            return ("CAUTION - CHECK REGULARLY", "#FFD700")
        
        # Good condition
        return ("GOOD CONDITION", "#00AA00")
    
    def _calculate_urgency_score(
        self,
        remaining_months: float,
        damage_severity: str,
        usage_hours: float,
        confidence: float
    ) -> int:
        """
        Calculate replacement urgency score (0-100)
        Higher score = more urgent
        """
        score = 0
        
        # Time-based urgency (0-40 points)
        if remaining_months < 2:
            score += 40
        elif remaining_months < 6:
            score += 30
        elif remaining_months < 12:
            score += 20
        else:
            score += max(0, 40 - remaining_months)
        
        # Damage-based urgency (0-40 points)
        severity_scores = {
            "critical": 40,
            "severe": 30,
            "moderate": 20,
            "minor": 10,
            "good": 0
        }
        score += severity_scores.get(damage_severity, 20)
        
        # Usage-based urgency (0-10 points)
        if usage_hours > 60:
            score += 10
        elif usage_hours > 40:
            score += 5
        
        # Confidence adjustment (0-10 points)
        score += int(confidence * 10)
        
        return min(100, score)
    
    def _generate_recommendation(
        self,
        status: str,
        remaining_months: float,
        damage_type: str,
        damage_severity: str,
        usage_hours: float
    ) -> Dict:
        """Generate detailed recommendations"""
        recommendations = []
        action_required = "none"
        replacement_timeline = "normal_schedule"
        
        # Critical status
        if "CRITICAL" in status:
            action_required = "immediate"
            replacement_timeline = "immediately"
            recommendations.append("🚨 Replace tyre IMMEDIATELY - safety risk")
            recommendations.append("Do not drive on this tyre")
            recommendations.append("Visit nearest tyre service center")
        
        # Urgent status
        elif "URGENT" in status:
            action_required = "urgent"
            replacement_timeline = "within_1_week"
            recommendations.append("⚠️ Schedule tyre replacement within 1 week")
            recommendations.append("Avoid long trips or high-speed driving")
            recommendations.append("Check tyre pressure daily")
        
        # Warning status
        elif "WARNING" in status:
            action_required = "soon"
            replacement_timeline = f"within_{int(remaining_months)}_months"
            recommendations.append(f"⚠️ Plan to replace within {int(remaining_months)} months")
            recommendations.append("Increase inspection frequency to weekly")
            recommendations.append("Monitor for further deterioration")
        
        # Caution status
        elif "CAUTION" in status:
            action_required = "monitor"
            replacement_timeline = "routine_replacement"
            recommendations.append("💡 Continue normal use with regular monitoring")
            recommendations.append("Inspect tyre monthly for changes")
            recommendations.append("Maintain proper inflation pressure")
        
        # Good status
        else:
            action_required = "none"
            replacement_timeline = "normal_schedule"
            recommendations.append("✅ Tyre is in good condition")
            recommendations.append("Continue routine maintenance")
            recommendations.append("Regular pressure checks recommended")
        
        # Add specific recommendations based on damage type
        if "treadwear" in damage_type:
            recommendations.append("🔧 Check wheel alignment and balancing")
            if damage_severity in ["moderate", "severe", "critical"]:
                recommendations.append("Rotate tyres if possible to extend life")
        
        if "crack" in damage_type:
            recommendations.append("Avoid high-speed driving and sharp turns")
            recommendations.append("Reduce load if carrying heavy items")
            if damage_type == "crack_2":
                recommendations.append("⚠️ High-level cracks are serious - replacement highly recommended")
        
        # Usage-based recommendations
        if usage_hours > 50:
            recommendations.append("Consider reducing usage hours if possible")
            recommendations.append("High usage accelerates tyre wear")
        
        return {
            "action_required": action_required,
            "replacement_timeline": replacement_timeline,
            "recommendations": recommendations,
            "estimated_replacement_date": self._calculate_replacement_date(
                remaining_months,
                action_required
            )
        }
    
    def _calculate_replacement_date(self, remaining_months: float, action: str) -> str:
        """Calculate estimated replacement date"""
        from datetime import timedelta
        
        now = datetime.utcnow()
        
        if action == "immediate":
            target_date = now
        elif action == "urgent":
            target_date = now + timedelta(days=7)
        elif action == "soon":
            target_date = now + timedelta(days=int(remaining_months * 30 * 0.8))
        else:
            target_date = now + timedelta(days=int(remaining_months * 30))
        
        return target_date.strftime("%Y-%m-%d")


# Initialize global predictor instance
_predictor_instance = None

def get_predictor() -> TyreLifePredictor:
    """Get or create predictor singleton"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = TyreLifePredictor()
    return _predictor_instance
