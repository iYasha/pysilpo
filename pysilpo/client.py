from typing import Literal, Optional

from pysilpo.services.authorization import User
from pysilpo.services.cheque import Cheque
from pysilpo.services.product import Product
from pysilpo.services.store import City, Store
from pysilpo.utils.cache import SQLiteCache
from pysilpo.utils.exceptions import SilpoAuthorizationException


class Silpo:
    product = Product
    store = Store
    city = City

    def __init__(
        self,
        phone_number: Optional[str] = None,
        otp_delivery_method: Literal["sms", "viber-sms"] = "sms",
    ):
        self._user = None
        self._cheque = None
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

    @classmethod
    def clear_cache(cls):
        SQLiteCache().clear()
