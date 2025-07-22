# embed.py
import os
import json
from pathlib import Path

import openai

# OpenAI 配置（保持不变）
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key, base_url="https://xiaoai.plus/v1")
embed_model = "text-embedding-3-large"

def create_or_update_embeddings(chunks_folder, persist_directory, only_files=None):
    """
    增量向量化并写入Chroma。
    - chunks_folder: 所有分块json所在目录
    - persist_directory: Chroma数据库保存路径
    - only_files: 若指定，仅处理这些stem对应的文件（无后缀）
    """
    # 修正为 langchain_community
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Chroma

    # 收集所有 chunk
    chunk_files = [
        fn for fn in os.listdir(chunks_folder)
        if fn.endswith("_chunks.json") and (only_files is None or os.path.splitext(fn)[0] in only_files)
    ]
    all_chunks = []
    for fn in chunk_files:
        with open(os.path.join(chunks_folder, fn), "r", encoding="utf-8") as f:
            all_chunks.extend(json.load(f))

    # 检查并去重 chunk_id
    seen_ids = set()
    unique_chunks = []
    duplicate_ids = set()
    for chunk in all_chunks:
        cid = chunk.get("chunk_id", "")
        if cid in seen_ids:
            duplicate_ids.add(cid)
            continue
        seen_ids.add(cid)
        unique_chunks.append(chunk)

    if duplicate_ids:
        print(f"[Embed] Skipped duplicate chunk_ids: {', '.join(duplicate_ids)}")

    embeddings = OpenAIEmbeddings(model=embed_model)
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="literature_chunks"
    )

    # 批量 upsert
    texts = [c["chunk_text"] for c in unique_chunks]
    metadatas = [c["metadata"] for c in unique_chunks]
    ids = [c["chunk_id"] for c in unique_chunks]
    if texts:
        db.add_texts(texts, metadatas=metadatas, ids=ids)
    # ...existing code...
    print(f"[Chroma] Persisted to {persist_directory}")

def generate_embedding(text, model=embed_model, api_key=None, base_url=None):
    """
    用 OpenAI API 生成一个文本的 embedding。
    返回 embedding 向量（list of float）或 None。
    """
    _api_key = api_key or os.getenv("OPENAI_API_KEY")
    _base_url = base_url or "https://xiaoai.plus/v1"
    try:
        _client = openai.OpenAI(api_key=_api_key, base_url=_base_url)
        response = _client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[generate_embedding] Error: {e}")
        return None

if __name__ == "__main__":
    BASE = Path(__file__).parent
    CHUNKS = BASE / "data" / "processed" / "chunks"
    DB_DIR = BASE / "data" / "vectorstore" / "chroma_db"
    create_or_update_embeddings(str(CHUNKS), str(DB_DIR))
