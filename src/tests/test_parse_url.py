import pytest
from utils.parse_url import parse_url

def test_parse_url_valid():
    url = "https://github.com/user/repo"
    result = parse_url(url)
    assert result["user_name"] == "user"
    assert result["repo_name"] == "repo"
    assert result["url"] == "https://github.com/user/repo"

def test_parse_url_invalid():
    url = "https://invalid.com/user/repo"
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        parse_url(url) 