FROM node:26.3.0-bookworm-slim

WORKDIR /repo

COPY package.json package-lock.json turbo.json ./
COPY apps/web/package.json apps/web/package.json
COPY apps/api/package.json apps/api/package.json
COPY packages/brand/package.json packages/brand/package.json
RUN npm ci

COPY apps/web apps/web
COPY packages/brand packages/brand

EXPOSE 5173

CMD ["npm", "run", "dev", "--workspace", "@citenook/web", "--", "--host", "0.0.0.0"]
