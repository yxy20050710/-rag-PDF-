# llm翻译模块
'''
    加载千问api
    构建提示词工程prompt
    调用千问翻译

    接收模块1的pdf文件
    调用模块2的术语库
    调用llm进行翻译
    返回翻译格式 模块1生成pdf
'''
import os
import json
from dotenv import load_dotenv
import dashscope # 千问官方sdk
from dashscope import Generation #文本生成接口
from .rag_utils import retrieve_similar_terms #导入模块2的检索模块  #使用相对导入 解决检索不到的情况

# 加载千问api 利用dotenv加载env文件
load_dotenv() #加载env文件
API_Key = os.getenv("DASHSCOPE_API_KEY")
#配置全局apikey
dashscope.api_key = API_Key

# 检查密钥是否存在
def init_llm_check():
    if not dashscope.api_key or dashscope.api_key.strip() == "":
        print("【llm初始化错误】未检测到api，请检查env文件")
        return False
    else:
        print("[llm初始化成功】密钥加载完成")
        return True

#构建prompt +调用千问
def translate_single_text(text:str,rag_terms:list,source_lang,target_lang):
    """

    Args:
        text: 待翻译文本
        rag_terms: rag检索术语
        source_lang: 源语言
        target_lang: 目标语言

    Returns:翻译结果

    """
    # 若文本为空 直接返回
    if not text or text.strip() == "":
        return ""

    # 将检索到的rag拼成字符串
    term_str = "\n".join(rag_terms) if rag_terms else "无术语参考"

    #构建prompt
    prompt=f"""
你是香港刑事检控科专业法律翻译专员，严格遵守以下规则：
1. 翻译方向：{source_lang} → {target_lang}
2. 法律术语必须严格使用下面的参考术语，不得随意修改
3. 翻译保持法律文书正式、严谨、流畅
4. 不添加任何解释、备注、符号、格式标签
5. 只输出纯翻译结果，不要多余内容
6. 句子完整，不删减原文含义
7. 必须将所有文字都进行翻译

---------------------
专业术语参考：
{term_str}
---------------------

待翻译文本：
{text}
"""
    # 调用千问api
    try:
        response = Generation.call(
            model="qwen-turbo",
            messages=[  # 关键：message → messages
                {"role": "user", "content": prompt}
            ],
            temperature = 0.1,
            result_format = "message",
            max_tokens = 2048
        )

        if response.status_code == 200:
            result = response.output.choices[0].message.content.strip()
            print(f"【翻译成功】{source_lang}->{target_lang}: {text[:25]}……")
            return result
        else:
            print(f"【翻译失败】")
            return text

    except Exception as e:
        print(f"【翻译异常】{e}")
        return text


# 批量翻译整个pdf

def batch_translate_pdf(pdf_content_list,source_lang,target_lang):
    """

    Args:
        pdf_content_list: 模块1 read——pdf返回的列表
        source_lang: 源语言
        target_lang: 目标语言

    Returns:犯戒结果

    """
    if not init_llm_check(): #检查llm是否初始化成功
        return []

    if not pdf_content_list:
        print(f"批量翻译内容为空")
        return []

    translated_result=[]
    total = len(pdf_content_list)

    print(f"\n【开始批量翻译】共 {total} 段文本，{source_lang} → {target_lang}")

    #遍历每段
    for idx,chunk in enumerate(pdf_content_list,1):
        original_text = chunk["text"].strip()
        format_info = chunk['format_info']


        print(f"\n--- 第 {idx}/{total} 段 ---")

        #检索相似术语
        similar_terms = retrieve_similar_terms(original_text)

        #翻译
        translated_text = translate_single_text(
            text = original_text,
            rag_terms = similar_terms,
            source_lang = source_lang,
            target_lang = target_lang
        )

        #组装未模块1的格式
        translated_result.append({
            "translated_text": translated_text,
            "format_info": format_info,
        })

        print(f"\n【批量翻译完成】总计翻译 {len(translated_result)} 段")
    return translated_result








# ===================== 模块3 步骤4：独立测试代码（必写！） =====================
if __name__ == "__main__":

    # 先初始化检查
    init_llm_check()

    # 测试1：单句翻译（模拟法律文本）
    test_text = "协从一方应当按照其犯罪情节承担相应的刑事责任。"
    test_terms = [
        "法律术语：协从一方，英文：secondary party，领域：刑事检控",
        "法律术语：刑事责任，英文：criminal responsibility，领域：法律"
    ]

    res = translate_single_text(
        text=test_text,
        rag_terms=test_terms,
        source_lang="简体中文",
        target_lang="英文"
    )
    print("\n===== 单句测试翻译结果 =====")
    print("原文：", test_text)
    print("译文：", res)

    # 测试2：繁体→英文
    test_tw = "協從一方應當按照其犯罪情節承擔相應的刑事責任。"
    res2 = translate_single_text(test_tw, test_terms, "繁体中文", "英文")
    print("\n繁体测试：")
    print("译文：", res2)
