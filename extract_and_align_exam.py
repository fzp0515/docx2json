import argparse
import json
import os
import glob
from pathlib import Path
import re
import matplotlib.pyplot as plt
import zipfile
import base64
import pandas as pd
import os
import time

from exam_alignment.exam_parser_container import ExamParserContainer
from exam_alignment.utils.alignment_utils import one_file_per_process
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers_in_not_start
from exam_alignment.utils.alignment_utils import one_file_per_process
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers_in_not_start
from exam_alignment.utils.alignment_utils import longest_increasing_subsequence_index
from exam_alignment.utils.alignment_utils import find_answer_split_str
from exam_alignment.utils.alignment_utils import find_next_question_index
from exam_alignment.utils.alignment_utils import refine_answers
from exam_alignment.utils.alignment_utils import match_specific_from_end
from exam_alignment.utils.alignment_utils import remove_chinese_num_title
from exam_alignment.utils.alignment_utils import remove_chinese_num_title
from exam_alignment.utils.alignment_utils import align_answers_in_questions
from exam_alignment.utils.alignment_utils import match_specific_from_start
from exam_alignment.utils.alignment_utils import type_of_judgment
from exam_alignment.utils.alignment_utils import split_question
from exam_alignment.utils.alignment_utils import find_continuous_sequence
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers_in_not_start_by_number
from exam_alignment.utils.alignment_utils import count_answer_keywords
import shutil


def convert_image_to_binary(image_path):
    '''
    图片转二进制
    :param image_path:
    :return:
    '''
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def find_recode_images_in_docx(docx_path):
    '''
    通过路径与文件名找到同名docx，并解压，找到其中的图片路径，返回字典
    :param docx_path: 文件路径
    :return: 图片字典，key是图片名，value是二进制
    '''
    image_base64_dic = {}

    #防止有md没docx
    if not os.path.exists(docx_path):
        print("找不到" + docx_path)
        return image_base64_dic

    # Unzip the docx file
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        # Extract to a temporary directory

        directory, file_name = os.path.split(docx_path)
        base_name, _ = os.path.splitext(file_name)

        # Create new directory path
        extract_path = os.path.join(directory, base_name)
        zip_ref.extractall(extract_path)



    media_folder_path = os.path.join(extract_path, 'word', 'media')
    if not os.path.exists(media_folder_path):
        print(file_name+"没有图片")
        return image_base64_dic

    for root, dirs, files in os.walk(media_folder_path):
        for file in files:
            image_path=os.path.join(media_folder_path,file)
            image_base64_dic[file]=convert_image_to_binary(image_path)

    return image_base64_dic







def process(md_text: str, file_local: Path, output_local: Path,not_rec_files: list, fail_files: list,handle_pic):
    '''
    处理md全文，包括模板匹配，分割与对齐，然后写入json文档
    :param md_text: 待处理全文
    :param file_local: 写入文件夹路径
    :param output_local: 输出文件夹地址
    :param not_rec_files: 无法识别文件名列表
    :param fail_files: 对齐失败文件名列表
    :param handle_pic: 是否处理图片
    :return:
    '''
    print(f"=====开始处理 '{file_local.name}' ======")

    #分离图片和文本，防止切割题目连黏
    regex_pattern = r"!\[\]\(media/(.+?)\)"
    modified_text = re.sub(regex_pattern, r"![](media/\1)\n", md_text)


    examParserContainer = ExamParserContainer(modified_text)
    exam_parser = examParserContainer.get_exam_parser()

    if not exam_parser:
        print(f"'{file_local.name}'已加入not文件夹")
        not_rec_files.append(file_local)
        return

    try:
        align_qustion = exam_parser.align()

    except:
        print(f"exam_parser.align()报错")
        print(f"'{file_local.name}' 已加入align fail文件夹")
        fail_files.append(file_local)
        return

    if not align_qustion:
        print(f"align_qustion为空")
        print(f"'{file_local.name}' 已加入align fail文件夹")
        fail_files.append(file_local)
        return

    #仅处理
    if handle_pic:

        # 得到docx文件下图片转成base64的字典
        try:
            docx_file_path = os.path.join(os.path.dirname(file_local),file_local.name.replace(".md", ".docx"))
            images_base64_dic = find_recode_images_in_docx(docx_file_path)
        except:
            print("【图片解析错误】")


    for qustion_with_answer in align_qustion:
        #得到问答对的字符串
        concatenated_string = ''.join([str(value) for value in qustion_with_answer.values()])
        #抽取字符串里的图片名字
        pic_file=extract_image_filenames(concatenated_string)
        pic_count=len(pic_file)
        if pic_count and not handle_pic:
            continue

        image_base64_forsingle_dic = {}
        if handle_pic and pic_count:
            #单个试题里包含的图片二进制存成字典
            try:
                if pic_count!=0:
                    for file in pic_file:
                        image_base64_forsingle_dic[file]=images_base64_dic[file]
            except:
                print("【图片对齐有问题】")

        #增加试卷detail data
        qustion_with_answer["detail_data"]={

            "origin":str(file_local.name),#出处
            "pic_count":pic_count,#图片数量
            "images":image_base64_forsingle_dic#图片二进制字典
        }


        with open(output_local, "a",encoding='utf-8') as ff:

            ff.write(json.dumps(qustion_with_answer, ensure_ascii=False) + '\n')


def extract_image_filenames(text):
    '''
    匹配文本中的图片插入位置
    :param text: 待匹配文本
    :return: matchs组，包含图片名
    '''
    # 定义正则表达式
    regex_pattern = r"!\[\]\(media/(.+?)\)"

    # 使用findall函数查找所有匹配项
    matches = re.findall(regex_pattern, text)
    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', type=str, help="输入目录, 包含md文档的文件夹")
    parser.add_argument('output_file', type=str,  help="输出文件, jsonl格式")
    parser.add_argument('notRec_dir', type=str,  help="无法识别模式的文档所在的文件夹")
    parser.add_argument('fail_dir', type=str, help="无法对齐的文档所在的文件夹")
    parser.add_argument('--handle_pic', action='store_true', help='是否仅处理不带图片的题目')
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_local = Path(args.output_file)
    notRec_path = Path(args.notRec_dir)
    fail_path = Path(args.fail_dir)
    handle_pic=args.handle_pic


    not_rec_files = []
    fail_files = []
    file_count=0
    for file in input_path.glob("**/*.md"):
        file_count+=1
        with open(file, "r", encoding="utf-8") as f:
            md_text = one_file_per_process(f.read())
            process(md_text, file, output_local,not_rec_files, fail_files,handle_pic)


    # 移动无法识别的文件
    for file in not_rec_files:
        shutil.move(str(file), str(notRec_path / file.name))
        docx_file_path = os.path.join(os.path.dirname(file),file.name.replace(".md", ".docx"))
        try:
            shutil.move(str(docx_file_path), str(notRec_path / file.name.replace(".md", ".docx")))
        except:
            print("找不到"+file.name.replace(".md", ".docx"))

    # 移动对齐失败的文件
    for file in fail_files:
        shutil.move(str(file), str(fail_path / file.name))
        docx_file_path = os.path.join(os.path.dirname(file), file.name.replace(".md", ".docx"))
        try:
            shutil.move(str(docx_file_path), str(fail_path / file.name.replace(".md", ".docx")))
        except:
            print("找不到"+file.name.replace(".md", ".docx"))


    #绘制柱状图分析图象
    # 数据
    categories = ['align fail', 'not rec', 'correct']
    values = [len(fail_files), len(not_rec_files),file_count-len(fail_files)-len(not_rec_files)]

    # 创建柱状图
    plt.bar(categories, values)

    # 添加标题和轴标签
    plt.title('analysis of batch')
    plt.xlabel('type')
    plt.ylabel('num')

    # 显示图表
    plt.show()

