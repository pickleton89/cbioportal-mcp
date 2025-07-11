import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class APIHTTPError(APIClientError):
    """Raised when an HTTP error occurs during API request."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_text: str = "",
        endpoint: str = "",
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.endpoint = endpoint


class APINetworkError(APIClientError):
    """Raised when a network/request error occurs during API request."""

    def __init__(self, message: str, endpoint: str = ""):
        super().__init__(message)
        self.endpoint = endpoint


class APITimeoutError(APINetworkError):
    """Raised when a timeout occurs during API request."""

    pass


class APIParseError(APIClientError):
    """Raised when there's an error parsing the API response."""

    def __init__(self, message: str, endpoint: str = "", response_text: str = ""):
        super().__init__(message)
        self.endpoint = endpoint
        self.response_text = response_text


class APIClient:
    """
    A client for making asynchronous API requests to the cBioPortal API.
    Manages an httpx.AsyncClient instance.
    """

    def __init__(
        self,
        base_url: str = "https://www.cbioportal.org/api",
        client_timeout: float = 480.0,
    ):
        """
        Initializes the APIClient.

        Args:
            base_url: The base URL for the cBioPortal API.
            client_timeout: Timeout in seconds for the HTTP client.
        """
        self.base_url = base_url.rstrip("/")
        self.client_timeout = client_timeout
        self._client: Optional[httpx.AsyncClient] = None
        logger.debug(
            f"APIClient initialized with base_url: {self.base_url}, timeout: {self.client_timeout}"
        )

    async def startup(self):
        """
        Initializes the asynchronous HTTP client.
        Should be called before making any API requests.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.client_timeout
            )
            logger.info(
                f"APIClient's httpx.AsyncClient started with base_url: {self.base_url} and timeout: {self.client_timeout}s"
            )
        else:
            logger.info("APIClient's httpx.AsyncClient was already started.")

    async def shutdown(self):
        """
        Closes the asynchronous HTTP client.
        Should be called when the client is no longer needed.
        """
        if self._client:
            await self._client.aclose()
            self._client = None  # Mark as closed
            logger.info("APIClient's httpx.AsyncClient closed.")
        else:
            logger.info(
                "APIClient's httpx.AsyncClient was already closed or not initialized."
            )

    async def make_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
    ) -> Any:
        """
        Makes an asynchronous API request to the cBioPortal API.

        Args:
            endpoint: The API endpoint path (e.g., "studies").
            method: HTTP method, "GET" or "POST".
            params: URL query parameters.
            json_data: JSON body for POST requests.

        Returns:
            The JSON response from the API.

        Raises:
            RuntimeError: If the client is not started.
            ValueError: If an unsupported HTTP method is provided.
            Exception: For API request failures (HTTP errors, request errors, etc.).
        """
        if self._client is None:
            raise RuntimeError(
                "APIClient._client is not initialized. Call APIClient.startup() before making requests."
            )

        # Use relative path since base_url is configured in the client
        endpoint_path = endpoint.lstrip("/")
        logger.debug(
            f"Making {method.upper()} request to {endpoint_path} with params: {params}, json_data: {json_data is not None}"
        )

        try:
            if method.upper() == "GET":
                response = await self._client.get(endpoint_path, params=params)
            elif method.upper() == "POST":
                response = await self._client.post(
                    endpoint_path, json=json_data, params=params
                )
            else:
                logger.error(
                    f"Unsupported HTTP method: {method} for endpoint: {endpoint_path}"
                )
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            if not response.text:  # Handle empty response body
                logger.debug(
                    f"Empty response body from {response.url} (status: {response.status_code}). Endpoint: {endpoint}"
                )
                # Original logic: if endpoint implies a list (plural 's' or 'fetch'), return empty list.
                if endpoint.endswith("s") or endpoint.endswith("fetch"):
                    return []
                return {}  # Otherwise, return empty dict.

            return response.json()

        except httpx.HTTPStatusError as e:
            error_text_snippet = (
                e.response.text[:500] if e.response.text else "No response body"
            )
            logger.error(
                f"HTTP error {e.response.status_code} for {method.upper()} {endpoint_path}: {error_text_snippet}..."
            )
            raise APIHTTPError(
                f"API request to {endpoint} failed with status {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                response_text=e.response.text,
                endpoint=endpoint,
            ) from e
        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout error for {method.upper()} {endpoint_path}: {str(e)}"
            )
            raise APITimeoutError(
                f"API request to {endpoint} timed out: {str(e)}", endpoint=endpoint
            ) from e
        except httpx.RequestError as e:  # Catches network errors, etc.
            logger.error(
                f"Request error for {method.upper()} {endpoint_path}: {str(e)}"
            )
            raise APINetworkError(
                f"API request to {endpoint} failed due to a network error: {str(e)}",
                endpoint=endpoint,
            ) from e
        except (ValueError, TypeError) as e:  # JSON decode errors, etc.
            logger.error(
                f"Parse error during API request to {method.upper()} {endpoint_path}: {str(e)}"
            )
            raise APIParseError(
                f"Failed to parse response from {endpoint}: {str(e)}", endpoint=endpoint
            ) from e
        except Exception as e:  # Catch-all for other unexpected errors
            logger.error(
                f"Unexpected error during API request to {method.upper()} {endpoint_path}: {str(e)}"
            )
            raise APIClientError(
                f"Unexpected error during API request to {endpoint}: {str(e)}"
            ) from e
