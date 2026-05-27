from app.models.supplier import Supplier
from app.repositories.supplier import SupplierRepository
from app.services.base import BaseService


class SupplierService(BaseService[Supplier]):
    repository: SupplierRepository

    def __init__(self, repository: SupplierRepository) -> None:
        super().__init__(repository)
