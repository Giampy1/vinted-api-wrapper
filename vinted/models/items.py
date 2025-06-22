from .base import VintedResponse
from .money import CurrencyAmount, Conversion, MethodPay, Price
from .photos import PhotoHighResolution, PhotoThumbnail
from .users import UserPhoto, ItemUser
from dataclasses import dataclass
from typing import List, Any, Optional
from numbers import Number


@dataclass
class User:
    id: int
    login: str
    profile_url: str
    photo: Optional[UserPhoto]
    business: bool


@dataclass
class BrandDto:
    id: int
    title: Optional[str]
    slug: Optional[str]
    favourite_count: int
    pretty_favourite_count: Optional[str]
    item_count: int
    pretty_item_count: Optional[str]
    is_visible_in_listings: bool
    requires_authenticity_check: bool
    is_luxury: bool
    is_hvf: bool
    path: Optional[str]
    url: Optional[str]
    is_favourite: bool


@dataclass
class BrandDtoShort:
    id: int
    title: Optional[str]
    slug: Optional[str]
    path: Optional[str]
    is_favourite: bool


@dataclass
class ItemBox:
    first_line: Optional[str]
    second_line: Optional[str]


@dataclass
class SearchParams:
    score: Optional[Number]
    matched_queries: Any


@dataclass
class ItemPhoto:
    id: int
    image_no: int
    width: int
    height: int
    dominant_color: Optional[str]
    dominant_color_opaque: Optional[str]
    url: Optional[str]
    is_main: bool
    thumbnails: List[PhotoThumbnail]
    high_resolution: PhotoHighResolution
    is_suspicious: bool
    full_size_url: Optional[str]
    is_hidden: bool
    extra: Any


@dataclass
class Item:
    id: int
    title: str
    price: Optional[Price | str]
    is_visible: bool
    discount: Optional[Any]
    brand_title: Optional[str]
    user: User
    url: str
    promoted: bool
    photo: ItemPhoto
    favourite_count: int
    is_favourite: bool
    badge: Optional[Any]
    conversion: Optional[Conversion]
    service_fee: Optional[CurrencyAmount | str]
    total_item_price: Optional[CurrencyAmount | str]
    view_count: int
    size_title: Optional[str]
    content_source: Optional[str]
    status: str
    icon_badges: List[any]
    item_box: Optional[ItemBox]
    search_tracking_params: Optional[SearchParams]


@dataclass
class ItemAttribute:
    code: Optional[str]
    ids: List[int]


@dataclass
class DescriptionAttribute:
    code: Optional[str]
    title: Optional[str]
    value: Optional[str]
    faq_id: Any


@dataclass
class ItemAlert:
    # TODO: Define structure
    pass


@dataclass
class DetailedItem:
    id: int
    title: str
    description: Optional[str]
    status_id: int
    disposal_conditions: int
    catalog_id: int
    is_hidden: bool
    is_hidden_with_item_restrictions: bool
    is_reserved: bool
    is_closed: bool
    is_draft: bool
    is_processing: bool
    item_closing_action: Optional[Any]
    currency: str
    photos: List[ItemPhoto]
    price: str
    transaction_permitted: bool
    transaction_permitted_with_item_restrictions: bool
    reservation: Optional[Any]
    offline_verification: bool
    offer_price: Optional[str]
    conversion: Optional[Conversion]
    is_cross_currency_payment: bool
    favourite_count: int
    is_favourite: bool
    view_count: int
    user: ItemUser
    can_edit: bool
    can_delete: bool
    can_reserve: bool
    instant_buy: bool
    can_buy: bool
    can_bundle: bool
    promoted: bool
    brand_dto: Optional[BrandDtoShort]
    path: str
    url: str
    color1: Optional[Any]
    status: str
    localization: str
    item_alert: Optional[ItemAlert]
    service_fee: str
    offline_verification_fee: Optional[str]
    total_item_price: str
    can_push_up: bool
    stats_visible: bool


@dataclass
class ItemsResponse(VintedResponse):
    item: DetailedItem
    plugins: Optional[List[Any]]  # TODO: Define a proper type for plugins


@dataclass
class UserItemsResponse(VintedResponse):
    drafts: Optional[List[DetailedItem]]
    items: List[DetailedItem]
