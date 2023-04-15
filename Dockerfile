FROM python:3.10-alpine

WORKDIR /app

RUN apk update && \
    apk upgrade && \
    apk add gcc libc-dev libffi-dev cargo && \
    python -m pip install --upgrade pip && \
    pip install poetry


COPY ["pyproject.toml", "./"]

RUN poetry install

COPY . .

RUN pip install .

CMD [ "mitmproxy2swagger" ]
