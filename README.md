# Tool-Calling Agent

A production-quality tool-calling agent with multi-provider LLM support (OpenAI and Anthropic), built with FastAPI and Python.

## Features

- **Multi-Provider Support**: Seamlessly switch between OpenAI (GPT-4) and Anthropic (Claude 3.5+)
- **Automatic Tool Selection**: LLM intelligently selects and executes tools based on user queries
- **5 Production Tools**: Financial calculations, currency conversion, weather data, date utilities, and text analysis
- **Loop Prevention**: Maximum tool call limits to prevent infinite loops (configurable, default: 5)
- **Tool Validation**: Output validation and sanitization before returning to LLM
- **Structured Logging**: JSON logging with correlation IDs for production debugging
- **Comprehensive Testing**: 80%+ test coverage with unit and integration tests
- **Docker Ready**: Multi-stage Dockerfile for optimized production deployment
- **Production Features**: Health checks, error handling, CORS support, request validation

## Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key or Anthropic API key (or both)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd tool-calling-agent
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Run the application:**
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
# Build and run with Docker Compose
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Usage

### Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate compound interest on $10,000 at 6% for 15 years",
    "provider": "openai",
    "max_tool_calls": 5
  }'
```

### Example Response

```json
{
  "response": "With an initial investment of $10,000 at an annual interest rate of 6% compounded annually for 15 years, you would have approximately $23,965.58. This means you would earn about $13,965.58 in interest over the 15-year period.",
  "tool_calls_made": 1,
  "provider": "openai",
  "correlation_id": "abc-123-def-456"
}
```

## Available Tools

The agent comes with 5 production-ready tools:

1. **calculate_compound_interest**: Calculate compound interest with various compounding frequencies
2. **convert_currency**: Convert between 9 major currencies (USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR)
3. **get_weather**: Get weather information for any city (mock data for demo)
4. **calculate_date_difference**: Calculate differences between dates with business day support
5. **analyze_text**: Comprehensive text analysis including readability and sentiment

## Project Structure

```
tool-calling-agent/
├── app/
│   ├── core/              # Core agent and provider logic
│   │   ├── agent.py       # Main ToolAgent class
│   │   ├── schemas.py     # Schema generation
│   │   └── providers/     # LLM provider adapters
│   ├── tools/             # Tool implementations
│   │   ├── registry.py    # Tool registry
│   │   ├── financial.py   # Financial tools
│   │   ├── data.py        # Data retrieval tools
│   │   └── utilities.py   # Utility tools
│   ├── api/               # FastAPI routes and models
│   ├── utils/             # Logging and validation
│   ├── config.py          # Configuration management
│   └── main.py            # Application entry point
├── tests/                 # Comprehensive test suite
├── docker/                # Docker configuration
├── docs/                  # Documentation
└── pyproject.toml         # Project metadata
```

## Configuration

Configuration is managed through environment variables. See `.env.example` for all options.

Key settings:
- `DEFAULT_LLM_PROVIDER`: Choose 'openai' or 'anthropic'
- `MAX_TOOL_CALLS_PER_TURN`: Prevent infinite loops (default: 5)
- `ENABLE_TOOL_VALIDATION`: Enable output validation (default: true)
- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_tools.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code with Black
black app/ tests/

# Lint with Ruff
ruff check app/ tests/

# Type checking with mypy
mypy app/
```

### Adding New Tools

See [docs/TOOLS.md](docs/TOOLS.md) for a comprehensive guide on creating and registering new tools.

## Best Practices Implemented

This project follows best practices from AI agent research:

1. **Rich Tool Descriptions**: Each tool has detailed descriptions with examples (40% accuracy improvement per Google ADK research)
2. **Tool Output Validation**: All tool outputs are validated before returning to the LLM
3. **Few-Shot Examples**: Tool schemas include example inputs/outputs for better LLM understanding
4. **Loop Prevention**: Maximum 3-5 tool calls per turn to prevent infinite loops
5. **Structured Logging**: Correlation IDs and structured logs for production debugging
6. **Error Recovery**: Graceful handling of tool failures with informative error messages

## API Endpoints

- `POST /api/v1/query` - Execute agent query with tool calling
- `GET /api/v1/tools` - List all available tools
- `GET /api/v1/health` - Health check endpoint
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Documentation

- [API Documentation](docs/API.md) - Detailed API reference
- [Tool Creation Guide](docs/TOOLS.md) - How to create custom tools
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions

## Testing

The project includes comprehensive tests:

- **Unit Tests**: Individual tool testing with edge cases
- **Integration Tests**: API endpoint testing
- **Provider Tests**: LLM provider adapter testing
- **Agent Tests**: Core agent logic including loop prevention

Current test coverage: **80%+**

## Production Readiness

This project is production-ready with:

- ✅ Environment-based configuration
- ✅ Structured JSON logging
- ✅ Health check endpoints
- ✅ Docker containerization
- ✅ Error handling and recovery
- ✅ Input validation with Pydantic
- ✅ CORS support
- ✅ Comprehensive testing
- ✅ Security best practices (non-root user, input sanitization)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built following best practices from:
- Google's Agent Development Kit (ADK) research on tool descriptions
- OpenAI's function calling documentation
- Anthropic's Claude tool use guidelines
- FastAPI production deployment patterns

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Version**: 1.0.0
**Author**: Your Name
**Last Updated**: 2024
