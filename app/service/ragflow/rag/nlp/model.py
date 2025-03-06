from openai import OpenAI
from llama_index.core.data_structs import Node
from llama_index.core.schema import NodeWithScore
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank
import numpy as np

import os
os.environ["DASHSCOPE_API_KEY"] = "sk-f25b431f918a4796b65b1ae4a2c3ce56"

def rerank_similarity(query, texts):
    # 创建节点列表
    nodes = [NodeWithScore(node=Node(text=text), score=1.0) for text in texts]

    # 初始化 DashScopeRerank
    dashscope_rerank = DashScopeRerank(top_n=len(texts))

    # 执行重排序
    results = dashscope_rerank.postprocess_nodes(nodes, query_str=query)

    # 提取分数
    scores = [res.score for res in results]
    scores = np.array(scores)

    # 返回分数和一个占位符
    return scores, None




def generate_embedding(text: str, api_key: str = None, base_url: str = None, model_name: str = "text-embedding-v3", dimensions: int = 1024, encoding_format: str = "float"):
    api_key = "sk-f25b431f918a4796b65b1ae4a2c3ce56"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"    

    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 调用 OpenAI 的嵌入接口
    try:
        completion = client.embeddings.create(
            model=model_name,
            input=text,
            dimensions=dimensions,
            encoding_format=encoding_format
        )
        embedding = completion.data[0].embedding
        return embedding
    except Exception as e:
        print(f"OpenAI API 请求失败: {e}")
        return None


# 示例调用
if __name__ == "__main__":
    # 示例用法
    query = "你好"
    ins_tw = [["啦啦啦"], ["哈喽"], ["你好吗"]]  # 假设 ins_tw 是一个包含文本列表的列表
    
    # 假设 rmSpace 是一个函数，用于处理文本
    def rmSpace(text):
        return text.strip()
    
    # 使用 similarity 函数
    vtsim, _ = rerank_similarity(query, [rmSpace(" ".join(tks)) for tks in ins_tw])
    
    print("重排序后的分数:", vtsim)