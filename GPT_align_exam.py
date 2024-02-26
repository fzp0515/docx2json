
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
import itertools
import time
import logging as log
from exam_alignment.exam_parser_container import ExamParserContainer
from exam_alignment.utils.alignment_utils import one_file_per_process
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers
from exam_alignment.utils.alignment_utils import find_recode_images_in_docx
from exam_alignment.utils.alignment_utils import one_file_per_process
from exam_alignment.utils.alignment_utils import extract_image_filenames
from exam_alignment.utils.alignment_utils import remove_uncompleted_json_data
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
from exam_alignment.utils.alignment_utils import remove_gpt_json_format
from GPTAlignment.GPTAlignment import gpt_alignment_process
import shutil
log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s (%(funcName)s:%(lineno)d) - %(message)s')
SINGLE_QUESTION_JSON_FORMAT={
    "is_quality_control": False,
    "question": {
      "problem": "",
      "ground_truth_solution": "",
      "ground_truth_answer": ""
    },
    "metaData": {
      "origin": "",
      "align_method": 0
    },
    "attachment": {
      "pic_count": 0,
      "images": {}
    }
  }

def store_data(align_qustion,file_local,output_local,completed_falg):
    # if handle_pic:
    #     # 得到docx文件里图片转成base64的字典
    #     try:
    #         docx_file_path = os.path.join(os.path.dirname(file_local), file_local.name.replace(".md", ".docx"))
    #         images_base64_dic = find_recode_images_in_docx(docx_file_path)
    #     except:
    #         log.error("无法在docx找到对应图片")


    with open(output_local, "a", encoding='utf-8') as ff:
        for qustion_with_answer in align_qustion:
        #     # 得到问答对的字符串
        #     concatenated_string = ''.join([str(value) for value in qustion_with_answer])
        #
        #     # 抽取字符串里的图片名字
        #     pic_file = extract_image_filenames(concatenated_string)
        #     pic_count = len(pic_file)
        #     if pic_count and not handle_pic:
        #         continue
        #
        #     image_base64_forsingle_dic = {}
        #     if handle_pic and pic_count:
        #         # 单个试题里包含的图片二进制存成字典
        #         try:
        #             if pic_count != 0:
        #                 for file in pic_file:
        #                     image_base64_forsingle_dic[file] = images_base64_dic[file]
        #         except:
        #             log.error("docx图片与md图片无法对齐")

            # 填充入库数据
            single_question = SINGLE_QUESTION_JSON_FORMAT
            try:
                single_question["question"]["problem"] = qustion_with_answer["problem"]
                single_question["question"]["options"] = qustion_with_answer["options"]
                single_question["question"]["ground_truth_answer"] = qustion_with_answer["ground_truth_answer"]
                single_question["question"]["ground_truth_solution"] = qustion_with_answer["ground_truth_solution"]
            except:
                log.error("gpt抽取文本入库时报错")

            single_question["metaData"]["origin"] = str(file_local.name)
            if completed_falg:
                single_question["metaData"]["align_method"] = 1  # 0代表规则匹配 ，1代表GPT生成全部，2代表gpt因窗口长度没有生成全部
            else:
                single_question["metaData"]["align_method"] = 2

            try:
                single_question["attachment"]["pic_count"] = 0#pic_count
                single_question["attachment"]["images"] = {}#image_base64_forsingle_dic
            except:
                log.error("gpt抽取文本识别图片时报错")
            ff.write(json.dumps(single_question, ensure_ascii=False) + '\n')


def process_by_GPT(md_text: str, file_local: Path, output_local: Path,key):
    log.info("开始用GPT处理：" + file_local.name)
    # 分离图片和文本，防止切割题目连黏
    regex_pattern = r"!\[\]\(media/(.+?)\)"
    add_enter_text = re.sub(regex_pattern, r"![](media/\1)\n", md_text)

    # 去除"，防止json.loads转义编码报错
    text_without_quotes = add_enter_text.replace('"', '')

    json_str=remove_gpt_json_format(gpt_alignment_process(text_without_quotes,key))

    if "报错" in json_str:
        return False

    #判断gpt有没有生成全部数据
    completed_flag=False

    if json_str.endswith('}\n]') or json_str.endswith('}]'):
        completed_flag=True

    else:
        json_str=remove_uncompleted_json_data(json_str)

    try:
        align_question=json.loads(json_str)

    except:
        print(json_str)
        log.error("GPT抽取json数据的格式有误")
        return False

    store_data(align_question, file_local, output_local, completed_flag)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', type=str, help="GPT成功识别的文档转至input文件夹")
    parser.add_argument('output_file', type=str,  help="输出文件, jsonl格式")
    parser.add_argument('notRec_dir', type=str,  help="无法识别模式的文档所在的文件夹")
    parser.add_argument('fail_dir', type=str, help="无法对齐的文档所在的文件夹")
    parser.add_argument('key', type=str, help='gpt api key')
    args = parser.parse_args()

    output_local = Path(args.output_file)
    notRec_path = Path(args.notRec_dir)
    fail_path = Path(args.fail_dir)
    success_path=Path(args.input_dir)
    KEY=args.key


    GPT_align_success_file = []

    for file_path in notRec_path.glob("**/*.md"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_text = one_file_per_process(f.read())
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在。")
        is_gpt_success = process_by_GPT(md_text, file_path, output_local, KEY)
        if is_gpt_success:
            GPT_align_success_file.append(file_path)
            shutil.move(str(file_path), str(success_path / file_path.name))
            docx_file_path = os.path.join(os.path.dirname(file_path), file_path.name.replace(".md", ".docx"))
            try:
                shutil.move(str(docx_file_path), str(success_path / file_path.name.replace(".md", ".docx")))
            except:
                print("找不到" + file_path.name.replace(".md", ".docx"))


    for file_path in fail_path.glob("**/*.md"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_text = one_file_per_process(f.read())
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在。")
        is_gpt_success = process_by_GPT(md_text, file_path, output_local, KEY)
        if is_gpt_success:
            GPT_align_success_file.append(file_path)
            shutil.move(str(file_path), str(success_path / file_path.name))
            docx_file_path = os.path.join(os.path.dirname(file_path), file_path.name.replace(".md", ".docx"))
            try:
                shutil.move(str(docx_file_path), str(success_path / file_path.name.replace(".md", ".docx")))
            except:
                print("找不到" + file_path.name.replace(".md", ".docx"))


