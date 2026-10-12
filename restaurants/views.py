import os

from django.shortcuts import render

from .places import DIET_CHOICES, PRICE_CHOICES, PlacesError, get_restaurants


def _coord(value, low, high):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if low <= number <= high else None


def search(request):
    area = request.GET.get("area", "").strip()
    price = request.GET.get("price", "")
    diet = request.GET.get("diet", "")
    if price not in PRICE_CHOICES:
        price = ""
    if diet not in DIET_CHOICES:
        diet = ""

    user_lat, user_lng = _coord(request.GET.get("lat"), -90, 90), _coord(request.GET.get("lng"), -180, 180)
    if user_lat is None or user_lng is None:
        user_lat = user_lng = None

    searched = "area" in request.GET
    restaurants, error = [], ""
    if searched:
        try:
            restaurants = get_restaurants(area=area, price=price, diet=diet, lat=user_lat, lng=user_lng)
        except PlacesError as exc:
            error = str(exc)

    return render(
        request,
        "restaurants/search.html",
        {
            "area": area,
            "price": price,
            "diet": diet,
            "price_choices": PRICE_CHOICES,
            "diet_choices": DIET_CHOICES,
            "restaurants": restaurants,
            "map_points": [
                {"name": r["name"], "lat": r.get("lat"), "lng": r.get("lng"), "price": r.get("price", ""), "url": r.get("maps_url", "")}
                for r in restaurants
                if r.get("lat") is not None and r.get("lng") is not None
            ],
            "maps_key": os.environ.get("GOOGLE_MAPS_JS_KEY", ""),
            "user_lat": user_lat,
            "user_lng": user_lng,
            "error": error,
            "searched": searched,
        },
    )
