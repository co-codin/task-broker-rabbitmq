import json

from typing import Tuple, Union, Dict

from app.errors import DeserializeJSONQueryError, DictKeyError


def parse_mq_query(body: str, key: str) -> Tuple[str, Union[str, Dict]]:
    payload = _deserialize_json_query(body)
    guid = _get_value_from_payload(payload, 'guid')
    result = _get_value_from_payload(payload, key)
    return guid, result


def _get_value_from_payload(payload: Dict, key: str) -> Union[str, Dict]:
    try:
        value = payload[key]
    except KeyError as key_err:
        raise DictKeyError(key, payload) from key_err
    else:
        return value


def _deserialize_json_query(json_query: str) -> Dict:
    try:
        payload = json.loads(json_query)
    except json.JSONDecodeError as json_decode_err:
        raise DeserializeJSONQueryError(json_query) from json_decode_err
    if not isinstance(payload, Dict):
        raise DeserializeJSONQueryError(json_query)
    return payload
