# Frontend Dockerfile
from  node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json* package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build Next.js app
RUN npm run build

# Production image
from  node:20-alpine

WORKDIR /app

# Copy from  builder
COPY --from =builder /app/node_modules ./node_modules
COPY --from =builder /app/.next ./.next
COPY --from =builder /app/public ./public
COPY package.json ./

EXPOSE 3000

CMD ["npm", "start"]
