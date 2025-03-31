# Form Monkey

Form Monkey is an automated form filling and security testing tool designed to help test web applications for various vulnerabilities, including SQL injection, XSS, CSRF, and security headers.

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
├── src/                    # Source code
│   ├── config/             # Configuration files
│   │   └── config.json     # Default configuration
│   ├── data/               # Data files
│   │   └── random_data.json # Random data for form filling
│   ├── modes/              # Testing modes
│   │   ├── __init__.py     # Package initialization
│   │   ├── submit.py       # Form submission module
│   │   ├── sql_inject.py   # SQL injection testing module
│   │   ├── xss.py          # XSS testing module
│   │   ├── csrf.py         # CSRF testing module
│   │   ├── headers.py      # Security headers testing module
│   │   └── comprehensive.py # Comprehensive testing module
│   └── utils/              # Utility functions
│       ├── __init__.py     # Package initialization
│       ├── utils.py        # General utilities
│       └── security_report.py # Security report generation
├── main.py                 # Main entry point (legacy)
├── Dockerfile              # Docker configuration
└── README.md               # Project documentation
```

## Installation

### Prerequisites

- Python 3.7+
- Chrome browser
- ChromeDriver (for Selenium)

### Using pip

```bash
# Clone the repository
git clone https://github.com/username/form-monkey.git
cd form-monkey

# Install dependencies
pip install -r requirements.txt
```

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
python src/main.py --mode submit

# Run SQL injection test
python src/main.py --mode sql_inject

# Run XSS test
python src/main.py --mode xss

# Run CSRF test
python src/main.py --mode csrf

# Run security headers test
python src/main.py --mode headers

# Run comprehensive test (all modes)
python src/main.py --mode comprehensive

# Generate HTML report
python src/main.py --mode comprehensive --report

# Generate specific report format
python src/main.py --mode comprehensive --report --report-format json
```

### Using Configuration Files

You can specify a custom configuration file:

```bash
python src/main.py --config my_config.json --mode submit
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
