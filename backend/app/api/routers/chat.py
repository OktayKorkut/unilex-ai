from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat():
    # TODO: Faz 4'te implement edilecek — RAG agent buraya bağlanacak
    return {"message": "Chat endpoint — coming soon"}
