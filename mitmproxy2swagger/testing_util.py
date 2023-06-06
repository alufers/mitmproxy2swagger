# -*- coding: utf-8 -*-

import tempfile
from typing import Any, List, Optional

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
    input_file: str, url_prefix: str, extra_args: Optional[List[str]] = None
) -> Any:
    """Runs mitmproxy2swagger on the given input file twice, and returns the detected
    endpoints."""
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
