# -*- coding: utf-8 -*-
import sys
import tempfile
from typing import Any, List

import ruamel.yaml as ruamel

from .mitmproxy2swagger import main


def get_nested_key(obj: Any, path: str) -> Any:
    """Gets a nested key from a dict."""
    keys = path.split(".")
    for key in keys:
        if not isinstance(obj, dict):
            return None
        if key not in obj:
            return None
        obj = obj[key]
    return obj


def mitmproxy2swagger_e2e_test(
    input_file: str, url_prefix: str, extra_args: List[str] | None = None
) -> Any:
    """Runs mitmproxy2swagger on the given input file twice, and returns the
    detected endpoints."""
    yaml_tmp_path = tempfile.mktemp(suffix=".yaml", prefix="sklep.lisek.")
    main(
        [
            "-i",
            input_file,
            "-o",
            yaml_tmp_path,
            "-p",
            url_prefix,
        ]
        + (extra_args or [])
    )
    yaml = ruamel.YAML()

    data = None
    # try to parse the file
    with open(yaml_tmp_path, "r") as f:
        data = yaml.load(f.read())
    assert data is not None
    assert "x-path-templates" in data
    assert "servers" in data
    # remove all of the ignore:prefixes in x-path-templates
    data["x-path-templates"] = [
        x.replace("ignore:", "") for x in data["x-path-templates"]
    ]

    # save the file
    with open(yaml_tmp_path, "w") as f:
        yaml.dump(data, f)

    # run mitmproxy2swagger again
    main(
        [
            "-i",
            input_file,
            "-o",
            yaml_tmp_path,
            "-p",
            url_prefix,
        ]
        + (extra_args or [])
    )

    # load the file again
    with open(yaml_tmp_path, "r") as f:
        data = yaml.load(f.read())
    return data


def test_mitmproxy2swagger_generates_swagger_from_har():
    data = mitmproxy2swagger_e2e_test(
        "testdata/sklep.lisek.app.har", "https://sklep.lisek.app/"
    )
    assert data is not None
    assert "paths" in data
    assert len(data["paths"]) > 3  # check if any paths were generated

    # assert "/api/darkstores" in data["paths"]
    # assert (
    #     "get" in data["paths"]["/api/darkstores"]
    # )  # check if the method was generated


def test_mitmproxy2swagger_generates_swagger_from_mitmproxy_flow_file():
    data = mitmproxy2swagger_e2e_test(
        "testdata/test_flows",
        "https://httpbin.org/",
        [
            "--format",
            "flow",
        ],
    )
    assert data is not None
    assert "paths" in data
    yaml = ruamel.YAML()
    yaml.dump(data, sys.stdout)
    assert len(data["paths"]) == 3  # 4 paths in the test file
    assert get_nested_key(data, "paths./get.get.responses.200.content") is not None


def test_mitmproxy2swagger_generates_swagger_from_mitmproxy_flow_file_with_form_data():
    data = mitmproxy2swagger_e2e_test(
        "testdata/form_data_flows",
        "https://httpbin.org/",
        [
            "--format",
            "flow",
        ],
    )
    assert data is not None

    assert (
        get_nested_key(
            data,
            "paths./post.post.requestBody.content.application/x-www-form-urlencoded.schema",
        )
        is not None
    )


def test_mitmproxy2swagger_generates_headers_for_flow_files():
    data = mitmproxy2swagger_e2e_test(
        "testdata/form_data_flows",
        "https://httpbin.org/",
        [
            "--format",
            "flow",
            "--headers",
        ],
    )
    assert data is not None
    assert get_nested_key(data, "paths./post.post.responses.200.headers.content-type") is not None
