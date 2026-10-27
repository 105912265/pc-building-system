# Switch Shared Price Lookup v1 from OpenAI to Gemini 2.5 Flash-Lite

This is a **replacement provider adapter**, not a new database migration.

## Files to place in the existing repository

```
pc-building-system/
├── backend/
│   ├── price_web_search.py          <-- REPLACE
│   ├── price_routes.py              <-- REPLACE (one env key check)
│   └── tests/
│       └── test_gemini_price.py     <-- ADD
├── requirements-price.txt          <-- REPLACE
├── price-env.example               <-- REPLACE (sample only)
└── README-GEMINI-SWITCH.md         <-- ADD
```

Leave `backend/main.py`, `backend/database.py`, `backend/price_auth.py`, `.env`, the MySQL schema, and imported component records in place. Previously created tables `price_account` and `ai_price_usage` remain valid.

## Installation

1. Get a Gemini API key from https://aistudio.google.com/api-keys . Your project must have permission to use `gemini-2.5-flash-lite` (Google has limited 2.5-model access for some newer projects).
2. In the activated virtual environment, from repo root:

   ```powershell
   python -m pip install -r requirements-price.txt
   ```

   `google-genai` is the official package. You do not have to uninstall `openai` immediately; it will simply no longer be used by these routes.

3. Add to your existing `.env` while retaining MySQL/JWT settings:

   ```env
   GEMINI_API_KEY=YOUR_SECRET_KEY
   GEMINI_PRICE_MODEL=gemini-2.5-flash-lite
   ```

   Remove old `OPENAI_API_KEY`/`OPENAI_PRICE_MODEL` variables if unused elsewhere. Never commit `.env`.
4. Ensure `backend/price_routes.py` now checks `GEMINI_API_KEY` and imports `find_online_price` from the replacement `price_web_search.py`.
5. Test locally without API calls:

   ```powershell
   python -m unittest backend.tests.test_price_features backend.tests.test_gemini_price -v
   ```

6. Restart:

   ```powershell
   python -m uvicorn backend.main:app --reload
   ```

7. Open `http://127.0.0.1:8000/docs`; authenticate using your existing test account, first call `GET /auth/me` and `GET /components/{id}/price`, then intentionally test **one** `POST /components/{id}/price-check` with your free-tier provider key.

8. Verify stored type, source and checked date with `GET /components/{id}/price` and in MySQL:

   ```sql
   SELECT component_id, model, price,
     JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.type')) AS price_type,
     JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.source_url')) AS source_url,
     JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.checked_at')) AS checked_at
   FROM component WHERE component_id = 86;
   ```

## How Gemini price lookup works

- The first API call runs Gemini with Google Search grounding and obtains citations. It **must actually execute a search** or the price is rejected.
- A second, ungrounded Gemini call converts grounded research into JSON (the old OpenAI-style constrained JSON+search combination is not used).
- A candidate is rejected if no grounded source, no explicit matching price in the grounded research, no compatible product title, unknown condition, wrong currency, or implausible amount.
- Grounding URLs can be Google redirect URLs rather than retailer-direct links. Show their source title/link and disclose that a user should confirm the listing before purchasing. **Source attribution is not independent proof that the price is current.**
- The pre-existing FastAPI route persists an accepted price into `component.price` and `specifications.price_metadata`. All accounts see it. A manual refresh consumes one account credit, even if no offer is verified.
- No real payment subscriptions are included. Keep Free/Premium as demonstration tiers.

## Current-access caveat

Google's 2.5 Flash-Lite model page warns that some **new projects are not granted 2.5 access**. If your key gets a model-not-found/permission error, confirm model access in Google AI Studio first. Do not silently switch to a model with different pricing. See:
- https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/google-search

## Safety and limits

This is a **university demo**. Do not expose public registration on the open internet with an unrestricted provider key. API provider quotas are separate from your application quotas (Free 3/day, Premium 30/day), and these limits don't guarantee Google will allow that many daily requests. Google quotas can vary by project. A failed provider lookup does not overwrite existing MySQL prices.
