FROM docker.io/library/python:3.8.12-buster AS build

WORKDIR /run/

COPY requirements.txt /run/
RUN pip install -r requirements.txt

COPY docs /run/docs
COPY mkdocs.yml /run/

RUN mkdocs build


FROM alpine:3.13.2

RUN apk add thttpd

RUN adduser -D static
USER static
WORKDIR /home/static

COPY --from=build /run/site /home/static

EXPOSE 8001

CMD ["thttpd", "-D", "-h", "0.0.0.0", "-p", "8001", "-d", "/home/static", "-u", "static", "-l", "-", "-M", "60"]
