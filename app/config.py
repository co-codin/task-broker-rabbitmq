from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = True
    db_connection_string: str = 'postgresql+asyncpg://postgres:dwh@db:5432'
    mq_connection_string: str = 'amqp://dwh:dwh@rabbit:5672'

    exchange_compile = 'query_compile'
    query_compile = 'compile_tasks'
    query_compile_result = 'compile_results'


settings = Settings()
