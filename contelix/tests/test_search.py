"""Unit tests for web search tools."""

from unittest.mock import patch, MagicMock

import pytest

from contelix.tools.search import competitive_search, search_news


def _set_search_keys(monkeypatch, tavily_key="", bocha_key=""):
    """Set search API keys in both config module and search module for testing."""
    import contelix.config
    import contelix.tools.search
    monkeypatch.setattr(contelix.config, "TAVILY_API_KEY", tavily_key)
    monkeypatch.setattr(contelix.config, "BOCHA_API_KEY", bocha_key)
    # search.py imported these at module level, so patch its bindings too
    monkeypatch.setattr(contelix.tools.search, "TAVILY_API_KEY", tavily_key)
    monkeypatch.setattr(contelix.tools.search, "BOCHA_API_KEY", bocha_key)
    if tavily_key:
        monkeypatch.setenv("TAVILY_API_KEY", tavily_key)


class TestCompetitiveSearch:
    """Tests for competitive_search tool."""

    def test_no_api_keys_configured(self, clean_env, monkeypatch):
        """Should return error when no search API key is set."""
        _set_search_keys(monkeypatch, tavily_key="", bocha_key="")
        result = competitive_search.invoke({"query": "test query"})
        assert "ERROR" in result or "No search" in result

    @patch("contelix.tools.search.TavilySearchResults")
    def test_tavily_search_success(self, mock_tavily, clean_env, monkeypatch):
        """Should use Tavily when TAVILY_API_KEY is set."""
        _set_search_keys(monkeypatch, tavily_key="tvly-test-key", bocha_key="")
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = [
            {"content": "Test result about AI", "url": "https://example.com/ai"},
        ]
        mock_tavily.return_value = mock_instance

        result = competitive_search.invoke({"query": "AI companies", "num_results": 2})
        assert "Test result about AI" in result
        assert "https://example.com/ai" in result

    @patch("contelix.tools.search.requests.post")
    def test_bocha_search_success(self, mock_post, clean_env, monkeypatch):
        """Should use BochaAI when TAVILY_API_KEY is empty."""
        _set_search_keys(monkeypatch, tavily_key="", bocha_key="bocha-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "webPages": {
                    "value": [
                        {
                            "name": "Bocha Result",
                            "url": "https://bocha.example.com",
                            "snippet": "Bocha search snippet",
                        }
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        result = competitive_search.invoke({"query": "test query"})
        assert "Bocha Result" in result
        assert "https://bocha.example.com" in result

    @patch("contelix.tools.search.requests.post")
    def test_bocha_search_http_error(self, mock_post, clean_env, monkeypatch):
        """Should handle BochaAI API errors gracefully."""
        _set_search_keys(monkeypatch, tavily_key="", bocha_key="bocha-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = competitive_search.invoke({"query": "test"})
        assert "Search failed" in result or "Error" in result


class TestSearchNews:
    """Tests for search_news tool."""

    def test_search_news_delegates_to_competitive_search(self, clean_env, monkeypatch):
        """search_news should call competitive_search with 'latest news' suffix."""
        _set_search_keys(monkeypatch, bocha_key="test-key")

        with patch("contelix.tools.search.competitive_search") as mock_cs:
            mock_cs.invoke.return_value = "News results here"
            result = search_news.invoke({"query": "Tesla", "num_results": 3})
            assert result == "News results here"
            call_args = mock_cs.invoke.call_args[0][0]
            assert "latest news" in call_args["query"]
            assert call_args["num_results"] == 3
