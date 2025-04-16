import logging
from datetime import datetime, timedelta
from src.models import db
from src.models.social.reputation import ReputationScore, ReputationEvent
from src.models.player import Player

logger = logging.getLogger(__name__)

class ReputationController:
    """Controller for managing player reputation and credit scores"""
    
    # Define event types and their impact at the class level
    EVENT_IMPACTS = {
        # Positive Events
        "property_developed": {"score_change": 1, "cooldown": timedelta(days=1)},
        "paid_rent_on_time": {"score_change": 0.5, "cooldown": timedelta(hours=6)},
        "won_auction": {"score_change": 2, "cooldown": timedelta(days=3)},
        "completed_community_goal": {"score_change": 5, "cooldown": timedelta(days=7)},
        "donated_to_community_fund": {"score_change": 3, "cooldown": timedelta(days=2)},
        "helped_alliance_member": {"score_change": 2, "cooldown": timedelta(days=1)},
        
        # Negative Events
        "declared_bankruptcy": {"score_change": -20, "cooldown": None}, # Permanent large hit
        "failed_to_pay_rent": {"score_change": -3, "cooldown": timedelta(hours=12)},
        "property_foreclosed": {"score_change": -10, "cooldown": timedelta(days=7)},
        "committed_crime_minor": {"score_change": -2, "cooldown": timedelta(days=1)}, 
        "committed_crime_major": {"score_change": -5, "cooldown": timedelta(days=3)},
        "low_community_standing": {"score_change": -1, "cooldown": timedelta(days=1)}, # Triggered periodically if standing is low
        "betrayed_alliance_member": {"score_change": -8, "cooldown": timedelta(days=5)}
    }
    
    # Base score and scaling factors at the class level
    BASE_CREDIT_SCORE = 500
    MAX_CREDIT_SCORE = 850
    MIN_CREDIT_SCORE = 300
    REPUTATION_SCALE_FACTOR = 3.5 # How much reputation affects credit score

    def __init__(self, socketio, app_config=None):
        """Initialize ReputationController with SocketIO instance and app_config"""
        self.socketio = socketio
        self.app_config = app_config # Store app_config
        logger.info("ReputationController initialized")
        
        # Potentially get other needed controllers from app_config here if needed
        # e.g., self.social_controller = app_config.get('social_controller')
    
    def get_player_reputation(self, player_id):
        """Get a player's reputation score"""
        try:
            # Get or create reputation score
            reputation = self._get_or_create_reputation(player_id)
            
            # Return reputation data
            return {
                "success": True,
                "reputation": reputation.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting player reputation: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting player reputation: {str(e)}"
            }
    
    def record_reputation_event(self, player_id, event_type, description, impact, category=None, game_id=None):
        """Record a reputation-affecting event"""
        try:
            # Validate input
            if impact < -20 or impact > 20:
                return {
                    "success": False,
                    "error": "Impact value must be between -20 and 20"
                }
            
            # Get or create reputation score
            reputation = self._get_or_create_reputation(player_id)
            
            # Record the event
            event = reputation.record_event(
                event_type=event_type,
                description=description,
                impact=impact,
                category=category
            )
            
            # Set game ID if provided
            if game_id:
                event.game_id = game_id
            
            db.session.commit()
            
            # Notify player of reputation change
            self._notify_reputation_change(player_id, event, reputation)
            
            return {
                "success": True,
                "reputation": reputation.to_dict(),
                "event": event.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error recording reputation event: {str(e)}")
            return {
                "success": False,
                "error": f"Error recording reputation event: {str(e)}"
            }
    
    def get_player_reputation_events(self, player_id, limit=10, offset=0, category=None):
        """Get reputation events for a player"""
        try:
            # Get player's reputation
            reputation = ReputationScore.query.filter_by(player_id=player_id).first()
            if not reputation:
                return {
                    "success": True,
                    "events": [],
                    "count": 0
                }
            
            # Query events
            query = ReputationEvent.query.filter_by(player_id=player_id)
            
            # Filter by category if specified
            if category:
                query = query.filter_by(category=category)
            
            # Get count for pagination
            total_count = query.count()
            
            # Apply pagination
            events = query.order_by(ReputationEvent.timestamp.desc()) \
                          .offset(offset).limit(limit).all()
            
            return {
                "success": True,
                "events": [e.to_dict() for e in events],
                "count": total_count,
                "has_more": total_count > (offset + limit)
            }
            
        except Exception as e:
            logger.error(f"Error getting reputation events: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting reputation events: {str(e)}"
            }
    
    def get_credit_score(self, player_id):
        """Get a player's credit score (financial score) for loan considerations"""
        try:
            # Get or create reputation
            reputation = self._get_or_create_reputation(player_id)
            
            # Credit score is based primarily on financial score with some influence from overall
            credit_score = int(reputation.financial_score * 0.8 + reputation.overall_score * 0.2)
            
            return {
                "success": True,
                "credit_score": credit_score,
                "financial_score": reputation.financial_score,
                "overall_score": reputation.overall_score
            }
            
        except Exception as e:
            logger.error(f"Error getting credit score: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting credit score: {str(e)}"
            }
    
    def adjust_reputation(self, player_id, adjustment, reason=None, admin_id=None):
        """Admin function to manually adjust a player's reputation"""
        try:
            # Validate adjustment
            if not isinstance(adjustment, dict):
                return {
                    "success": False,
                    "error": "Adjustment must be a dictionary"
                }
            
            # Get reputation
            reputation = self._get_or_create_reputation(player_id)
            
            # Apply adjustments
            changed = False
            
            categories = ['overall', 'trade', 'agreement', 'community', 'financial']
            for category in categories:
                if category in adjustment:
                    value = adjustment[category]
                    
                    # Validate value
                    if not isinstance(value, int):
                        continue
                    
                    # Apply adjustment
                    if category == 'overall':
                        reputation.overall_score = max(0, min(100, reputation.overall_score + value))
                        changed = True
                    elif category == 'trade':
                        reputation.trade_score = max(0, min(100, reputation.trade_score + value))
                        changed = True
                    elif category == 'agreement':
                        reputation.agreement_score = max(0, min(100, reputation.agreement_score + value))
                        changed = True
                    elif category == 'community':
                        reputation.community_score = max(0, min(100, reputation.community_score + value))
                        changed = True
                    elif category == 'financial':
                        reputation.financial_score = max(0, min(100, reputation.financial_score + value))
                        changed = True
            
            if not changed:
                return {
                    "success": False,
                    "error": "No valid adjustments provided"
                }
            
            # Update reputation
            reputation.updated_at = datetime.utcnow()
            
            # Record admin adjustment event
            description = reason or "Administrative adjustment"
            event = ReputationEvent(
                reputation_id=reputation.id,
                player_id=player_id,
                event_type='admin_adjustment',
                description=description,
                impact=adjustment.get('overall', 0),
                category='admin'
            )
            db.session.add(event)
            
            db.session.commit()
            
            # Notify player
            self._notify_admin_adjustment(player_id, adjustment, reason, admin_id)
            
            return {
                "success": True,
                "reputation": reputation.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adjusting reputation: {str(e)}")
            return {
                "success": False,
                "error": f"Error adjusting reputation: {str(e)}"
            }
    
    def reset_reputation(self, player_id, admin_id=None, reason=None):
        """Admin function to reset a player's reputation to default values"""
        try:
            # Get reputation
            reputation = ReputationScore.query.filter_by(player_id=player_id).first()
            if not reputation:
                # No reputation to reset
                return {
                    "success": True,
                    "message": "Player had no reputation to reset"
                }
            
            # Record reset event
            description = reason or "Administrative reset"
            event = ReputationEvent(
                reputation_id=reputation.id,
                player_id=player_id,
                event_type='admin_reset',
                description=description,
                impact=0,
                category='admin'
            )
            db.session.add(event)
            
            # Reset scores
            reputation.overall_score = 50
            reputation.trade_score = 50
            reputation.agreement_score = 50
            reputation.community_score = 50
            reputation.financial_score = 50
            reputation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Notify player
            self._notify_reputation_reset(player_id, reason, admin_id)
            
            return {
                "success": True,
                "reputation": reputation.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting reputation: {str(e)}")
            return {
                "success": False,
                "error": f"Error resetting reputation: {str(e)}"
            }
    
    def _get_or_create_reputation(self, player_id):
        """Get or create a player's reputation score"""
        reputation = ReputationScore.query.filter_by(player_id=player_id).first()
        
        if not reputation:
            # Create new reputation
            reputation = ReputationScore(player_id=player_id)
            db.session.add(reputation)
            db.session.commit()
        
        return reputation
    
    def _notify_reputation_change(self, player_id, event, reputation):
        """Notify player of reputation change"""
        event_data = {
            "event": event.to_dict(),
            "new_score": {
                "overall": reputation.overall_score,
                "category_score": getattr(reputation, f"{event.category}_score", reputation.overall_score)
            }
        }
        
        self.socketio.emit('reputation_change', event_data, room=f"player_{player_id}")
    
    def _notify_admin_adjustment(self, player_id, adjustment, reason, admin_id):
        """Notify player of admin adjustment to reputation"""
        adjustment_data = {
            "adjustments": adjustment,
            "reason": reason,
            "admin_id": admin_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.socketio.emit('reputation_adjusted', adjustment_data, room=f"player_{player_id}")
    
    def _notify_reputation_reset(self, player_id, reason, admin_id):
        """Notify player of reputation reset"""
        reset_data = {
            "reason": reason,
            "admin_id": admin_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.socketio.emit('reputation_reset', reset_data, room=f"player_{player_id}") 