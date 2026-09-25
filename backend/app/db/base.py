from sqlalchemy import MetaData

# SQLAlchemy Core, not the full ORM, per docs/backend-architecture/00.md:
# explicit select()/insert() construction, no model classes duplicating
# the Pydantic schemas already used for API validation. Every table
# defined under app/models/ attaches to this one MetaData instance, and
# Alembic's env.py targets it for autogeneration.
metadata = MetaData()
