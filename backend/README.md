# Backend

FastAPI implementation starts on Day 2. Planned internal packages:

```text
app/
├── api/
├── core/
├── db/
├── identity/
├── production/
├── quality/
├── intelligence/
├── alerts/
├── simulator/
└── tests/
```

HTTP handlers will depend on service interfaces; business rules and SQL queries will not be placed directly in route functions.

