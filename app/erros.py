"""Project-wide exceptions for the reservation domain."""


class AppError(Exception):
    """Base domain error."""


class ValidationError(AppError):
    """Raised when persisted values do not satisfy documented rules."""


class ConflictError(AppError):
    """Raised when resource availability or business constraints are violated."""


class PermissionError(AppError):
    """Raised when authorization rules are violated."""
