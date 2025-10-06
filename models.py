from pydantic import BaseModel


class AddDocument(BaseModel):
    job_title:str
    job_description:str
    responsibilities:list[str]
    requirements:list[str]
    location:str
    employment_type:str


class RetrieveDocument(BaseModel):
    query:str
    top_k:int=3