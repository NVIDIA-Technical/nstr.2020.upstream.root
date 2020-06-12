import asyncio
import os
from .decorators import async_timeout


@async_timeout(20)
async def clone_repo(repo_url: str, digest_id: str) -> str:
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth=1",
            "--single-branch",
            repo_url,
            f"../tmp/{digest_id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        return digest_id
    except Exception as e:
        print(f"Clone failed with exception: {str(e)}")
        return f"Error cloning repository: {str(e)}"

def delete_repo(digest_id: str):
    os.system(f"rm -drf ../tmp/{digest_id}")
    os.system(f"rm -f ../tmp/ingest-{digest_id}")
