-- Pinopoly Master Database Initialization
-- This script runs when the PostgreSQL container is first created

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- USERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    total_games_played INT DEFAULT 0,
    total_wins INT DEFAULT 0,
    lifetime_earnings BIGINT DEFAULT 0
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- =============================================================================
-- GAMES TABLE (Catalog of all games)
-- =============================================================================
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_code VARCHAR(6) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'lobby',
    schema_name VARCHAR(63),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    host_user_id UUID REFERENCES users(id),
    winner_user_id UUID REFERENCES users(id),
    game_config JSONB NOT NULL DEFAULT '{}',
    final_snapshot JSONB,
    duration_seconds INT
);

CREATE INDEX idx_games_room_code ON games(room_code);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_created_at ON games(created_at);
CREATE INDEX idx_games_host ON games(host_user_id);

-- =============================================================================
-- GAME PARTICIPANTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS game_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    player_name VARCHAR(50) NOT NULL,
    token VARCHAR(20) NOT NULL,
    color VARCHAR(7) NOT NULL,
    is_bot BOOLEAN DEFAULT FALSE,
    bot_personality VARCHAR(20),
    final_position INT,
    final_net_worth BIGINT,
    joined_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_participants_game ON game_participants(game_id);
CREATE INDEX idx_participants_user ON game_participants(user_id);

-- =============================================================================
-- AUDIT LOG
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    game_id UUID REFERENCES games(id),
    player_id UUID,
    action_type VARCHAR(50) NOT NULL,
    action_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_game ON audit_log(game_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action_type ON audit_log(action_type);

-- =============================================================================
-- SESSIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_token ON sessions(token_hash);

-- =============================================================================
-- DAILY STATS (Analytics)
-- =============================================================================
CREATE TABLE IF NOT EXISTS daily_stats (
    date DATE PRIMARY KEY,
    games_started INT DEFAULT 0,
    games_completed INT DEFAULT 0,
    unique_players INT DEFAULT 0,
    total_play_time_seconds BIGINT DEFAULT 0,
    most_popular_bot VARCHAR(20),
    avg_game_duration_seconds INT
);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to update user stats after game
CREATE OR REPLACE FUNCTION update_user_game_stats(
    p_user_id UUID,
    p_won BOOLEAN,
    p_earnings BIGINT
)
RETURNS void AS $$
BEGIN
    UPDATE users
    SET
        total_games_played = total_games_played + 1,
        total_wins = total_wins + CASE WHEN p_won THEN 1 ELSE 0 END,
        lifetime_earnings = lifetime_earnings + p_earnings
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Create a system user for anonymous players
INSERT INTO users (id, username, email, password_hash)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'anonymous',
    NULL,
    'not-a-real-password'
) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant permissions to pinopoly user (should already have full access as owner)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pinopoly;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pinopoly;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO pinopoly;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Pinopoly master database initialized successfully!';
END $$;
