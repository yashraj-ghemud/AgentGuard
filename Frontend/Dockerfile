FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY . .

ARG NEXT_PUBLIC_API_URL=https://agentguard-backend.onrender.com
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

EXPOSE 3000

CMD ["sh", "-c", "npm run start -- --hostname 0.0.0.0 --port ${PORT:-3000}"]
