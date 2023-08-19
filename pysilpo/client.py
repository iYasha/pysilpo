import os
from collections import namedtuple
from datetime import datetime
from typing import Any, Dict

import requests
from pysilpo.models import User, Cheque, ChequeDetail, SilpoBaseModel
import pysilpo


class QueryBuilder:
    def __init__(self):
        self.query = ""
        self.variables = {}
        self._mapping = {}

    def fetch_me(self) -> "QueryBuilder":
        self.query += (
            """
        query me {
            me {
                %s
            }
        }
        """
            % User.to_graphql()
        )
        self._mapping.update(
            {
                "me": User,
            }
        )
        return self

    def fetch_cheques(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10000,
        offset: int = 1,
    ) -> "QueryBuilder":
        self.query += (
            """
        query cheques($offset: Int, $limit: Int, $dateFrom: DateTime, $dateTo: DateTime) {
          cheques(offset: $offset, limit: $limit, dateFrom: $dateFrom, dateTo: $dateTo) {
            %s
          }
        }
        """
            % Cheque.to_graphql()
        )
        self.variables.update(
            {
                "offset": offset,
                "limit": limit,
                "dateFrom": date_from.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "dateTo": date_to.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            }
        )
        self._mapping.update(
            {
                "cheques": Cheque,
            }
        )
        return self

    def fetch_cheque(
        self, filial_id: int, created_at: datetime, loyalty_fact_id: int
    ) -> "QueryBuilder":
        self.query += (
            """
        query cheque($filialId: ID!, $creationDate: DateTime!, $loyaltyFactId: ID!) {
          cheque(
            filialId: $filialId
            creationDate: $creationDate
            loyaltyFactId: $loyaltyFactId
          ) {
            %s
          }
        }
        """
            % ChequeDetail.to_graphql()
        )
        self.variables.update(
            {
                "filialId": filial_id,
                "creationDate": created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "loyaltyFactId": loyalty_fact_id,
            }
        )
        self._mapping.update(
            {
                "cheque": ChequeDetail,
            }
        )
        return self

    def get_query(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "variables": self.variables,
        }

    @property
    def mapping(self) -> Dict[str, SilpoBaseModel]:
        return self._mapping

    def get(self):
        return APIClient.get(self)


class APIClientMeta(type):
    def __getattr__(cls, name) -> QueryBuilder:
        if name in QueryBuilder.__dict__:
            return getattr(QueryBuilder(), name)


class APIClient(metaclass=APIClientMeta):
    @classmethod
    def get(cls, builder: QueryBuilder):
        access_token = pysilpo.api_key or os.getenv("SILPO_ACCESS_TOKEN")
        assert access_token, "SILPO_ACCESS_TOKEN env variable is not set"
        response = requests.post(
            pysilpo.api_base,
            json=builder.get_query(),
            headers={
                "Access-Token": access_token,
            },
        )
        content = response.json()
        if "errors" in content:
            raise Exception(content["errors"])
        return cls._parse(builder.mapping, content["data"])

    @classmethod
    def _parse(cls, mapping, data):
        result = {}
        for key, value in data.items():
            if key in mapping:
                model = mapping[key]
                if isinstance(value, list):
                    result[key] = [model(**item) for item in value]
                else:
                    result[key] = model(**value)
            else:
                result[key] = value
        return namedtuple("Response", result.keys())(*result.values())
