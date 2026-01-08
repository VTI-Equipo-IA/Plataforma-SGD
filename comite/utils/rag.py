import os
from typing import Callable, List
from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

def _load_texts_from_pdfs(folder: str) -> List[tuple]:
    texts, metas = [], []
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname.lower().endswith(".pdf"):
            reader = PdfReader(path)
            for i, page in enumerate(reader.pages):
                content = page.extract_text() or ""
                if content.strip():
                    texts.append(content)
                    metas.append({"fuente": fname, "pagina": i + 1})
        elif fname.lower().endswith((".txt", ".md")):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if content.strip():
                    texts.append(content)
                    metas.append({"fuente": fname, "pagina": 1})
    return texts, metas

def build_index(docs_folder: str, index_folder: str, emb_model: str):
    texts, metas = _load_texts_from_pdfs(docs_folder)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.create_documents(texts, metas)
    embeddings = OpenAIEmbeddings(model=emb_model)
    vs = FAISS.from_documents(docs, embeddings)
    os.makedirs(index_folder, exist_ok=True)
    vs.save_local(index_folder)
    return index_folder

def load_retriever(index_folder: str, emb_model: str, k: int) -> Callable[[str], str]:
    embeddings = OpenAIEmbeddings(model=emb_model)
    vs = FAISS.load_local(index_folder, embeddings, allow_dangerous_deserialization=True)
    def retrieve(query: str) -> str:
        docs = vs.similarity_search(query, k=k)
        parts = []
        for d in docs:
            src = d.metadata.get("fuente", "?")
            pg = d.metadata.get("pagina", "?")
            parts.append(f"[{src} p.{pg}] {d.page_content}")
        return "\n\n".join(parts)
    return retrieve
