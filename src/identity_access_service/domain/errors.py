class UserNotFoundError(Exception):
    pass


class EmailAlreadyInUseError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class TokenInvalidError(Exception):
    pass
