
from fastapi import HTTPException, APIRouter
from fastapi.responses import Response


router = APIRouter()


@router.get("/download/{ingest_id}")
async def download_ingest(ingest_id: str):
    try:
        with open(f"../tmp/ingest-{ingest_id}.txt", "r") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=gitingest-{ingest_id[:8]}.txt"
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Digest not found")