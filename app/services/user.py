from app.models.user import User
from app.repositories.user import UserRepository
from app.services.base import BaseService


class UserService(BaseService[User]):
    repository: UserRepository

    def __init__(self, repository: UserRepository) -> None:
        super().__init__(repository)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(email)
