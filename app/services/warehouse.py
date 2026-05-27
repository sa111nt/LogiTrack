from app.models.warehouse import Warehouse
from app.repositories.warehouse import WarehouseRepository
from app.services.base import BaseService


class WarehouseService(BaseService[Warehouse]):
    repository: WarehouseRepository

    def __init__(self, repository: WarehouseRepository) -> None:
        super().__init__(repository)
