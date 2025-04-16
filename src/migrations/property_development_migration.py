"""
Database migration for property development system implementation

This migration adds:
1. New columns to property for advanced development levels
2. New columns for zoning regulations and approvals
3. New columns for environmental studies
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'property_development_001'
down_revision = 'event_system_001'  # Depends on the event system migration
depends_on = None


def upgrade():
    # Add columns to properties table for development system
    op.add_column('properties', sa.Column('max_development_level', sa.Integer(), nullable=False, server_default='4'))
    op.add_column('properties', sa.Column('has_community_approval', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('properties', sa.Column('has_environmental_study', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('properties', sa.Column('environmental_study_expires', sa.DateTime(), nullable=True))
    
    # Update existing properties with appropriate max_development_level based on group
    conn = op.get_bind()
    
    # Brown and Light Blue property groups - max level 3
    conn.execute(text("UPDATE properties SET max_development_level = 3 WHERE LOWER(group_name) IN ('brown', 'light_blue')"))
    
    # Railroad and Utility property groups - max level 0 (no development)
    conn.execute(text("UPDATE properties SET max_development_level = 0 WHERE LOWER(group_name) IN ('railroad', 'utility')"))
    
    # All other property groups keep default max level 4


def downgrade():
    # Remove new columns
    op.drop_column('properties', 'max_development_level')
    op.drop_column('properties', 'has_community_approval')
    op.drop_column('properties', 'has_environmental_study')
    op.drop_column('properties', 'environmental_study_expires') 