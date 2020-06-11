import asyncio
import os
from typing import Tuple
from utils.decorators import async_timeout

def get_repo_id(repo_url: str) -> str:
    """Extract a unique identifier from a GitHub URL."""
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Please provide a valid GitHub repository URL.")
    repo_url = repo_url.split(" ")[0]
    
    id = repo_url.replace("https://github.com/", "").replace("/", "-")
    return id

@async_timeout(20)
async def clone_repo(repo_url: str, id: str) -> str:
    """Clone a GitHub repository with a timeout."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth=1",
            "--single-branch",
            repo_url,
            f"../tmp/{id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        return id
    except Exception as e:
        print(f"Clone failed with exception: {str(e)}")
        return f"Error cloning repository: {str(e)}"

def delete_repo(repo_id: str):
    """Delete a cloned repository and its associated files."""
    os.system(f"rm -drf ../tmp/{repo_id}")
    os.system(f"rm -f ../tmp/ingest-{repo_id}")
