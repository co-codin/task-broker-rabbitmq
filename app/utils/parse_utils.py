import json

from app.errors import DeserializeJSONQueryError, DictKeyError


def get_payload_value(payload: dict, key: str) -> str | dict:
    try:
        value = payload[key]
    except KeyError as key_err:
        raise DictKeyError(key, payload) from key_err
    else:
        return value


def deserialize_json_query(json_query: str) -> dict:
    try:
        payload = json.loads(json_query)
    except json.JSONDecodeError as json_decode_err:
        raise DeserializeJSONQueryError(json_query) from json_decode_err
    if not isinstance(payload, dict):
        raise DeserializeJSONQueryError(json_query)
    return payload
