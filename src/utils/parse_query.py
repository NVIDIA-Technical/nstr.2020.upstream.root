import uuid
import re
from utils.log_convert import logSliderToSize
from typing import List

from config import TMP_BASE_PATH, DEFAULT_IGNORE_PATTERNS

def validate_github_url(url: str) -> bool:
    if not url.startswith('https://'):
        url = 'https://' + url
        
    github_pattern = r'^https://github\.com/[^/]+/[^/]+'
    return bool(re.match(github_pattern, url))

def parse_url(url: str) -> dict:
    parsed = {
        "user_name": None,
        "repo_name": None,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": None,
        "url": None,
    }
    
    if not validate_github_url(url):
        raise ValueError("Invalid GitHub URL. Please provide a valid GitHub repository URL.")
    
    url = url.split(" ")[0]
    url = url.replace("https://github.com/", "")
    path_parts = url.split('/')

    parsed["user_name"] = path_parts[0]
    parsed["repo_name"] = path_parts[1]
    

    parsed["url"] = f"https://github.com/{parsed['user_name']}/{parsed['repo_name']}"
    parsed['slug'] = parsed["url"].replace("https://github.com/", "").replace("/", "-")
    parsed["id"] = str(uuid.uuid4())
    parsed["local_path"] = f"{TMP_BASE_PATH}/{parsed['id']}/{parsed['slug']}"
    

    if len(path_parts) > 3:
        parsed["type"] = path_parts[2]
        parsed["branch"] = path_parts[3]
        if len(parsed['branch']) == 40 and all(c in '0123456789abcdefABCDEF' for c in parsed['branch']):
            parsed["commit"] = parsed['branch']
            
        parsed["subpath"] = "/" + "/".join(path_parts[4:])
    return parsed


def parse_pattern(pattern: str) -> List[str]:
    for p in pattern.split(","):
        if not all(c.isalnum() or c in "-_./+*" for c in p.strip()):
            raise ValueError(f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed.")
    return [p.strip() for p in pattern.split(",")]


def parse_query(input_text: str, slider_position: int, pattern_type: str, pattern: str) -> dict:
    query = parse_url(input_text)
    query['max_file_size'] = logSliderToSize(slider_position)
    query['pattern_type'] = pattern_type
    parsed_pattern = parse_pattern(pattern)
    if pattern_type == 'include':
        query['include_patterns'] = parsed_pattern
        query['ignore_patterns'] = DEFAULT_IGNORE_PATTERNS
    else:
        #this adds the patterns to the default ignore patterns
        query['ignore_patterns'] = DEFAULT_IGNORE_PATTERNS + parsed_pattern
        query['include_patterns'] = None


    return query
