# retrieve.py

import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma  # updated import

# ——— OpenAI 配置（保持不变） ———
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key, base_url="https://xiaoai.plus/v1")
EMBED_MODEL = "text-embedding-3-large"


def initialize_chroma(persist_directory: str, collection_name: str = "literature_chunks"):
    """
    初始化并返回一个 Chroma 对象，用于后续检索。
    persist_directory: Chroma 数据持久化路径
    """
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name
    )
    return db


def search(query: str,
           top_k: int,
           db: Chroma,
           relevance_threshold: float = None):  # 可选，不做硬筛选
    """
    用 Chroma 检索最相关的 chunks。
    """
    qe = db._embedding_function.embed_query(query)
    resp = db._collection.query(
        query_embeddings=[qe],
        n_results=top_k,
        include=["metadatas", "distances"]
    )
    metas_list     = resp["metadatas"][0]
    distances_list = resp["distances"][0]
    
    results = []
    for i, (meta, dist) in enumerate(zip(metas_list, distances_list)):
        cid = meta.get("chunk_id", None)
        if cid is None:
            print(f"[DEBUG] Skipping result with missing chunk_id: {meta}")
            continue
        source = meta.get("source_file", meta.get("source", "unknown"))
        results.append({
            "rank":     i + 1,
            "chunk_id": cid,
            "source":   source,
            "distance": dist
        })
    
    # 只在有结果时打印统计信息
    if distances_list:
        print(f"[DEBUG] Distance stats: min={min(distances_list):.4f}, "
              f"max={max(distances_list):.4f}, "
              f"avg={sum(distances_list)/len(distances_list):.4f}")
    else:
        print("[DEBUG] No results found within threshold")

    print(f"[DEBUG] search() returning {len(results)} results")
    return results



if __name__ == "__main__":
    # 简单测试
    CHROMA_DIR = os.path.join("data", "vectorstore", "chroma_db")
    db = initialize_chroma(CHROMA_DIR)
    hits = search(
        query="Your query here",
        top_k=5,
        db=db,
        relevance_threshold=1.0  # 调高看看更多结果
    )
    for h in hits:
        print(h)
