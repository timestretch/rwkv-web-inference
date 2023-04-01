FROM node:18.15.0

WORKDIR /app
COPY ./package* /app/

RUN npm ci

COPY . /app/
RUN npm run build

ENTRYPOINT ["npx", "next", "start"]
# RUN npm ci --only=production
