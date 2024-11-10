class SilpoException(Exception):
    pass


class SilpoRequestException(SilpoException):
    pass


class SilpoAuthorizationException(SilpoRequestException):
    pass


class SilpoOTPInvalidException(SilpoAuthorizationException):
    pass
