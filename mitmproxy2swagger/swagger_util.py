# -*- coding: utf-8 -*-
import urllib
import uuid
from typing import Any, List

VERBS = [
    "add",
    "create",
    "delete",
    "get",
    "attach",
    "detach",
    "update",
    "push",
    "extendedcreate",
    "activate",
]


# generate a name for the endpoint from the path template
# POST /api/v1/things/{id}/create -> POST create thing by id
def path_template_to_endpoint_name(method, path_template):
    path_template = path_template.strip("/")
    segments = path_template.split("/")
    # remove params to a separate array
    params = []
    for idx, segment in enumerate(segments):
        if segment.startswith("{") and segment.endswith("}"):
            params.append(segment)
            segments[idx] = "{}"
    # remove them from the segments
    segments = [segment for segment in segments if segment != "{}"]
    # reverse the segments
    segments.reverse()
    name_parts = []
    for segment in segments:
        if segment in VERBS:
            # prepend to the name_parts
            name_parts.insert(0, segment.lower())
        else:
            name_parts.insert(0, segment.lower())
            break
    for param in params:
        name_parts.append("by " + param.replace("{", "").replace("}", ""))
        break
    return method.upper() + " " + " ".join(name_parts)


# when given an url and its path template, generates the parameters section of the request
def url_to_params(url, path_template):
    path_template = path_template.strip("/")
    segments = path_template.split("/")
    url_segments = url.split("?")[0].strip("/").split("/")
    params = []
    for idx, segment in enumerate(segments):
        if segment.startswith("{") and segment.endswith("}"):
            params.append(
                {
                    "name": segment.replace("{", "").replace("}", ""),
                    "in": "path",
                    "required": True,
                    "schema": {
                        "type": "number" if url_segments[idx].isdigit() else "string"
                    },
                }
            )
    query_string = urllib.parse.urlparse(url).query
    if query_string:
        query_params = urllib.parse.parse_qs(query_string)
        for key in query_params:
            params.append(
                {
                    "name": key,
                    "in": "query",
                    "required": False,
                    "schema": {
                        "type": "number" if query_params[key][0].isdigit() else "string"
                    },
                }
            )
    return params


def request_to_headers(headers: dict[str, List[Any]], add_example: bool = False):
    """When given an url and its path template, generates the parameters section of the
    request."""
    params = []
    if headers:
        for key in headers:
            h = {
                "name": key,
                "in": "header",
                "required": False,
                "schema": {"type": "number" if headers[key][0].isdigit() else "string"},
            }
            if add_example:
                h["example"] = headers[key][0]
            params.append(h)
    return params


def response_to_headers(headers):
    header = {}
    if headers:
        for key in headers:
            header[key] = {
                "description": headers[key][0],
                "schema": {"type": "number" if headers[key][0].isdigit() else "string"},
            }
    return header


def value_to_schema(value):
    # check if value is a number
    if type(value) is int or type(value) is float:
        return {"type": "number"}
    # check if value is a boolean
    elif isinstance(value, bool):
        return {"type": "boolean"}
    # check if value is a string
    elif isinstance(value, str):
        return {"type": "string"}
    # check if value is a list
    elif isinstance(value, list):
        if len(value) == 0:
            return {"type": "array", "items": {}}

        return {"type": "array", "items": value_to_schema(value[0])}
    # check if value is a dict
    elif isinstance(value, dict):
        all_keys_are_numeric = all(is_numeric_string(key) for key in value)
        all_keys_are_uuid = all(is_uuid(key) for key in value)
        keys_are_generic = all_keys_are_numeric or all_keys_are_uuid

        if keys_are_generic and len(value) > 0:
            return {
                "type": "object",
                "additionalProperties": value_to_schema(list(value.values())[0]),
            }
        return {
            "type": "object",
            "properties": {key: value_to_schema(value[key]) for key in value},
        }
    # if it is none, return null
    elif value is None:
        return {"type": "object", "nullable": True}


def is_uuid(key):
    return isinstance(key, str) and is_valid_uuid(key)


def is_numeric_string(key):
    return isinstance(key, str) and key.isnumeric()


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


MAX_EXAMPLE_ARRAY_ELEMENTS = 10
MAX_EXAMPLE_OBJECT_PROPERTIES = 150


# recursively scan an example value and limit the number of elements and properties
def limit_example_size(example):
    if isinstance(example, list):
        new_list = []
        for element in example:
            if len(new_list) >= MAX_EXAMPLE_ARRAY_ELEMENTS:
                break
            new_list.append(limit_example_size(element))
        return new_list
    elif isinstance(example, dict):
        new_dict = {}
        for key in example:
            if len(new_dict) >= MAX_EXAMPLE_OBJECT_PROPERTIES:
                break
            new_dict[key] = limit_example_size(example[key])
        return new_dict
    else:
        return example
