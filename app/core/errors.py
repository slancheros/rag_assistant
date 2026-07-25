class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
    ) -> None:
        super().__init__(message)

        self.code = code
        self.message = message
        self.status_code = status_code


class ProviderUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="provider_unavailable",
            message=(
                "The assistant is temporarily unavailable."
            ),
            status_code=503,
        )