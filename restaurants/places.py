"""Data access for restaurants.

Views only call get_restaurants(). To switch from Google Places to a
downloaded dataset (e.g. Kaggle), replace the body of get_restaurants()
and keep the return shape the same.

Google terms restrict caching/bulk storage of Places data, so we call the
API at request time and store nothing.
"""
import os

import requests

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.priceLevel",
        "places.servesVegetarianFood",
        "places.googleMapsUri",
    ]
)

# Google price level -> display + sort order
PRICE_LABELS = {
    "PRICE_LEVEL_FREE": "Free",
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}

# Diet filter -> Google place type (None = use the servesVegetarianFood field)
DIET_TYPES = {
    "vegan": "vegan_restaurant",
    "halal": "halal_restaurant",
}

PRICE_CHOICES = ["$", "$$", "$$$", "$$$$"]
DIET_CHOICES = ["vegetarian", "vegan", "halal"]


class PlacesError(Exception):
    """Raised with a user-friendly message when the data source fails."""


def _normalize(place):
    price = PRICE_LABELS.get(place.get("priceLevel", ""), "")
    veg = place.get("servesVegetarianFood")  # True / False / None (unknown)
    return {
        "id": place.get("id", ""),
        "name": place.get("displayName", {}).get("text", "(no name)"),
        "address": place.get("formattedAddress", ""),
        "price": price,
        "vegetarian": veg,
        "lat": place.get("location", {}).get("latitude"),
        "lng": place.get("location", {}).get("longitude"),
        "maps_url": place.get("googleMapsUri", ""),
    }


def _where(area):
    return "near me" if area == "me" else f"in {area}"


def get_restaurants(area="New York", price="", diet="", lat=None, lng=None, api_key=None):
    """Return a list of restaurant dicts for the given filters.

    area:  free text place/neighborhood, e.g. "Brooklyn"
    price: "", "$", "$$", "$$$" or "$$$$"
    diet:  "", "vegetarian", "vegan" or "halal"
    lat/lng: optional user location; results are biased toward it (~2 km)
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise PlacesError("GOOGLE_API_KEY is not set. Add it to your .env file.")

    use_location = lat is not None and lng is not None
    area = (area or "").strip()
    if use_location and not area:
        area = "me"  # "restaurants near me", biased by the coordinates below
    else:
        area = area or "New York"
        if "new york" not in area.lower() and "nyc" not in area.lower():
            area = f"{area}, New York"

    body = {"maxResultCount": 20, "languageCode": "en"}
    if use_location:
        body["locationBias"] = {
            "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": 2000.0}
        }
    if diet in DIET_TYPES:
        body["textQuery"] = f"{diet} restaurants {_where(area)}"
        body["includedType"] = DIET_TYPES[diet]
    elif diet == "vegetarian":
        body["textQuery"] = f"vegetarian restaurants {_where(area)}"
    else:
        body["textQuery"] = f"healthy restaurants {_where(area)}"

    try:
        resp = requests.post(
            SEARCH_URL,
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": FIELD_MASK,
            },
            timeout=10,
        )
    except requests.RequestException:
        raise PlacesError("Could not reach Google Places. Try again in a moment.")

    if resp.status_code != 200:
        raise PlacesError(
            f"Google Places returned an error ({resp.status_code}). "
            "Check the API key, billing, and that Places API (New) is enabled."
        )

    places = [_normalize(p) for p in resp.json().get("places", [])]

    # Filters applied here so the behaviour is the same for any data source.
    if price:
        places = [p for p in places if p["price"] == price]
    if diet == "vegetarian":
        places = [p for p in places if p["vegetarian"] is True]

    return places
