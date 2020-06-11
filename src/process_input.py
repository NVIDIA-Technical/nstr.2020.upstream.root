from utils.gitclone import get_repo_id, delete_repo, clone_repo
from ingest import analyze_codebase


async def process_input(text: str) -> str:
    if not text.startswith("https://github.com/"):
        return "Invalid GitHub URL. Please provide a valid GitHub repository URL."
    
    repo_id = get_repo_id(text)
    if not repo_id:
        return "Invalid GitHub URL. Please provide a valid GitHub repository URL."
    
    delete_repo(repo_id)
    await clone_repo(text, repo_id)
        
    result = analyze_codebase(f"../tmp/{repo_id}")
    delete_repo(repo_id)
    
    if not result:
        return "Repository processing failed or timed out after 30 seconds."
        
    return result
