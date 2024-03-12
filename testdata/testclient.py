# -*- coding: utf-8 -*-
from typing import Any, Callable

import requests  # type: ignore


def testclient(
    contentType: str,
    getData: Callable[[], Any],
    decodeData: Callable[[Any], Any],
) -> None:
    url = "http://localhost:8082"
    headers = {"Content-Type": contentType}
    response = requests.post(
        url,
        data=getData(),
        headers=headers,
        proxies={"http": "http://localhost:8080", "https": "http://localhost:8080"},
    )

    # Print the response
    print(response.status_code)
    print(response.headers)

    # convert the response data from MessagePack to JSON
    data = decodeData(response.content)
    print(data)
