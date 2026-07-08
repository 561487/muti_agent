"""Unit tests for web scraping tools."""

from unittest.mock import patch, MagicMock

from contelix.tools.scraping import scrape_webpages, extract_key_info


class TestScrapeWebpages:
    """Tests for scrape_webpages tool."""

    def test_empty_urls_returns_message(self):
        """Should return a message when no URLs are provided."""
        result = scrape_webpages.invoke({"urls": []})
        assert "No URLs" in result

    @patch("contelix.tools.scraping.WebBaseLoader")
    def test_scrape_single_url(self, mock_loader_class):
        """Should scrape and return content from URLs."""
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Test Page", "source": "https://example.com"}
        mock_doc.page_content = "This is the extracted content from the page."

        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_doc]
        mock_loader_class.return_value = mock_loader

        result = scrape_webpages.invoke({"urls": ["https://example.com"]})
        assert "Test Page" in result
        assert "extracted content" in result

    @patch("contelix.tools.scraping.WebBaseLoader")
    def test_scrape_truncates_content(self, mock_loader_class):
        """Should truncate very long page content at 8000 chars."""
        long_content = "X" * 10000
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Long Page", "source": "https://example.com"}
        mock_doc.page_content = long_content

        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_doc]
        mock_loader_class.return_value = mock_loader

        result = scrape_webpages.invoke({"urls": ["https://example.com"]})
        assert len(result) < 10000  # Should be truncated

    @patch("contelix.tools.scraping.WebBaseLoader")
    def test_scrape_url_limit(self, mock_loader_class):
        """Should limit to max 5 URLs per call."""
        urls = [f"https://example.com/{i}" for i in range(10)]

        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Page", "source": "https://example.com"}
        mock_doc.page_content = "Content"

        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_doc]
        mock_loader_class.return_value = mock_loader

        scrape_webpages.invoke({"urls": urls})
        # Verify only 5 URLs were passed to the loader
        called_urls = mock_loader_class.call_args[0][0]
        assert len(called_urls) <= 5


class TestExtractKeyInfo:
    """Tests for extract_key_info tool."""

    @patch("contelix.tools.scraping.WebBaseLoader")
    def test_extract_key_info(self, mock_loader_class):
        """Should extract and return key info from a URL."""
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Company Profile"}
        mock_doc.page_content = "Company details here..."

        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_doc]
        mock_loader_class.return_value = mock_loader

        result = extract_key_info.invoke({
            "url": "https://example.com",
            "focus_areas": "products, pricing",
        })
        assert "Company Profile" in result
        assert "products" in result
        assert "pricing" in result
