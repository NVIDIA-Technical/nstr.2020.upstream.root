import asyncio
import os

from .decorators import async_timeout
from config import TMP_BASE_PATH, CLONE_TIMEOUT


@async_timeout(CLONE_TIMEOUT)
async def clone_repo(query: dict) -> str:
    #Clean up any existing repo 
    delete_repo(query['slug'])

    proc = await asyncio.create_subprocess_exec(
        "git",
        "clone",
        "--depth=1",
        "--single-branch",
        query['url'],
        query['local_path'],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    stdout, stderr = await proc.communicate()
def delete_repo(slug: str):
    os.system(f"rm -drf {TMP_BASE_PATH}/{slug}")
