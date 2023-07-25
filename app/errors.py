from fastapi import status


class APIError(Exception):
    status_code: int


class NoAMQPConnection(APIError):
    def __init__(self, mq_connection_str: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._mq_connection_str = mq_connection_str

    def __str__(self):
        return f"No AMQP connection established with {self._mq_connection_str}"


class NoDBConnection(APIError):
    def __init__(self, db_connection_str: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._db_connection_str = db_connection_str

    def __str__(self):
        return f"No DB connection established with {self._db_connection_str}"


class DBError(APIError):
    def __init__(self):
        self.status_code = status.HTTP_400_BAD_REQUEST

    def __str__(self):
        return f"DB error occurred during transaction"


class NoTaskFound(APIError):
    def __init__(self, guid: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._guid = guid

    def __str__(self):
        return f"Task with guid={self._guid} was not found"


class DeserializeJSONQueryError(Exception):
    def __init__(self, query):
        self._query = query

    def __str__(self):
        return f"Couldn't deserialize the input json query {self._query}"


class DictKeyError(Exception):
    def __init__(self, key: str, dict_: dict):
        self._key = key
        self._dict = dict_

    def __str__(self):
        return f"Key {self._key} not found in {self._dict}"


class QueryExecutorTimeoutError(Exception):
    def __init__(self, api_query_executor_url):
        self.api_query_executor_url = api_query_executor_url

    def __str__(self):
        return f"No response from {self.api_query_executor_url}"
