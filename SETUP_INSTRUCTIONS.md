# WALCheckMate Setup Instructions

This document provides instructions for setting up WALCheckMate, including firewall configuration and other necessary steps.

## Prerequisites

- A server running a recent version of Ubuntu (18.04 or later recommended)
- Docker and Docker Compose installed
- A domain name pointed to your server's IP address

## Step 1: Clone the Repository

Clone the WALCheckMate repository to your server:

```bash
git clone https://your-repository-url.git
cd WALCheckMate
```

## Step 2: Configure the Firewall

1. Make the firewall setup script executable:

```bash
chmod +x setup_firewall.sh
```

2. Run the firewall setup script:

```bash
sudo ./setup_firewall.sh
```

This script will:
- Install ufw (Uncomplicated Firewall) if not already installed
- Set default policies to deny incoming and allow outgoing connections
- Allow SSH (port 22), HTTP (port 80), HTTPS (port 443), and the custom HTTPS port (8086)
- Enable the firewall

## Step 3: Configure Nginx and Let's Encrypt

1. Edit the `nginx.conf` file and replace `example.com` with your actual domain name.

2. Edit the `init-letsencrypt.sh` script:
   - Replace `example.com` and `www.example.com` with your domain(s)
   - Set a valid email address for Let's Encrypt notifications

3. Make the Let's Encrypt initialization script executable:

```bash
chmod +x init-letsencrypt.sh
```

4. Run the Let's Encrypt initialization script:

```bash
./init-letsencrypt.sh
```

This script will set up Let's Encrypt SSL certificates for your domain.

## Step 4: Configure Environment Variables

1. Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

2. Edit the `.env` file and set the necessary environment variables, including:
   - FACEBOOK_ACCESS_TOKEN
   - SLACK_BOT_TOKEN
   - SLACK_CHANNEL
   - Any other required variables for your specific setup

## Step 5: Start the Application

Start the WALCheckMate application using Docker Compose:

```bash
docker-compose up -d
```

This command will start the web application, Nginx reverse proxy, and Certbot for SSL certificate management.

## Accessing the Application

After completing these steps, WALCheckMate should be accessible at:

`https://your-domain.com:8086`

## Troubleshooting

- If you encounter any issues with the firewall, you can check its status using:
  ```bash
  sudo ufw status verbose
  ```

- To view logs for the application, use:
  ```bash
  docker-compose logs
  ```

- Ensure that your domain's DNS settings are correctly pointing to your server's IP address.

## Maintenance

- SSL certificates will automatically renew when needed.
- Regularly update your server and Docker images for security patches.
- Monitor the application logs for any errors or issues.

For any additional help or issues, please contact the WALCheckMate support team.