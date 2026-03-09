# main.py：命令行交互式选择翻译方向（输入数字1/2/3...）
import os
import sys

# 把src目录加入路径，确保能导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块（完全不动）
from src.pdf_work2 import pdf_2_docx, process_docx,split_text_to_chunks,write_translation_docx
from src.rag_utils import build_term_database
from src.llm_utils import batch_translate_pdf

# ===================== 配置路径（和之前一致） =====================
CSV_PATH = "./document/刑事检控科.csv"
PDF_PATH = "./document/Criminal Case Report.pdf"
TEMP_DOCX = "./test/pdf_2_word.docx"
OUTPUT_PATH = "./test/翻译结果.docx"

# ===================== 核心：数字选择翻译方向 =====================
def choose_translation_direction():
    """
    命令行交互式选择翻译方向：输入数字即可
    1 = 简体→英文
    2 = 简体→繁体
    3 = 繁体→英文
    4 = 繁体→简体
    5 = 英文→简体
    6 = 英文→繁体
    """
    # 打印选择菜单
    print("="*50)
    print("        法律PDF多语言翻译工具")
    print("="*50)
    print("请选择翻译方向（输入数字1-6）：")
    print("1 → 简体中文 → 英文")
    print("2 → 简体中文 → 繁体中文")
    print("3 → 繁体中文 → 英文")
    print("4 → 繁体中文 → 简体中文")
    print("5 → 英文 → 简体中文")
    print("6 → 英文 → 繁体中文")
    print("="*50)

    # 循环接收输入，直到选对为止
    while True:
        try:
            choice = input("请输入数字（1-6）：").strip()
            # 匹配数字和对应的语言
            if choice == "1":
                return "简体中文", "英文"
            elif choice == "2":
                return "简体中文", "繁体中文"
            elif choice == "3":
                return "繁体中文", "英文"
            elif choice == "4":
                return "繁体中文", "简体中文"
            elif choice == "5":
                return "英文", "简体中文"
            elif choice == "6":
                return "英文", "繁体中文"
            else:
                print("❌ 输入错误！请输入1-6之间的数字")
        except:
            print("❌ 输入异常！请输入数字（比如1、2）")

# ===================== 全流程执行（核心代码完全不动） =====================
if __name__ == "__main__":
    # 步骤1：选择翻译方向
    source_lang, target_lang = choose_translation_direction()
    print(f"\n✅ 已选择翻译方向：{source_lang} → {target_lang}")

    # 步骤2：构建RAG术语库（模块2，完全不动）
    print("\n===== 步骤1：构建RAG法律术语库（模块2） =====")
    build_term_database(CSV_PATH)

    # 步骤3：读取pdf 并转为doc 进行分块（模块1）
    print("\n===== 步骤2：pdf读取转换板块 =====")
    docx_path = pdf_2_docx(PDF_PATH,TEMP_DOCX)
    if not docx_path:
        print("❌ pdf转换失败，程序退出")
        sys.exit(1)

    clean_paras = process_docx(docx_path)
    if not clean_paras:
        print("❌ Word处理失败，终止流程")
        exit(1)

    translation_chunks = split_text_to_chunks(clean_paras)
    if not translation_chunks:
        print("❌ 分块失败，终止流程")
        exit(1)

    # 步骤4：批量翻译（模块3，完全不动）
    print("\n===== 步骤3：批量翻译（模块3） =====")
    print("开始翻译……")
    
    # 将整个translation_chunks列表传递给batch_translate_pdf函数
    translated_content = batch_translate_pdf(
        pdf_content_list=translation_chunks,
        source_lang=source_lang,
        target_lang=target_lang
    )
    
    if not translated_content:
        print("❌ 翻译失败，程序退出")
        sys.exit(1)
    
    # 处理翻译结果
    translated_chunks = []
    for idx, item in enumerate(translated_content):
        translated_chunks.append({
            "text": item["translated_text"],
            "format_info": item["format_info"]
        })

    # 步骤5：生成翻译后的PDF（模块1，完全不动）
    print("\n===== 步骤4：生成翻译后的docx（模块1） =====")
    write_translation_docx(translated_chunks, OUTPUT_PATH)

    # 完成提示
    print(f"\n🎉 全部完成！")
    print(f"📄 翻译后的docx路径：{os.path.abspath(OUTPUT_PATH)}")