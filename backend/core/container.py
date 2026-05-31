# Dependency Injection Container - instantiates all repositories and services, wired together.
# Instead of each service constructing its own dependencies, we handle it centrally here.

from repositories.user_repository import UserRepository
from repositories.token_repository import TokenRepository
from repositories.deck_repository import DeckRepository
from repositories.card_repository import CardRepository
from repositories.stats_repository import StatsRepository


class Container:
    def __init__(self):
        # Instantiate repositories (data access layer)
        self.user_repository = UserRepository()
        self.token_repository = TokenRepository()
        self.deck_repository = DeckRepository()
        self.card_repository = CardRepository()
        self.stats_repository = StatsRepository()

        # Import services locally to avoid circular dependencies
        from services.auth_service import AuthService
        from services.deck_service import DeckService
        from services.stats_service import StatsService

        # Instantiate services and inject required repositories (Constructor Dependency Injection)
        self.auth_service = AuthService(
            self.user_repository,
            self.token_repository,
            self.stats_repository
        )
        self.deck_service = DeckService(
            self.deck_repository,
            self.card_repository,
            self.user_repository,
            self.stats_repository
        )
        self.stats_service = StatsService(
            self.stats_repository,
            self.deck_repository,
            self.card_repository,
            self.user_repository
        )


# Singleton instance of the DI container shared across the application.
# All blueprints/routes import this instance to interact with services.
container = Container()
