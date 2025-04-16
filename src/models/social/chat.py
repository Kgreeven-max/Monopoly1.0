from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models import db
import uuid

class Channel(db.Model):
    """Chat channel model"""
    __tablename__ = 'channels'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    type = db.Column(db.String(20), nullable=False, default='public')  # public, private, group
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('players.id'))
    
    # Relationships
    messages = db.relationship('Message', backref='channel', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('ChannelMember', backref='channel', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert channel to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'member_count': self.members.count()
        }
    
    def add_member(self, player_id):
        """Add a member to this channel"""
        if not self.is_member(player_id):
            member = ChannelMember(channel_id=self.id, player_id=player_id)
            db.session.add(member)
            return True
        return False
    
    def remove_member(self, player_id):
        """Remove a member from this channel"""
        member = ChannelMember.query.filter_by(
            channel_id=self.id, player_id=player_id).first()
        if member:
            db.session.delete(member)
            return True
        return False
    
    def is_member(self, player_id):
        """Check if a player is a member of this channel"""
        return ChannelMember.query.filter_by(
            channel_id=self.id, player_id=player_id).first() is not None


class ChannelMember(db.Model):
    """Channel membership model"""
    __tablename__ = 'channel_members'
    
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(36), db.ForeignKey('channels.id'), nullable=False)
    player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        db.UniqueConstraint('channel_id', 'player_id', name='unique_channel_membership'),
    )
    
    def to_dict(self):
        """Convert membership to dictionary"""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'player_id': self.player_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'last_read': self.last_read.isoformat() if self.last_read else None
        }


class Message(db.Model):
    """Chat message model"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id = db.Column(db.String(36), db.ForeignKey('channels.id'), nullable=False)
    sender_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='text')  # text, image, system
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime)
    
    # Relationships
    reactions = db.relationship('MessageReaction', backref='message', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'sender_id': self.sender_id,
            'content': self.content,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'edited': self.edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'reactions': {r.emoji: r.count for r in self.get_reaction_counts()}
        }
    
    def edit(self, new_content):
        """Edit message content"""
        self.content = new_content
        self.edited = True
        self.edited_at = datetime.utcnow()
    
    def add_reaction(self, player_id, emoji):
        """Add a reaction to this message"""
        # Check if player already reacted with this emoji
        existing = MessageReaction.query.filter_by(
            message_id=self.id, player_id=player_id, emoji=emoji).first()
        
        if existing:
            return False
        
        # Add new reaction
        reaction = MessageReaction(message_id=self.id, player_id=player_id, emoji=emoji)
        db.session.add(reaction)
        return True
    
    def remove_reaction(self, player_id, emoji):
        """Remove a reaction from this message"""
        reaction = MessageReaction.query.filter_by(
            message_id=self.id, player_id=player_id, emoji=emoji).first()
        
        if reaction:
            db.session.delete(reaction)
            return True
        return False
    
    def get_reaction_counts(self):
        """Get counts of reactions by emoji"""
        return db.session.query(
            MessageReaction.emoji, 
            db.func.count(MessageReaction.id).label('count')
        ).filter(
            MessageReaction.message_id == self.id
        ).group_by(
            MessageReaction.emoji
        ).all()


class MessageReaction(db.Model):
    """Message reaction model for emoji reactions"""
    __tablename__ = 'message_reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=False)
    player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    emoji = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate reactions
    __table_args__ = (
        db.UniqueConstraint('message_id', 'player_id', 'emoji', name='unique_message_reaction'),
    )
    
    def to_dict(self):
        """Convert reaction to dictionary"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'player_id': self.player_id,
            'emoji': self.emoji,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 