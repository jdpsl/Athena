# {{project_name}}

{{description}}

## Features

- FastAPI web framework
- Pydantic for data validation
- Async/await support
- Automatic API documentation (Swagger/ReDoc)
- Environment-based configuration
- Comprehensive testing setup (pytest)
- Code quality tools (ruff, black)
- GitHub Actions CI/CD

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Run development server
uvicorn {{project_name_snake}}.main:app --reload

# API will be available at:
# - http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## Development

```bash
# Run tests
pytest

# Run linter
ruff check .

# Format code
black .

# Run with coverage
pytest --cov={{project_name_snake}}
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check
- `GET /docs` - Interactive API documentation
- `GET /redoc` - ReDoc documentation

## Project Structure

```
{{project_name}}/
├── src/{{project_name_snake}}/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   ├── routers/          # API routes
│   └── models/           # Pydantic models
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── .github/
│   └── workflows/
│       └── test.yml
├── pyproject.toml
├── .gitignore
├── .env.example
├── LICENSE
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Add your environment variables here
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

{{license}}

---

Generated with [Athena AI](https://github.com/jdpsl/Athena)
