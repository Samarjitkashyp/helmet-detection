from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DEFAULT_SETTINGS, Setting


def load_settings(db: Session) -> dict:
    """Detection settings: defaults overridden by rows edited in the admin panel."""
    values = dict(DEFAULT_SETTINGS)
    values.update({s.key: s.value for s in db.scalars(select(Setting))})
    return values
