import logging
from datetime import datetime
from src.models import db
from src.models.social.alliance import Alliance, AllianceMember, AllianceInvite
from src.models.social.chat import Channel, ChannelMember
from src.controllers.social.chat_controller import ChatController
from src.models.player import Player
from flask_socketio import emit

logger = logging.getLogger(__name__)

class AllianceController:
    """Controller for player alliances"""
    
    def __init__(self, socketio, app_config=None):
        """Initialize AllianceController with SocketIO instance and app_config"""
        self.socketio = socketio
        self.app_config = app_config
        logger.info("AllianceController initialized")
    
    def create_alliance(self, creator_id, name, description=None, is_public=True):
        """Create a new player alliance"""
        try:
            # Input validation
            if not name or len(name) < 3 or len(name) > 100:
                return {
                    "success": False,
                    "error": "Invalid alliance name (must be 3-100 characters)"
                }
                
            if description and len(description) > 255:
                return {
                    "success": False,
                    "error": "Description too long (max 255 characters)"
                }
            
            # Create alliance
            alliance = Alliance(
                name=name,
                description=description or f"Alliance created by player {creator_id}",
                is_public=is_public,
                created_by=creator_id
            )
            
            db.session.add(alliance)
            db.session.flush()  # Flush to get alliance ID
            
            # Create a corresponding chat channel
            chat_controller = self.app_config.get('social_controller')
            if not chat_controller:
                logger.error("ChatController not found in app_config during alliance creation.")
                alliance.chat_channel_id = None
            else:
                chat_result = chat_controller.create_channel(
                    creator_id=creator_id,
                    name=f"Alliance: {name}",
                    description=f"Chat for alliance: {name}",
                    members=[creator_id],
                    channel_type='group'
                )
                if chat_result["success"]:
                    alliance.chat_channel_id = chat_result["channel_id"]
                else:
                    logger.warning(f"Failed to create chat channel for alliance {alliance.id}: {chat_result.get('error')}")
                    alliance.chat_channel_id = None
            
            # Add creator as a member with leader role
            member = AllianceMember(
                alliance_id=alliance.id,
                player_id=creator_id,
                role='leader'
            )
            db.session.add(member)
            
            db.session.commit()
            
            # Notify alliance creation via WebSocket
            self._notify_alliance_creation(alliance)
            
            return {
                "success": True,
                "alliance_id": alliance.id,
                "alliance": alliance.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating alliance: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating alliance: {str(e)}"
            }
    
    def invite_player(self, alliance_id, inviter_id, invitee_id):
        """Invite a player to join an alliance"""
        try:
            # Check if alliance exists
            alliance = Alliance.query.get(alliance_id)
            if not alliance:
                return {
                    "success": False,
                    "error": "Alliance not found"
                }
            
            # Check if inviter is a member with invite permissions
            inviter_membership = AllianceMember.query.filter_by(
                alliance_id=alliance_id, player_id=inviter_id, status='active'
            ).first()
            
            if not inviter_membership or inviter_membership.role not in ['leader', 'officer']:
                return {
                    "success": False,
                    "error": "You don't have permission to invite players"
                }
            
            # Check if invitee is already a member
            if alliance.is_member(invitee_id):
                return {
                    "success": False,
                    "error": "Player is already a member of this alliance"
                }
            
            # Check for existing pending invite
            existing_invite = AllianceInvite.query.filter_by(
                alliance_id=alliance_id, player_id=invitee_id, status='pending'
            ).first()
            
            if existing_invite:
                return {
                    "success": False,
                    "error": "Player already has a pending invitation"
                }
            
            # Create invitation
            invite = AllianceInvite(
                alliance_id=alliance_id,
                player_id=invitee_id,
                inviter_id=inviter_id
            )
            
            db.session.add(invite)
            db.session.commit()
            
            # Notify invitee via WebSocket
            self._notify_alliance_invitation(invite)
            
            return {
                "success": True,
                "invite_id": invite.id,
                "invite": invite.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error inviting player to alliance: {str(e)}")
            return {
                "success": False,
                "error": f"Error inviting player to alliance: {str(e)}"
            }
    
    def respond_to_invite(self, invite_id, player_id, accept):
        """Accept or decline an alliance invitation"""
        try:
            # Check if invitation exists
            invite = AllianceInvite.query.get(invite_id)
            if not invite:
                return {
                    "success": False,
                    "error": "Invitation not found"
                }
            
            # Check if the invitation is for this player
            if invite.player_id != player_id:
                return {
                    "success": False,
                    "error": "This invitation is not for you"
                }
            
            # Check if invitation is still pending
            if invite.status != 'pending':
                return {
                    "success": False,
                    "error": f"Invitation has already been {invite.status}"
                }
            
            # Process response
            if accept:
                # Accept invitation
                result = invite.accept()
                if result:
                    # Add player to alliance chat channel
                    alliance = Alliance.query.get(invite.alliance_id)
                    if alliance and alliance.chat_channel_id:
                        channel = Channel.query.get(alliance.chat_channel_id)
                        if channel:
                            channel.add_member(player_id)
                    
                    # Notify alliance members
                    self._notify_player_joined(invite.alliance_id, player_id)
                    
                    return {
                        "success": True,
                        "message": "Invitation accepted successfully",
                        "alliance_id": invite.alliance_id
                    }
                else:
                    return {
                        "success": False,
                        "error": "Error accepting invitation"
                    }
            else:
                # Decline invitation
                result = invite.decline()
                if result:
                    # Notify inviter
                    self._notify_invite_declined(invite)
                    
                    return {
                        "success": True,
                        "message": "Invitation declined"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Error declining invitation"
                    }
                
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error responding to alliance invitation: {str(e)}")
            return {
                "success": False,
                "error": f"Error responding to alliance invitation: {str(e)}"
            }
    
    def leave_alliance(self, alliance_id, player_id):
        """Leave an alliance"""
        try:
            # Check if alliance exists
            alliance = Alliance.query.get(alliance_id)
            if not alliance:
                return {
                    "success": False,
                    "error": "Alliance not found"
                }
            
            # Check if player is a member
            if not alliance.is_member(player_id):
                return {
                    "success": False,
                    "error": "You are not a member of this alliance"
                }
            
            # Check if player is the last leader
            membership = AllianceMember.query.filter_by(
                alliance_id=alliance_id, player_id=player_id, status='active'
            ).first()
            
            is_leader = membership and membership.role == 'leader'
            
            if is_leader:
                # Count other active leaders
                other_leaders = AllianceMember.query.filter(
                    AllianceMember.alliance_id == alliance_id,
                    AllianceMember.role == 'leader',
                    AllianceMember.status == 'active',
                    AllianceMember.player_id != player_id
                ).count()
                
                if other_leaders == 0:
                    # Check for officers to promote
                    officer = AllianceMember.query.filter(
                        AllianceMember.alliance_id == alliance_id,
                        AllianceMember.role == 'officer',
                        AllianceMember.status == 'active'
                    ).first()
                    
                    if officer:
                        # Promote an officer to leader
                        officer.role = 'leader'
                        logger.info(f"Promoted player {officer.player_id} to leader of alliance {alliance_id}")
                    else:
                        # Check for regular members to promote
                        member = AllianceMember.query.filter(
                            AllianceMember.alliance_id == alliance_id,
                            AllianceMember.status == 'active',
                            AllianceMember.player_id != player_id
                        ).first()
                        
                        if member:
                            # Promote a regular member to leader
                            member.role = 'leader'
                            logger.info(f"Promoted player {member.player_id} to leader of alliance {alliance_id}")
                        else:
                            # Last member is leaving, disband alliance
                            alliance.status = 'disbanded'
                            logger.info(f"Alliance {alliance_id} disbanded as last leader left")
            
            # Remove player from alliance
            result = alliance.remove_member(player_id)
            
            # Remove player from alliance chat channel
            if alliance.chat_channel_id:
                chat_controller = self.app_config.get('social_controller')
                if chat_controller:
                    leave_result = chat_controller.leave_channel(player_id, alliance.chat_channel_id)
                    if not leave_result.get('success'):
                        logger.warning(f"Failed to remove player {player_id} from alliance chat channel {alliance.chat_channel_id}: {leave_result.get('error')}")
                else:
                    logger.error("ChatController not found, cannot remove player from alliance chat channel.")
            
            db.session.commit()
            
            # Notify remaining alliance members
            self._notify_player_left(alliance_id, player_id)
            
            if result:
                return {
                    "success": True,
                    "message": "Left alliance successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Error leaving alliance"
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error leaving alliance: {str(e)}")
            return {
                "success": False,
                "error": f"Error leaving alliance: {str(e)}"
            }
    
    def get_player_alliances(self, player_id):
        """Get all alliances a player is a member of"""
        try:
            # Get player's alliance memberships
            memberships = AllianceMember.query.filter_by(
                player_id=player_id, status='active'
            ).all()
            
            # Get alliance details for each membership
            alliances = []
            for membership in memberships:
                alliance = Alliance.query.get(membership.alliance_id)
                if alliance and alliance.status == 'active':
                    alliance_dict = alliance.to_dict()
                    alliance_dict['role'] = membership.role
                    alliances.append(alliance_dict)
            
            # Get public alliances player is not a member of
            if len(alliances) > 0:
                joined_alliance_ids = [m.alliance_id for m in memberships]
                public_alliances = Alliance.query.filter(
                    Alliance.is_public == True,
                    Alliance.status == 'active',
                    ~Alliance.id.in_(joined_alliance_ids)
                ).all()
            else:
                public_alliances = Alliance.query.filter_by(
                    is_public=True, status='active'
                ).all()
            
            # Get pending invites
            invites = AllianceInvite.query.filter_by(
                player_id=player_id, status='pending'
            ).all()
            
            # Format the data
            return {
                "success": True,
                "alliances": {
                    "memberships": alliances,
                    "public": [a.to_dict() for a in public_alliances],
                    "invites": [i.to_dict() for i in invites]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting player alliances: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting player alliances: {str(e)}"
            }
    
    def get_alliance_details(self, alliance_id, player_id=None):
        """Get detailed information about an alliance"""
        try:
            # Check if alliance exists
            alliance = Alliance.query.get(alliance_id)
            if not alliance:
                return {
                    "success": False,
                    "error": "Alliance not found"
                }
            
            # Check if player has access to non-public alliance
            if not alliance.is_public and player_id and not alliance.is_member(player_id):
                return {
                    "success": False,
                    "error": "You don't have access to this alliance"
                }
            
            # Get alliance data
            alliance_data = alliance.to_dict()
            
            # Get members
            members = []
            for member in alliance.members.filter_by(status='active').all():
                members.append({
                    "player_id": member.player_id,
                    "role": member.role,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None
                })
            
            alliance_data['members'] = members
            
            # Check if requesting player is a member
            if player_id:
                membership = AllianceMember.query.filter_by(
                    alliance_id=alliance_id, player_id=player_id, status='active'
                ).first()
                
                alliance_data['is_member'] = membership is not None
                alliance_data['member_role'] = membership.role if membership else None
                
                # If member has leadership role, include pending invites
                if membership and membership.role in ['leader', 'officer']:
                    invites = AllianceInvite.query.filter_by(
                        alliance_id=alliance_id, status='pending'
                    ).all()
                    
                    alliance_data['pending_invites'] = [i.to_dict() for i in invites]
            
            return {
                "success": True,
                "alliance": alliance_data
            }
            
        except Exception as e:
            logger.error(f"Error getting alliance details: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting alliance details: {str(e)}"
            }
    
    def update_alliance(self, alliance_id, updater_id, update_data):
        """Update alliance information"""
        try:
            # Check if alliance exists
            alliance = Alliance.query.get(alliance_id)
            if not alliance:
                return {
                    "success": False,
                    "error": "Alliance not found"
                }
            
            # Check if updater has permission
            membership = AllianceMember.query.filter_by(
                alliance_id=alliance_id, player_id=updater_id, status='active'
            ).first()
            
            if not membership or membership.role not in ['leader', 'officer']:
                return {
                    "success": False,
                    "error": "You don't have permission to update this alliance"
                }
            
            # Update fields
            if 'name' in update_data and update_data['name']:
                name = update_data['name']
                if len(name) < 3 or len(name) > 100:
                    return {
                        "success": False,
                        "error": "Invalid name (must be 3-100 characters)"
                    }
                alliance.name = name
            
            if 'description' in update_data:
                description = update_data['description']
                if description and len(description) > 255:
                    return {
                        "success": False,
                        "error": "Description too long (max 255 characters)"
                    }
                alliance.description = description
            
            if 'is_public' in update_data:
                alliance.is_public = bool(update_data['is_public'])
            
            if 'benefits' in update_data:
                benefits = update_data['benefits']
                
                if 'rent_discount' in benefits:
                    discount = float(benefits['rent_discount'])
                    if 0 <= discount <= 0.5:  # Max 50% discount
                        alliance.rent_discount = discount
                
                if 'development_discount' in benefits:
                    discount = float(benefits['development_discount'])
                    if 0 <= discount <= 0.5:  # Max 50% discount
                        alliance.development_discount = discount
            
            db.session.commit()
            
            # Notify alliance members
            self._notify_alliance_updated(alliance)
            
            return {
                "success": True,
                "alliance": alliance.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating alliance: {str(e)}")
            return {
                "success": False,
                "error": f"Error updating alliance: {str(e)}"
            }
    
    def update_member_role(self, alliance_id, updater_id, member_id, new_role):
        """Update a member's role within an alliance"""
        try:
            # Check if alliance exists
            alliance = Alliance.query.get(alliance_id)
            if not alliance:
                return {
                    "success": False,
                    "error": "Alliance not found"
                }
            
            # Check if updater has permission
            updater_membership = AllianceMember.query.filter_by(
                alliance_id=alliance_id, player_id=updater_id, status='active'
            ).first()
            
            if not updater_membership or updater_membership.role != 'leader':
                return {
                    "success": False,
                    "error": "Only alliance leaders can change member roles"
                }
            
            # Check if member exists
            member_membership = AllianceMember.query.filter_by(
                alliance_id=alliance_id, player_id=member_id, status='active'
            ).first()
            
            if not member_membership:
                return {
                    "success": False,
                    "error": "Member not found in alliance"
                }
            
            # Validate role
            if new_role not in ['member', 'officer', 'leader']:
                return {
                    "success": False,
                    "error": "Invalid role"
                }
            
            # If demoting self from leader, ensure there's another leader
            if updater_id == member_id and updater_membership.role == 'leader' and new_role != 'leader':
                other_leaders = AllianceMember.query.filter(
                    AllianceMember.alliance_id == alliance_id,
                    AllianceMember.role == 'leader',
                    AllianceMember.status == 'active',
                    AllianceMember.player_id != updater_id
                ).count()
                
                if other_leaders == 0:
                    return {
                        "success": False,
                        "error": "Cannot demote yourself from leader without another leader"
                    }
            
            # Update role
            member_membership.role = new_role
            db.session.commit()
            
            # Notify alliance members
            self._notify_role_changed(alliance_id, member_id, new_role)
            
            return {
                "success": True,
                "message": f"Role updated to {new_role}"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating member role: {str(e)}")
            return {
                "success": False,
                "error": f"Error updating member role: {str(e)}"
            }
    
    def calculate_alliance_benefits(self, player1_id, player2_id):
        """Calculate benefits between two players based on shared alliances"""
        try:
            # Get player 1's alliances
            player1_memberships = AllianceMember.query.filter_by(
                player_id=player1_id, status='active'
            ).all()
            
            player1_alliance_ids = [m.alliance_id for m in player1_memberships]
            
            if not player1_alliance_ids:
                return {
                    "success": True,
                    "has_alliance": False,
                    "benefits": {
                        "rent_discount": 0.0,
                        "development_discount": 0.0
                    }
                }
            
            # Check if player 2 is in any of the same alliances
            shared_memberships = AllianceMember.query.filter(
                AllianceMember.player_id == player2_id,
                AllianceMember.status == 'active',
                AllianceMember.alliance_id.in_(player1_alliance_ids)
            ).all()
            
            if not shared_memberships:
                return {
                    "success": True,
                    "has_alliance": False,
                    "benefits": {
                        "rent_discount": 0.0,
                        "development_discount": 0.0
                    }
                }
            
            # Find the alliance with best benefits
            shared_alliance_ids = [m.alliance_id for m in shared_memberships]
            alliances = Alliance.query.filter(
                Alliance.id.in_(shared_alliance_ids),
                Alliance.status == 'active'
            ).all()
            
            best_alliance = max(alliances, key=lambda a: a.rent_discount + a.development_discount)
            
            return {
                "success": True,
                "has_alliance": True,
                "alliance_id": best_alliance.id,
                "alliance_name": best_alliance.name,
                "benefits": {
                    "rent_discount": best_alliance.rent_discount,
                    "development_discount": best_alliance.development_discount
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating alliance benefits: {str(e)}")
            return {
                "success": False,
                "error": f"Error calculating alliance benefits: {str(e)}"
            }
    
    def _notify_alliance_creation(self, alliance):
        """Notify players about alliance creation"""
        alliance_dict = alliance.to_dict()
        
        # Notify creator
        self.socketio.emit('alliance_created', alliance_dict, room=f"player_{alliance.created_by}")
        
        # If public, notify all players
        if alliance.is_public:
            self.socketio.emit('public_alliance_created', {
                "alliance_id": alliance.id,
                "name": alliance.name,
                "description": alliance.description,
                "created_by": alliance.created_by
            })
    
    def _notify_alliance_invitation(self, invite):
        """Notify a player about an alliance invitation"""
        alliance = Alliance.query.get(invite.alliance_id)
        
        invite_data = {
            "invite_id": invite.id,
            "alliance_id": invite.alliance_id,
            "alliance_name": alliance.name,
            "inviter_id": invite.inviter_id,
            "created_at": invite.created_at.isoformat() if invite.created_at else None
        }
        
        # Notify invitee
        self.socketio.emit('alliance_invite_received', invite_data, room=f"player_{invite.player_id}")
        
        # Notify alliance leaders and officers
        leader_memberships = AllianceMember.query.filter(
            AllianceMember.alliance_id == invite.alliance_id,
            AllianceMember.role.in_(['leader', 'officer']),
            AllianceMember.status == 'active'
        ).all()
        
        for membership in leader_memberships:
            if membership.player_id != invite.inviter_id:  # Don't notify the inviter
                self.socketio.emit('alliance_invite_sent', invite_data, room=f"player_{membership.player_id}")
    
    def _notify_player_joined(self, alliance_id, player_id):
        """Notify alliance members when a new player joins"""
        # Get alliance and player details
        alliance = Alliance.query.get(alliance_id)
        
        join_data = {
            "alliance_id": alliance_id,
            "alliance_name": alliance.name,
            "player_id": player_id
        }
        
        # Notify all alliance members
        memberships = AllianceMember.query.filter_by(
            alliance_id=alliance_id, status='active'
        ).all()
        
        for membership in memberships:
            if membership.player_id != player_id:  # Don't notify the player who joined
                self.socketio.emit('player_joined_alliance', join_data, room=f"player_{membership.player_id}")
    
    def _notify_invite_declined(self, invite):
        """Notify alliance leaders when an invitation is declined"""
        alliance = Alliance.query.get(invite.alliance_id)
        
        decline_data = {
            "alliance_id": invite.alliance_id,
            "alliance_name": alliance.name,
            "player_id": invite.player_id,
            "inviter_id": invite.inviter_id
        }
        
        # Notify inviter
        self.socketio.emit('alliance_invite_declined', decline_data, room=f"player_{invite.inviter_id}")
        
        # Notify alliance leaders and officers
        leader_memberships = AllianceMember.query.filter(
            AllianceMember.alliance_id == invite.alliance_id,
            AllianceMember.role.in_(['leader', 'officer']),
            AllianceMember.status == 'active'
        ).all()
        
        for membership in leader_memberships:
            if membership.player_id != invite.inviter_id:  # Don't duplicate notification to inviter
                self.socketio.emit('alliance_invite_declined', decline_data, room=f"player_{membership.player_id}")
    
    def _notify_player_left(self, alliance_id, player_id):
        """Notify alliance members when a player leaves"""
        # Get alliance details
        alliance = Alliance.query.get(alliance_id)
        
        leave_data = {
            "alliance_id": alliance_id,
            "alliance_name": alliance.name,
            "player_id": player_id
        }
        
        # Notify all remaining alliance members
        memberships = AllianceMember.query.filter_by(
            alliance_id=alliance_id, status='active'
        ).all()
        
        for membership in memberships:
            self.socketio.emit('player_left_alliance', leave_data, room=f"player_{membership.player_id}")
    
    def _notify_alliance_updated(self, alliance):
        """Notify alliance members when alliance details are updated"""
        alliance_dict = alliance.to_dict()
        
        # Notify all alliance members
        memberships = AllianceMember.query.filter_by(
            alliance_id=alliance.id, status='active'
        ).all()
        
        for membership in memberships:
            self.socketio.emit('alliance_updated', alliance_dict, room=f"player_{membership.player_id}")
    
    def _notify_role_changed(self, alliance_id, member_id, new_role):
        """Notify alliance members when a member's role changes"""
        # Get alliance details
        alliance = Alliance.query.get(alliance_id)
        
        role_data = {
            "alliance_id": alliance_id,
            "alliance_name": alliance.name,
            "player_id": member_id,
            "new_role": new_role
        }
        
        # Notify all alliance members
        memberships = AllianceMember.query.filter_by(
            alliance_id=alliance_id, status='active'
        ).all()
        
        for membership in memberships:
            self.socketio.emit('alliance_role_changed', role_data, room=f"player_{membership.player_id}") 