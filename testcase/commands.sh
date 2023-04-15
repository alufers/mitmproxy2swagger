#!/bin/bash

python3.9 -m venv env
source env/bin/activate
pip install mitmproxy mitmproxy2swagger
mitmproxy2swagger -i flows -o specs.yml -p https://api.ah.nl
cat specs.yml

