from collections.abc import Generator
from datetime import datetime
from functools import cached_property
from typing import Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field, PrivateAttr

from pysilpo.authorization import User
from pysilpo.enums import PayTypeEnum
from pysilpo.utils import get_logger, subtract_months


class ChequeRewardModel(BaseModel):
    reward_type_id: int = Field(..., alias="rewardTypeId")
    apply_text: str = Field(..., alias="applyText")
    reward_value: float = Field(..., alias="rewardValue")
    sign_text: str = Field(..., alias="signText")
    unit_text: str = Field(..., alias="unitText")
    gold_coupon_promo_type: Optional[str] = Field(..., alias="goldCouponPromoType")
    promo_id: Optional[int] = Field(..., alias="promoId")
    used_text: Optional[str] = Field(..., alias="usedText")
    used_count_text: Optional[str] = Field(..., alias="usedCountText")
    used_unit_text: Optional[str] = Field(..., alias="usedUnitText")

    class Meta:
        alternative_name = "chequeRewards"


class ChequePositionModel(BaseModel):
    cheque_line_id: int = Field(..., alias="chequeLineId")
    lager_id: int = Field(..., alias="lagerId")
    lager_name_ua: str = Field(..., alias="lagerNameUA")
    lager_unit: str = Field(..., alias="lagerUnit")
    count: float = Field(..., alias="kolvo")
    price_out: float = Field(..., alias="priceOut")
    unit_text: str = Field(..., alias="unitText")
    image_url: Optional[str] = Field(None, alias="fileName")
    sum_cashback_line: float = Field(default=0.0, alias="sumCashbackLine")

    def get_full_image_url(self, width: int = 480, height: int = 480) -> Optional[str]:
        if self.image_url is not None:
            size = f"{width}x{height}wwm"
            return (
                f"https://content.silpo.ua/sku/ecommerce/{int(self.lager_id / 1e4)}"
                f"/{size}/{self.lager_id}_{size}_{self.image_url}"
            )
        return None

    class Meta:
        alternative_name = "chequeLines"


class ChequeActionModel(BaseModel):
    action_type: int = Field(..., alias="actionType")  # TODO: Create an enum
    action_type_code_name: Optional[str] = Field(None, alias="actionTypeCodeName")
    action_id: int = Field(..., alias="actionId")
    discpercent: Optional[float] = Field(default=None, alias="discPercent")
    discount: Optional[float] = Field(None, alias="discount")
    varchar_data: Optional[str] = Field(None, alias="varcharData")


class ChequeDetailModel(BaseModel):
    cheque_header: "ChequeModel" = Field(..., alias="chequeHeader")
    sum_discount: float = Field(..., alias="sumDiscount")
    positions: Optional[list[ChequePositionModel]] = Field(..., alias="chequeLines")
    actions: Optional[list[ChequeActionModel]] = Field(..., alias="chequeActions")
    ch_prediction: str = Field(..., alias="chPrediction")
    sum_cashback: float = Field(..., alias="sumCashback")


class ChequeModel(BaseModel):
    _cheque_service: Optional["Cheque"] = PrivateAttr(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cheque_service = kwargs.pop("cheque_service", None)

    loyalty_fact_id: int = Field(..., alias="loyaltyFactId")
    sum_reg: float = Field(..., alias="sumReg")
    sum_balance: float = Field(..., alias="sumBalance")
    filial_name: str = Field(..., alias="filialName")
    city_name: str = Field(..., alias="cityName")
    fr_id: int = Field(..., alias="frId")
    z_id: int = Field(..., alias="zId")
    fr_cheque_id: int = Field(..., alias="frChequeId")
    pay_type: PayTypeEnum = Field(..., alias="payType")
    filial_id: int = Field(..., alias="filId")
    cheque_id: int = Field(..., alias="chequeId")
    created: datetime
    fiscal_number: str = Field(..., alias="fiscalNumber")
    business_card_id: int = Field(..., alias="businessCardId")
    external_operation_id: str = Field(..., alias="externalOperationId")

    @cached_property
    def detail(self) -> ChequeDetailModel:
        if self._cheque_service is None:
            raise ValueError("Cheque service is not set")
        return self._cheque_service.get_detail(
            self.cheque_id,
            self.created,
            self.filial_id,
            self.loyalty_fact_id,
        )


class Cheque:
    logger = get_logger("pysilpo.cheque.Cheque")
    _DOMAIN = "https://loyalty-platform-public-api.silpo.ua"
    _ALL_CHEQUES_URL = urljoin(_DOMAIN, "/api/v1/profile/my/cheque/cheque-headers")
    _CHEQUE_DETAIL_URL = urljoin(_DOMAIN, "/api/v1/profile/my/cheque/cheque-info")

    def __init__(self, user: User):
        self.user = user

    def get_detail(self, cheque_id: int, created: datetime, fill_id: int, loyalty_fact_id: int) -> ChequeDetailModel:
        payload = {
            "filId": fill_id,
            "chequeId": cheque_id,
            "created": created.isoformat(),
            "loyaltyFactId": loyalty_fact_id,
        }
        self.logger.debug("Fetching cheque detail for %s", payload)
        resp = requests.post(
            self._CHEQUE_DETAIL_URL,
            json=payload,
            headers={"Authorization": f"Bearer {self.user.access_token}"},
        )
        resp.raise_for_status()
        return ChequeDetailModel(**resp.json())

    def get_all(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page_size: int = 0,
        row_number: int = 0,
    ) -> Generator[ChequeModel, None, None]:
        if date_to is None:
            date_to = datetime.now()

        # Start with the latest 3-month chunk and work backwards
        current_date_to = date_to
        current_date_from = max(
            subtract_months(current_date_to, 3),
            date_from if date_from is not None else datetime.min,
        )

        first_cheque_id_in_chunk: Optional[int] = None

        while date_from is None or current_date_to > date_from:
            payload = {
                "rowNumber": row_number,
                "pageSize": page_size,
                "dateStart": current_date_from.isoformat(),
                "dateEnd": current_date_to.isoformat(),
            }
            self.logger.debug("Fetching cheques from %s to %s", current_date_from, current_date_to)
            resp = requests.post(
                self._ALL_CHEQUES_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self.user.access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()

            # If no more data, exit the loop, but it's unlikely to happen, see the next check
            if not data:
                break

            """
            Silpo API returns data even if it's out of the date range, so we need to prevent duplicates by checking
            if the first cheque ID in the chunk is the same as the previous one.
            """
            if data[0]["chequeId"] == first_cheque_id_in_chunk:
                break  # No more data
            first_cheque_id_in_chunk = data[0]["chequeId"]

            # Yield each item in a flat structure
            for item in data:
                yield ChequeModel(**item, cheque_service=self)

            # Update dates for the next iteration (previous 3-month chunk)
            current_date_to = subtract_months(current_date_from, 3)
            current_date_from = max(
                subtract_months(current_date_to, 3),
                subtract_months(datetime.fromisoformat(data[-1]["created"]), 3) if date_from is None else date_from,
            )
