FROM docker.io/library/python:3.8.12-buster
RUN pip install poetry

WORKDIR /run/

COPY poetry.lock /run/
COPY pyproject.toml /run/

RUN poetry install

COPY dmt_chairmanmao /run/dmt_chairmanmao
COPY data /run/data

CMD ["poetry", "run", "chairmanmao"]
