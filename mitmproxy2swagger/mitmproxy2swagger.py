#!/usr/bin/env python
"""
Converts a mitmproxy dump file to a swagger schema.
"""
from mitmproxy.exceptions import FlowReadException
import json
import argparse
import ruamel.yaml
import re
from . import swagger_util
from .har_capture_reader import HarCaptureReader, har_archive_heuristic
from .mitmproxy_capture_reader import MitmproxyCaptureReader, mitmproxy_dump_file_huristic
from . import console_util


def path_to_regex(path):
    # replace the path template with a regex
    path = path.replace('{', '(?P<')
    path = path.replace('}', '>[^/]+)')
    path = path.replace('*', '.*')
    path = path.replace('/', '\\/')
    return "^" + path + "$"


def strip_query_string(path):
    # remove the query string from the path
    return path.split('?')[0]


def set_key_if_not_exists(dict, key, value):
    if key not in dict:
        dict[key] = value


def progress_callback(progress):
    console_util.print_progress_bar(progress)


def main():
    parser = argparse.ArgumentParser(
        description='Converts a mitmproxy dump file or HAR to a swagger schema.')
    parser.add_argument(
        '-i', '--input', help='The input mitmproxy dump file or HAR dump file (from DevTools)', required=True)
    parser.add_argument(
        '-o', '--output', help='The output swagger schema file (yaml). If it exists, new endpoints will be added', required=True)
    parser.add_argument('-p', '--api-prefix', help='The api prefix', required=True)
    parser.add_argument('-e', '--examples', action='store_true',
                        help='Include examples in the schema. This might expose sensitive information.')
    args = parser.parse_args()

    yaml = ruamel.yaml.YAML()
    caputre_reader = None
    # detect the input file type
    if har_archive_heuristic(args.input) > mitmproxy_dump_file_huristic(args.input):
        caputre_reader = HarCaptureReader(args.input, progress_callback)
    else:
        caputre_reader = MitmproxyCaptureReader(args.input, progress_callback)
    swagger = None

    # try loading the existing swagger file
    try:
        with open(args.output, 'r') as f:
            swagger = yaml.load(f)
    except FileNotFoundError:
        print("No existing swagger file found. Creating new one.")
        pass
    if swagger is None:
        swagger = ruamel.yaml.comments.CommentedMap({
            "openapi": "3.0.0",
            "info": {
                "title": args.input + " Mitmproxy2Swagger",
                "version": "1.0.0"
            },
        })
    # strip the trailing slash from the api prefix
    args.api_prefix = args.api_prefix.rstrip('/')

    if 'servers' not in swagger or swagger['servers'] is None:
        swagger['servers'] = []

    # add the server if it doesn't exist
    if not any(server['url'] == args.api_prefix for server in swagger['servers']):
        swagger['servers'].append({
            "url": args.api_prefix,
            "description": "The default server"
        })

    if 'paths' not in swagger or swagger['paths'] is None:
        swagger['paths'] = {}

    if 'x-path-templates' not in swagger or swagger['x-path-templates'] is None:
        swagger['x-path-templates'] = []

    path_templates = []
    for path in swagger['paths']:
        path_templates.append(path)

    # also add paths from the the x-path-templates array
    if 'x-path-templates' in swagger and swagger['x-path-templates'] is not None:
        for path in swagger['x-path-templates']:
            path_templates.append(path)

    # new endpoints will be added here so that they can be added as comments in the swagger file
    new_path_templates = []

    path_template_regexes = [re.compile(path_to_regex(path))
                             for path in path_templates]

    try:
        for f in caputre_reader.captured_requests():
            # strip the api prefix from the url
            url = f.get_url()
            if not url.startswith(args.api_prefix):
                continue
            method = f.get_method().lower()
            path = strip_query_string(url).removeprefix(args.api_prefix)
            status = f.get_response_status_code()

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
            set_key_if_not_exists(
                swagger['paths'], path_template_to_set, {})

            set_key_if_not_exists(swagger['paths'][path_template_to_set], method, {
                'summary': swagger_util.path_template_to_endpoint_name(method, path_template_to_set),
                'responses': {}
            })

            params = swagger_util.url_to_params(url, path_template_to_set)

            if params is not None and len(params) > 0:
                set_key_if_not_exists(swagger['paths'][path_template_to_set][method], 'parameters', params)

            if method not in ['get', 'head']:
                body = f.get_request_body()
                if body is not None:
                    body_val = None
                    # try to parse the body as json
                    try:
                        body_val = json.loads(f.get_request_body())
                    except json.decoder.JSONDecodeError:
                        pass
                    if body_val is not None:
                        content_to_set = {
                            'content': {
                                'application/json': {
                                    'schema': swagger_util.value_to_schema(body_val)
                                }
                            }
                        }
                        if args.examples:
                            content_to_set['content']['application/json']['example'] = swagger_util.limit_example_size(
                                body_val)
                        set_key_if_not_exists(
                            swagger['paths'][path_template_to_set][method], 'requestBody', content_to_set)

            # try parsing the response as json
            response_body = f.get_response_body()
            if response_body is not None:
                try:
                    response_json = json.loads(response_body)
                except json.decoder.JSONDecodeError:
                    response_json = None
                if response_json is not None:
                    resp_data_to_set = {
                        'description': f.get_response_reason(),
                        'content': {
                            'application/json': {
                                'schema': swagger_util.value_to_schema(response_json)
                            }
                        }
                    }
                    if args.examples:
                        resp_data_to_set['content']['application/json']['example'] = swagger_util.limit_example_size(
                            response_json)
                    set_key_if_not_exists(swagger['paths'][path_template_to_set][method]['responses'], str(
                        status), resp_data_to_set)

    except FlowReadException as e:
        print(f"Flow file corrupted: {e}")

    new_path_templates.sort()

    # add suggested path templates
    # basically inspects urls and replaces segments containing only numbers with a parameter
    new_path_templates_with_suggestions = []
    for idx, path in enumerate(new_path_templates):
        # check if path contains number-only segments
        segments = path.split('/')
        if any(segment.isdigit() for segment in segments):
            # replace digit segments with {id}, {id1}, {id2} etc
            new_segments = []
            param_id = 0
            for segment in segments:
                if segment.isdigit():
                    param_name = 'id' + str(param_id)
                    if param_id == 0:
                        param_name = 'id'
                    new_segments.append('{' + param_name + '}')
                    param_id += 1
                else:
                    new_segments.append(segment)
            suggested_path = '/'.join(new_segments)
            # prepend the suggested path to the new_path_templates list
            if suggested_path not in new_path_templates_with_suggestions:
                new_path_templates_with_suggestions.append(
                    "ignore:" + suggested_path)
        new_path_templates_with_suggestions.append("ignore:" + path)

    # remove the ending comments not to add them twice

    # append the contents of new_path_templates_with_suggestions to swagger['x-path-templates']
    for path in new_path_templates_with_suggestions:
        swagger['x-path-templates'].append(path)

    # remove elements already generated
    swagger['x-path-templates'] = [
        path for path in swagger['x-path-templates'] if path not in swagger['paths']]

    # remove duplicates while preserving order
    def f7(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]
    swagger['x-path-templates'] = f7(swagger['x-path-templates'])

    swagger['x-path-templates'] = ruamel.yaml.comments.CommentedSeq(
        swagger['x-path-templates'])
    swagger['x-path-templates'].yaml_set_start_comment(
        'Remove the ignore: prefix to generate an endpoint with its URL\nLines that are closer to the top take precedence, the matching is greedy')
    # save the swagger file
    with open(args.output, 'w') as f:
        yaml.dump(swagger, f)
    print("Done!")


if __name__ == "__main__":
    main()
