## Testing

- Write tests for all service-layer functions.
- Use descriptive test names: `it("should return 404 when item not found")`.
- Mock only at system boundaries (HTTP, DB); never mock internal logic.
- Never hardcode values in tests that can become invalid over time or drift from the source of truth:
  - **Dates** — compute dynamically (e.g. `date.today() + timedelta(days=60)`)
  - **Prices and config values** — read from seed data constants or query the DB; never assume a specific dollar amount
  - **Reference data** (zip codes, item IDs) — define as named constants at the top of the test file with a comment pointing to the seed file, so drift is obvious
