FROM python:3.10

WORKDIR /app

RUN apt update -qq && \
    python -m pip install --upgrade pip && \
    pip install poetry 


COPY ["pyproject.toml", "./"]

RUN poetry install 

COPY . .

RUN pip install .

CMD [ "mitmproxy2swagger" ]

