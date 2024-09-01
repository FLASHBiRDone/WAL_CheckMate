# WALCheckMate Documentation

## Introduction

WALCheckMate is a web application designed to monitor Facebook ad campaigns with daily budgets. It provides real-time notifications via Slack, allows users to manage campaign visibility, and offers a web interface for easy campaign management. The app integrates with the Facebook Ads API and Slack, and is built using Python with the Flask framework.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Key Components](#key-components)
3. [Main Functions](#main-functions)
4. [Data Flow](#data-flow)
5. [Security Considerations](#security-considerations)
6. [Deployment](#deployment)
7. [Maintenance and Monitoring](#maintenance-and-monitoring)

## Architecture Overview

WALCheckMate follows a client-server architecture:

- Backend: Python Flask application
- Frontend: HTML, CSS, and JavaScript
- Database: SQLite for storing campaign and account data
- External Services: Facebook Ads API, Slack API
- Deployment: Docker containers with Nginx as a reverse proxy

The application is designed to run as a set of Docker containers, with Nginx handling SSL termination and reverse proxy to the Flask application.

## Key Components

1. **Flask Application (app.py)**: The core of the backend, handling all business logic, API requests, and database interactions.

2. **Frontend (templates/index.html)**: The user interface for managing accounts and viewing campaign data.

3. **Database (SQLite)**: Stores information about hidden accounts, hidden campaigns, and notification status.

4. **Facebook Ads API Integration**: Fetches ad account and campaign data.

5. **Slack Integration**: Sends notifications and handles user interactions via Slack.

6. **Nginx**: Acts as a reverse proxy and handles SSL termination.

7. **Docker**: Containerizes the application for easy deployment and scaling.

## Main Functions

### 1. Campaign Data Update (update_campaign_data)

- Fetches ad accounts and campaigns from Facebook Ads API
- Identifies campaigns with daily budgets
- Updates the local database with campaign information
- Triggers Slack notifications for new daily budget campaigns

### 2. Slack Notifications (send_slack_message)

- Sends formatted messages to a specified Slack channel
- Includes interactive buttons for managing campaign notifications

### 3. Campaign Visibility Management (toggle_visibility, hide_campaign)

- Allows users to hide/show specific ad accounts or campaigns
- Updates the local database to reflect visibility changes

### 4. Manual Check (manual_check)

- Initiates an on-demand update of campaign data
- Can be triggered via the web interface or Slack command

### 5. Scheduled Updates (scheduled_update)

- Runs automatic updates of campaign data at regular intervals (every 3 hours)

### 6. Web Interface

- Displays campaign data in a user-friendly format
- Allows users to initiate manual checks and manage account/campaign visibility

## Data Flow

1. The application fetches ad account and campaign data from the Facebook Ads API.
2. Campaign data is processed and stored in the local SQLite database.
3. New daily budget campaigns trigger Slack notifications.
4. Users can interact with the data via the web interface or Slack.
5. User actions (e.g., hiding campaigns) update the local database.
6. The web interface periodically refreshes to display the most current data.

## Security Considerations

- HTTPS is used for all communications.
- API tokens and sensitive data are stored in environment variables.
- The application runs behind a firewall with only necessary ports exposed.
- Regular updates and security patches are crucial for maintaining security.

## Deployment

The application is deployed using Docker and Docker Compose. Key steps include:

1. Setting up the server environment
2. Configuring the firewall
3. Setting up SSL certificates with Let's Encrypt
4. Building and running Docker containers

Detailed deployment instructions are available in SETUP_INSTRUCTIONS.md (English) and OPPSETTINSTRUKSJONER.md (Norwegian).

## Maintenance and Monitoring

- Regular backups of the SQLite database should be performed.
- Monitor application logs for errors or unusual activity.
- Keep the server, Docker images, and application dependencies up to date.
- Regularly review and update Facebook and Slack API tokens.

For more detailed information on specific components or functions, refer to the inline comments in the source code.