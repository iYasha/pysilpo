from datetime import datetime
from datetime import datetime
from typing import Optional, List, get_args, Tuple, Union

from pydantic import BaseModel, Field

from pysilpo.enums import PayTypeEnum


class SilpoBaseModel(BaseModel):
    @classmethod
    def _get_nested_field(cls, field):
        try:
            if issubclass(field, SilpoBaseModel):
                return field
        except TypeError:
            pass

        args = get_args(field)
        if args:
            for arg in args:
                nested = cls._get_nested_field(arg)
                if nested:
                    return nested
        return None

    @classmethod
    def get_fields(cls) -> List[Union[str, Tuple[str, List[str]]]]:
        fields = []
        for name, field in cls.model_fields.items():
            nested_field = cls._get_nested_field(field.annotation)
            if nested_field:
                fields.append(
                    (nested_field.Meta.alternative_name, nested_field.get_fields())
                )
            else:
                fields.append(field.alias or name)
        return fields

    @classmethod
    def to_graphql(
        cls, fields: Optional[List[Union[str, Tuple[str, List[str]]]]] = None
    ) -> str:
        graph_str = ""
        if fields is None:
            fields = cls.get_fields()
        for field in fields:
            if isinstance(field, tuple):
                graph_str += f"{field[0]} {{\n"
                graph_str += cls.to_graphql(field[1]) + "}\n"
            else:
                graph_str += f"{field}\n"

        return graph_str


class User(SilpoBaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    middle_name: str = Field(..., alias="middleName")
    full_phone_number: str = Field(..., alias="fullPhoneNumber")
    email: str
    email_confirmed: bool = Field(..., alias="emailConfirmed")
    current_bonus: float = Field(..., alias="currentBonus")
    current_balance: int = Field(..., alias="currentBalance")
    notification: str
    balance: int
    barcode: str
    bonus_amount: int = Field(..., alias="bonusAmount")
    vouchers_amount: int = Field(..., alias="vouchersAmount")
    spawn_next_coupon_date: str = Field(..., alias="spawnNextCouponDate")


class Cheque(SilpoBaseModel):
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


class ChequeReward(SilpoBaseModel):
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


class ChequePosition(SilpoBaseModel):
    cheque_line_id: int = Field(..., alias="chequeLineId")
    lager_id: int = Field(..., alias="lagerId")
    lager_name_ua: str = Field(..., alias="lagerNameUA")
    lager_unit: str = Field(..., alias="lagerUnit")
    count: float = Field(..., alias="kolvo")
    price_out: float = Field(..., alias="priceOut")
    unit_text: str = Field(..., alias="unitText")
    image_url: str = Field(..., alias="imageUrl")

    class Meta:
        alternative_name = "chequeLines"


class CashbackPosition(SilpoBaseModel):
    cheque_line_id: int = Field(..., alias="chequeLineId")
    cashback_sum: float = Field(..., alias="cashbackSum")
    competitor_name: str = Field(..., alias="competitorName")
    competitor_price: float = Field(..., alias="competitorPrice")
    silpo_price: float = Field(..., alias="silpoPrice")
    detection_date: datetime = Field(..., alias="detectionDate")

    class Meta:
        alternative_name = "cashbackLines"


class ChequeCashback(SilpoBaseModel):
    sum_cashback: float = Field(..., alias="sumCashback")
    city: str
    positions: List[CashbackPosition] = Field(..., alias="cashbackLines")

    class Meta:
        alternative_name = "cashback"


class ChequeDetail(SilpoBaseModel):
    loyalty_fact_id: int = Field(..., alias="loyaltyFactId")
    filial_id: int = Field(..., alias="filId")
    created: datetime = Field(..., alias="created")
    sum_discount: float = Field(..., alias="sumDiscount")
    pay_type: PayTypeEnum = Field(..., alias="payType")
    ch_prediction: str = Field(..., alias="chPrediction")
    rewards: Optional[List[ChequeReward]] = Field(..., alias="chequeRewards")
    positions: Optional[List[ChequePosition]] = Field(..., alias="chequeLines")
    cashback: Optional[ChequeCashback] = Field(..., alias="cashback")
