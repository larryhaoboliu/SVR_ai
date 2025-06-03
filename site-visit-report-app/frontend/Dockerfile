FROM node:18-alpine as build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production=false

COPY . .

# Set environment variables for build
ENV REACT_APP_API_URL=https://svr-backend.fly.dev
ENV GENERATE_SOURCEMAP=false
ENV CI=false

# Build the app
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 