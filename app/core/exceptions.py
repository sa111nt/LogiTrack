"""
Custom exceptions raised in the Repository / Service layer
"""


class LogiTrackError(Exception):
    def __init__(self, detail: str = "An unexpected error occurred"):
        self.detail = detail
        super().__init__(self.detail)


class NotFoundError(LogiTrackError):
    def __init__(self, entity: str, identifier: int | str):
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} with id={identifier} not found")


class AlreadyExistsError(LogiTrackError):
    def __init__(self, entity: str, field: str, value: str):
        self.entity = entity
        self.field = field
        self.value = value
        super().__init__(f"{entity} with {field}={value!r} already exists")


class InvalidMovementError(LogiTrackError):
    def __init__(self, detail: str):
        super().__init__(detail)
