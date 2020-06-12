
def reconstruct_github_url(full_path: str) -> str:
    path_parts = full_path.split('/')
    
    
    # Reconstruct the GitHub URL
    github_url = f"https://github.com/{path_parts[0]}/{path_parts[1]}"
    return github_url



def id_from_repo_url(repo_url: str) -> str:
    """Extract a unique identifier from a GitHub URL."""
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Please provide a valid GitHub repository URL.")
    repo_url = repo_url.split(" ")[0]
    
    id = repo_url.replace("https://github.com/", "").replace("/", "-")
    return id
