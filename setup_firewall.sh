#!/bin/bash

# Install ufw if not already installed
sudo apt-get update
sudo apt-get install -y ufw

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change 22 to your SSH port if it's different)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow custom HTTPS port
sudo ufw allow 8086/tcp

# Enable firewall
sudo ufw --force enable

echo "Firewall setup complete. Current status:"
sudo ufw status verbose