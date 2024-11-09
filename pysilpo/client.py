from typing import Literal, Optional

from pysilpo.authorization import User
from pysilpo.cheque import Cheque
from pysilpo.exceptions import SilpoAuthorizationException
from pysilpo.product import Product


class Silpo:
    def __init__(
        self,
        phone_number: Optional[str] = None,
        otp_delivery_method: Literal["sms", "viber-sms"] = "sms",
    ):
        self._user = None
        self._cheque = None
        self._product = Product
        if phone_number is not None:
            self._user = User(phone_number=phone_number).request_otp(otp_delivery_method).login()
            self._cheque = Cheque(self._user)

    @property
    def cheque(self) -> Cheque:
        if self._cheque is None:
            raise SilpoAuthorizationException(
                "User is not authorized. " "Please provide phone number e.g. Silpo(phone_number='+380123456789')"
            )
        return self._cheque

    @property
    def product(self) -> type[Product]:
        return self._product
