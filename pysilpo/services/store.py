import json
import random
import string
from typing import Optional
from urllib.parse import urljoin

import requests
from cryptography.utils import cached_property
from pydantic import BaseModel, Field, PrivateAttr

from pysilpo.utils.cursor import Cursor
from pysilpo.utils.exceptions import SilpoRequestException

_GRAPHQL_API_URL = "https://graphql.silpo.ua/graphql"


class CityModel(BaseModel):
    _stores: Cursor["StoreModel"] = PrivateAttr(None)
    id: str
    title: str
    slug: str

    def __init__(self, **data):
        super().__init__(**data)
        stores = data.pop("storeFilterable", None)
        if stores is not None:
            stores = [StoreModel(**x) for x in stores]
            self._stores = Cursor(generator=lambda _offset: (stores, len(stores)), page_size=len(stores))

    @cached_property
    def stores(self) -> Cursor["StoreModel"]:
        if not self._stores:
            self._stores = Store.all(city_id=self.id)
        return self._stores


class StoreModel(BaseModel):
    def __init__(self, **data):
        super().__init__(**data)
        filial_id = data.get("filial_id")
        if filial_id is not None:
            self.filial_id = filial_id

    id: str = Field(..., alias="id")
    images: list[dict] = Field(..., alias="images")
    electricity_state: int = Field(..., alias="electricityState")
    is_designed: bool = Field(..., alias="isDesigned")
    is_lesilpo: bool = Field(..., alias="isLesilpo")
    filial_id: Optional[int] = Field(None, alias="filialId")
    link: Optional[str] = Field(None, alias="link")
    title: str = Field(..., alias="title")
    premium: bool = Field(..., alias="premium")
    map_link: Optional[str] = Field(None, alias="mapLink")
    slug: str = Field(..., alias="slug")
    active: bool = Field(..., alias="active")
    cache_amount: int = Field(..., alias="cacheAmount")
    terminal_enabled: bool = Field(..., alias="terminalEnabled")
    with_generator: bool = Field(..., alias="withGenerator")
    with_wifi: bool = Field(..., alias="withWifi")
    with_starlink: bool = Field(..., alias="withStarlink")
    active_hours: dict = Field(..., alias="activeHours")
    filial_type: str = Field(..., alias="filialType")
    location: dict = Field(..., alias="location")
    city: CityModel
    updated_at: Optional[str] = Field(None, alias="updatedAt")

    @cached_property
    def branch_id(self) -> Optional[str]:
        try:
            if self.filial_id is None:
                return None
            return Store.get_branch_id(self.filial_id)[0].branch_id
        except IndexError:
            raise SilpoRequestException(f"Branch not found for filial_id: {self.filial_id}") from None


class FilialModel(BaseModel):
    branch_id: str = Field(..., alias="branchId")
    company_id: str = Field(..., alias="companyId")
    filial_id: str = Field(..., alias="filialId")


class Store:
    _BASE_RESTFUL_DOMAIN = "https://sf-ecom-api.silpo.ua"

    _GET_BRANCH_BY_FILIAL_ID_URL = urljoin(_BASE_RESTFUL_DOMAIN, "/v1/branches/by-filial-ids")

    _ALL_STORES_QUERY = """query stores($filter: StoreFilterInputType, $pagingInfo: InputBatch!) {
      stores(filter: $filter, pagingInfo: $pagingInfo) {
        limit
        offset
        count
        items {
          ...StoreBaseFragment
          updatedAt
          __typename
        }
        __typename
      }
    }

    fragment StoreBaseFragment on Store {
      id
      images {
        image {
          url
          __typename
        }
        __typename
      }
      electricityState
      isDesigned
      isLesilpo
      filial_id
      link
      title
      premium
      mapLink
      slug
      active
      cacheAmount
      terminalEnabled
      withGenerator
      withWifi
      withStarlink
      activeHours {
        start
        end
        __typename
      }
      filialType
      location {
        ...LocationBaseFragment
        __typename
      }
      city {
        ...CityBaseFragment
        __typename
      }
      __typename
    }

    fragment CityBaseFragment on City {
      id
      title
      slug
      __typename
    }

    fragment LocationBaseFragment on Location {
      lat
      lng
      __typename
    }"""

    @classmethod
    def all(cls, city_id: Optional[str] = None) -> Cursor[StoreModel]:
        form_data = {
            "query": cls._ALL_STORES_QUERY,
            "variables": {
                "filter": {
                    "filialId": None,
                    "cityId": city_id,
                    "start": None,
                    "end": None,
                    "hasCertificate": None,
                    "servicesIds": None,
                },
                "pagingInfo": {"limit": 400, "offset": 0},
            },
            "operationName": "stores",
        }

        # Custom boundary string
        boundary = "----WebKitFormBoundary" + "".join(random.choices(string.ascii_letters + string.digits, k=16))  # noqa: S311

        # Create the multipart form data manually
        body_parts = []
        for key, value in form_data.items():
            # Handle JSON fields as text
            if isinstance(value, dict):
                value = json.dumps(value)

            body_parts.append(
                f"--{boundary}\r\n" f'Content-Disposition: form-data; name="{key}"\r\n\r\n' f"{value}\r\n"
            )

        # Join all the parts with boundary and include the final boundary
        body = "".join(body_parts) + f"--{boundary}--\r\n"

        # Set headers with the custom boundary
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}

        def generator(_offset: int):
            # Update the offset for pagination
            form_data["variables"]["pagingInfo"]["offset"] = _offset

            # Send the POST request
            resp = requests.post(_GRAPHQL_API_URL, headers=headers, data=body)

            if not resp.ok:
                raise SilpoRequestException(f"Failed to fetch stores: {resp.text}")

            # Extract relevant data from the response
            data = resp.json()["data"]["stores"]
            return [StoreModel(**x) for x in data["items"]], data["count"]

        return Cursor(generator=generator, page_size=form_data["variables"]["pagingInfo"]["limit"])

    @classmethod
    def get_branch_id(cls, *filial_ids: int) -> list[FilialModel]:
        resp = requests.get(cls._GET_BRANCH_BY_FILIAL_ID_URL, params={"filialIds[]": filial_ids})
        resp.raise_for_status()
        return [FilialModel(**item) for item in resp.json()["items"]]


class City:
    _CITY_QUERY = """query cityWithStores($slug: String) {
          city(slug: $slug) {
            ...CityBaseFragment
            storeFilterable {
              ...StoreBaseFragment
              __typename
            }
            __typename
          }
        }

        fragment StoreBaseFragment on Store {
          id
          images {
            image {
              url
              __typename
            }
            __typename
          }
          electricityState
          isDesigned
          isLesilpo
          filial_id
          link
          title
          premium
          mapLink
          slug
          active
          cacheAmount
          terminalEnabled
          withGenerator
          withWifi
          withStarlink
          activeHours {
            start
            end
            __typename
          }
          filialType
          location {
            ...LocationBaseFragment
            __typename
          }
          city {
            ...CityBaseFragment
            __typename
          }
          __typename
        }

        fragment CityBaseFragment on City {
          id
          title
          slug
          __typename
        }

        fragment LocationBaseFragment on Location {
          lat
          lng
          __typename
        }"""

    @classmethod
    def get(cls, slug: str) -> CityModel:
        resp = requests.post(
            _GRAPHQL_API_URL,
            json={
                "query": cls._CITY_QUERY,
                "variables": {"slug": slug},
                "operationName": "cityWithStores",
            },
        )
        resp.raise_for_status()
        data = resp.json()["data"]["city"]
        return CityModel(**data) if data else None
