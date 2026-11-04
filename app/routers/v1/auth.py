from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter()
@router.get("/auth")
async def read_root():
    return {"Hello": "World"}