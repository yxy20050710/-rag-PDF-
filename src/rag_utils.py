#rag模块
'''
         文本拆分
         转为向量
         存储到向量库
         将待翻译文本进行相似度匹配

'''
import csv
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_CACHE'] = "./huggingface_model_cache"
os.environ["CUDA_VISIBLE_DEVICES"] = "1" #强制使用cpu
print("已配置国内镜像网站")
print("√模型本地缓存路径：",os.environ["HF_ENDPOINT"])

#   初始化全局变量
#向量库 向量化embedding模型 文本分块的工具
# ？如何选择合适的工具2和3
import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter #递归式分割（首选分段策略）

#初始化 向量化模型
embeddings_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 初始化 向量库
chroma_client = chromadb.Client()
    #创建集合  若原先集合存在将其删除 之后使用get_or_create_collection方法，如果集合不存在就创建集合对象
    #create_collection 直接创建集合 get_or_create_collection集合不存在则创建
try:
    chroma_client.delete_collection(name = "translation_terms")
except:
    pass
term_collection = chroma_client.get_or_create_collection(name = "translation_terms")

#   文本分块 ？在pdf板块不是进行了分快操作吗 文本块那部分 这俩个地方不是一样的吗
'''
        拆成小块token
        按照段落 句子 字符 逐个拆
        保留原格式
'''
def split_text(pdf_content:list,chunk_size:int = 500,chunk_overlap: int =50) -> list:
    '''

    Args:
        pdf_content: 读取的pdf返回列表
        chunk_size: 每块的最大字符
        chunk_overlap: 块的重叠字符数

    Returns:分快后的列表

    '''
    # 提取纯文字
    raw_texts = [item['text'] for item in pdf_content]
    combined_text = "\n".join(raw_texts) #将文字拼接起来

    #初始化分块器（langchain 网上搜索直接获取）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap,
        # 拆分优先级：先段落→换行→中文标点→英文标点
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"]

    )

    #进行分块
    text_chunks = text_splitter.split_text(combined_text)
    chunked_content = [] #存分块+格式

    # 匹配原格式
    for chunk in text_chunks:
        for item in pdf_content:
            if chunk in item['text']:
                chunked_content.append({
                    'text_chunk': item['text'],
                    'format': item['format'],
                })
                break  # ？没看懂这部分式是怎么工作运行的 逻辑 怎么理解

    print(f"【成功】拆成{len(chunked_content)}个块")
    return chunked_content

#读取csv
def load_terms_csv(csv_path):
    '''

    Args:
        csv_path: csv术语库

    Returns:包含所有语言的术语库

    '''
    terms =[]
    with open(csv_path,"r",encoding = "utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader: #提取字段
            tw = row.get("tw","").strip()
            ch = row.get("ch","").strip()
            en = row.get("en","").strip()

            #过滤无效数据
            valid_count = 0
            if tw:valid_count += 1
            if ch:valid_count += 1
            if en:valid_count += 1
            if valid_count <2:
                continue

            #组装词典
            term_dict ={
                "tw":tw,
                "ch":ch,
                "en":en,
                "filed":"刑事检控科"
            }
            terms.append(term_dict)
    print(f"【csv读取成功】共加载{len(terms)}条有效术语")
    return terms

# 构建术语库
"""
        读取csv
        格式化
        确定的唯一id
        向量化 入库
"""
def build_term_database(csv_path):

    #读取csv
    term_list = load_terms_csv(csv_path)
    if not term_list:
        print("[错误]无有效术语")
        return

    #格式化
    formatted_terms=[]
    for term in term_list:
        format_base = f"""
简体术语：{term["ch"] or '无'}
繁体术语：{term["tw"] or '无'}
英文术语：{term["en"] or '无'}
应用领域：{term['filed']}
"""
        formatted_terms.append(format_base)

    #向量化 入库
    term_embeddings = embeddings_model.encode(formatted_terms)
    term_ids = [f"term_{i} " for i in range(len(formatted_terms))]

    term_collection.add(
        documents = formatted_terms,
        ids = term_ids,
        embeddings = term_embeddings.tolist() #?
    )
    print(f"【术语库构建完成】共入库{len(formatted_terms)}条")

#检索函数 相似度计算
"""
        将待翻译文本转成向量
        在向量库中进行相似度比较 找top-k前3术语
        返回术语列表
"""
def retrieve_similar_terms(text_chunk:str,top_k:int = 3) -> list:
    chunk_embedding = embeddings_model.encode([text_chunk])
    try:
        results=term_collection.query(
            query_embeddings = chunk_embedding.tolist(),
            n_results = top_k
        )
        similar_terms = results['documents'][0] if results['documents'] else []
        print(f"【检索成功】找到{len(similar_terms)}条相似术语")
        return similar_terms
    except Exception as e:
        print(f"【错误】{e}")
        return []


if __name__ == "__main__":
    # 你的CSV路径
    csv_path = "../document/刑事检控科.csv"
    # 构建多语言术语库
    build_term_database(csv_path)

    # 测试检索（简体/繁体/英文都能检索）
    test_ch = "协从一方"  # 简体
    test_tw = "協從一方"  # 繁体
    test_en = "secondary party"  # 英文

    print("\n【检索简体】")
    retrieve_similar_terms(test_ch)

    print("\n【检索繁体】")
    retrieve_similar_terms(test_tw)

    print("\n【检索英文】")
    retrieve_similar_terms(test_en)