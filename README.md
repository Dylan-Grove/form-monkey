# Form Monkey

Form Monkey is an automated form filling and security testing tool designed to help test web applications for various vulnerabilities, including SQL injection, XSS, CSRF, and security headers. It uses a selenium driverwith anti-bot detection patches to send fake data on submission forms, try SQL injections, and more, running on a docker container.

All configuration of the container uses config.json. You can also launch the container with environment variable flags if you don't want to use a config file.

## Features

- **Form Submission**: Automate form submissions with random or predefined data
- **SQL Injection Testing**: Test forms for SQL injection vulnerabilities
- **XSS Testing**: Test forms for Cross-Site Scripting vulnerabilities
- **CSRF Analysis**: Analyze forms for Cross-Site Request Forgery protections
- **Security Headers Analysis**: Evaluate HTTP security headers
- **Comprehensive Testing**: Run all testing modes in sequence or parallel
- **Detailed Reporting**: Generate HTML, JSON, or PDF security reports

## Directory Structure

```
form-monkey/
├── config.json             # Default configuration
├── main.py                 # Main entry point
├── mode_submit.py          # Form submission module
├── mode_sql_inject.py      # SQL injection testing module
├── mode_xss.py             # XSS testing module
├── mode_csrf.py            # CSRF testing module
├── mode_headers.py         # Security headers testing module
├── mode_comprehensive.py   # Comprehensive testing module
├── security_report.py      # Security report generation
├── utils.py                # Utility functions
├── random_data.json        # Random data for form filling
├── Dockerfile              # Docker configuration
└── README.md               # Project documentation
```

## Installation

### Prerequisites (Installed with the dockerfile to the container)

- Python 3.7+
- Chrome browser
- ChromeDriver (for Selenium)

### Using Docker

```bash
# Build the Docker image
docker build -t form-monkey .

# Run the Docker container
docker run --rm form-monkey
```

## Usage

Form Monkey can be run in different modes to test various aspects of web applications.

### Basic Usage

```bash
# Run form submission with default configuration
python main.py --mode submit

# Run SQL injection test
python main.py --mode sql_inject

# Run XSS test
python main.py --mode xss

# Run CSRF test
python main.py --mode csrf

# Run security headers test
python main.py --mode headers

# Run comprehensive test (all modes)
python main.py --mode comprehensive

# Generate HTML report
python main.py --mode comprehensive --report

# Generate specific report format
python main.py --mode comprehensive --report --report-format json
```

### Using Configuration Files

You can specify a custom configuration file in the container (If none is provided, it will use the default):

```bash
python main.py --config my_config.json --mode submit
```

### Using Docker

```bash
# Run with Docker
docker run --rm -e FORM=example_submit form-monkey

# Run in verbose mode
docker run --rm -e FORM=example_submit -e VERBOSITY=verbose form-monkey
```

## Configuration

Form Monkey is configured via JSON files. Here's an example configuration:

```json
{
  "verbosity": "balanced",
  "timing": {
    "element_wait_time": 10,
    "min_interval": 300,
    "max_interval": 2700
  },
  "example_submit": {
    "url": "https://example.com/contact",
    "fields": [
      {
        "id": "first_name",
        "name": "first_name",
        "type": "css",
        "field_type": "first_name",
        "required": true
      },
      {
        "id": "last_name",
        "name": "last_name",
        "type": "css",
        "field_type": "last_name",
        "required": true
      }
    ],
    "submit_button": {
      "type": "css",
      "selector": "button[type='submit']"
    },
    "verbosity": "balanced",
    "submissions": 1
  }
}
```

## Environment Variables

The following environment variables can be used to configure Form Monkey:

- `FORM`: Name of the form configuration to use
- `VERBOSITY`: Logging verbosity level (quiet, minimal, normal, balanced, verbose, debug)
- `CONFIG_PATH`: Path to the configuration file
- `MIN_INTERVAL`: Minimum interval between form submissions (in seconds)
- `MAX_INTERVAL`: Maximum interval between form submissions (in seconds)

## Security Reports

Form Monkey can generate security reports in various formats:

- **HTML**: Interactive reports with charts and detailed findings
- **JSON**: Machine-readable reports for integration with other tools
- **PDF**: Portable document format reports for sharing

Reports include:

- Executive summary of findings
- Vulnerability counts by severity
- Charts and visualizations
- Detailed findings with recommendations
- Test results for each mode

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
