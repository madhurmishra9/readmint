# Migrations

History/audit tables are created automatically by `services/history.py` via
`metadata.create_all` on first use, so Alembic is optional for the single
`readmint_runs` table today.

When the schema grows beyond one table, initialise Alembic here:

```bash
cd backend
alembic init migrations
# set sqlalchemy.url from RF_DATABASE_URL, then:
alembic revision --autogenerate -m "init"
alembic upgrade head
```
