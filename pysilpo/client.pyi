from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, NamedTuple

from models import SilpoBaseModel

class QueryBuilder:
    def __init__(self):
        self.query = ""
        self.variables = {}
        self._mapping = {}
    def fetch_me(self) -> QueryBuilder: ...
    def fetch_cheques(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10000,
        offset: int = 1,
    ) -> QueryBuilder: ...
    def fetch_cheque(
        self, filial_id: int, created_at: datetime, loyalty_fact_id: int
    ) -> QueryBuilder: ...
    def get_query(self) -> Dict[str, Any]: ...
    @property
    def mapping(self) -> Dict[str, SilpoBaseModel]: ...
    def get(self) -> NamedTuple: ...

class APIClientMeta(type):
    def __getattr__(cls, name) -> QueryBuilder: ...

class APIClient(metaclass=APIClientMeta):
    @classmethod
    def get(cls, builder: QueryBuilder) -> NamedTuple: ...
    @classmethod
    def _parse(cls, mapping, data) -> NamedTuple: ...
    @classmethod
    def fetch_me(cls) -> QueryBuilder: ...
    @classmethod
    def fetch_cheques(
        cls,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10000,
        offset: int = 1,
    ) -> QueryBuilder: ...
    @classmethod
    def fetch_cheque(
        cls, filial_id: int, created_at: datetime, loyalty_fact_id: int
    ) -> QueryBuilder: ...
