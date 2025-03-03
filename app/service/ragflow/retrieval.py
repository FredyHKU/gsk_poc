from service.ragflow.rag.utils.es_conn import ESConnection
from service.ragflow.rag.utils.doc_store_conn import MatchExpr, OrderByExpr, MatchTextExpr, MatchDenseExpr, FusionExpr
from openai import OpenAI

es_connection = ESConnection()

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


def search_documents(
    question: str,
    indexNames: str,
    # knowledgebaseIds: list,
    selectFields: list = ["content_ltks", "title_tks"],
    highlightFields: list = ["content_ltks"],
    condition: dict = {"available_int": 1},
    offset: int = 0,
    limit: int = 10,
    aggFields: list = ["content_with_weight.keyword"],
    rank_feature: dict = {"pagerank": 10},
    topn: int = 10,
    text_match_weight: float = 0.3,
    dense_match_weight: float = 0.7,
    similarity_threshold: float = 0.5,
    minimum_should_match: float = 0.3
):
    """
    封装搜索文档的逻辑。

    :param question: 用户问题
    :param indexNames: 索引名称
    :param knowledgebaseIds: 知识库 ID 列表
    :param selectFields: 查询字段列表
    :param highlightFields: 高亮字段列表
    :param condition: 查询条件
    :param offset: 分页偏移量
    :param limit: 每页大小
    :param aggFields: 聚合字段列表
    :param rank_feature: 排序特征
    :param topn: 返回结果数量
    :param text_match_weight: 文本匹配权重
    :param dense_match_weight: 向量匹配权重
    :param similarity_threshold: 向量相似度阈值
    :param minimum_should_match: 文本匹配最小匹配度
    :return: 搜索结果
    """
    # 生成问题向量
    question_vector = generate_embedding(question)

    # 定义匹配表达式
    matchExprs = [
        MatchTextExpr(
            fields=["content_ltks"],
            matching_text=question,
            topn=topn,
            extra_options={"minimum_should_match": minimum_should_match}
        ),
        MatchDenseExpr(
            vector_column_name="q_1024_vec",
            embedding_data_type="float",
            distance_type="cosine",
            topn=topn,
            embedding_data=question_vector,
            extra_options={"similarity": similarity_threshold}
        ),
        FusionExpr(
            method="weighted_sum",
            topn=topn,
            fusion_params={"weights": f"{text_match_weight}, {dense_match_weight}"}
        )
    ]

    # 定义排序规则
    order_by_expr = OrderByExpr()
    order_by_expr.asc("create_timestamp_flt")  # 按创建时间升序
    order_by_expr.desc("pagerank.keyword")     # 按 PageRank 降序

    # 执行搜索
    results = es_connection.search(
        selectFields=selectFields,
        highlightFields=highlightFields,
        condition=condition,
        matchExprs=matchExprs,
        orderBy=order_by_expr,
        offset=offset,
        limit=limit,
        indexNames=indexNames,
        knowledgebaseIds=[" "],
        aggFields=aggFields,
        rank_feature=rank_feature
    )

    return results