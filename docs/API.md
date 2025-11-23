# API Documentation

Complete API reference for the Tool-Calling Agent.

## Base URL

```
http://localhost:8000
```

In production, replace with your actual domain.

## API Version

Current API version: `v1`

All endpoints are prefixed with `/api/v1`

## Authentication

Currently, the API does not require authentication. For production deployment, consider adding:
- API key authentication
- OAuth2/JWT tokens
- Rate limiting per client

## Endpoints

### 1. Query Agent

Execute a query with automatic tool calling.

**Endpoint:** `POST /api/v1/query`

**Request Body:**

```json
{
  "query": "string (required, 1-5000 chars)",
  "provider": "string (optional, 'openai' or 'anthropic')",
  "max_tool_calls": "integer (optional, 1-10)",
  "correlation_id": "string (optional)"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | User query or prompt (1-5000 characters) |
| provider | string | No | LLM provider to use ('openai' or 'anthropic'). Defaults to config setting. |
| max_tool_calls | integer | No | Maximum tool calls allowed (1-10). Defaults to 5. |
| correlation_id | string | No | Custom correlation ID for tracking. Auto-generated if not provided. |

**Response:**

```json
{
  "response": "string",
  "tool_calls_made": "integer",
  "provider": "string",
  "correlation_id": "string",
  "conversation_history": "array (optional)"
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Convert 500 USD to EUR and tell me the weather in Paris",
    "provider": "openai",
    "max_tool_calls": 5
  }'
```

**Example Response:**

```json
{
  "response": "500 USD converts to approximately 462.50 EUR. The weather in Paris is currently 18°C and partly cloudy with 65% humidity and light winds at 12 km/h.",
  "tool_calls_made": 2,
  "provider": "openai",
  "correlation_id": "abc-123-def-456"
}
```

**Status Codes:**

- `200 OK`: Successful response
- `400 Bad Request`: Invalid input or tool execution error
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Unexpected server error

**Error Response:**

```json
{
  "detail": {
    "error": "ValidationError",
    "message": "Query must be between 1 and 5000 characters",
    "correlation_id": "abc-123-def-456"
  }
}
```

---

### 2. List Tools

Get information about all available tools.

**Endpoint:** `GET /api/v1/tools`

**Parameters:** None

**Response:**

```json
{
  "tools": [
    {
      "name": "string",
      "description": "string"
    }
  ],
  "count": "integer"
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/tools"
```

**Example Response:**

```json
{
  "tools": [
    {
      "name": "calculate_compound_interest",
      "description": "Calculate compound interest on an investment"
    },
    {
      "name": "convert_currency",
      "description": "Convert amount between different currencies"
    },
    {
      "name": "get_weather",
      "description": "Get current weather information for a specified city"
    },
    {
      "name": "calculate_date_difference",
      "description": "Calculate the difference between two dates"
    },
    {
      "name": "analyze_text",
      "description": "Analyze text and return various statistics and insights"
    }
  ],
  "count": 5
}
```

**Status Codes:**

- `200 OK`: Successful response

---

### 3. Health Check

Check service health and configuration.

**Endpoint:** `GET /api/v1/health`

**Parameters:** None

**Response:**

```json
{
  "status": "string",
  "version": "string",
  "environment": "string",
  "provider": "string",
  "tools_registered": "integer"
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**Example Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "provider": "openai",
  "tools_registered": 5
}
```

**Status Codes:**

- `200 OK`: Service is healthy

---

### 4. Root Endpoint

Get API information and links.

**Endpoint:** `GET /`

**Parameters:** None

**Response:**

```json
{
  "name": "string",
  "version": "string",
  "environment": "string",
  "docs": "string",
  "health": "string",
  "tools": "string",
  "query": "string"
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/"
```

**Example Response:**

```json
{
  "name": "Tool-Calling Agent API",
  "version": "1.0.0",
  "environment": "production",
  "docs": "/docs",
  "health": "/api/v1/health",
  "tools": "/api/v1/tools",
  "query": "/api/v1/query"
}
```

---

## Interactive Documentation

### Swagger UI

Access interactive API documentation with try-it-out functionality:

```
http://localhost:8000/docs
```

### ReDoc

Access alternative API documentation:

```
http://localhost:8000/redoc
```

---

## Rate Limiting

Currently not implemented. For production, consider adding rate limiting:

```python
# Example: 60 requests per minute per client IP
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

---

## CORS

CORS is configured to allow requests from:
- `http://localhost:3000`
- `http://localhost:8000`

To add more origins, update the `CORS_ORIGINS` environment variable:

```bash
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

---

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

### Validation Errors (422)

```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "details": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Tool Execution Errors (400)

```json
{
  "detail": {
    "error": "ToolExecutionError",
    "message": "Tool 'convert_currency' execution failed: Unsupported currency: XYZ",
    "correlation_id": "abc-123-def-456"
  }
}
```

### Internal Server Errors (500)

```json
{
  "detail": {
    "error": "InternalServerError",
    "message": "An unexpected error occurred. Please try again later.",
    "correlation_id": "abc-123-def-456"
  }
}
```

---

## Request/Response Examples

### Example 1: Financial Calculation

**Request:**
```json
{
  "query": "If I invest $5000 at 7.5% annual interest for 10 years with quarterly compounding, how much will I have?"
}
```

**Response:**
```json
{
  "response": "With an initial investment of $5,000 at 7.5% annual interest compounded quarterly for 10 years, you will have approximately $10,511.07. This means you'll earn about $5,511.07 in interest.",
  "tool_calls_made": 1,
  "provider": "openai",
  "correlation_id": "xyz-789"
}
```

### Example 2: Multi-Tool Query

**Request:**
```json
{
  "query": "What's the weather in Tokyo and how many business days are there from today (2024-01-15) until the end of the month (2024-01-31)?"
}
```

**Response:**
```json
{
  "response": "The weather in Tokyo is currently 12°C and clear. From January 15, 2024 to January 31, 2024, there are 12 business days (excluding weekends).",
  "tool_calls_made": 2,
  "provider": "openai",
  "correlation_id": "abc-456"
}
```

### Example 3: Text Analysis

**Request:**
```json
{
  "query": "Analyze this text: 'Artificial intelligence is transforming how we work and live. It's an exciting time for technology!'"
}
```

**Response:**
```json
{
  "response": "The text contains 16 words and 2 sentences, with an average word length of 5.56 characters. The readability score is 58.3, which is at a standard 8th-9th grade reading level. The sentiment is positive, with 1 positive word detected ('exciting').",
  "tool_calls_made": 1,
  "provider": "openai",
  "correlation_id": "def-123"
}
```

---

## Monitoring and Debugging

### Correlation IDs

All requests include a `correlation_id` in the response. Use this to:
- Track requests across logs
- Debug issues
- Correlate errors with specific requests

### Structured Logging

Logs are output in JSON format (production) or pretty-printed (development):

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "event": "query_received",
  "correlation_id": "abc-123",
  "query_preview": "Calculate compound interest...",
  "provider": "openai"
}
```

---

## Performance Considerations

- Average response time: 2-5 seconds (depends on LLM provider)
- Tool execution timeout: 30 seconds (configurable)
- Maximum query length: 5000 characters
- Maximum tool calls per query: 5 (configurable, prevents infinite loops)

---

## SDK Examples

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "query": "Calculate 10% interest on $1000 for 5 years",
        "provider": "openai"
    }
)

data = response.json()
print(data["response"])
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Calculate 10% interest on $1000 for 5 years',
    provider: 'openai'
  })
});

const data = await response.json();
console.log(data.response);
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate 10% interest on $1000 for 5 years"}'
```

---

## Versioning

The API uses URL versioning (`/api/v1/`). Future versions will be released as `/api/v2/`, etc., with backward compatibility maintained for at least one major version.
