# Form Monkey - Automated Form Submission Tool

A Python-based tool for automated form submissions with support for various phone number formats, SQL injection testing, and anti-bot detection.

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
- SQL Injection testing for form security
- Docker support

## Configuration

### Form Configuration (form_config.json)

The tool uses a JSON configuration file to define form fields, operation modes, and their properties:

```json
{
    "example_form": {
        "url": "https://example.com/form",
        "mode": "submit",  // "submit" or "sql_inject"
        "verbosity": "balanced",
        "timing": {
            "min_interval": 300,
            "max_interval": 2700
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
    },
    "sql_injection_example": {
        "url": "https://example.com/form",
        "mode": "sql_inject",
        "verbosity": "balanced",
        "fields": {
            "first_name": {
                "selector": "input[name='first_name']",
                "type": "css",
                "required": true
            }
        },
        "sql_injection_settings": {
            "test_all_fields": true,
            "max_attempts_per_field": 10,
            "payload_categories": ["basic", "error", "time", "stacked", "complex"]
        }
    }
}
```

### Operation Modes

The tool supports two operation modes:

1. **Submit Mode** (`"mode": "submit"`): Automated form submission with random data
2. **SQL Injection Mode** (`"mode": "sql_inject"`): Tests the form for SQL injection vulnerabilities

### Phone Number Formats

The tool supports various phone number formats based on the `area_code_type` configuration:

- Single type: `"area_code_type": "canadian"`
- Multiple types: `"area_code_type": ["canadian", "american"]`

When multiple types are specified, the tool will randomly choose one type for each submission.

### SQL Injection Settings

When using SQL Injection mode, you can customize the testing behavior:

- `test_all_fields`: Whether to test all form fields or stop after finding a vulnerability
- `max_attempts_per_field`: Limit the number of payloads to test per field (0 = test all)
- `payload_categories`: Categories of SQL injection payloads to test:
  - `basic`: Simple SQL injection tests like `' OR '1'='1'`
  - `error`: Error-based SQL injection techniques
  - `time`: Time-based SQL injection tests
  - `stacked`: Tests for stacked queries (multiple statements)
  - `complex`: More advanced SQL injection patterns
  - `nosql`: NoSQL injection patterns
  - `xss`: SQL injection combined with XSS
  - `encoding`: URL-encoded SQL injection tests

## Usage

### Running with Docker

```bash
# Build the Docker image
docker build -t form-monkey .

# Run in form submission mode
docker run -it --rm -e FORM_CONFIG=example_form -e VERBOSITY=balanced form-monkey

# Run in SQL injection mode
docker run -it --rm -e FORM_CONFIG=sql_injection_example form-monkey
```

### Command Line Arguments

- `--config` or `-c`: Specify the form configuration to use
- `--verbosity` or `-v`: Set logging verbosity (minimal/balanced/verbose)
- `--min-interval`: Override minimum time between submissions
- `--max-interval`: Override maximum time between submissions
- `--url`: Override the URL from the configuration

### Environment Variables

- `FORM_CONFIG`: Form configuration to use
- `VERBOSITY`: Logging verbosity level
- `MIN_INTERVAL`: Minimum time between submissions
- `MAX_INTERVAL`: Maximum time between submissions
- `TARGET_URL`: Override the URL from the configuration

## Best Practices for SQL Injection Prevention

- Use parameterized queries/prepared statements
- Implement input validation and sanitization
- Apply the principle of least privilege for database users
- Use stored procedures for complex operations
- Escape special characters in user input
- Consider using an ORM (Object-Relational Mapping) library

## Requirements

- Python 3.9+
- Chrome/Chromium browser
- Docker (optional)

## License

MIT License
