from uuid import uuid4
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, DateTime, BigInteger, String, Text
from sqlalchemy.sql import func

from app.db.session import Base


__all__ = (
    'QUERY_STATUS',
    'Query',
)


class QUERY_STATUS(Enum):
    CREATED = 'created'
    COMPILING = 'compiling'
    COMPILED = 'compiled'
    RUNNING = 'running'
    CANCELLING = 'cancelling'
    CANCELED = 'canceled'
    DONE = 'done'
    ERROR_ACCESS_DENIED = 'no_access'
    ERROR_EXECUTION_ERROR = 'sql_error'


class Query(Base):
    __tablename__ = 'queries'

    id = Column(BigInteger, primary_key=True)
    guid = Column(String(36), nullable=False, default=lambda: str(uuid4()), unique=True, index=True)
    query = Column(Text, nullable=False)
    last_run_id = Column(BigInteger)
    compiled_query = Column(Text, nullable=True)
    status = Column(String(64), default=QUERY_STATUS.CREATED.value, nullable=False)
    error_description = Column(Text)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_onupdate=func.now())
