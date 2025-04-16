"""
Database migration for event system implementation

This migration adds:
1. New columns to property for damage tracking
2. New columns to game_state for temporary effects
3. New column to player for socket_id
4. New column to loan for original_interest_rate
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'event_system_001'
down_revision = None
depends_on = None


def upgrade():
    # Add damage_amount and is_water_adjacent to properties table
    op.add_column('properties', sa.Column('damage_amount', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('properties', sa.Column('is_water_adjacent', sa.Boolean(), nullable=True, server_default='0'))
    
    # Add temporary_effects, game_id, and last_event_lap to game_state table
    op.add_column('game_state', sa.Column('_temporary_effects', sa.Text(), nullable=True, server_default='[]'))
    op.add_column('game_state', sa.Column('game_id', sa.String(36), nullable=True))
    op.add_column('game_state', sa.Column('last_event_lap', sa.Integer(), nullable=True, server_default='0'))
    
    # Set game_id for existing game states
    conn = op.get_bind()
    conn.execute(text("UPDATE game_state SET game_id = SUBSTR(HEX(RANDOMBLOB(16)), 1, 8) || '-' || "
                     "SUBSTR(HEX(RANDOMBLOB(16)), 1, 4) || '-4' || "
                     "SUBSTR(HEX(RANDOMBLOB(16)), 1, 3) || '-' || "
                     "SUBSTR('89AB', 1 + (ABS(RANDOM()) % 4), 1) || "
                     "SUBSTR(HEX(RANDOMBLOB(16)), 1, 3) || '-' || "
                     "SUBSTR(HEX(RANDOMBLOB(16)), 1, 12) "
                     "WHERE game_id IS NULL"))
    
    # Make game_id not nullable after populating
    op.alter_column('game_state', 'game_id', nullable=False)
    
    # Add socket_id to players table
    op.add_column('players', sa.Column('socket_id', sa.String(50), nullable=True))
    
    # Add original_interest_rate to loans table
    op.add_column('loans', sa.Column('original_interest_rate', sa.Float(), nullable=True))
    
    # Set original_interest_rate equal to interest_rate for existing loans
    conn.execute(text("UPDATE loans SET original_interest_rate = interest_rate WHERE original_interest_rate IS NULL"))


def downgrade():
    # Remove new columns
    op.drop_column('properties', 'damage_amount')
    op.drop_column('properties', 'is_water_adjacent')
    op.drop_column('game_state', '_temporary_effects')
    op.drop_column('game_state', 'game_id')
    op.drop_column('game_state', 'last_event_lap')
    op.drop_column('players', 'socket_id')
    op.drop_column('loans', 'original_interest_rate') 