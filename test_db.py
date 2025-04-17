from app import app, db
from src.models.player import Player
from src.models.property import Property

# Use application context
with app.app_context():
    # Query all players
    print("Players in the database:")
    players = Player.query.all()
    for p in players:
        # Get the property count
        property_count = Property.query.filter_by(owner_id=p.id).count()
        in_game_status = "In Game" if p.in_game else "Not In Game"
        bot_status = "Bot" if p.is_bot else "Human"
        print(f"ID: {p.id}, Name: {p.username}, Status: {in_game_status}, Type: {bot_status}, Money: ${p.money}, Property Count: {property_count}")

    # Check if there are any bots in the game
    bots = Player.query.filter_by(is_bot=True).all()
    print(f"\nTotal bots in database: {len(bots)}")

    active_bots = Player.query.filter_by(is_bot=True, in_game=True).all()
    print(f"Active bots in game: {len(active_bots)}")

    # Check if there are any humans in the game
    humans = Player.query.filter_by(is_bot=False).all()
    print(f"\nTotal humans in database: {len(humans)}")

    active_humans = Player.query.filter_by(is_bot=False, in_game=True).all()
    print(f"Active humans in game: {len(active_humans)}")

    # Print all players that should be in the game
    print("\nPlayers that should be in the game:")
    in_game_players = Player.query.filter_by(in_game=True).all()
    for p in in_game_players:
        print(f"ID: {p.id}, Name: {p.username}, Is Bot: {p.is_bot}") 