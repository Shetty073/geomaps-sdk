"""
Unit Tests for Location SDK

Comprehensive test suite for the Location SDK using unittest framework.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json

from geomaps_sdk import (
    LocationClient,
    BaseLocationProvider,
    GeoapifyProvider,
    GeoPoint,
    Address,
    GeocodingResult,
    AutocompleteResult,
    RouteInfo,
    DistanceMatrixResult,
    TravelMode,
    DistanceUnit,
    ValidationError,
    APIError,
    AuthenticationError,
    RateLimitError,
)


# ============================================================================
# Test Data Models
# ============================================================================

class TestGeoPoint(unittest.TestCase):
    """Tests for GeoPoint data model."""

    def test_geopoint_creation(self):
        """Test creating a GeoPoint."""
        point = GeoPoint(latitude=37.7749, longitude=-122.4194)
        self.assertEqual(point.latitude, 37.7749)
        self.assertEqual(point.longitude, -122.4194)

    def test_geopoint_to_dict(self):
        """Test converting GeoPoint to dict."""
        point = GeoPoint(latitude=37.7749, longitude=-122.4194)
        d = point.to_dict()
        self.assertEqual(d["latitude"], 37.7749)
        self.assertEqual(d["longitude"], -122.4194)

    def test_geopoint_str(self):
        """Test GeoPoint string representation."""
        point = GeoPoint(latitude=37.7749, longitude=-122.4194)
        self.assertEqual(str(point), "37.7749,-122.4194")


class TestAddress(unittest.TestCase):
    """Tests for Address data model."""

    def test_address_creation(self):
        """Test creating an Address."""
        addr = Address(
            street="1600 Amphitheatre Parkway",
            city="Mountain View",
            postcode="94043",
            country="United States",
        )
        self.assertEqual(addr.street, "1600 Amphitheatre Parkway")
        self.assertEqual(addr.city, "Mountain View")

    def test_address_to_dict(self):
        """Test converting Address to dict (excludes None values)."""
        addr = Address(street="Main St", city="Boston")
        d = addr.to_dict()
        self.assertEqual(d["street"], "Main St")
        self.assertEqual(d["city"], "Boston")
        self.assertNotIn("postcode", d)  # None values excluded

    def test_address_to_query_params(self):
        """Test converting Address to query parameters."""
        addr = Address(
            street="Main St",
            house_number="123",
            city="Boston",
            postcode="02101",
        )
        params = addr.to_query_params()
        self.assertEqual(params["street"], "Main St")
        self.assertEqual(params["housenumber"], "123")
        self.assertEqual(params["city"], "Boston")
        self.assertEqual(params["postcode"], "02101")


class TestGeocodingResult(unittest.TestCase):
    """Tests for GeocodingResult data model."""

    def test_geocoding_result_creation(self):
        """Test creating a GeocodingResult."""
        location = GeoPoint(latitude=37.7749, longitude=-122.4194)
        address = Address(city="San Francisco", country="United States")
        result = GeocodingResult(
            location=location,
            address=address,
            confidence=0.95,
        )
        self.assertEqual(result.location.latitude, 37.7749)
        self.assertEqual(result.confidence, 0.95)

    def test_geocoding_result_to_dict(self):
        """Test converting GeocodingResult to dict."""
        location = GeoPoint(latitude=37.7749, longitude=-122.4194)
        address = Address(city="San Francisco")
        result = GeocodingResult(location=location, address=address)
        d = result.to_dict()
        self.assertIn("location", d)
        self.assertIn("address", d)


class TestRouteInfo(unittest.TestCase):
    """Tests for RouteInfo data model."""

    def test_route_info_creation(self):
        """Test creating a RouteInfo."""
        route = RouteInfo(distance=5000, duration=300)
        self.assertEqual(route.distance, 5000)
        self.assertEqual(route.duration, 300)

    def test_route_info_calculations(self):
        """Test convenience properties calculation."""
        route = RouteInfo(distance=5000, duration=300)
        self.assertAlmostEqual(route.distance_km, 5.0)
        self.assertAlmostEqual(route.duration_minutes, 5.0)


# ============================================================================
# Test Enums
# ============================================================================

class TestEnums(unittest.TestCase):
    """Tests for Enum definitions."""

    def test_travel_mode_enum(self):
        """Test TravelMode enum values."""
        self.assertEqual(TravelMode.DRIVING.value, "drive")
        self.assertEqual(TravelMode.WALKING.value, "walk")
        self.assertEqual(TravelMode.CYCLING.value, "bike")
        self.assertEqual(TravelMode.TRUCK.value, "truck")

    def test_distance_unit_enum(self):
        """Test DistanceUnit enum values."""
        self.assertEqual(DistanceUnit.KILOMETERS.value, "km")
        self.assertEqual(DistanceUnit.MILES.value, "mi")
        self.assertEqual(DistanceUnit.METERS.value, "m")


# ============================================================================
# Test Exceptions
# ============================================================================

class TestExceptions(unittest.TestCase):
    """Tests for custom exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        with self.assertRaises(ValidationError):
            raise ValidationError("Invalid input")

    def test_api_error(self):
        """Test APIError."""
        with self.assertRaises(APIError):
            raise APIError("API request failed")

    def test_authentication_error(self):
        """Test AuthenticationError."""
        with self.assertRaises(AuthenticationError):
            raise AuthenticationError("Invalid API key")

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        with self.assertRaises(RateLimitError):
            raise RateLimitError("Rate limit exceeded")


# ============================================================================
# Test GeoapifyProvider
# ============================================================================

class TestGeoapifyProvider(unittest.TestCase):
    """Tests for GeoapifyProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.provider = GeoapifyProvider(api_key=self.api_key)

    def tearDown(self):
        """Clean up after tests."""
        self.provider.close()

    def test_provider_initialization(self):
        """Test provider initialization."""
        self.assertEqual(self.provider.api_key, self.api_key)
        self.assertEqual(self.provider.timeout, 10)

    def test_provider_initialization_with_custom_timeout(self):
        """Test provider initialization with custom timeout."""
        provider = GeoapifyProvider(api_key=self.api_key, timeout=30)
        self.assertEqual(provider.timeout, 30)
        provider.close()

    def test_provider_initialization_invalid_api_key(self):
        """Test provider initialization with invalid API key."""
        with self.assertRaises(ValidationError):
            GeoapifyProvider(api_key="")

        with self.assertRaises(ValidationError):
            GeoapifyProvider(api_key=None)

    def test_validate_location_valid(self):
        """Test location validation with valid location."""
        location = GeoPoint(latitude=37.7749, longitude=-122.4194)
        # Should not raise
        GeoapifyProvider._validate_location(location)

    def test_validate_location_invalid_latitude(self):
        """Test location validation with invalid latitude."""
        location = GeoPoint(latitude=91, longitude=-122.4194)
        with self.assertRaises(ValidationError):
            GeoapifyProvider._validate_location(location)

    def test_validate_location_invalid_longitude(self):
        """Test location validation with invalid longitude."""
        location = GeoPoint(latitude=37.7749, longitude=-181)
        with self.assertRaises(ValidationError):
            GeoapifyProvider._validate_location(location)

    def test_validate_locations_list_empty(self):
        """Test locations list validation with empty list."""
        with self.assertRaises(ValidationError):
            GeoapifyProvider._validate_locations_list([])

    def test_validate_locations_list_invalid(self):
        """Test locations list validation with non-list."""
        with self.assertRaises(ValidationError):
            GeoapifyProvider._validate_locations_list("not a list")

    @patch('geomaps_sdk.maps_sdk.GeoapifyProvider._make_request')
    def test_geocode_success(self, mock_make_request):
        """Test successful geocoding."""
        # Mock API response
        mock_make_request.return_value = {
            "results": [
                {
                    'datasource': {
                        'sourcename': 'openstreetmap',
                        'attribution': '© OpenStreetMap contributors',
                        'license': 'Open Database License',
                        'url': 'https://www.openstreetmap.org/copyright'
                    },
                    'country': 'Germany',
                    'country_code': 'de',
                    'state': 'Hesse',
                    'county': 'Wetteraukreis',
                    'city': 'Butzbach',
                    'municipality': 'Butzbach',
                    'postcode': '35510',
                    'street': 'Gabelsberger Straße',
                    'housenumber': '14',
                    'iso3166_2': 'DE-HE',
                    'lon': 8.661188482054381,
                    'lat': 50.4334353,
                    'state_code': 'HE',
                    'result_type': 'building',
                    'NUTS_3': 'DE71E',
                    'formatted': 'Gabelsberger Straße 14, 35510 Butzbach, Germany',
                    'address_line1': 'Gabelsberger Straße 14',
                    'address_line2': '35510 Butzbach, Germany',
                    'category': 'building',
                    'timezone': {
                        'name': 'Europe/Berlin',
                        'offset_STD': '+01:00',
                        'offset_STD_seconds': 3600,
                        'offset_DST': '+02:00',
                        'offset_DST_seconds': 7200,
                        'abbreviation_STD': 'CET',
                        'abbreviation_DST': 'CEST'
                    },
                    'plus_code': '9F2CCMM6+9F',
                    'plus_code_short': 'M6+9F Butzbach, Wetteraukreis, Germany',
                    'rank': {
                        'importance': 9.99999999995449e-06,
                        'confidence': 0.99,
                        'confidence_street_level': 0.99,
                        'confidence_building_level': 0.99,
                        'match_type': 'full_match'
                    },
                    'place_id': '51b6d4f54b87522140594a37d3ce7a374940f00102f9016ac6680900000000c00203',
                    'bbox': {
                        'lon1': 8.6610684,
                        'lat1': 50.4333647,
                        'lon2': 8.6613094,
                        'lat2': 50.433488
                    }
                }
            ]
        }

        # Test geocoding
        results = self.provider.geocode("Google HQ")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].location.latitude, 50.4334353)
        self.assertEqual(results[0].location.longitude, 8.661188482054381)
        self.assertEqual(results[0].confidence, 0.99)

    @patch('geomaps_sdk.maps_sdk.requests.Session.get')
    def test_geocode_no_results(self, mock_get):
        """Test geocoding with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response

        results = self.provider.geocode("Nonexistent Place XYZ")
        self.assertEqual(len(results), 0)

    def test_geocode_invalid_query(self):
        """Test geocoding with invalid query."""
        with self.assertRaises(ValidationError):
            self.provider.geocode("")

        with self.assertRaises(ValidationError):
            self.provider.geocode(None)

    @patch('geomaps_sdk.maps_sdk.GeoapifyProvider._make_request')
    def test_reverse_geocode_success(self, mock_make_request):
        """Test successful reverse geocoding."""
        mock_make_request.return_value = {
            "results": [
                {
                    'datasource': {
                        'sourcename': 'openstreetmap',
                        'attribution': '© OpenStreetMap contributors',
                        'license': 'Open Database License',
                        'url': 'https://www.openstreetmap.org/copyright'
                    },
                    'country': 'Germany',
                    'country_code': 'de',
                    'state': 'Hesse',
                    'county': 'Wetteraukreis',
                    'city': 'Butzbach',
                    'municipality': 'Butzbach',
                    'postcode': '35510',
                    'street': 'Gabelsberger Straße',
                    'housenumber': '14',
                    'iso3166_2': 'DE-HE',
                    'lon': 8.661188482054381,
                    'lat': 50.4334353,
                    'state_code': 'HE',
                    'result_type': 'building',
                    'NUTS_3': 'DE71E',
                    'formatted': 'Gabelsberger Straße 14, 35510 Butzbach, Germany',
                    'address_line1': 'Gabelsberger Straße 14',
                    'address_line2': '35510 Butzbach, Germany',
                    'category': 'building',
                    'timezone': {
                        'name': 'Europe/Berlin',
                        'offset_STD': '+01:00',
                        'offset_STD_seconds': 3600,
                        'offset_DST': '+02:00',
                        'offset_DST_seconds': 7200,
                        'abbreviation_STD': 'CET',
                        'abbreviation_DST': 'CEST'
                    },
                    'plus_code': '9F2CCMM6+9F',
                    'plus_code_short': 'M6+9F Butzbach, Wetteraukreis, Germany',
                    'rank': {
                        'importance': 9.99999999995449e-06,
                        'confidence': 1,
                        'confidence_street_level': 1,
                        'confidence_building_level': 1,
                        'match_type': 'full_match'
                    },
                    'place_id': '51b6d4f54b87522140594a37d3ce7a374940f00102f9016ac6680900000000c00203',
                    'bbox': {
                        'lon1': 8.6610684,
                        'lat1': 50.4333647,
                        'lon2': 8.6613094,
                        'lat2': 50.433488
                    }
                }
            ]
        }

        location = GeoPoint(latitude=37.4220, longitude=-122.0841)
        addresses = self.provider.reverse_geocode(location)
        
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0].address.city, "Butzbach")

    def test_reverse_geocode_invalid_location(self):
        """Test reverse geocoding with invalid location."""
        with self.assertRaises(ValidationError):
            self.provider.reverse_geocode(GeoPoint(latitude=91, longitude=0))

    @patch('geomaps_sdk.maps_sdk.GeoapifyProvider._make_request')
    def test_autocomplete_success(self, mock_make_request):
        """Test successful address autocomplete."""
        mock_make_request.return_value = {
            "results": [
                {
                    'datasource': {
                        'sourcename': 'openstreetmap',
                        'attribution': '© OpenStreetMap contributors',
                        'license': 'Open Database License',
                        'url': 'https://www.openstreetmap.org/copyright'
                    },
                    'country': 'Germany',
                    'country_code': 'de',
                    'state': 'Hesse',
                    'county': 'Wetteraukreis',
                    'city': 'Butzbach',
                    'municipality': 'Butzbach',
                    'postcode': '35510',
                    'street': 'Gabelsberger Straße',
                    'housenumber': '14',
                    'iso3166_2': 'DE-HE',
                    'lon': 8.661188482054381,
                    'lat': 50.4334353,
                    'state_code': 'HE',
                    'result_type': 'building',
                    'NUTS_3': 'DE71E',
                    'formatted': 'Gabelsberger Straße 14, 35510 Butzbach, Germany',
                    'address_line1': 'Gabelsberger Straße 14',
                    'address_line2': '35510 Butzbach, Germany',
                    'category': 'building',
                    'timezone': {
                        'name': 'Europe/Berlin',
                        'offset_STD': '+01:00',
                        'offset_STD_seconds': 3600,
                        'offset_DST': '+02:00',
                        'offset_DST_seconds': 7200,
                        'abbreviation_STD': 'CET',
                        'abbreviation_DST': 'CEST'
                    },
                    'plus_code': '9F2CCMM6+9F',
                    'plus_code_short': 'M6+9F Butzbach, Wetteraukreis, Germany',
                    'rank': {
                        'importance': 9.99999999995449e-06,
                        'confidence': 1,
                        'confidence_street_level': 1,
                        'confidence_building_level': 1,
                        'match_type': 'full_match'
                    },
                    'place_id': '51b6d4f54b87522140594a37d3ce7a374940f00102f9016ac6680900000000c00203',
                    'bbox': {
                        'lon1': 8.6610684,
                        'lat1': 50.4333647,
                        'lon2': 8.6613094,
                        'lat2': 50.433488
                    }
                },
                {
                    'datasource': {
                        'sourcename': 'openstreetmap',
                        'attribution': '© OpenStreetMap contributors',
                        'license': 'Open Database License',
                        'url': 'https://www.openstreetmap.org/copyright'
                    },
                    'country': 'Germany',
                    'country_code': 'de',
                    'state': 'Hesse',
                    'county': 'Wetteraukreis',
                    'city': 'Butzbach',
                    'municipality': 'Butzbach',
                    'postcode': '35510',
                    'street': 'Gabelsberger Straße',
                    'housenumber': '14',
                    'iso3166_2': 'DE-HE',
                    'lon': 8.661188482054381,
                    'lat': 50.4334353,
                    'state_code': 'HE',
                    'result_type': 'building',
                    'NUTS_3': 'DE71E',
                    'formatted': 'Gabelsberger Straße 14, 35510 Butzbach, Germany',
                    'address_line1': 'Gabelsberger Straße 14',
                    'address_line2': '35510 Butzbach, Germany',
                    'category': 'building',
                    'timezone': {
                        'name': 'Europe/Berlin',
                        'offset_STD': '+01:00',
                        'offset_STD_seconds': 3600,
                        'offset_DST': '+02:00',
                        'offset_DST_seconds': 7200,
                        'abbreviation_STD': 'CET',
                        'abbreviation_DST': 'CEST'
                    },
                    'plus_code': '9F2CCMM6+9F',
                    'plus_code_short': 'M6+9F Butzbach, Wetteraukreis, Germany',
                    'rank': {
                        'importance': 9.99999999995449e-06,
                        'confidence': 1,
                        'confidence_street_level': 1,
                        'confidence_building_level': 1,
                        'match_type': 'full_match'
                    },
                    'place_id': '51b6d4f54b87522140594a37d3ce7a374940f00102f9016ac6680900000000c00203',
                    'bbox': {
                        'lon1': 8.6610684,
                        'lat1': 50.4333647,
                        'lon2': 8.6613094,
                        'lat2': 50.433488
                    }
                }
            ]
        }

        results = self.provider.autocomplete("Street", limit=5)
        self.assertEqual(len(results), 2)

    def test_autocomplete_invalid_limit(self):
        """Test autocomplete with invalid limit."""
        with self.assertRaises(ValidationError):
            self.provider.autocomplete("Query", limit=0)

        with self.assertRaises(ValidationError):
            self.provider.autocomplete("Query", limit=100)

    @patch('geomaps_sdk.maps_sdk.requests.Session.get')
    def test_authentication_error(self, mock_get):
        """Test API authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            self.provider.geocode("Test")

    @patch('geomaps_sdk.maps_sdk.requests.Session.get')
    def test_rate_limit_error(self, mock_get):
        """Test API rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with self.assertRaises(RateLimitError):
            self.provider.geocode("Test")

    @patch('geomaps_sdk.maps_sdk.requests.Session.get')
    def test_api_error(self, mock_get):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with self.assertRaises(APIError):
            self.provider.geocode("Test")

    @patch('geomaps_sdk.maps_sdk.requests.Session.get')
    def test_timeout_error(self, mock_get):
        """Test timeout error handling."""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Request timed out")

        with self.assertRaises(APIError):
            self.provider.geocode("Test")

    @patch("geomaps_sdk.maps_sdk.GeoapifyProvider._make_request")
    def test_distance_matrix_success(self, mock_make_request):
        """Test successful distance matrix calculation."""
        
        mock_make_request.return_value = {
            "sources_to_targets": [
                [
                    {"distance": 50000, "time": 1800},
                    {"distance": 60000, "time": 2100}
                ],
                [
                    {"distance": 45000, "time": 1600},
                    {"distance": 55000, "time": 1900}
                ]
            ]
        }

        sources = [
            GeoPoint(latitude=37.7749, longitude=-122.4194),
            GeoPoint(latitude=34.0522, longitude=-118.2437)
        ]
        targets = [
            GeoPoint(latitude=39.7392, longitude=-104.9903),
            GeoPoint(latitude=40.7128, longitude=-74.0060)
        ]

        result = self.provider.distance_matrix(sources, targets)
        
        self.assertEqual(len(result.distances), 2)
        self.assertEqual(len(result.distances[0]), 2)
        self.assertEqual(result.distances[0][0], 50000)

    def test_distance_matrix_too_many_sources(self):
        """Test distance matrix with too many sources."""
        sources = [GeoPoint(latitude=i, longitude=i) for i in range(15)]
        targets = [GeoPoint(latitude=0, longitude=0)]

        with self.assertRaises(ValidationError):
            self.provider.distance_matrix(sources, targets)


# ============================================================================
# Test LocationClient
# ============================================================================

class TestLocationClient(unittest.TestCase):
    """Tests for LocationClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = Mock(spec=BaseLocationProvider)
        self.client = LocationClient(provider=self.provider)

    def test_client_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.provider, self.provider)

    def test_client_initialization_invalid_provider(self):
        """Test client initialization with invalid provider."""
        with self.assertRaises(ValidationError):
            LocationClient(provider="not a provider")

    def test_client_geocode_delegates_to_provider(self):
        """Test that geocode delegates to provider."""
        expected_results = [Mock(spec=GeocodingResult)]
        self.provider.geocode.return_value = expected_results

        results = self.client.geocode("Test Address")
        
        self.provider.geocode.assert_called_once_with("Test Address")
        self.assertEqual(results, expected_results)

    def test_client_reverse_geocode_delegates_to_provider(self):
        """Test that reverse_geocode delegates to provider."""
        location = GeoPoint(latitude=37.7749, longitude=-122.4194)
        expected_addresses = [Mock(spec=Address)]
        self.provider.reverse_geocode.return_value = expected_addresses

        addresses = self.client.reverse_geocode(location)
        
        self.provider.reverse_geocode.assert_called_once_with(location)
        self.assertEqual(addresses, expected_addresses)

    def test_client_autocomplete_delegates_to_provider(self):
        """Test that autocomplete delegates to provider."""
        expected_results = [Mock(spec=AutocompleteResult)]
        self.provider.autocomplete.return_value = expected_results

        results = self.client.autocomplete("Test", limit=5)
        
        self.provider.autocomplete.assert_called_once_with("Test", 5)
        self.assertEqual(results, expected_results)

    def test_client_distance_matrix_delegates_to_provider(self):
        """Test that distance_matrix delegates to provider."""
        sources = [GeoPoint(latitude=0, longitude=0)]
        targets = [GeoPoint(latitude=1, longitude=1)]
        expected_result = Mock(spec=DistanceMatrixResult)
        self.provider.distance_matrix.return_value = expected_result

        result = self.client.distance_matrix(sources, targets)
        
        self.provider.distance_matrix.assert_called_once_with(
            sources, targets, TravelMode.DRIVING, DistanceUnit.KILOMETERS
        )
        self.assertEqual(result, expected_result)

    def test_client_route_delegates_to_provider(self):
        """Test that route delegates to provider."""
        source = GeoPoint(latitude=0, longitude=0)
        target = GeoPoint(latitude=1, longitude=1)
        expected_route = Mock(spec=RouteInfo)
        self.provider.route.return_value = expected_route

        route = self.client.route(source, target)
        
        self.provider.route.assert_called_once_with(
            source, target, TravelMode.DRIVING, DistanceUnit.KILOMETERS
        )
        self.assertEqual(route, expected_route)

    def test_client_context_manager(self):
        """Test client as context manager."""
        provider = Mock(spec=BaseLocationProvider)
        
        with LocationClient(provider=provider) as client:
            self.assertEqual(client.provider, provider)
        
        provider.close.assert_called_once()


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
