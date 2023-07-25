from pydantic import BaseSettings


class Settings(BaseSettings):
    port: int = 8000

    debug: bool = False
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "task_broker.log"
    db_connection_string: str = 'postgresql+asyncpg://postgres:dwh@db.lan:5432/broker'
    db_migration_connection_string: str = 'postgresql+psycopg2://postgres:dwh@db.lan:5432/broker'
    mq_connection_string: str = 'amqp://dwh:dwh@rabbit.lan:5672'

    exchange_compile: str = 'query_compile'
    query_compile: str = 'compile_tasks'
    query_compile_result: str = 'compile_results'

    exchange_execute: str = 'query_execute'
    query_execute_result: str = 'execute_results'

    api_query_executor: str = 'http://query-executor.lan:8000/v1'
    api_iam: str = 'http://iam.lan:8000'
    api_data_catalog: str = 'http://data-catalog.lan:8000'

    class Config:
        env_prefix = "dwh_task_broker_"
        case_sensitive = False

    """RabbitMQ constants"""
    heartbeat: int = 5
    connection_attempts: int = 5
    retry_delay: int = 10
    timeout: int = 15


settings = Settings()
