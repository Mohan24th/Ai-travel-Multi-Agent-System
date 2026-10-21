from travel_agent.utils.source_extractor import extract_urls


def test_extracts_urls():
    text = "1. Hotel site\n   https://example.com/hotel\n   Hotel details"
    assert extract_urls(text) == ["https://example.com/hotel"]


def test_removes_duplicate_urls():
    text = "https://example.com https://example.com"
    assert extract_urls(text) == ["https://example.com"]


def test_ignores_invalid_urls():
    text = "Not a URL: example.com and https://"
    assert extract_urls(text) == []


def test_empty_input():
    assert extract_urls("") == []
    assert extract_urls(None) == []
