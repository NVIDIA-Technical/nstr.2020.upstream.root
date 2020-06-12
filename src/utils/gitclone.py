import asyncio
import os

from .decorators import async_timeout
from config import TMP_BASE_PATH, CLONE_TIMEOUT


@async_timeout(CLONE_TIMEOUT)
async def clone_repo(repo_url: str, digest_id: str) -> str:
    #Clean up any existing repo
    delete_repo(digest_id)

    proc = await asyncio.create_subprocess_exec(
        "git",
        "clone",
        "--depth=1",
        "--single-branch",
        repo_url,
        f"{TMP_BASE_PATH}/{digest_id}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    stdout, stderr = await proc.communicate()

def delete_repo(digest_id: str):
    os.system(f"rm -drf {TMP_BASE_PATH}/{digest_id}")
