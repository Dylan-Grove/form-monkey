# Form Monkey - Automated Form Submission Tool

Connect a monkey with a keyboard to your websites form submission.

A Python-based tool for automated form submissions with support for various phone number formats and anti-bot detection.

## Features

- Automated form submission with random delays
- Support for multiple phone number formats:
  - Canadian (e.g., (416) 555-1234)
  - American (e.g., (212) 555-1234)
  - Russian (e.g., +7 (495) 123-45-67)
  - Chinese (e.g., +86 10 1234 5678)
  - Mexican (e.g., +52 (55) 1234-5678)
  - UK (e.g., +44 20 7123 4567)
  - Australian (e.g., +61 2 1234 5678)
- Anti-bot detection evasion
- Configurable submission intervals
- Verbosity levels for logging
- Docker support

## Configuration

### Form Configuration (form_config.json)

The tool uses a JSON configuration file to define form fields and their properties:

```json
{
    "example_form": {
        "url": "https://example.com/form",
        "verbosity": "balanced",
        "timing": {
            "min_interval": 180,
            "max_interval": 1800
        },
        "fields": {
            "first_name": {
                "selector": "input[name='first_name']",
                "type": "css",
                "required": true,
                "min_length": 2
            },
            "phone": {
                "selector": "input[name='phone']",
                "type": "css",
                "required": true,
                "area_code_type": ["canadian", "american"]  // Can be a single string or array of types
            }
        }
    }
}
```

### Phone Number Formats

The tool supports various phone number formats based on the `area_code_type` configuration:

- Single type: `"area_code_type": "canadian"`
- Multiple types: `"area_code_type": ["canadian", "american"]`

When multiple types are specified, the tool will randomly choose one type for each submission.

## Usage

### Running with Docker

```bash
# Build the Docker image
docker build -t form-monkey .

# Run with specific configuration
docker run -it --rm -e FORM_CONFIG=example_form -e VERBOSITY=balanced form-monkey
```

### Command Line Arguments

- `--config` or `-c`: Specify the form configuration to use
- `--verbosity` or `-v`: Set logging verbosity (minimal/balanced/verbose)
- `--min-interval`: Override minimum time between submissions
- `--max-interval`: Override maximum time between submissions

### Environment Variables

- `FORM_CONFIG`: Form configuration to use
- `VERBOSITY`: Logging verbosity level
- `MIN_INTERVAL`: Minimum time between submissions
- `MAX_INTERVAL`: Maximum time between submissions
- `TARGET_URL`: Override the URL from the configuration

## Requirements

- Python 3.9+
- Chrome/Chromium browser
- Docker (optional)

## License

MIT License
