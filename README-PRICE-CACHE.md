# Phase 5: AI price lookup + shared cache (backend v1)

## What this version does
- Public GET of latest cached/estimated component price without spending API credits.
- Email/password sign-up and login with scrypt password hashing and short-lived JWTs.
- **Free = 3** and **Premium = 30** AI searches/day, reset at midnight UTC.
- Uses OpenAI **Responses API + `web_search`** to find an Australian-dollar offer.
- Checks the cited URL, model identifier, currency, condition, and price bounds *before* saving.
- If a search is accepted, atomically updates `component.price` and `component.specifications.price_metadata` (type/source/check timestamp). Everyone sees the stored result without a new API call.
- If search cannot substantiate a match, returns an error and **does not modify the old price**.
- Every attempted external AI call consumes one daily search credit, even if no suitable result is found; viewing cached results costs no credits.
- No real payments. Premium is a local demonstration tier enabled by an authenticated administrator (no payment processing).

## Limitations to explain to your tutor
- Search-supported LLM output with a cited source is **not a guaranteed retail price**. Results may be stale, wrong or sold out; confirm the linked product page before purchase. This v1 validates source citations and model information, but **does not independently re-fetch retailer pages** and verify displayed amount.
- Daily quotas are per account, not IP address. Open public registration plus paid search is **not safe for uncontrolled Internet deployment** without signup throttling, email verification, spending caps and abuse prevention. **Run locally for your presentation only.**
- Simultaneous lookups by different accounts for the same component may still cause duplicate search API calls. A single account's daily quota increments atomically.
- No historical prices: `component.price` holds the latest accepted value; earlier prices are replaced. Existing Phase 3 prices continue until user explicitly refreshes.
- The `specifications` JSON metadata contains the last check, not a separate table/column. Keeping metadata nested here is pragmatic for this assignment, but a price-history table would be more extensible for production.
- You must display online-search source links as clickable links in your future website to meet citation visibility guidance.

## Setup — follow in order
1. Commit/back up the current working branch and take a full MySQL Workbench **Dump Structure and Data** backup.
2. Extract package into the repository root. It adds new files; **do not replace `backend/main.py` or `backend/database.py`**.
3. In MySQL Workbench, execute `backend/migrations/002_shared_price_lookup.sql` (on a copy first if possible). This creates exactly two new tables, `price_account` and `ai_price_usage`. The existing `component` schema does not change.
4. In your activated `.venv` install dependencies: `python -m pip install -r requirements-price.txt`. Keep your working `mysql-connector-python` v26.10.0 installation.
5. Add values in `.env`: `JWT_SECRET` (a unique random token, 32+ chars), `OPENAI_API_KEY` (your own API project key), `OPENAI_PRICE_MODEL=gpt-6-luna`. Do **not** commit `.env`. Set a low API spending limit in the provider dashboard; price searches cost money. ChatGPT Plus does **not** include API credits.
6. At the bottom of your existing `backend/main.py` (after `app = FastAPI(...)`), add only:

   ```python
   from backend.price_auth import router as price_auth_router
   from backend.price_routes import router as price_router
   app.include_router(price_auth_router)
   app.include_router(price_router)
   ```

7. Restart: `python -m uvicorn backend.main:app --reload` from the repository root.
8. Go to `http://127.0.0.1:8000/docs` and try in this order:
   - `POST /auth/register` using a NEW test email and password (10+ characters).
   - `POST /auth/login` to obtain a token.
   - Click **Authorize** and paste the token (Swagger HTTP Bearer scheme).
   - `GET /auth/me` to confirm free tier, 3 searches/day.
   - `GET /components/86/price` to view an existing component without any credits.
   - `POST /components/86/price-check` to explicitly refresh its price. **This incurs real API costs.**
   - `GET /components/86/price` again and check that the price type is `online_checked`, with seller/URL/timestamp, if a valid offer was found.
   - Log in as a second account: read GET `/components/86/price`; shared cached price needs no API call.
9. Use `python -m unittest backend.tests.test_price_features -v` for unit checks. This does not contact an external API or write to MySQL.

## Demonstrate Admin + Premium (without payments)
First register TWO test accounts (one admin-to-be, one Premium-to-be).
To bootstrap the **first admin** (development only), run in MySQL Workbench:

```sql
UPDATE price_account AS pa
JOIN `user` AS u ON u.user_id = pa.user_id
SET pa.role = 'admin'
WHERE u.email = 'admin-demo@example.com';
```

Sign in to that account, click **Authorize**, then call **PATCH `/auth/admin/accounts/{user_id}/tier`** using the Premium-to-be account user ID and body:

```json
{"account_tier":"premium"}
```

The admin-only endpoint changes the target tier; free users get **403 Forbidden**. Call `/auth/me` as the upgraded account and verify its daily limit is 30. **Never allow arbitrary users to choose Premium or Admin at registration.**


## Database verification
```sql
SELECT component_id, model, price,
       JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.type')) AS price_type,
       JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.checked_at')) AS checked_at,
       JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.source_url')) AS source_url
FROM component WHERE component_id = 86;

SELECT user_id, usage_date, used_count
FROM ai_price_usage ORDER BY usage_date DESC, user_id;
```

## Git milestone
Once /register, /login, /me, and /components/{id}/price all work, commit before using paid API calls:

```
git status
git add backend/migrations/002_shared_price_lookup.sql backend/price_auth.py backend/price_routes.py backend/price_web_search.py backend/tests/test_price_features.py backend/main.py requirements-price.txt README-PRICE-CACHE.md price-env.example
git diff --cached --name-only
git commit -m "feat: add account quotas and shared component price cache"
git push
```

Do not commit real `.env` files, passwords, backups, tokens, or API keys.
