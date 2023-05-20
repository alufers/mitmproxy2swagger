#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Converts a mitmproxy dump file to a swagger schema."""
import argparse
import json
import os
import re
import sys
import traceback
import urllib
from typing import Any, Optional, Sequence, Union

import ruamel.yaml
from mitmproxy.exceptions import FlowReadException

from mitmproxy2swagger import console_util, swagger_util
from mitmproxy2swagger.har_capture_reader import HarCaptureReader, har_archive_heuristic
from mitmproxy2swagger.mitmproxy_capture_reader import (
    MitmproxyCaptureReader,
    mitmproxy_dump_file_huristic,
)


def path_to_regex(path):
    # replace the path template with a regex
    path = re.escape(path)
    path = path.replace(r"\{", "(?P<")
    path = path.replace(r"\}", ">[^/]+)")
    path = path.replace(r"\*", ".*")
    return "^" + path + "$"


def strip_query_string(path):
    # remove the query string from the path
    return path.split("?")[0]


def set_key_if_not_exists(dict, key, value):
    if key not in dict:
        dict[key] = value


def progress_callback(progress):
    console_util.print_progress_bar(progress)


def detect_input_format(file_path):
    har_score = har_archive_heuristic(file_path)
    mitmproxy_score = mitmproxy_dump_file_huristic(file_path)
    if "MITMPROXY2SWAGGER_DEBUG" in os.environ:
        print("har score: " + str(har_score))
        print("mitmproxy score: " + str(mitmproxy_score))
    if har_score > mitmproxy_score:
        return HarCaptureReader(file_path, progress_callback)
    return MitmproxyCaptureReader(file_path, progress_callback)


def main(override_args: Optional[Sequence[str]] = None):
    parser = argparse.ArgumentParser(
        description="Converts a mitmproxy dump file or HAR to a swagger schema."
    )
    parser.add_argument(
        "-i",
        "--input",
        help="The input mitmproxy dump file or HAR dump file (from DevTools)",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="The output swagger schema file (yaml). If it exists, new endpoints will be added",
        required=True,
    )
    parser.add_argument("-p", "--api-prefix", help="The api prefix", required=True)
    parser.add_argument(
        "-e",
        "--examples",
        action="store_true",
        help="Include examples in the schema. This might expose sensitive information.",
    )
    parser.add_argument(
        "-hd",
        "--headers",
        action="store_true",
        help="Include headers in the schema. This might expose sensitive information.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["flow", "har"],
        help="Override the input file format auto-detection.",
    )
    parser.add_argument(
        "-r",
        "--param-regex",
        default="[0-9]+",
        help="Regex to match parameters in the API paths. Path segments that match this regex will be turned into parameter placeholders.",
    )
    parser.add_argument(
        "-s",
        "--suppress-params",
        action="store_true",
        help="Do not include API paths that have the original parameter values, only the ones with placeholders.",
    )
    args = parser.parse_args(override_args)

    try:
        args.param_regex = re.compile("^" + args.param_regex + "$")
    except re.error as e:
        print(
            f"{console_util.ANSI_RED}Invalid path parameter regex: {e}{console_util.ANSI_RESET}"
        )
        sys.exit(1)

    yaml = ruamel.yaml.YAML()

    capture_reader: Union[MitmproxyCaptureReader, HarCaptureReader]
    if args.format == "flow" or args.format == "mitmproxy":
        capture_reader = MitmproxyCaptureReader(args.input, progress_callback)
    elif args.format == "har":
        capture_reader = HarCaptureReader(args.input, progress_callback)
    else:
        capture_reader = detect_input_format(args.input)

    swagger = None

    # try loading the existing swagger file
    try:
        base_dir = os.getcwd()
        relative_path = args.output
        abs_path = os.path.join(base_dir, relative_path)
        with open(abs_path, "r") as f:
            swagger = yaml.load(f)
    except FileNotFoundError:
        print("No existing swagger file found. Creating new one.")
    if swagger is None:
        swagger = ruamel.yaml.comments.CommentedMap(
            {
                "openapi": "3.0.0",
                "info": {
                    "title": args.input + " Mitmproxy2Swagger",
                    "version": "1.0.0",
                },
            }
        )
    # strip the trailing slash from the api prefix
    args.api_prefix = args.api_prefix.rstrip("/")

    if "servers" not in swagger or swagger["servers"] is None:
        swagger["servers"] = []

    # add the server if it doesn't exist
    if not any(server["url"] == args.api_prefix for server in swagger["servers"]):
        swagger["servers"].append(
            {"url": args.api_prefix, "description": "The default server"}
        )

    if "paths" not in swagger or swagger["paths"] is None:
        swagger["paths"] = {}

    if "x-path-templates" not in swagger or swagger["x-path-templates"] is None:
        swagger["x-path-templates"] = []

    path_templates = []
    for path in swagger["paths"]:
        path_templates.append(path)

    # also add paths from the the x-path-templates array
    if "x-path-templates" in swagger and swagger["x-path-templates"] is not None:
        for path in swagger["x-path-templates"]:
            path_templates.append(path)

    # new endpoints will be added here so that they can be added as comments in the swagger file
    new_path_templates = []
    path_template_regexes = [re.compile(path_to_regex(path)) for path in path_templates]

    try:
        for req in capture_reader.captured_requests():
            # strip the api prefix from the url
            url = req.get_matching_url(args.api_prefix)

            if url is None:
                continue
            method = req.get_method().lower()
            path = strip_query_string(url).removeprefix(args.api_prefix)
            status = req.get_response_status_code()

            # check if the path matches any of the path templates, and save the index
            path_template_index = None
            for i, path_template_regex in enumerate(path_template_regexes):
                if path_template_regex.match(path):
                    path_template_index = i
                    break
            if path_template_index is None:
                if path in new_path_templates:
                    continue
                new_path_templates.append(path)
                continue

            path_template_to_set = path_templates[path_template_index]
            set_key_if_not_exists(swagger["paths"], path_template_to_set, {})

            set_key_if_not_exists(
                swagger["paths"][path_template_to_set],
                method,
                {
                    "summary": swagger_util.path_template_to_endpoint_name(
                        method, path_template_to_set
                    ),
                    "responses": {},
                },
            )

            params = swagger_util.url_to_params(url, path_template_to_set)
            if args.headers:
                headers_request = swagger_util.request_to_headers(
                    req.get_request_headers()
                )
                if headers_request is not None and len(headers_request) > 0:
                    set_key_if_not_exists(
                        swagger["paths"][path_template_to_set][method],
                        "parameters",
                        headers_request,
                    )
            if params is not None and len(params) > 0:
                set_key_if_not_exists(
                    swagger["paths"][path_template_to_set][method], "parameters", params
                )

            if method not in ["get", "head"]:
                body = req.get_request_body()
                if body is not None:
                    body_val = None
                    content_type = None
                    # try to parse the body as json
                    try:
                        body_val = json.loads(req.get_request_body())
                        content_type = "application/json"
                    except UnicodeDecodeError:
                        pass
                    except json.decoder.JSONDecodeError:
                        pass
                    if content_type is None:
                        # try to parse the body as form data
                        try:
                            body_val_bytes: Any = dict(
                                urllib.parse.parse_qsl(
                                    body, encoding="utf-8", keep_blank_values=True
                                )
                            )
                            body_val = {}
                            did_find_anything = False
                            for key, value in body_val_bytes.items():
                                did_find_anything = True
                                body_val[key.decode("utf-8")] = value.decode("utf-8")
                            if did_find_anything:
                                content_type = "application/x-www-form-urlencoded"
                            else:
                                body_val = None
                        except UnicodeDecodeError:
                            pass

                    if body_val is not None:
                        content_to_set = {
                            "content": {
                                content_type: {
                                    "schema": swagger_util.value_to_schema(body_val)
                                }
                            }
                        }
                        if args.examples:
                            content_to_set["content"][content_type][
                                "example"
                            ] = swagger_util.limit_example_size(body_val)
                        set_key_if_not_exists(
                            swagger["paths"][path_template_to_set][method],
                            "requestBody",
                            content_to_set,
                        )

            # try parsing the response as json
            response_body = req.get_response_body()
            if response_body is not None:
                try:
                    response_json = json.loads(response_body)
                except UnicodeDecodeError:
                    response_json = None
                except json.decoder.JSONDecodeError:
                    response_json = None
                if response_json is not None:
                    resp_data_to_set = {
                        "description": req.get_response_reason(),
                        "content": {
                            "application/json": {
                                "schema": swagger_util.value_to_schema(response_json)
                            }
                        },
                    }
                    if args.examples:
                        resp_data_to_set["content"]["application/json"][
                            "example"
                        ] = swagger_util.limit_example_size(response_json)
                    if args.headers:
                        resp_data_to_set["headers"] = swagger_util.response_to_headers(
                            req.get_response_headers()
                        )

                    set_key_if_not_exists(
                        swagger["paths"][path_template_to_set][method]["responses"],
                        str(status),
                        resp_data_to_set,
                    )
            if (
                "responses" in swagger["paths"][path_template_to_set][method]
                and len(swagger["paths"][path_template_to_set][method]["responses"])
                == 0
            ):
                # add a default response if there were no responses detected,
                # this is for compliance with the OpenAPI spec
                content_type = (
                    req.get_response_headers().get("content-type") or "text/plain"
                )

                swagger["paths"][path_template_to_set][method]["responses"]["200"] = {
                    "description": "OK",
                    "content": {},
                }

    except FlowReadException as e:
        print(f"Flow file corrupted: {e}")
        traceback.print_exception(*sys.exc_info())
        print(
            f"{console_util.ANSI_RED}Failed to parse the input file as '{capture_reader.name()}'. "
        )
        if not args.format:
            print(
                f"It might happen that the input format as incorrectly detected. Please try using '--format flow' or '--format har' to specify the input format.{console_util.ANSI_RESET}"
            )
        sys.exit(1)
    except ValueError as e:
        print(f"ValueError: {e}")
        # print stack trace
        traceback.print_exception(*sys.exc_info())
        print(
            f"{console_util.ANSI_RED}Failed to parse the input file as '{capture_reader.name()}'. "
        )
        if not args.format:
            print(
                f"It might happen that the input format as incorrectly detected. Please try using '--format flow' or '--format har' to specify the input format.{console_util.ANSI_RESET}"
            )
        sys.exit(1)

    def is_param(param_value):
        return args.param_regex.match(param_value) is not None

    new_path_templates.sort()

    # add suggested path templates
    # basically inspects urls and replaces segments containing only numbers with a parameter
    new_path_templates_with_suggestions = []
    for path in new_path_templates:
        # check if path contains number-only segments
        segments = path.split("/")
        has_param = any(is_param(segment) for segment in segments)
        if has_param:
            # replace digit segments with {id}, {id1}, {id2} etc
            new_segments = []
            param_id = 0
            for segment in segments:
                if is_param(segment):
                    param_name = "id" + str(param_id)
                    if param_id == 0:
                        param_name = "id"
                    new_segments.append("{" + param_name + "}")
                    param_id += 1
                else:
                    new_segments.append(segment)
            suggested_path = "/".join(new_segments)
            # prepend the suggested path to the new_path_templates list
            if suggested_path not in new_path_templates_with_suggestions:
                new_path_templates_with_suggestions.append("ignore:" + suggested_path)

        if not has_param or not args.suppress_params:
            new_path_templates_with_suggestions.append("ignore:" + path)

    # remove the ending comments not to add them twice

    # append the contents of new_path_templates_with_suggestions to swagger['x-path-templates']
    for path in new_path_templates_with_suggestions:
        swagger["x-path-templates"].append(path)

    # remove elements already generated
    swagger["x-path-templates"] = [
        path for path in swagger["x-path-templates"] if path not in swagger["paths"]
    ]

    # remove duplicates while preserving order
    def f7(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    swagger["x-path-templates"] = f7(swagger["x-path-templates"])

    swagger["x-path-templates"] = ruamel.yaml.comments.CommentedSeq(
        swagger["x-path-templates"]
    )
    swagger["x-path-templates"].yaml_set_start_comment(
        "Remove the ignore: prefix to generate an endpoint with its URL\nLines that are closer to the top take precedence, the matching is greedy"
    )
    # save the swagger file
    with open(args.output, "w") as f:
        yaml.dump(swagger, f)
    print("Done!")


if __name__ == "__main__":
    main()
