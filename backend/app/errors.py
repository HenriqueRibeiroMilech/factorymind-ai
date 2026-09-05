class AppError(Exception):
    def __init__(self, message, code="invalid_request", status=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class ProviderError(AppError):
    def __init__(self, message, code="provider_unavailable", status=503):
        super().__init__(message, code, status)
