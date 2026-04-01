# dependency injection container - создает все репозитории и сервисы и связывает их вместе
# вместо того чтобы каждый сервис сам создавал свои зависимости, мы делаем это здесь централизованно

from repositories.user_repository import UserRepository
from repositories.token_repository import TokenRepository
from repositories.deck_repository import DeckRepository
from repositories.card_repository import CardRepository
from repositories.stats_repository import StatsRepository


class Container:
    def __init__(self):
        # создаем все репозитории (слой работы с базой данных)
        self.user_repository = UserRepository()
        self.token_repository = TokenRepository()
        self.deck_repository = DeckRepository()
        self.card_repository = CardRepository()
        self.stats_repository = StatsRepository()

        # импортируем сервисы здесь чтобы избежать циклических импортов
        from services.auth_service import AuthService
        from services.deck_service import DeckService
        from services.stats_service import StatsService

        # создаем сервисы и внедряем в них репозитории через конструктор (di)
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


# единственный экземпляр контейнера на всё приложение (singleton)
# все маршруты импортируют этот объект
container = Container()
