"""
Usage Examples for Location SDK

This file demonstrates how to use the Location SDK for various use cases.
"""

from ..maps_sdk import (
    LocationClient,
    GeoapifyProvider,
    GeoPoint,
    Address,
    TravelMode,
    DistanceUnit,
    ValidationError,
    APIError,
    AuthenticationError,
)


# ============================================================================
# Example 1: Basic Geocoding
# ============================================================================

def example_basic_geocoding():
    """Convert an address to coordinates."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    # Initialize client with Geoapify provider
    client = LocationClient(provider=GeoapifyProvider(api_key=api_key))
    
    try:
        # Geocode an address
        results = client.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
        
        if results:
            top_result = results[0]
            print(f"Address: {top_result.address.formatted_address}")
            print(f"Location: {top_result.location.latitude}, {top_result.location.longitude}")
            print(f"Confidence: {top_result.confidence}")
        else:
            print("No results found")
    
    except ValidationError as e:
        print(f"Validation Error: {e}")
    except APIError as e:
        print(f"API Error: {e}")
    finally:
        client.close()


# ============================================================================
# Example 2: Reverse Geocoding
# ============================================================================

def example_reverse_geocoding():
    """Convert coordinates to an address."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            # Create a location point (Google headquarters)
            location = GeoPoint(latitude=37.4220, longitude=-122.0841)
            
            # Reverse geocode
            addresses = client.reverse_geocode(location)
            
            for addr in addresses:
                print(f"Address: {addr.formatted_address}")
                print(f"City: {addr.city}, Country: {addr.country}")
        
        except APIError as e:
            print(f"API Error: {e}")


# ============================================================================
# Example 3: Address Autocomplete
# ============================================================================

def example_address_autocomplete():
    """Get address suggestions as user types."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            # Get autocomplete suggestions
            query = "Gabelsbergerstr 14"
            results = client.autocomplete(query, limit=5)
            
            print(f"Suggestions for '{query}':")
            for idx, result in enumerate(results, 1):
                print(f"\n{idx}. {result.address.formatted_address}")
                print(f"   Location: ({result.location.latitude}, {result.location.longitude})")
        
        except APIError as e:
            print(f"API Error: {e}")


# ============================================================================
# Example 4: Distance Matrix Calculation
# ============================================================================

def example_distance_matrix():
    """Calculate distances between multiple locations."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            # Define source and target locations
            sources = [
                GeoPoint(latitude=37.4220, longitude=-122.0841),  # Google HQ
                GeoPoint(latitude=37.3382, longitude=-121.8863),  # San Jose
            ]
            
            targets = [
                GeoPoint(latitude=34.0522, longitude=-118.2437),  # Los Angeles
                GeoPoint(latitude=39.7392, longitude=-104.9903),  # Denver
            ]
            
            # Calculate distance matrix
            result = client.distance_matrix(
                sources=sources,
                targets=targets,
                mode=TravelMode.DRIVING,
                units=DistanceUnit.KILOMETERS,
            )
            
            # Display results
            print("Distance Matrix (in kilometers) and Duration (in minutes):")
            print("\nFrom\\To            | LA       | Denver")
            print("-------------------+----------+----------")
            
            for i, source in enumerate(sources):
                print(f"Location {i+1}     | ", end="")
                for j, target in enumerate(targets):
                    distance_km = result.distances[i][j] / 1000
                    duration_min = result.durations[i][j] / 60
                    print(f"{distance_km:6.1f} km | ", end="")
                print()
        
        except ValidationError as e:
            print(f"Validation Error: {e}")
        except APIError as e:
            print(f"API Error: {e}")


# ============================================================================
# Example 5: Route Information
# ============================================================================

def example_route_info():
    """Get route information between two points."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            source = GeoPoint(latitude=37.4220, longitude=-122.0841)  # Google HQ
            target = GeoPoint(latitude=34.0522, longitude=-118.2437)  # Los Angeles
            
            # Get route information
            route = client.route(
                source=source,
                target=target,
                mode=TravelMode.DRIVING,
            )
            
            print(f"Route Information:")
            print(f"Distance: {route.distance_km:.2f} km ({route.distance} m)")
            print(f"Duration: {route.duration_minutes:.2f} minutes ({route.duration} seconds)")
        
        except APIError as e:
            print(f"API Error: {e}")


# ============================================================================
# Example 6: Handling Different Travel Modes
# ============================================================================

def example_different_travel_modes():
    """Calculate distances for different travel modes."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            source = GeoPoint(latitude=37.7749, longitude=-122.4194)  # San Francisco
            target = GeoPoint(latitude=37.8044, longitude=-122.2712)  # Oakland
            
            modes = [
                TravelMode.DRIVING,
                TravelMode.WALKING,
                TravelMode.CYCLING,
            ]
            
            print("Travel times between San Francisco and Oakland:\n")
            
            for mode in modes:
                try:
                    route = client.route(source=source, target=target, mode=mode)
                    print(f"{mode.value.upper():10} | {route.duration_minutes:6.1f} min | {route.distance_km:7.2f} km")
                except APIError:
                    print(f"{mode.value.upper():10} | Not available")
        
        except Exception as e:
            print(f"Error: {e}")


# ============================================================================
# Example 7: Error Handling and Validation
# ============================================================================

def example_error_handling():
    """Demonstrate proper error handling."""
    api_key = "INVALID_API_KEY"
    
    try:
        client = LocationClient(provider=GeoapifyProvider(api_key=api_key))
        
        # This will fail due to invalid API key
        results = client.geocode("New York, NY")
        
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except ValidationError as e:
        print(f"Validation error: {e}")
    except APIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# ============================================================================
# Example 8: Custom Address Validation
# ============================================================================

def example_address_validation():
    """Find and validate addresses before use."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            # Geocode with confidence checking
            results = client.geocode("123 Main St, Springfield")
            
            for result in results:
                confidence = result.confidence or 0
                
                if confidence >= 0.95:
                    status = "✓ HIGH CONFIDENCE"
                elif confidence >= 0.7:
                    status = "~ MEDIUM CONFIDENCE"
                else:
                    status = "✗ LOW CONFIDENCE"
                
                print(f"{status} - {result.address.formatted_address}")
                print(f"  Confidence: {confidence:.2%}")
                print(f"  Location: ({result.location.latitude:.4f}, {result.location.longitude:.4f})")
                print()
        
        except APIError as e:
            print(f"API Error: {e}")


# ============================================================================
# Example 9: Batch Processing Multiple Addresses
# ============================================================================

def example_batch_geocoding():
    """Geocode multiple addresses."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    addresses = [
        "1600 Amphitheatre Parkway, Mountain View, CA",
        "1 Apple Park Way, Cupertino, CA",
        "350 Fifth Avenue, New York, NY",
    ]
    
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        print("Batch Geocoding Results:\n")
        
        for address in addresses:
            try:
                results = client.geocode(address)
                if results:
                    result = results[0]
                    print(f"✓ {address}")
                    print(f"  → ({result.location.latitude:.4f}, {result.location.longitude:.4f})")
                else:
                    print(f"✗ {address} - No results found")
            except APIError as e:
                print(f"✗ {address} - Error: {e}")
            
            print()


# ============================================================================
# Example 10: Context Manager Usage (Recommended)
# ============================================================================

def example_context_manager():
    """Use LocationClient with context manager for automatic cleanup."""
    api_key = "YOUR_GEOAPIFY_API_KEY"
    
    # Recommended approach - automatic cleanup
    with LocationClient(provider=GeoapifyProvider(api_key=api_key)) as client:
        try:
            results = client.geocode("Paris, France")
            if results:
                print(f"Found: {results[0].address.formatted_address}")
        except APIError as e:
            print(f"Error: {e}")
        # Session is automatically closed here


# ============================================================================
# Example 11: Custom Provider Implementation (Future Extension)
# ============================================================================

def example_custom_provider_structure():
    """
    This demonstrates how you would implement a custom provider for other vendors.
    
    Example: Google Maps, Mapbox, or Nominatim implementation would follow the same pattern.
    """
    
    # To implement a custom provider, you would:
    # 1. Create a new class that inherits from BaseLocationProvider
    # 2. Implement all abstract methods (geocode, reverse_geocode, etc.)
    # 3. Use the same GeoPoint, Address, and result classes
    # 4. No changes needed to client code - just swap the provider
    
    pass


if __name__ == "__main__":
    print("Location SDK Examples\n")
    print("=" * 50)
    
    # Uncomment the example you want to run
    # Make sure to set YOUR_GEOAPIFY_API_KEY first
    
    # example_basic_geocoding()
    # example_reverse_geocoding()
    # example_address_autocomplete()
    # example_distance_matrix()
    # example_route_info()
    # example_different_travel_modes()
    # example_error_handling()
    # example_address_validation()
    # example_batch_geocoding()
    # example_context_manager()
    
    print("\nNote: Replace 'YOUR_GEOAPIFY_API_KEY' with your actual API key")
    print("Get your free API key at: https://www.geoapify.com/")
