import logging
import time
from copy import deepcopy
from typing import List, Literal
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from dacite import from_dict

from .exceptions import RateLimitExceededException
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
        logger.info(f"Initializing Vinted client with domain: {domain}, proxy: {'enabled' if proxy else 'disabled'}")
        
        self.proxy = None
        if proxy:
            self.proxy = {"http": proxy, "https": proxy}
            logger.debug(f"Proxy configuration set: {self.proxy}")
        
        self.base_url = f"https://www.vinted.{domain}"
        self.api_url = f"{self.base_url}/api/v2"
        logger.debug(f"Base URL: {self.base_url}, API URL: {self.api_url}")
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        logger.debug(f"Headers configured: {self.headers}")
        
        self.cookies = self.fetch_cookies()
        logger.info("Vinted client initialization completed successfully")

    def fetch_cookies(self):
        logger.debug(f"Fetching cookies from: {self.base_url}")
        response = requests.get(self.base_url, headers=self.headers, proxies=self.proxy)
        logger.info(f"Cookies fetched successfully, status code: {response.status_code}")
        logger.debug(f"Cookies: {response.cookies}")
        return response.cookies

    def _call(self, method: Literal["get"], *args, **kwargs):
        logger.debug(f"Making {method.upper()} request with args: {args}, kwargs: {kwargs}")
        
        if params := kwargs.pop("params", {}):
            logger.debug(f"Processing parameters: {params}")
            updated_params = deepcopy(params)

            # Replace None values with empty strings
            processed_params = {
                k: "" if v is None else v for k, v in updated_params.items()
            }
            logger.debug(f"Processed parameters (None -> empty string): {processed_params}")

            # Encode parameters with '+' left untouched
            encoded_params = urlencode(processed_params, safe="+")
            logger.debug(f"Encoded parameters: {encoded_params}")

            # Assign updated params directly to the url as string
            updated_url = kwargs.get("url")
            updated_url = urlunparse(
                urlparse(updated_url)._replace(query=encoded_params)
            )
            kwargs["url"] = updated_url
            logger.debug(f"Final URL with parameters: {updated_url}")

        if "recursive" in kwargs:
            del kwargs["recursive"]

        logger.info(f"Executing {method.upper()} request to: {kwargs.get('url', 'unknown URL')}")
        response = requests.request(
            method=method,
            headers=self.headers,
            cookies=self.cookies,
            proxies=self.proxy,
            *args,
            **kwargs,
        )
        logger.info(f"Request completed with status code: {response.status_code}")
        if response.status_code == 429:
            raise RateLimitExceededException(
                "Rate limit exceeded. Please try again later."
            )
        return response

    def _get(
        self,
        endpoint: Endpoints,
        response_model: VintedResponse,
        format_values=None,
        wanted_status_code: int = 200,
        *args,
        **kwargs,
    ):
        logger.debug(f"GET request to endpoint: {endpoint.value}, format_values: {format_values}, expected status: {wanted_status_code}")
        
        if format_values:
            url = self.api_url + endpoint.value.format(format_values)
            logger.debug(f"Formatted endpoint URL: {url}")
        else:
            url = self.api_url + endpoint.value
            logger.debug(f"Standard endpoint URL: {url}")
            
        response = self._call(method="get", url=url, *args, **kwargs)
        
        if response.status_code != wanted_status_code and not kwargs.get("recursive"):
            logger.info(f"Status code {response.status_code} != expected {wanted_status_code}, refreshing cookies and retrying")
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
            logger.debug(f"Successfully parsed JSON response from {endpoint.value}")
            result = from_dict(response_model, json_response)
            logger.info(f"Successfully converted response to {response_model.__name__}")
            return result
        except requests.exceptions.JSONDecodeError:
            error_msg = f"HTTP {response.status_code}"
            logger.error(f"JSON decode error for {endpoint.value}: {error_msg}")
            return {"error": error_msg}

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
        logger.info(f"Starting search - query: '{query}', page: {page}, per_page: {per_page}, order: {order}")
        logger.debug(f"Search filters - price_from: {price_from}, price_to: {price_to}, catalog_ids: {catalog_ids}")
        logger.debug(f"Additional filters - size_ids: {size_ids}, brand_ids: {brand_ids}, status_ids: {status_ids}")
        logger.debug(f"More filters - color_ids: {color_ids}, patterns_ids: {patterns_ids}, material_ids: {material_ids}")
        logger.debug(f"Platform/country filters - video_game_platform_ids: {video_game_platform_ids}, country_ids: {country_ids}")
        
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
            logger.debug(f"Parsing additional parameters from URL: {url}")
            params.update(parse_url_to_params(url))

        logger.debug(f"Final search parameters: {params}")
        result = self._get(Endpoints.CATALOG_ITEMS, SearchResponse, params=params)
        logger.info("Search completed successfully")
        return result

    def search_users(
        self, query: str, page: int = 1, per_page: int = 36
    ) -> UserSearchResponse:
        logger.info(f"Searching users with query: '{query}', page: {page}, per_page: {per_page}")
        params = {"page": page, "per_page": per_page, "search_text": query}
        logger.debug(f"User search parameters: {params}")
        result = self._get(Endpoints.USERS, UserSearchResponse, params=params)
        logger.info("User search completed successfully")
        return result

    def item_info(self, item_id: int) -> ItemsResponse:
        logger.info(f"Fetching item info for item_id: {item_id}")
        result = self._get(Endpoints.ITEMS, ItemsResponse, item_id)
        logger.info(f"Item info retrieved successfully for item_id: {item_id}")
        return result

    def user_info(self, user_id: int, localize: bool = False) -> UserResponse:
        logger.info(f"Fetching user info for user_id: {user_id}, localize: {localize}")
        params = {"localize": localize}
        logger.debug(f"User info parameters: {params}")
        result = self._get(
            Endpoints.USER, UserResponse, user_id, params=params
        )  # this raises 'dacite.exceptions.MissingValueError: missing value for field "user"' for non valid user id
        logger.info(f"User info retrieved successfully for user_id: {user_id}")
        return result

    def user_items(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 96,
        order: SortOption = "newest_first",
    ) -> UserItemsResponse:
        logger.info(f"Fetching user items for user_id: {user_id}, page: {page}, per_page: {per_page}, order: {order}")
        params = {"page": page, "per_page": per_page, "order": order}
        logger.debug(f"User items parameters: {params}")
        result = self._get(
            Endpoints.USER_ITEMS, UserItemsResponse, user_id, params=params
        )
        logger.info(f"User items retrieved successfully for user_id: {user_id}")
        return result

    def user_feedbacks(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        by: Literal["all", "user", "system"] = "all",
    ) -> UserFeedbacksResponse:
        logger.info(f"Fetching user feedbacks for user_id: {user_id}, page: {page}, per_page: {per_page}, by: {by}")
        params = {"user_id": user_id, "page": page, "per_page": per_page, "by": by}
        logger.debug(f"User feedbacks parameters: {params}")
        result = self._get(Endpoints.USER_FEEDBACKS, UserFeedbacksResponse, params=params)
        logger.info(f"User feedbacks retrieved successfully for user_id: {user_id}")
        return result

    def user_feedbacks_summary(
        self,
        user_id: int,
    ) -> UserFeedbacksSummaryResponse:
        logger.info(f"Fetching user feedbacks summary for user_id: {user_id}")
        params = {"user_id": user_id}
        logger.debug(f"User feedbacks summary parameters: {params}")
        result = self._get(
            Endpoints.USER_FEEDBACKS_SUMMARY,
            UserFeedbacksSummaryResponse,
            params=params,
        )
        logger.info(f"User feedbacks summary retrieved successfully for user_id: {user_id}")
        return result

    def search_suggestions(self, query: str) -> SearchSuggestionsResponse:
        logger.info(f"Fetching search suggestions for query: '{query}'")
        result = self._get(
            Endpoints.SEARCH_SUGGESTIONS,
            SearchSuggestionsResponse,
            params={"query": query},
        )
        logger.info("Search suggestions retrieved successfully")
        return result

    def catalog_filters(
        self,
        query: str = None,
        catalog_ids: int = None,
        brand_ids: int | List[int] = None,
        status_ids: int | List[int] = None,
        color_ids: int | List[int] = None,
    ) -> FiltersResponse:
        logger.info(f"Fetching catalog filters - query: '{query}', catalog_ids: {catalog_ids}")
        logger.debug(f"Filter parameters - brand_ids: {brand_ids}, status_ids: {status_ids}, color_ids: {color_ids}")
        params = {
            "search_text": query,
            "catalog_ids": catalog_ids,
            "time": time.time(),
            "brand_ids": brand_ids,
            "status_ids": status_ids,
            "color_ids": color_ids,
        }
        logger.debug(f"Catalog filters parameters: {params}")
        result = self._get(Endpoints.CATALOG_FILTERS, FiltersResponse, params=params)
        logger.info("Catalog filters retrieved successfully")
        return result

    def catalogs_list(self) -> List[Catalog]:
        logger.info("Fetching catalogs list")
        params = {"page": 1, "time": time.time()}
        logger.debug(f"Catalogs list parameters: {params}")
        data: InitializersResponse = self._get(
            Endpoints.CATALOG_INITIALIZERS,
            InitializersResponse,
            params=params,
        )
        logger.info(f"Catalogs list retrieved successfully, found {len(data.dtos.catalogs)} catalogs")
        return data.dtos.catalogs

    def fetch_offer_description(self, url: str) -> str:
        """
        Fetches the offer description from a given Vinted item URL.
        :param url: The URL of the Vinted item.
        :return: The description of the item.
        """
        logger.info(f"Fetching offer description from URL: {url}")
        try:
            logger.debug("Making request to fetch offer description")
            response = requests.get(
                url, headers=self.headers, proxies=self.proxy, cookies=self.cookies
            )
            if response.status_code == 200:
                logger.debug("Parsing HTML response for description")
                soup = BeautifulSoup(response.text, "html.parser")
                description = soup.find("div", {"itemprop": "description"})
                if description:
                    description_text = description.get_text(strip=True)
                    logger.info(f"Description found, length: {len(description_text)} characters")
                    logger.debug(f"Description content: {description_text[:100]}...")
                    return description_text
                else:
                    logger.error("Description not found in the page.")
                    return None
            else:
                logger.error(f"Error fetching description: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"An error occurred while fetching the description: {e}")
            return None
