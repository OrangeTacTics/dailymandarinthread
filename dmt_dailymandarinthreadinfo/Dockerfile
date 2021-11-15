FROM docker.io/library/python:3.8.12-buster AS build

WORKDIR /run/

COPY requirements.txt /run/
RUN pip install -r requirements.txt

COPY docs /run/docs
COPY mkdocs.yml /run/

RUN mkdocs build


FROM docker.io/library/caddy

COPY Caddyfile /etc/caddy/
COPY --from=build /run/site /run/site

EXPOSE 8001
