FROM mongo:latest

# Create a custom configuration file
COPY mongod.conf /etc/mongod.conf

# Expose the MongoDB port
EXPOSE 27017

# Start MongoDB with custom configuration and authentication
CMD ["mongod", "--config", "/etc/mongod.conf", "--auth"] 