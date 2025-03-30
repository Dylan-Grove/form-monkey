# Form Submission Automation

A Python script that automates form submissions using Selenium WebDriver, designed to run in a Docker container.

## Features

- Configurable submission intervals (1-30 minutes)
- Random data generation for form fields
- Realistic Canadian phone numbers
- Random email generation with common domains
- Detailed logging
- Configurable form field selectors via JSON config
- Docker support for easy deployment

## Prerequisites

- Docker installed on your system
- Docker Desktop running (for Windows/Mac)

## Configuration

The script can be configured using environment variables:

- `MIN_INTERVAL`: Minimum time between submissions in seconds (default: 60)
- `MAX_INTERVAL`: Maximum time between submissions in seconds (default: 1800)
- `TARGET_URL`: The URL of the form to submit
- `FORM_CONFIG`: The form configuration to use from form_config.json (default: "default")

## Form Configuration

The script uses a JSON configuration file (`form_config.json`) to define form field selectors. You can add new configurations or modify existing ones.

Example configuration:
```json
{
    "default": {
        "first_name": {
            "selector": "input[name='first_name']",
            "type": "text",
            "required": true,
            "min_length": 2
        },
        "last_name": {
            "selector": "input[name='last_name']",
            "type": "text",
            "required": true,
            "min_length": 2
        },
        "email": {
            "selector": "input[name='email']",
            "type": "email",
            "required": true
        },
        "phone": {
            "selector": "input[name='phone']",
            "type": "tel",
            "required": true
        },
        "submit_button": {
            "selector": "//button[contains(text(), 'START')]",
            "type": "xpath"
        }
    }
}
```

## Building the Docker Image

```bash
docker build -t form-submitter .
```

## Running the Container

### Example 1: Using Default Configuration

```bash
docker run -it --rm \
  -e MIN_INTERVAL=60 \
  -e MAX_INTERVAL=1800 \
  -e TARGET_URL="https://example.com/form" \
  form-submitter
```

### Example 2: Using Custom Form Configuration

```bash
docker run -it --rm \
  -e MIN_INTERVAL=60 \
  -e MAX_INTERVAL=1800 \
  -e TARGET_URL="https://example.com/form" \
  -e FORM_CONFIG="custom_config" \
  form-submitter
```

### Example 3: Using Predefined Configuration (crzyunbelevableofer.club)

```bash
docker run -it --rm \
  -e MIN_INTERVAL=60 \
  -e MAX_INTERVAL=1800 \
  -e TARGET_URL="https://crzyunbelevableofer.club/cnt-frdscd/?oid=22&qze=3&hitid=9e8dc76f-77dc-445a-80b1-b5feda22964d&aff_sub=&saf=&cvu=&action=17at&aff_sub5=d8n6btsh5chjhfp837ugsme2&url_id=22&aff_sub2=&aff_sub3=&aff_sub4=17at&tracker=cg&language=&aff_sub6=&aff_sub7=&aff_sub8=&aff_sub9=&aff_sub10=&bzkbzk=gb" \
  -e FORM_CONFIG="crzyunbelevableofer" \
  form-submitter
```

## Logging

The script provides detailed logging of:
- Configuration parameters
- Form submission attempts
- Generated data
- Success/failure status
- Wait times between submissions

## Notes

- The script will submit a form immediately when started
- A small random delay (5-15 seconds) follows the first submission
- Subsequent submissions occur at random intervals between MIN_INTERVAL and MAX_INTERVAL
- To stop the script, press Ctrl+C in the terminal where it's running
