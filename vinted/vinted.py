import logging
import time
from copy import deepcopy
from typing import List, Literal
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from dacite import from_dict

from .endpoints import Endpoints
from .models.base import VintedResponse
from .models.filters import Catalog, FiltersResponse, InitializersResponse
from .models.items import ItemsResponse, UserItemsResponse
from .models.other import Domain, SortOption
from .models.search import SearchResponse, SearchSuggestionsResponse, UserSearchResponse
from .models.users import (
    UserFeedbacksResponse,
    UserFeedbacksSummaryResponse,
    UserResponse,
)
from .utils import parse_url_to_params

# Set up logging - datetime format, level, and format
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


class Vinted:
    def __init__(self, domain: Domain = "pl", proxy: str = None) -> None:
        self.proxy = None
        if proxy:
            self.proxy = {"http": proxy, "https": proxy}
        self.base_url = f"https://www.vinted.{domain}"
        self.api_url = f"{self.base_url}/api/v2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        self.cookies = self.fetch_cookies()

    def fetch_cookies(self):
        response = requests.get(self.base_url, headers=self.headers, proxies=self.proxy)
        return response.cookies

    def _call(self, method: Literal["get"], *args, **kwargs):
        if params := kwargs.pop("params", {}):
            updated_params = deepcopy(params)

            # Replace None values with empty strings
            processed_params = {
                k: "" if v is None else v for k, v in updated_params.items()
            }

            # Encode parameters with '+' left untouched
            encoded_params = urlencode(processed_params, safe="+")

            # Assign updated params directly to the url as string
            updated_url = kwargs.get("url")
            updated_url = urlunparse(
                urlparse(updated_url)._replace(query=encoded_params)
            )
            kwargs["url"] = updated_url

        if "recursive" in kwargs:
            del kwargs["recursive"]

        return requests.request(
            method=method,
            headers=self.headers,
            cookies=self.cookies,
            proxies=self.proxy,
            *args,
            **kwargs,
        )

    def _get(
        self,
        endpoint: Endpoints,
        response_model: VintedResponse,
        format_values=None,
        wanted_status_code: int = 200,
        *args,
        **kwargs,
    ):
        if format_values:
            url = self.api_url + endpoint.value.format(format_values)
        else:
            url = self.api_url + endpoint.value
        response = self._call(method="get", url=url, *args, **kwargs)
        if response.status_code != wanted_status_code and not kwargs.get("recursive"):
            self.fetch_cookies()
            return self._get(
                endpoint=endpoint,
                response_model=response_model,
                format_values=format_values,
                wanted_status_code=wanted_status_code,
                recursive=True,
                *args,
                **kwargs,
            )
        try:
            json_response = response.json()
            return from_dict(response_model, json_response)
        except requests.exceptions.JSONDecodeError:
            return {"error": f"HTTP {response.status_code}"}

    def search(
        self,
        url: str = None,
        page: int = 1,
        per_page: int = 96,
        query: str = None,
        price_from: float = None,
        price_to: float = None,
        order: SortOption = "newest_first",
        catalog_ids: int | List[int] = None,
        size_ids: int | List[int] = None,
        brand_ids: int | List[int] = None,
        status_ids: int | List[int] = None,
        color_ids: int | List[int] = None,
        patterns_ids: int | List[int] = None,
        material_ids: int | List[int] = None,
        video_game_platform_ids: int | List[int] = None,
        country_ids: str | List[str] = None,
    ) -> SearchResponse:
        params = {
            "page": page,
            "per_page": per_page,
            "time": time.time(),
            "search_text": query,
            "price_from": price_from,
            "price_to": price_to,
            "catalog_ids": catalog_ids,
            "order": order,
            "size_ids": size_ids,
            "brand_ids": brand_ids,
            "status_ids": status_ids,
            "color_ids": color_ids,
            "patterns_ids": patterns_ids,
            "material_ids": material_ids,
            "video_game_platform_ids": video_game_platform_ids,
            "country_ids": country_ids,
        }
        if url:
            params.update(parse_url_to_params(url))

        return self._get(Endpoints.CATALOG_ITEMS, SearchResponse, params=params)

    def search_users(
        self, query: str, page: int = 1, per_page: int = 36
    ) -> UserSearchResponse:
        params = {"page": page, "per_page": per_page, "search_text": query}
        return self._get(Endpoints.USERS, UserSearchResponse, params=params)

    def item_info(self, item_id: int) -> ItemsResponse:
        return self._get(Endpoints.ITEMS, ItemsResponse, item_id)

    def user_info(self, user_id: int, localize: bool = False) -> UserResponse:
        params = {"localize": localize}
        return self._get(
            Endpoints.USER, UserResponse, user_id, params=params
        )  # this raises 'dacite.exceptions.MissingValueError: missing value for field "user"' for non valid user id

    def user_items(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 96,
        order: SortOption = "newest_first",
    ) -> UserItemsResponse:
        params = {"page": page, "per_page": per_page, "order": order}
        return self._get(
            Endpoints.USER_ITEMS, UserItemsResponse, user_id, params=params
        )

    def user_feedbacks(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        by: Literal["all", "user", "system"] = "all",
    ) -> UserFeedbacksResponse:
        params = {"user_id": user_id, "page": page, "per_page": per_page, "by": by}
        return self._get(Endpoints.USER_FEEDBACKS, UserFeedbacksResponse, params=params)

    def user_feedbacks_summary(
        self,
        user_id: int,
    ) -> UserFeedbacksSummaryResponse:
        params = {"user_id": user_id}
        return self._get(
            Endpoints.USER_FEEDBACKS_SUMMARY,
            UserFeedbacksSummaryResponse,
            params=params,
        )

    def search_suggestions(self, query: str) -> SearchSuggestionsResponse:
        return self._get(
            Endpoints.SEARCH_SUGGESTIONS,
            SearchSuggestionsResponse,
            params={"query": query},
        )

    def catalog_filters(
        self,
        query: str = None,
        catalog_ids: int = None,
        brand_ids: int | List[int] = None,
        status_ids: int | List[int] = None,
        color_ids: int | List[int] = None,
    ) -> FiltersResponse:
        params = {
            "search_text": query,
            "catalog_ids": catalog_ids,
            "time": time.time(),
            "brand_ids": brand_ids,
            "status_ids": status_ids,
            "color_ids": color_ids,
        }
        return self._get(Endpoints.CATALOG_FILTERS, FiltersResponse, params=params)

    def catalogs_list(self) -> List[Catalog]:
        data: InitializersResponse = self._get(
            Endpoints.CATALOG_INITIALIZERS,
            InitializersResponse,
            params={"page": 1, "time": time.time()},
        )
        return data.dtos.catalogs

    def fetch_offer_description(self, url: str) -> str:
        """
        Fetches the offer description from a given Vinted item URL.
        :param url: The URL of the Vinted item.
        :return: The description of the item.
        """
        try:
            response = requests.get(
                url, headers=self.headers, proxies=self.proxy, cookies=self.cookies
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                description = soup.find("div", {"itemprop": "description"})
                if description:
                    return description.get_text(strip=True)
                else:
                    logger.error("Description not found in the page.")
                    return None
            else:
                logger.error(f"Error fetching description: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"An error occurred while fetching the description: {e}")
            return None
