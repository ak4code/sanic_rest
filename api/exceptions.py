from sanic.exceptions import SanicException


class ActivationCodeError(SanicException):
    def __init__(self, message="Code error"):
        super().__init__(message, 400)


class AuthorizationError(SanicException):
    def __init__(self, message):
        super().__init__(message, 403)


class CredentialsError(SanicException):
    def __init__(self, message, code=400):
        super().__init__(message, code)


class NotFoundError(SanicException):
    def __init__(self, message):
        super().__init__(message, 404)


class InvalidSignature(SanicException):
    def __init__(self, message="Invalid signature"):
        super().__init__(message, 400)
