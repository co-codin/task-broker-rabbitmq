from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "task_broker.log"
    db_connection_string: str = 'postgresql+asyncpg://postgres:dwh@db:5432/broker'
    db_migration_connection_string: str = 'postgresql+psycopg2://postgres:dwh@db:5432/broker'
    mq_connection_string: str = 'amqp://dwh:dwh@rabbit:5672'

    exchange_compile = 'query_compile'
    query_compile = 'compile_tasks'
    query_compile_result = 'compile_results'

    exchange_execute = 'query_execute'
    query_execute_result = 'execute_results'

    api_query_executor = 'http://query_executor:8000/v1'


settings = Settings()
