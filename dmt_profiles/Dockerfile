FROM docker.io/library/node:14 AS build

WORKDIR /run/

COPY package.json /run/
RUN npm install

COPY tsconfig.json /run/
COPY package-lock.json /run/
COPY src/ /run/src/
COPY public/ /run/public/

RUN npm run build

FROM docker.io/library/caddy


COPY Caddyfile /etc/caddy/
COPY --from=build /run/build /run/build

EXPOSE 8005
