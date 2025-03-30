# Form Submission Automation

This project automates form submissions to a website using Selenium WebDriver in a Docker container.

## Requirements

- Docker installed on your system
- Internet connection

## Configuration

The script can be configured using environment variables:

- `MIN_INTERVAL`: Minimum time between submissions in seconds (default: 60)
- `MAX_INTERVAL`: Maximum time between submissions in seconds (default: 300)
- `TARGET_URL`: The URL to submit the form to (default: https://crzyunbelevableofer.club/)

## Building and Running

1. Build the Docker image:
```bash
docker build -t form-submitter .
```

2. Run the container with default settings (1-5 minutes between submissions):
```bash
docker run -it form-submitter
```

3. Run with custom intervals (example: 30-120 seconds):
```bash
docker run -it -e MIN_INTERVAL=30 -e MAX_INTERVAL=120 form-submitter
```

The script will continuously submit the form with random data, with a random delay between the configured min and max intervals. Each submission will be logged with detailed information including:
- Timestamp
- Submission number
- Generated data
- Success/failure status
- Next submission timing

To stop the container, press Ctrl+C.
