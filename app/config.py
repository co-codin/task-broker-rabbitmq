from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = True
    db_connection_string: str = 'postgresql+asyncpg://postgres:dwh@db:5432'
    mq_connection_string: str = 'amqp://dwh:dwh@rabbit:5672'

    exchange_compile = 'query_compile'
    query_compile = 'compile_tasks'
    query_compile_result = 'compile_results'

    exchange_execute = 'query_execute'
    query_execute_result = 'execute_results'

    api_query_executor = 'http://query_executor:8000/v1'

    """RabbitMQ constants"""
    heartbeat: int = 5
    connection_attempts: int = 5
    retry_delay: int = 10
    timeout: int = 15


settings = Settings()
