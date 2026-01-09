# Location SDK - Vendor-Agnostic Maps and Location Services

A flexible, extensible Python SDK for location-based services that abstracts away vendor-specific implementations. Start with Geoapify and easily switch to Google Maps, Mapbox, or Nominatim without changing your application code.

## Features

✨ **Vendor-Agnostic Design** - Abstract interface allows seamless provider switching  
🗺️ **Comprehensive Location APIs** - Geocoding, reverse geocoding, autocomplete, routing, distance matrices  
🔒 **Error Handling** - Custom exceptions for authentication, rate limiting, validation, and API errors  
📦 **Type-Safe** - Full type hints for better IDE support and code reliability  
🧪 **Well-Tested** - Comprehensive unit tests with 90%+ code coverage  
📚 **Production-Ready** - Follows Python best practices and PEP 8 standards  
🔄 **Context Managers** - Automatic resource cleanup with `with` statements  

## Installation

### Prerequisites
- Python 3.7+
- requests library

### Setup

```bash
pip install requests
```

Then copy `maps_sdk.py` to your project directory.

## Quick Start

### 1. Get an API Key

For Geoapify: Get your free Geoapify API key from [https://www.geoapify.com/](https://www.geoapify.com/)

### 2. Basic Usage

```python
from maps_sdk import LocationClient, GeoapifyProvider, GeoPoint

# Initialize client
client = LocationClient(provider=GeoapifyProvider(api_key="YOUR_API_KEY"))

# Geocode an address
results = client.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
if results:
    location = results[0].location
    print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")

# Reverse geocode coordinates
location = GeoPoint(latitude=37.4220, longitude=-122.0841)
addresses = client.reverse_geocode(location)
print(addresses[0].formatted_address)

# Get address suggestions
suggestions = client.autocomplete("San Francisco", limit=5)
for suggestion in suggestions:
    print(suggestion.address.formatted_address)

client.close()
```

### 3. Using Context Manager (Recommended)

```python
with LocationClient(provider=GeoapifyProvider(api_key="YOUR_API_KEY")) as client:
    results = client.geocode("Paris, France")
    print(results[0].address.formatted_address)
    # Session automatically closed here
```

## Core Concepts

### Data Models

#### GeoPoint
Represents a geographic coordinate with latitude and longitude.

```python
location = GeoPoint(latitude=37.7749, longitude=-122.4194)
print(location)  # 37.7749,-122.4194
print(location.to_dict())  # {"latitude": 37.7749, "longitude": -122.4194}
```

#### Address
Represents a structured postal address.

```python
address = Address(
    street="1600 Amphitheatre Parkway",
    house_number="1600",
    city="Mountain View",
    postcode="94043",
    country="United States",
    country_code="us"
)
print(address.to_dict())
print(address.to_query_params())
```

#### GeocodingResult
Result from geocoding operations with confidence scores.

```python
result = client.geocode("Address")[0]
print(result.location)  # GeoPoint
print(result.address)  # Address
print(result.confidence)  # 0.0-1.0
print(result.confidence_building_level)
```

#### RouteInfo
Information about a route between two points.

```python
route = client.route(source, target, mode=TravelMode.DRIVING)
print(f"Distance: {route.distance_km} km")
print(f"Duration: {route.duration_minutes} minutes")
```

#### DistanceMatrixResult
Result from distance matrix calculations.

```python
result = client.distance_matrix(sources, targets)
# result.distances[i][j] - distance in meters
# result.durations[i][j] - duration in seconds
```

### Enums

#### TravelMode
```python
from maps_sdk import TravelMode

TravelMode.DRIVING    # "drive"
TravelMode.WALKING    # "walk"
TravelMode.CYCLING    # "bike"
TravelMode.TRUCK      # "truck"
```

#### DistanceUnit
```python
from maps_sdk import DistanceUnit

DistanceUnit.KILOMETERS  # "km"
DistanceUnit.MILES       # "mi"
DistanceUnit.METERS      # "m"
```

## API Reference

### LocationClient

High-level client for location services.

#### Methods

##### `geocode(query: str) -> List[GeocodingResult]`
Convert address text to geographic coordinates.

```python
results = client.geocode("New York, NY")
for result in results:
    print(f"{result.address.formatted_address}")
    print(f"({result.location.latitude}, {result.location.longitude})")
    print(f"Confidence: {result.confidence:.2%}")
```

##### `reverse_geocode(location: GeoPoint) -> List[Address]`
Convert coordinates to address.

```python
location = GeoPoint(latitude=40.7128, longitude=-74.0060)
addresses = client.reverse_geocode(location)
```

##### `autocomplete(query: str, limit: int = 5) -> List[AutocompleteResult]`
Get address suggestions as user types.

```python
suggestions = client.autocomplete("San", limit=10)
```

##### `distance_matrix(sources: List[GeoPoint], targets: List[GeoPoint], mode: TravelMode = TravelMode.DRIVING, units: DistanceUnit = DistanceUnit.KILOMETERS) -> DistanceMatrixResult`
Calculate distances between multiple locations.

```python
sources = [GeoPoint(37.7749, -122.4194), GeoPoint(34.0522, -118.2437)]
targets = [GeoPoint(40.7128, -74.0060)]
result = client.distance_matrix(sources, targets, mode=TravelMode.DRIVING)
```

##### `route(source: GeoPoint, target: GeoPoint, mode: TravelMode = TravelMode.DRIVING) -> RouteInfo`
Calculate route between two points.

```python
source = GeoPoint(37.7749, -122.4194)
target = GeoPoint(40.7128, -74.0060)
route = client.route(source, target, mode=TravelMode.DRIVING)
```

### GeoapifyProvider

Geoapify API implementation.

Base URL: `https://api.geoapify.com/v1`

Free tier limits:
- Geocoding: 3,000 requests/day
- Address Autocomplete: 3,000 requests/day
- Distance Matrix: 3,000 requests/day
- Route Matrix: 3,000 requests/day

## Error Handling

The SDK provides specific exception classes for different error scenarios:

```python
from maps_sdk import (
    LocationSDKError,      # Base exception
    ValidationError,       # Input validation failed
    APIError,             # API request failed
    AuthenticationError,  # Invalid API key
    RateLimitError        # Rate limit exceeded
)

try:
    results = client.geocode("Address")
except ValidationError as e:
    print(f"Invalid input: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Extending with Custom Providers

### Implementing a Custom Provider

To add support for a new vendor (Google Maps, Mapbox, etc.), implement the `BaseLocationProvider` interface:

```python
from maps_sdk import BaseLocationProvider, GeoPoint, Address, GeocodingResult

class GoogleMapsProvider(BaseLocationProvider):
    """Google Maps API implementation."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    
    def geocode(self, query: str) -> List[GeocodingResult]:
        # Implement Google Maps geocoding
        url = f"{self.BASE_URL}/geocode/json"
        params = {"address": query, "key": self.api_key}
        response = self._make_request(url, params=params)
        
        # Parse response and return List[GeocodingResult]
        pass
    
    def reverse_geocode(self, location: GeoPoint) -> List[Address]:
        # Implement Google Maps reverse geocoding
        pass
    
    def autocomplete(self, query: str, limit: int = 5) -> List[AutocompleteResult]:
        # Implement Google Maps autocomplete
        pass
    
    def distance_matrix(self, sources, targets, mode, units) -> DistanceMatrixResult:
        # Implement Google Maps distance matrix
        pass
    
    def route(self, source, target, mode) -> RouteInfo:
        # Implement Google Maps routing
        pass

# Use with existing client code - no changes needed!
client = LocationClient(provider=GoogleMapsProvider(api_key="google_api_key"))
results = client.geocode("Address")  # Same interface!
```

### Key Design Patterns

1. **Abstract Factory Pattern** - `BaseLocationProvider` defines the interface
2. **Dependency Injection** - Provider injected into `LocationClient`
3. **Strategy Pattern** - Different implementations can be swapped
4. **Data Classes** - Clean, immutable data models
5. **Context Manager Protocol** - Resource cleanup with `with` statements

## Configuration

### Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('maps_sdk')
logger.setLevel(logging.DEBUG)

client = LocationClient(provider=GeoapifyProvider(api_key="key"))
# Debug logs will now be printed
```

### Custom Timeout

```python
# Set custom request timeout (default: 10 seconds)
provider = GeoapifyProvider(api_key="key", timeout=30)
client = LocationClient(provider=provider)
```

## Testing

### Running Tests

```bash
python -m pytest ./tests/tests.py -v
# or
python -m unittest ./tests/tests.py -v
```

### Test Coverage

```bash
pip install coverage
coverage run -m unittest ./tests/tests.py
coverage report -m
coverage html  # generates htmlcov/index.html
```

### Mocking API Calls

```python
from unittest.mock import patch, Mock

with patch('maps_sdk.requests.Session.get') as mock_get:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "features": [{"properties": {...}, "geometry": {...}}]
    }
    mock_get.return_value = mock_response
    
    results = client.geocode("Address")
    assert len(results) == 1
```

## Best Practices

### 1. Use Context Managers
```python
with LocationClient(provider=GeoapifyProvider(api_key="key")) as client:
    results = client.geocode("Address")
    # Automatic cleanup
```

### 2. Handle Exceptions
```python
try:
    results = client.geocode(user_input)
except ValidationError:
    # Handle invalid input
except RateLimitError:
    # Implement retry logic
except APIError:
    # Log and handle API errors
```

### 3. Validate Confidence Scores
```python
results = client.geocode("Address")
for result in results:
    if result.confidence >= 0.95:
        use_result(result)
    elif result.confidence >= 0.7:
        ask_user_for_confirmation(result)
    else:
        request_more_details()
```

### 4. Cache Results
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_coordinates(address: str) -> GeoPoint:
    results = client.geocode(address)
    return results[0].location if results else None
```

### 5. Batch Operations Efficiently
```python
addresses = ["Address 1", "Address 2", ...]
results = [client.geocode(addr)[0] for addr in addresses]
```

## Limitations (subject to the API vendor choosen)

- **Rate Limits**: 3,000 requests/day for free tier (Geoapify)
- **Maximum Locations**: Distance matrix limited to 10x10 (100 pairs) (Geoapify)

## Comparison with Alternatives

| Feature | This SDK | Google Maps | Mapbox | Nominatim |
|---------|----------|-------------|--------|-----------|
| Vendor Agnostic | ✓ | ✗ | ✗ | ✗ |
| Free Tier | ✓ | ✓ | ✓ | ✓ |
| Geocoding | ✓ | ✓ | ✓ | ✓ |
| Reverse Geocoding | ✓ | ✓ | ✓ | ✓ |
| Autocomplete | ✓ | ✓ | ✓ | Limited |
| Distance Matrix | ✓ | ✓ | ✓ | ✗ |
| Routing | ✓ | ✓ | ✓ | Limited |
| Easy Provider Switching | ✓ | ✗ | ✗ | ✗ |

## Troubleshooting

### Authentication Error
```
AuthenticationError: Invalid API key or insufficient permissions
```
**Solution**: Verify your API key is correct and has required permissions.

### Rate Limit Error
```
RateLimitError: API rate limit exceeded. Please try again later.
```
**Solution**: Implement exponential backoff or upgrade your plan.

### Validation Error
```
ValidationError: Query must be a non-empty string
```
**Solution**: Check your input parameters match expected types.

## Contributing

To add support for a new provider:

1. Create a new class inheriting from `BaseLocationProvider`
2. Implement all abstract methods
3. Add comprehensive tests
4. Update documentation with provider-specific details

## License

MIT License - see LICENSE file

## Support

For issues, questions, or suggestions:
- Check the [examples.py](examples/examples.py) file for usage examples
- Review the [tests.py](tests/tests.py) file for test patterns
- Consult the Geoapify API documentation at https://apidocs.geoapify.com/

## Changelog

### Version 1.0.0 (Initial Release)
- Vendor-agnostic SDK design
- Geoapify provider implementation as a starter
- Core APIs: geocoding, reverse geocoding, autocomplete, distance matrix, routing
- Comprehensive error handling
- Full type hints
- Unit tests included
- Complete documentation

---

## Want to help extend this project with other vendors or features?

### Feel free to clone this project and add your bugfixes / enhancements by raising a pull request to the main branch.
- Please ensure that your tets cases are passing and your code doesn't drift away from the code style of this repo.

---
**Made with ❤️ for developers who want clean, maintainable location services code.**

[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
