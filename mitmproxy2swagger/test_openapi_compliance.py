# -*- coding: utf-8 -*-
from openapi_spec_validator import validate_spec

from mitmproxy2swagger.testing_util import mitmproxy2swagger_e2e_test


def test_mitmproxy2swagger_compliance_from_mitmproxy_flow_file():
    data = mitmproxy2swagger_e2e_test(
        "testdata/test_flows",
        "https://httpbin.org/",
        [
            "--format",
            "flow",
        ],
    )
    assert data is not None
    validate_spec(data)


def test_mitmproxy2swagger_compliance_from_mitmproxy_flow_file_with_headers():
    data = mitmproxy2swagger_e2e_test(
        "testdata/test_flows",
        "https://httpbin.org/",
        [
            "--format",
            "flow",
            "--headers",
        ],
    )
    assert data is not None
    validate_spec(data)


def test_mitmproxy2swagger_compliance_from_har_file_with_headers():
    data = mitmproxy2swagger_e2e_test(
        "testdata/sklep.lisek.app.har",
        "https://api2.lisek.app/",
        [
            "--format",
            "har",
            "--headers",
        ],
    )
    assert data is not None
    validate_spec(data)


def test_mitmproxy2swagger_compliance_from_form_data_file_with_headers():
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
    validate_spec(data)


def test_mitmproxy2swagger_compliance_from_msgpack_file_with_headers():
    data = mitmproxy2swagger_e2e_test(
        "testdata/msgpack_flows",
        "http://localhost:8082/",
        [
            "--format",
            "flow",
            "--headers",
        ],
    )
    assert data is not None
    validate_spec(data)


def test_mitmproxy2swagger_compliance_from_generic_keys_file_with_headers():
    data = mitmproxy2swagger_e2e_test(
        "testdata/generic_keys_flows",
        "http://localhost:8082/",
        [
            "--format",
            "flow",
            "--headers",
        ],
    )
    assert data is not None
    validate_spec(data)
