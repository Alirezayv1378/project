# Django Project README

## Project Overview
This is a Django project configured to run in both development and production environments using Docker Compose. Follow the instructions below to set up and run the project.

## Prerequisites
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system.
- A `template.env` file in the project root (provided or created by you).

## Setup Instructions

### 1. Clone the Repository
Clone the project repository to your local machine:
```bash
git clone https://github.com/Alirezayv1378/project.git
cd <project-directory>
```

### 2. Create .env File
Create a .env file by copying the provided template.env file:

Edit the .env file to configure environment-specific settings (e.g., database credentials, secret keys, etc.). Ensure sensitive information is not committed to version control.

### 3. Running the Project
#### Development Mode
To start the project in development mode, use the following command:
```bash
docker-compose --profile dev up --build
```
This will:
- Build the Docker images.
- Start the Django development server and locust.

To stop the containers, press Ctrl+C or run:
```bash
docker-compose --profile dev down
```


#### Production Mode
To start the project in production mode, use the following command:
```bash
docker-compose --profile prod up --build
```
This will:
- Build the Docker images.
- Start only the Django production server.

To stop the containers, press Ctrl+C or run:
```bash
docker-compose --profile prod down
```
