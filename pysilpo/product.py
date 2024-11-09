from enum import Enum
from typing import Literal, Optional
from urllib.parse import urljoin

import requests
from cryptography.utils import cached_property
from pydantic import BaseModel, Field

from pysilpo.utils import Cursor


class SortBy(str, Enum):
    POPULARITY = "popularity"
    PROMOTION = "promotion"
    RATING = "rating"
    NAME = "name"
    PRICE = "price"
    PRODUCTS_LIST = "productsList"


class ProductModel(BaseModel):
    id: str = Field(..., alias="id")
    title: str = Field(..., alias="title")
    icon: str = Field(..., alias="icon")
    price: float = Field(..., alias="price")
    old_price: Optional[float] = Field(None, alias="oldPrice")
    offer_id: str = Field(..., alias="offerId")
    ratio: str = Field(..., alias="ratio")
    section_slug: str = Field(..., alias="sectionSlug")
    company_id: str = Field(..., alias="companyId")
    branch_id: str = Field(..., alias="branchId")
    external_product_id: int = Field(..., alias="externalProductId")
    promotions: list[dict] = Field(..., alias="promotions")
    special_prices: list[dict] = Field(..., alias="specialPrices")
    created_at: str = Field(..., alias="createdAt")
    slug: str = Field(..., alias="slug")
    add_to_basket_step: float = Field(..., alias="addToBasketStep")
    stock: float = Field(..., alias="stock")
    display_price: float = Field(..., alias="displayPrice")
    display_old_price: Optional[float] = Field(None, alias="displayOldPrice")
    display_ratio: str = Field(..., alias="displayRatio")
    guest_product_rating: Optional[float] = Field(None, alias="guestProductRating")
    guest_product_rating_count: Optional[int] = Field(None, alias="guestProductRatingCount")
    classifier_sap_id: Optional[str] = Field(None, alias="classifierSapId")
    origin_type: Optional[str] = Field(None, alias="originType")
    brand_id: Optional[str] = Field(None, alias="brandId")
    brand_title: Optional[str] = Field(None, alias="brandTitle")
    weighted: bool = Field(..., alias="weighted")
    blur_for_under_aged: bool = Field(..., alias="blurForUnderAged")


class CategoryModel(BaseModel):
    id: str = Field(..., alias="id")
    slug: str = Field(..., alias="slug")
    parent_id: Optional[str] = Field(None, alias="parentId")
    title: str = Field(..., alias="title")
    media: dict = Field(..., alias="media")
    tile_size: dict = Field(..., alias="tileSize")
    order: int = Field(..., alias="order")
    visibility: bool = Field(..., alias="visibility")
    updated_at: str = Field(..., alias="updatedAt")

    @cached_property
    def products(self) -> Cursor[ProductModel]:
        return Product.all(category_slug=self.slug, include_child_categories=False)


class Product:
    _DOMAIN = "https://sf-ecom-api.silpo.ua"
    _PRODUCTS_URL = urljoin(_DOMAIN, "/v1/uk/branches/{branch_id}/products")
    _CATEGORIES_URL = urljoin(_DOMAIN, "/v1/uk/branches/{branch_id}/categories")

    _DEFAULT_BRANCH_ID = "00000000-0000-0000-0000-000000000000"

    @classmethod
    def categories(cls, branch_id=_DEFAULT_BRANCH_ID) -> Cursor[CategoryModel]:
        full_url = cls._CATEGORIES_URL.format(branch_id=branch_id)

        def generator(_offset: int):
            resp = requests.get(full_url, params={"limit": 1000, "offset": _offset})
            resp.raise_for_status()
            data = resp.json()
            return [CategoryModel(**category) for category in data["items"]], data["total"]

        return Cursor[CategoryModel](generator=generator, page_size=1000)

    @classmethod
    def all(
        cls,
        branch_id=_DEFAULT_BRANCH_ID,
        category_slug: Optional[str] = None,
        search: Optional[str] = None,
        include_child_categories: bool = True,
        sort_by: SortBy = SortBy.POPULARITY,
        sort_direction: Literal["desc", "asc"] = "desc",
        delivery_type: Optional[
            Literal["DeliveryHome", "LongDelivery", "SelfPickup", "DeliveryExpressByPromise"]
        ] = None,
        in_stock: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Cursor[ProductModel]:
        """
        Get all products from the branch

        :param branch_id: Branch where to get products from
        :param category_slug: You can get category slug from get_categories method
        :param search: Search query
        :param include_child_categories: Do you want to include child categories of the category_slug
        :param sort_by: SortBy enum
        :param sort_direction: asc (A-Z) or desc (Z-A)
        :param delivery_type: Delivery type
        :param in_stock: Get only in stock products
        :param limit: How many products to get per request
        :param offset: How many products to skip
        :return:
        """
        # TODO: Add support for other query parameters, e.g. get data by products, productsIds, productsSlugs,
        #  category, set, mustHavePromotion, search, offersIds, isFavorite, isCarousel; Filter by etc.
        full_url = cls._PRODUCTS_URL.format(branch_id=branch_id)
        query_params = {
            "limit": limit,
            "offset": offset,
            "category": category_slug,
            "includeChildCategories": include_child_categories,
            "sortBy": sort_by,
            "sortDirection": sort_direction,
            "inStock": in_stock,
        }
        if delivery_type:
            query_params["deliveryType"] = delivery_type
        if search:
            query_params["search"] = search

        def generator(_offset: int):
            query_params["offset"] = _offset
            resp = requests.get(full_url, params=query_params)
            resp.raise_for_status()
            data = resp.json()
            return [ProductModel(**product) for product in data["items"]], data["total"]

        return Cursor(generator=generator, page_size=limit)

    @classmethod
    def search(
        cls,
        search: str,
        branch_id=_DEFAULT_BRANCH_ID,
        **kwargs,
    ) -> Cursor[ProductModel]:
        """
        Search for products

        :param search: Search query
        :param branch_id: Branch where to search products
        :param kwargs: Other query parameters from Product.all(...)
        :return:
        """
        return cls.all(branch_id=branch_id, search=search, sort_by=SortBy.PRODUCTS_LIST, **kwargs)
