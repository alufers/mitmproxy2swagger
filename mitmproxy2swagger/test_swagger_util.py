from mitmproxy2swagger.swagger_util import url_to_params


def test_url_to_params_infers_path_parameter_type_from_url_path():
    params = url_to_params(
        "https://api.example.test/v1/users/123?limit=5", "/v1/users/{id}"
    )

    assert params == [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "schema": {"type": "number"},
        },
        {
            "name": "limit",
            "in": "query",
            "required": False,
            "schema": {"type": "number"},
        },
    ]


def test_url_to_params_keeps_string_path_parameter_type():
    params = url_to_params("https://api.example.test/v1/users/alice", "/v1/users/{id}")

    assert params[0]["schema"]["type"] == "string"
