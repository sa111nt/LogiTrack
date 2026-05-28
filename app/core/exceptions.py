"""Custom exceptions raised in the Repository / Service layer."""


class LogiTrackError(Exception):
    def __init__(self, detail: str = "An unexpected error occurred"):
        self.detail = detail
        super().__init__(self.detail)


class AlreadyExistsError(LogiTrackError):
    def __init__(self, entity: str, field: str, value: str):
        self.entity = entity
        self.field = field
        self.value = value
        super().__init__(f"{entity} with {field}={value!r} already exists")


class InvalidMovementError(LogiTrackError):
    def __init__(self, detail: str):
        super().__init__(detail)


class InsufficientStockError(LogiTrackError):
    def __init__(
        self,
        product_id: int,
        warehouse_id: int,
        requested: int,
        available: int,
    ):
        self.product_id = product_id
        self.warehouse_id = warehouse_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product_id={product_id} "
            f"at warehouse_id={warehouse_id}: "
            f"requested={requested}, available={available}"
        )
