from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.services.base import BaseService


class CategoryService(BaseService[Category]):
    repository: CategoryRepository

    def __init__(self, repository: CategoryRepository) -> None:
        super().__init__(repository)
