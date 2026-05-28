from app.models.product import Product
from app.repositories.product import ProductRepository
from app.services.base import BaseService


class ProductService(BaseService[Product]):
    repository: ProductRepository

    def __init__(self, repository: ProductRepository) -> None:
        super().__init__(repository)

    async def get_all(
        self, offset: int = 0, limit: int = 100, category_id: int | None = None
    ) -> tuple[list[Product], int]:
        return await self.repository.get_all(offset, limit, category_id)

    async def get_by_id_with_category(self, product_id: int) -> Product | None:
        return await self.repository.get_by_id_with_category(product_id)
