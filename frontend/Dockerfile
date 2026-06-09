# Use lightweight Node Alpine base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY . .

# Expose React development server port
EXPOSE 3000

# Start React app development server
CMD ["npm", "start"]
