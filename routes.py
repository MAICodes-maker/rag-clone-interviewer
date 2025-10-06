from fastapi import APIRouter

from models import AddDocument,RetrieveDocument
from helpers import create_documents,retrieve_documents


job_router = APIRouter(prefix="/job")


@job_router.post("/add")
async def add_job_document(document: AddDocument):
    return create_documents(document)


@job_router.post("/retrieve")
async def retrieve_job_document(query: RetrieveDocument):
    return retrieve_documents(query=query.query, top_k=query.top_k)