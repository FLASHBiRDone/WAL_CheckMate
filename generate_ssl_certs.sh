#!/bin/bash

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl/key.pem -out ssl/cert.pem -subj "/C=NO/ST=Oslo/L=Oslo/O=WAL/OU=IT/CN=localhost"

echo "Self-signed SSL certificates generated in the ssl directory."