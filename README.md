# Form Monkey 🐒

A chaos engineering tool for automated form submissions with configurable delays and randomization.

## Features

- Configurable form submission intervals (3-30 minutes)
- Random data generation for form fields
- Support for multiple form configurations
- Verbosity levels (minimal, balanced, verbose)
- Anti-bot detection bypass
- Detailed logging and debugging

## Requirements

- Python 3.9+
- Docker (for containerized execution)
- Chrome/Chromium browser (for form submission)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/form-monkey.git
cd form-monkey
```

2. Build the Docker image:
```bash
docker build -t form-monkey .
```

## Usage

### Basic Usage

Run the form submitter with default configuration:
```bash
docker run -it --rm form-monkey
```

### Configuration

1. Create a form configuration in `form_config.json`:
```json
{
    "default": {
        "verbosity": "balanced",
        "timing": {
            "min_interval": 180,
            "max_interval": 1800
        }
    },
    "example_form": {
        "url": "https://example.com/form",
        "verbosity": "balanced",
        "timing": {
            "min_interval": 180,
            "max_interval": 1800
        },
        "fields": {
            "first_name": {
                "selector": "#first_name",
                "type": "text",
                "required": true,
                "validation": {
                    "min_length": 2,
                    "max_length": 50
                }
            },
            "last_name": {
                "selector": "#last_name",
                "type": "text",
                "required": true,
                "validation": {
                    "min_length": 2,
                    "max_length": 50
                }
            },
            "email": {
                "selector": "#email",
                "type": "email",
                "required": true,
                "validation": {
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                }
            },
            "phone": {
                "selector": "#phone",
                "type": "tel",
                "required": true,
                "validation": {
                    "pattern": "^\\d{10}$"
                }
            }
        }
    }
}
```

2. Run with specific configuration:
```bash
docker run -it --rm -e FORM_CONFIG=example_form form-monkey
```

### Environment Variables

- `FORM_CONFIG`: Name of the form configuration to use (default: "default")
- `VERBOSITY`: Logging verbosity level (minimal, balanced, verbose)
- `MIN_INTERVAL`: Minimum time between submissions in seconds (overrides config)
- `MAX_INTERVAL`: Maximum time between submissions in seconds (overrides config)

### Help

Run with --help to see all available options:
```bash
docker run -it --rm form-monkey --help
```

## Development

### Adding New Form Configurations

1. Add a new configuration section to `form_config.json`
2. Define form fields with their selectors and validation rules
3. Run with the new configuration name

### Customizing Data Generation

The tool uses the Faker library for generating random data. You can customize the data generation by modifying the lists of:
- Common words
- Email domains
- Area codes
- Special characters

## License

MIT License - see LICENSE file for details
