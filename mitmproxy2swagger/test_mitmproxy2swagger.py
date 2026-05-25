from .testing_util import get_nested_key, mitmproxy2swagger_e2e_test


def test_mitmproxy2swagger_generates_swagger_from_har():
    data = mitmproxy2swagger_e2e_test(
        "testdata/sklep.lisek.app.har", "https://api2.lisek.app/"
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


def test_mitmproxy2swagger_generates_swagger_from_har_file_with_form_data():
    # Regression test for https://github.com/alufers/mitmproxy2swagger/pull/174
    # HAR bodies are already decoded strings; calling .decode() on them raised AttributeError
    data = mitmproxy2swagger_e2e_test(
        "testdata/form_data_har.har",
        "https://httpbin.org/",
    )
    assert data is not None

    assert (
        get_nested_key(
            data,
            "paths./post.post.requestBody.content.application/x-www-form-urlencoded.schema",
        )
        is not None
    )


def test_mitmproxy2swagger_generates_swagger_from_mitmproxy_flow_file_with_generic_keys():
    data = mitmproxy2swagger_e2e_test(
        "testdata/generic_keys_flows",
        "http://localhost:8082/",
        [
            "--format",
            "flow",
        ],
    )
    assert data is not None

    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/json.schema.properties.numeric.properties",
        )
        is None
    )
    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/json.schema.properties.uuid.properties",
        )
        is None
    )
    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/json.schema.properties.numeric.additionalProperties",
        )
        is not None
    )
    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/json.schema.properties.numeric.additionalProperties",
        )
        is not None
    )

    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/json.schema.properties.mixed.properties",
        )
        is not None
    )
    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/json.schema.properties.mixed.additionalProperties",
        )
        is None
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
    assert (
        get_nested_key(data, "paths./post.post.responses.200.headers.content-type")
        is not None
    )


def test_mitmproxy2swagger_includes_both_headers_and_query_params_with_hd_flag():
    # Regression test for https://github.com/alufers/mitmproxy2swagger/pull/220
    # With --headers, query params were dropped; without it, headers were dropped
    data = mitmproxy2swagger_e2e_test(
        "testdata/headers_and_params_har.har",
        "https://httpbin.org/",
        ["--headers"],
    )
    assert data is not None

    parameters = get_nested_key(data, "paths./get.get.parameters")
    assert parameters is not None

    param_names = [p["name"] for p in parameters]
    assert "X-Api-Key" in param_names, "Request header missing from parameters"
    assert "search" in param_names, "Query parameter missing from parameters"


def test_mitmproxy2swagger_parses_msgpack_requests_and_responses():
    data = mitmproxy2swagger_e2e_test(
        "testdata/msgpack_flows",
        "http://localhost:8082/",
        [
            "--format",
            "flow",
        ],
    )
    assert data is not None

    assert (
        get_nested_key(data, "paths./.post.responses.200.content.application/msgpack")
        is not None
    )
    assert (
        get_nested_key(
            data,
            "paths./.post.responses.200.content.application/msgpack.schema.properties.new_field.type",
        )
        == "string"
    )
    assert (
        get_nested_key(data, "paths./.post.requestBody.content.application/msgpack")
        is not None
    )
    assert (
        get_nested_key(
            data,
            "paths./.post.requestBody.content.application/msgpack.schema.properties.field1.type",
        )
        == "string"
    )
