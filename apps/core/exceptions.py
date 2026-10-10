"""Excepciones de dominio reutilizadas por todas las apps."""

from __future__ import annotations


class DomainError(Exception):
    """Excepcion base para errores de reglas de negocio.

    Cualquier ``Exception`` capturada en services o vistas que derive
    de esta clase sera mapeada a HTTP 400 por el handler de DRF.
    """

    def __init__(self, message: str = "") -> None:
        """Inicializa con un mensaje legible para el usuario final."""
        super().__init__(message or self.__class__.__name__)
        self.message = message


class InsufficientStockError(DomainError):
    """Se lanza cuando no hay cantidad suficiente para una salida."""

    def __init__(self, message: str = "Stock insuficiente.") -> None:
        """Inicializa con un mensaje por defecto."""
        super().__init__(message)


class InvalidStateTransitionError(DomainError):
    """Se lanza cuando una transicion de estado no esta permitida."""

    def __init__(self, message: str = "Transicion de estado no permitida.") -> None:
        """Inicializa con un mensaje por defecto."""
        super().__init__(message)


class InvalidQuantityError(DomainError):
    """Se lanza cuando una cantidad es cero o negativa."""

    def __init__(self, message: str = "Cantidad invalida.") -> None:
        """Inicializa con un mensaje por defecto."""
        super().__init__(message)


class LotRequiredError(DomainError):
    """Se lanza cuando un producto requiere lote y no se proporcinó."""

    def __init__(self, message: str = "El producto requiere numero de lote.") -> None:
        """Inicializa con un mensaje por defecto."""
        super().__init__(message)


class BusinessRuleError(DomainError):
    """Error generico de regla de negocio no contemplado en otras clases."""

    def __init__(self, message: str = "Regla de negocio violada.") -> None:
        """Inicializa con un mensaje por defecto."""
        super().__init__(message)
