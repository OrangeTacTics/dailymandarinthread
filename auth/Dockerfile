FROM docker.io/library/python:3.8.12-buster
RUN pip install poetry

WORKDIR /run/

COPY poetry.lock /run/
COPY pyproject.toml /run/

RUN poetry install

COPY dmt_auth /run/dmt_auth

EXPOSE 8004

CMD ["poetry", "run", "dmt-auth"]
