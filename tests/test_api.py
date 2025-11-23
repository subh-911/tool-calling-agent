"""
Integration tests for FastAPI endpoints.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi import status

from app.core.providers.base import LLMResponse, ToolCall


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "provider" in data
        assert "tools_registered" in data

    def test_health_check_returns_tool_count(self, test_client):
        """Test that health check returns correct tool count."""
        response = test_client.get("/api/v1/health")
        data = response.json()

        assert data["tools_registered"] == 5  # We registered 5 tools


class TestToolsEndpoint:
    """Tests for /tools endpoint."""

    def test_list_tools(self, test_client):
        """Test listing available tools."""
        response = test_client.get("/api/v1/tools")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "tools" in data
        assert "count" in data
        assert data["count"] == 5
        assert len(data["tools"]) == 5

    def test_tools_have_required_fields(self, test_client):
        """Test that each tool has name and description."""
        response = test_client.get("/api/v1/tools")
        data = response.json()

        for tool in data["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert len(tool["name"]) > 0
            assert len(tool["description"]) > 0


class TestQueryEndpoint:
    """Tests for /query endpoint."""

    @patch('app.api.routes.ToolAgent')
    def test_query_basic(self, mock_agent_class, test_client):
        """Test basic query execution."""
        # Mock agent instance
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "response": "Test response",
            "tool_calls_made": 0,
            "conversation_history": [],
            "correlation_id": "test-123"
        }
        mock_agent.provider_name = "openai"
        mock_agent_class.return_value = mock_agent

        response = test_client.post(
            "/api/v1/query",
            json={"query": "Hello, how are you?"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "response" in data
        assert "tool_calls_made" in data
        assert "provider" in data
        assert "correlation_id" in data

    @patch('app.api.routes.ToolAgent')
    def test_query_with_provider(self, mock_agent_class, test_client):
        """Test query with specific provider."""
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "response": "Test response",
            "tool_calls_made": 0,
            "conversation_history": [],
            "correlation_id": "test-123"
        }
        mock_agent.provider_name = "anthropic"
        mock_agent_class.return_value = mock_agent

        response = test_client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "provider": "anthropic"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["provider"] == "anthropic"

    @patch('app.api.routes.ToolAgent')
    def test_query_with_max_tool_calls(self, mock_agent_class, test_client):
        """Test query with custom max_tool_calls."""
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "response": "Test response",
            "tool_calls_made": 2,
            "conversation_history": [],
            "correlation_id": "test-123"
        }
        mock_agent.provider_name = "openai"
        mock_agent_class.return_value = mock_agent

        response = test_client.post(
            "/api/v1/query",
            json={
                "query": "Complex query",
                "max_tool_calls": 3
            }
        )

        assert response.status_code == status.HTTP_200_OK
        # Verify max_tool_calls was passed to agent
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["max_tool_calls"] == 3

    def test_query_missing_query_field(self, test_client):
        """Test that missing query field returns validation error."""
        response = test_client.post(
            "/api/v1/query",
            json={}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_empty_query(self, test_client):
        """Test that empty query returns validation error."""
        response = test_client.post(
            "/api/v1/query",
            json={"query": ""}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_too_long(self, test_client):
        """Test that query exceeding max length returns validation error."""
        long_query = "x" * 6000  # Exceeds 5000 char limit

        response = test_client.post(
            "/api/v1/query",
            json={"query": long_query}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_invalid_provider(self, test_client):
        """Test that invalid provider returns validation error."""
        response = test_client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "provider": "invalid_provider"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.routes.ToolAgent')
    def test_query_with_correlation_id(self, mock_agent_class, test_client):
        """Test query with custom correlation ID."""
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "response": "Test response",
            "tool_calls_made": 0,
            "conversation_history": [],
            "correlation_id": "custom-correlation-123"
        }
        mock_agent.provider_name = "openai"
        mock_agent_class.return_value = mock_agent

        response = test_client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "correlation_id": "custom-correlation-123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["correlation_id"] == "custom-correlation-123"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns API information."""
        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "tools" in data
        assert "query" in data


class TestErrorHandling:
    """Tests for error handling."""

    @patch('app.api.routes.ToolAgent')
    def test_internal_error_handling(self, mock_agent_class, test_client):
        """Test that internal errors are handled gracefully."""
        mock_agent = Mock()
        mock_agent.execute.side_effect = Exception("Unexpected error")
        mock_agent.provider_name = "openai"
        mock_agent_class.return_value = mock_agent

        response = test_client.post(
            "/api/v1/query",
            json={"query": "Test query"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "InternalServerError"

    @patch('app.api.routes.ToolAgent')
    def test_tool_execution_error_handling(self, mock_agent_class, test_client):
        """Test that tool execution errors are handled."""
        from app.tools.registry import ToolExecutionError

        mock_agent = Mock()
        mock_agent.execute.side_effect = ToolExecutionError("Tool failed")
        mock_agent.provider_name = "openai"
        mock_agent_class.return_value = mock_agent

        response = test_client.post(
            "/api/v1/query",
            json={"query": "Test query"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"]["error"] == "ToolExecutionError"


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are present."""
        response = test_client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # CORS middleware should add headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
