from app.models.product import Product
from app.repositories.product import ProductRepository
from app.services.base import BaseService


class ProductService(BaseService[Product]):
    repository: ProductRepository

    def __init__(self, repository: ProductRepository) -> None:
        super().__init__(repository)


