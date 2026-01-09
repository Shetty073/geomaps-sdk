"""
Vendor-agnostic Maps and Location SDK

This SDK provides a clean, extensible interface for various location-based services
including geocoding, reverse geocoding, address autocomplete, and routing.

The design follows the Abstract Factory pattern to allow easy vendor switching without
changing client code.

Author: Location SDK
License: MIT
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Optional, Any, Union
import logging

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError


# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ============================================================================
# Data Models and Enums
# ============================================================================

class TravelMode(Enum):
    """Supported travel modes for routing and distance calculations."""
    DRIVING = "drive"
    WALKING = "walk"
    CYCLING = "bike"
    TRUCK = "truck"


class DistanceUnit(Enum):
    """Distance measurement units."""
    KILOMETERS = "km"
    MILES = "mi"
    METERS = "m"


@dataclass
class GeoPoint:
    """Represents a geographic point with latitude and longitude."""
    latitude: float
    longitude: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {"latitude": self.latitude, "longitude": self.longitude}

    def __str__(self) -> str:
        return f"{self.latitude},{self.longitude}"


@dataclass
class Address:
    """Represents a structured address."""
    street: Optional[str] = None
    house_number: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    state: Optional[str] = None
    formatted_address: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_query_params(self) -> Dict[str, str]:
        """Convert to query parameters for structured address queries."""
        params = {}
        if self.street:
            params["street"] = self.street
        if self.house_number:
            params["housenumber"] = self.house_number
        if self.city:
            params["city"] = self.city
        if self.postcode:
            params["postcode"] = self.postcode
        if self.country:
            params["country"] = self.country
        return params


@dataclass
class GeocodingResult:
    """Result from geocoding operation."""
    location: GeoPoint
    address: Address
    confidence: Optional[float] = None
    confidence_building_level: Optional[float] = None
    confidence_street_level: Optional[float] = None
    confidence_city_level: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "location": self.location.to_dict(),
            "address": self.address.to_dict(),
            "confidence": self.confidence,
            "confidence_building_level": self.confidence_building_level,
            "confidence_street_level": self.confidence_street_level,
            "confidence_city_level": self.confidence_city_level,
        }


@dataclass
class AutocompleteResult:
    """Result from address autocomplete operation."""
    address: Address
    location: GeoPoint
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class RouteInfo:
    distance_km: float
    duration_minutes: float

    def __init__(
        self,
        distance: float | None = None,          # meters
        duration: float | None = None,          # seconds
        *,
        distance_km: float | None = None,
        duration_minutes: float | None = None,
    ):
        if distance_km is not None:
            self.distance_km = distance_km
        elif distance is not None:
            self.distance_km = distance / 1000
        else:
            raise TypeError("Either distance or distance_km must be provided")

        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        elif duration is not None:
            self.duration_minutes = duration / 60
        else:
            raise TypeError("Either duration or duration_minutes must be provided")

    # 🔹 What your tests expect
    @property
    def distance(self) -> int:
        """Distance in meters."""
        return int(self.distance_km * 1000)

    @property
    def duration(self) -> int:
        """Duration in seconds."""
        return int(self.duration_minutes * 60)

    # 🔹 Convenience aliases (optional but nice)
    @property
    def distance_meters(self) -> int:
        return self.distance

    @property
    def duration_seconds(self) -> int:
        return self.duration


@dataclass
class DistanceMatrixResult:
    """Result from distance matrix calculation."""
    distances: List[List[float]]  # meters
    durations: List[List[float]]  # seconds
    unit: str = "metric"  # metric or imperial
    sources: Optional[List[GeoPoint]] = None
    targets: Optional[List[GeoPoint]] = None


# ============================================================================
# Exception Classes
# ============================================================================

class LocationSDKError(Exception):
    """Base exception for Location SDK."""
    pass


class AuthenticationError(LocationSDKError):
    """Raised when API authentication fails."""
    pass


class APIError(LocationSDKError):
    """Raised when API request fails."""
    pass


class ValidationError(LocationSDKError):
    """Raised when input validation fails."""
    pass


class RateLimitError(LocationSDKError):
    """Raised when API rate limit is exceeded."""
    pass


# ============================================================================
# Abstract Base Classes (Vendor Interface)
# ============================================================================

class BaseLocationProvider(ABC):
    """
    Abstract base class defining the interface for location providers.
    
    Implementations should override these methods to support different vendors
    (Google Maps, Mapbox, Nominatim, etc.)
    """

    def __init__(self, api_key: str, timeout: int = 10):
        """
        Initialize the provider.

        Args:
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key must be a non-empty string")
        
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    @abstractmethod
    def geocode(self, query: str) -> List[GeocodingResult]:
        """
        Convert address text to geographic coordinates.

        Args:
            query: Address or location name to geocode

        Returns:
            List of geocoding results, ordered by relevance

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        pass

    @abstractmethod
    def reverse_geocode(self, location: GeoPoint) -> List[Address]:
        """
        Convert geographic coordinates to address.

        Args:
            location: Geographic point to reverse geocode

        Returns:
            List of addresses for the given location

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        pass

    @abstractmethod
    def autocomplete(self, query: str, limit: int = 5) -> List[AutocompleteResult]:
        """
        Get address suggestions as user types.

        Args:
            query: Partial address string
            limit: Maximum number of suggestions to return

        Returns:
            List of autocomplete suggestions

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        pass

    @abstractmethod
    def distance_matrix(
        self,
        sources: List[GeoPoint],
        targets: List[GeoPoint],
        mode: TravelMode = TravelMode.DRIVING,
        units: DistanceUnit = DistanceUnit.KILOMETERS,
    ) -> DistanceMatrixResult:
        """
        Calculate distances and durations between multiple locations.

        Args:
            sources: List of source locations
            targets: List of target locations
            mode: Travel mode (driving, walking, cycling, etc.)
            units: Distance unit (kilometers, miles, etc.)

        Returns:
            Distance matrix with distances and durations

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        pass

    @abstractmethod
    def route(
        self,
        source: GeoPoint,
        target: GeoPoint,
        mode: TravelMode = TravelMode.DRIVING,
    ) -> RouteInfo:
        """
        Calculate route information between two points.

        Args:
            source: Starting location
            target: Destination location
            mode: Travel mode (driving, walking, cycling, etc.)

        Returns:
            Route information including distance and duration

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        pass

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            headers: Custom headers

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the request fails
        """
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params, json=data, headers=headers, timeout=self.timeout)
            else:
                raise ValidationError(f"Unsupported HTTP method: {method}")

            # Handle authentication errors
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError("Invalid API key or insufficient permissions")

            # Handle rate limiting
            if response.status_code == 429:
                raise RateLimitError("API rate limit exceeded. Please try again later.")

            # Handle other HTTP errors
            if response.status_code >= 400:
                logger.error(f"API Error {response.status_code}: {response.text}")
                raise APIError(f"API request failed with status {response.status_code}: {response.text}")

            return response.json()

        except Timeout:
            raise APIError(f"API request timed out after {self.timeout} seconds")
        except RequestsConnectionError as e:
            raise APIError(f"Connection error: {str(e)}")
        except RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise APIError(f"Failed to parse API response: {str(e)}")

    def close(self):
        """Close the session and clean up resources."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============================================================================
# Geoapify Implementation
# ============================================================================

class GeoapifyProvider(BaseLocationProvider):
    """
    Geoapify Maps API implementation.
    
    Supports geocoding, reverse geocoding, address autocomplete, and routing.
    Documentation: https://apidocs.geoapify.com/
    """

    BASE_URL = "https://api.geoapify.com/v1"

    def geocode(self, query: str) -> List[GeocodingResult]:
        """
        Convert address text to geographic coordinates using Geoapify.

        Args:
            query: Address or location name to geocode

        Returns:
            List of geocoding results

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        if not query or not isinstance(query, str) or not query.strip():
            raise ValidationError("Query must be a non-empty string")

        url = f"{self.BASE_URL}/geocode/search"
        params = {
            "text": query,
            "apiKey": self.api_key,
            "format": "json",
        }

        response = self._make_request(url, params=params)
        results = []

        if "features" in response:
            for feature in response["features"]:
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])

                if coords and len(coords) >= 2:
                    location = GeoPoint(latitude=coords[1], longitude=coords[0])
                    address = Address(
                        street=props.get("street"),
                        house_number=props.get("housenumber"),
                        city=props.get("city"),
                        postcode=props.get("postcode"),
                        country=props.get("country"),
                        country_code=props.get("country_code"),
                        state=props.get("state"),
                        formatted_address=props.get("formatted"),
                    )

                    rank = props.get("rank", {})
                    result = GeocodingResult(
                        location=location,
                        address=address,
                        confidence=rank.get("confidence"),
                        confidence_building_level=rank.get("confidence_building_level"),
                        confidence_street_level=rank.get("confidence_street_level"),
                        confidence_city_level=rank.get("confidence_city_level"),
                        raw_data=feature,
                    )
                    results.append(result)

        return results

    def reverse_geocode(self, location: GeoPoint) -> List[Address]:
        """
        Convert geographic coordinates to address using Geoapify.

        Args:
            location: Geographic point to reverse geocode

        Returns:
            List of addresses for the given location

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        self._validate_location(location)

        url = f"{self.BASE_URL}/geocode/reverse"
        params = {
            "lat": location.latitude,
            "lon": location.longitude,
            "apiKey": self.api_key,
            "format": "json",
        }

        response = self._make_request(url, params=params)
        addresses = []

        if "features" in response:
            for feature in response["features"]:
                props = feature.get("properties", {})
                address = Address(
                    street=props.get("street"),
                    house_number=props.get("housenumber"),
                    city=props.get("city"),
                    postcode=props.get("postcode"),
                    country=props.get("country"),
                    country_code=props.get("country_code"),
                    state=props.get("state"),
                    formatted_address=props.get("formatted"),
                )
                addresses.append(address)

        return addresses

    def autocomplete(self, query: str, limit: int = 5) -> List[AutocompleteResult]:
        """
        Get address suggestions as user types using Geoapify.

        Args:
            query: Partial address string
            limit: Maximum number of suggestions to return

        Returns:
            List of autocomplete suggestions

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        if not query or not isinstance(query, str) or not query.strip():
            raise ValidationError("Query must be a non-empty string")

        if limit < 1 or limit > 50:
            raise ValidationError("Limit must be between 1 and 50")

        url = f"{self.BASE_URL}/geocode/autocomplete"
        params = {
            "text": query,
            "apiKey": self.api_key,
            "format": "json",
            "limit": limit,
        }

        response = self._make_request(url, params=params)
        results = []

        if "features" in response:
            for feature in response["features"]:
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])

                if coords and len(coords) >= 2:
                    location = GeoPoint(latitude=coords[1], longitude=coords[0])
                    address = Address(
                        street=props.get("street"),
                        house_number=props.get("housenumber"),
                        city=props.get("city"),
                        postcode=props.get("postcode"),
                        country=props.get("country"),
                        country_code=props.get("country_code"),
                        state=props.get("state"),
                        formatted_address=props.get("formatted"),
                    )

                    result = AutocompleteResult(
                        address=address,
                        location=location,
                        raw_data=feature,
                    )
                    results.append(result)

        return results

    def distance_matrix(
        self,
        sources: List[GeoPoint],
        targets: List[GeoPoint],
        mode: TravelMode = TravelMode.DRIVING,
        units: DistanceUnit = DistanceUnit.KILOMETERS,
    ) -> DistanceMatrixResult:
        """
        Calculate distances and durations between multiple locations using Geoapify.

        Args:
            sources: List of source locations
            targets: List of target locations
            mode: Travel mode (driving, walking, cycling, etc.)
            units: Distance unit (kilometers, miles, etc.)

        Returns:
            Distance matrix with distances and durations

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        self._validate_locations_list(sources, "sources")
        self._validate_locations_list(targets, "targets")

        if len(sources) > 10 or len(targets) > 10:
            raise ValidationError("Maximum 10 sources and 10 targets are supported per request")

        url = f"{self.BASE_URL}/routematrix"

        # Format locations
        sources_str = "|".join([f"{loc.latitude},{loc.longitude}" for loc in sources])
        targets_str = "|".join([f"{loc.latitude},{loc.longitude}" for loc in targets])

        params = {
            "sources": sources_str,
            "targets": targets_str,
            "apiKey": self.api_key,
        }

        response = self._make_request(url, params=params)
        
        # Parse distance matrix from response
        distances = []
        durations = []

        if "sources_to_targets" in response:
            for source_matrix in response["sources_to_targets"]:
                distance_row = []
                duration_row = []

                for target in source_matrix:
                    distance_row.append(target.get("distance", 0))
                    duration_row.append(target.get("time", 0))

                distances.append(distance_row)
                durations.append(duration_row)

        return DistanceMatrixResult(
            distances=distances,
            durations=durations,
            unit="metric",
            sources=sources,
            targets=targets,
        )

    def route(
        self,
        source: GeoPoint,
        target: GeoPoint,
        mode: TravelMode = TravelMode.DRIVING,
    ) -> RouteInfo:
        """
        Calculate route information between two points using Geoapify.

        Args:
            source: Starting location
            target: Destination location
            mode: Travel mode (driving, walking, cycling, etc.)

        Returns:
            Route information including distance and duration

        Raises:
            APIError: If the API request fails
            ValidationError: If input is invalid
        """
        self._validate_location(source, "source")
        self._validate_location(target, "target")

        url = f"{self.BASE_URL}/routing"
        params = {
            "from": f"{source.latitude},{source.longitude}",
            "to": f"{target.latitude},{target.longitude}",
            "mode": mode.value,
            "apiKey": self.api_key,
        }

        response = self._make_request(url, params=params)

        # Extract route information
        if "features" and len(response.get("features", [])) > 0:
            feature = response["features"][0]
            props = feature.get("properties", {})
            distance = props.get("distance", 0)
            duration = props.get("time", 0)

            return RouteInfo(distance=distance, duration=duration)

        raise APIError("No route found between the provided locations")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    def _validate_location(location: Union[GeoPoint, Dict], name: str = "location") -> None:
        """Validate a single location."""
        if isinstance(location, dict):
            if "latitude" not in location or "longitude" not in location:
                raise ValidationError(f"{name} must have 'latitude' and 'longitude' keys")
            lat, lon = location["latitude"], location["longitude"]
        elif isinstance(location, GeoPoint):
            lat, lon = location.latitude, location.longitude
        else:
            raise ValidationError(f"{name} must be a GeoPoint or dict with latitude and longitude")

        if not (-90 <= lat <= 90):
            raise ValidationError(f"{name} latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValidationError(f"{name} longitude must be between -180 and 180")

    @staticmethod
    def _validate_locations_list(locations: List[GeoPoint], name: str = "locations") -> None:
        """Validate a list of locations."""
        if not locations or len(locations) == 0:
            raise ValidationError(f"{name} must not be empty")
        if not isinstance(locations, list):
            raise ValidationError(f"{name} must be a list of GeoPoint objects")

        for idx, location in enumerate(locations):
            try:
                GeoapifyProvider._validate_location(location, f"{name}[{idx}]")
            except ValidationError as e:
                raise ValidationError(str(e))


# ============================================================================
# LocationClient - High-Level API
# ============================================================================

class LocationClient:
    """
    High-level client for location-based services.
    
    This is the main entry point for using the SDK. It abstracts away the details
    of specific providers while maintaining a consistent interface.
    
    Example:
        >>> client = LocationClient(provider=GeoapifyProvider(api_key="YOUR_API_KEY"))
        >>> results = client.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
        >>> print(results[0].location)
    """

    def __init__(self, provider: BaseLocationProvider):
        """
        Initialize the client with a specific provider.

        Args:
            provider: Location provider instance (e.g., GeoapifyProvider)
        """
        if not isinstance(provider, BaseLocationProvider):
            raise ValidationError("Provider must be an instance of BaseLocationProvider")
        self.provider = provider

    def geocode(self, query: str) -> List[GeocodingResult]:
        """
        Convert address text to geographic coordinates.

        Args:
            query: Address or location name to geocode

        Returns:
            List of geocoding results
        """
        return self.provider.geocode(query)

    def reverse_geocode(self, location: GeoPoint) -> List[Address]:
        """
        Convert geographic coordinates to address.

        Args:
            location: Geographic point to reverse geocode

        Returns:
            List of addresses
        """
        return self.provider.reverse_geocode(location)

    def autocomplete(self, query: str, limit: int = 5) -> List[AutocompleteResult]:
        """
        Get address suggestions as user types.

        Args:
            query: Partial address string
            limit: Maximum number of suggestions

        Returns:
            List of autocomplete suggestions
        """
        return self.provider.autocomplete(query, limit)

    def distance_matrix(
        self,
        sources: List[GeoPoint],
        targets: List[GeoPoint],
        mode: TravelMode = TravelMode.DRIVING,
        units: DistanceUnit = DistanceUnit.KILOMETERS,
    ) -> DistanceMatrixResult:
        """
        Calculate distances and durations between multiple locations.

        Args:
            sources: List of source locations
            targets: List of target locations
            mode: Travel mode
            units: Distance unit

        Returns:
            Distance matrix result
        """
        return self.provider.distance_matrix(sources, targets, mode, units)

    def route(
        self,
        source: GeoPoint,
        target: GeoPoint,
        mode: TravelMode = TravelMode.DRIVING,
    ) -> RouteInfo:
        """
        Calculate route between two points.

        Args:
            source: Starting location
            target: Destination location
            mode: Travel mode

        Returns:
            Route information
        """
        return self.provider.route(source, target, mode)

    def close(self):
        """Close the client and clean up resources."""
        self.provider.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Data Models
    "GeoPoint",
    "Address",
    "GeocodingResult",
    "AutocompleteResult",
    "RouteInfo",
    "DistanceMatrixResult",
    # Enums
    "TravelMode",
    "DistanceUnit",
    # Exceptions
    "LocationSDKError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "RateLimitError",
    # Base Classes
    "BaseLocationProvider",
    # Implementations
    "GeoapifyProvider",
    # Client
    "LocationClient",
]
