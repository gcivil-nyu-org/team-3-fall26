from unittest.mock import MagicMock, patch

from django.test import TestCase

from .places import PlacesError, get_restaurants

FAKE = {
    "places": [
        {"id": "a", "displayName": {"text": "Veg Cheap"}, "formattedAddress": "1 A St",
         "priceLevel": "PRICE_LEVEL_INEXPENSIVE", "servesVegetarianFood": True},
        {"id": "b", "displayName": {"text": "Meat Mid"}, "formattedAddress": "2 B St",
         "priceLevel": "PRICE_LEVEL_MODERATE", "servesVegetarianFood": False},
        {"id": "c", "displayName": {"text": "Unknown"}, "formattedAddress": "3 C St"},
    ]
}


def fake_response(status=200, data=FAKE):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data
    return r


@patch("restaurants.places.requests.post")
class GetRestaurantsTests(TestCase):
    def test_no_filters_returns_all(self, post):
        post.return_value = fake_response()
        self.assertEqual(len(get_restaurants(api_key="k")), 3)

    def test_price_filter(self, post):
        post.return_value = fake_response()
        res = get_restaurants(price="$", api_key="k")
        self.assertEqual([r["name"] for r in res], ["Veg Cheap"])

    def test_vegetarian_filter_excludes_false_and_unknown(self, post):
        post.return_value = fake_response()
        res = get_restaurants(diet="vegetarian", api_key="k")
        self.assertEqual([r["name"] for r in res], ["Veg Cheap"])

    def test_vegan_uses_place_type(self, post):
        post.return_value = fake_response()
        get_restaurants(diet="vegan", api_key="k")
        self.assertEqual(post.call_args.kwargs["json"]["includedType"], "vegan_restaurant")

    def test_api_error_raises_friendly_message(self, post):
        post.return_value = fake_response(status=403)
        with self.assertRaises(PlacesError):
            get_restaurants(api_key="k")

    def test_missing_key_raises(self, post):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(PlacesError):
                get_restaurants()


@patch("restaurants.views.get_restaurants")
class ViewTests(TestCase):
    def test_page_loads_without_search(self, gr):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        gr.assert_not_called()

    def test_search_shows_results(self, gr):
        gr.return_value = [{"name": "Test Place", "address": "x", "price": "$$",
                            "vegetarian": True, "maps_url": ""}]
        resp = self.client.get("/", {"area": "Brooklyn", "price": "$$", "diet": "vegetarian"})
        self.assertContains(resp, "Test Place")

    def test_error_is_shown(self, gr):
        from .places import PlacesError
        gr.side_effect = PlacesError("boom")
        self.assertContains(self.client.get("/", {"area": "x"}), "boom")
