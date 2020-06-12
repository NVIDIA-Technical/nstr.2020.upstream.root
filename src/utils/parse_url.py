
def parse_url(url: str) -> dict:
    parsed = {
        "url": None,
        "user_name": None,
        "repo_name": None,
        "tree": False,
        "branch": None,
        "path": "/",
    }
    
    
    if not url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Please provide a valid GitHub repository URL.")
    
    
    
    # Remove anything after the first space
    url = url.split(" ")[0]

    url = url.replace("https://github.com/", "")
    path_parts = url.split('/')

    parsed["user_name"] = path_parts[0]
    parsed["repo_name"] = path_parts[1]

    parsed["url"] = f"https://github.com/{parsed['user_name']}/{parsed['repo_name']}"
    parsed['id'] = parsed["url"].replace("https://github.com/", "").replace("/", "-")

    if len(path_parts) > 2:
        if path_parts[2] == "tree":
            parsed["tree"] = True
            parsed["path"] = "/".join(path_parts[3:])
    print(parsed)
    return parsed