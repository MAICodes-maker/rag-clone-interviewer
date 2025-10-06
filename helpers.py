import os
import logging
from langchain_groq import ChatGroq
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain.vectorstores import FAISS
from fastapi import HTTPException

INDEX_NAME="vector_index"
client=MongoClient("mongodb://localhost:63931/?directConnection=true")
embeddings_collection=client["rag_interviewer_db"]["embeddings"]
FILTER_FIELDS=["job_title","is_active","job_description"]

def add_data(documents:Document,embeddings,collection_name:str):
    vector_store=MongoDBAtlasVectorSearch(
        collection=embeddings_collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    existing_indexes = embeddings_collection.index_information()

    vector_store.add_documents(documents)
    logging.info(f"Search Indexes: {existing_indexes}")
    if not existing_indexes:
        try:
            add_search_index(embeddings_collection, embeddings)
        except Exception as e:
            logging.error(f"Error creating search index: {e}")
            raise HTTPException(
                status_code=500, detail="Error occurred while creating a search index."
            )


# Function to add a search index
def add_search_index(collection, embedding_model):
    try:
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embedding_model,
            index_name=INDEX_NAME,
        )
        result = vector_store.create_vector_search_index(
            dimensions=int(os.getenv("NO_OF_DIM")),
            filters=FILTER_FIELDS,
        )
        logging.info(f"Search index created: {result}")
    except Exception as e:
        logging.error(f"Error in adding search index: {e}")
        raise HTTPException(
            status_code=500, detail="Error in creating vector search index."
        )
    
def search_intances(collection,embedding_model):
    try:
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embedding_model,
            index_name=INDEX_NAME,
        )
        return vector_store
    except Exception as e:
        logging.error(f"Error in initializing search instances: {e}")
        raise HTTPException(
            status_code=500, detail="Error in initializing search instances."
        )

def initialize_embeddings():
    return HuggingFaceEmbeddings(
    model_name = "sentence-transformers/all-MiniLM-L6-v2" #initializing the model name
    )


def create_documents(data):
    try:
        document=Document(
            page_content=data.job_description,
            metadata={
            "job_title":data.job_title,
            "responsibilities":data.responsibilities,
            "requirements":data.requirements,
            "location":data.location,
            "employment_type":data.employment_type,
            "is_active":True }
        )
        
        # Load existing FAISS index if available
        if os.path.exists("faiss_index"):
            vector_store = FAISS.load_local("faiss_index", initialize_embeddings(), allow_dangerous_deserialization=True)
            vector_store.add_documents([document])
        else:
            vector_store = FAISS.from_documents([document], initialize_embeddings())
        
        vector_store.save_local("faiss_index")

        # add_data(documents=document,embeddings=initialize_embeddings(),collection_name="embeddings")
        return {
                "message": "Data has been added to the database."
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in adding data {str(e)}")
    
def retrieve_documents(query:str,top_k:int):
    try:
        # vector_store=search_intances(
        #     collection=embeddings_collection,
        #     embedding_model=initialize_embeddings()
        # )

        # filter_condition={
        #     "is_active":True
        # }
        # retriever=vector_store.as_retriever(
        #     search_kwargs={"k":1,"pre_filter":filter_condition}
        # )

        # print("sources=",retriever.invoke(query))
        embeddings = initialize_embeddings()
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
        sources = retriever.invoke(query)
        llm=ChatGroq(
            model="deepseek-r1-distill-llama-70b",
        )

        prompt=f"""You are an AI interviewer.  
        You will generate  6 interview questions based on the following:  

        Job Description:
        {sources}

        RULES:
        - Ask clear, concise, role-specific questions.  
        - Mix technical, behavioral, and cultural fit questions.  
        - Do not invent details outside the provided context.  
        """

        ai_msg = llm.invoke(prompt)
        return ai_msg.content
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in retrieving data {str(e)}")


