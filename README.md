# HealthyFoodsNYC

Django app: find NYC restaurants and filter by area, price, and diet (Google Places API).

## Run locally (Mac)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your Google API key in .env
python manage.py runserver
```

Open http://127.0.0.1:8000

## Tests (no API key needed)

```bash
python manage.py test
```

## Notes

- `restaurants/places.py` is the only file that talks to the data source.
  Views call `get_restaurants()`. To switch to a Kaggle dataset, replace its body.
- Google terms restrict caching/bulk storage of Places data, so nothing is stored.
- Never commit `.env`.
