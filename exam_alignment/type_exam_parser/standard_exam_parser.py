from .abstract_exam_parser import AbstractExamParser
import re

import sys
import os

from exam_alignment.utils.alignment_utils import one_file_per_process
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers_in_not_start
from exam_alignment.utils.alignment_utils import longest_increasing_subsequence_index
from exam_alignment.utils.alignment_utils import find_answer_split_str
from exam_alignment.utils.alignment_utils import find_next_question_index
from exam_alignment.utils.alignment_utils import refine_answers
from exam_alignment.utils.alignment_utils import match_specific_from_end
from exam_alignment.utils.alignment_utils import remove_chinese_num_title
from exam_alignment.utils.alignment_utils import generate_answer_area_string
from exam_alignment.utils.alignment_utils import align_answers_in_questions
from exam_alignment.utils.alignment_utils import match_specific_from_start
from exam_alignment.utils.alignment_utils import type_of_judgment
from exam_alignment.utils.alignment_utils import split_question
from exam_alignment.utils.alignment_utils import find_continuous_sequence
from exam_alignment.utils.alignment_utils import count_answer_keywords

from exam_alignment.utils.alignment_utils import extract_and_combine_numbers_in_not_start_by_number
class StandardExamParser():

    def __init__(self, content):
        self.content=content
        # self.all_question=[]
        # self.all_answer=[]

    @staticmethod
    def detect_this_exam_type(content):
        '''
        检测题目是否为standard模板
        :param content: 全文
        :return: ismatch，通过答案列表与题目列表长度是否相等来判断
        '''
        print(f"【StandardExamParser开始】")


        try:
            all_question, all_answer = StandardExamParser.extract_questions_and_answers(content)
            question_count = len(all_question)
            answer_count = len(all_answer)
            print(f"question_list:'{question_count}'")
            print(f"answer_list:'{answer_count}'")
            is_match = question_count == answer_count
        except:
            print(f"【抽取题干答案报错】")
            return False

        if is_match:
            print(f"【题干答案已匹配】")
            print(f"【StandardExamParser匹配成功】")
        else:
            print(f"【题干答案不匹配】")
            print(f"【StandardExamParser匹配失败】")
        return is_match


    @staticmethod
    def extract_questions_and_answers(text):
        '''
        抽取文本中的题目与答案，如果不符合standard模板则返回空
        :param text: 全文
        :return: 题目列表，答案列表
        '''
        # 去除大写数字，如三、解答题这种标题行。
        remove_title_text = remove_chinese_num_title(text)

        lines = remove_title_text.splitlines()

        # 定义不准确的题目列表
        inaccuracy_question = []

        # 从0的位置寻找第一道题
        index = find_next_question_index(0, lines)

        while index < len(lines):
            # 寻找下一个题目的index
            next_index = find_next_question_index(index, lines)

            inaccuracy_question.append("\n".join(lines[index: next_index]))
            index = next_index

        #     print([(extract_and_combine_numbers(topic), i) for i, topic in enumerate(inaccuracy_question) if extract_and_combine_numbers(topic) is not None])
        # 通过"最长递增子序列"寻找每个精准的题目所在inaccuracy_question对应的下标
        all_question_indexs = longest_increasing_subsequence_index(inaccuracy_question)

        # 定义准确的题目列表
        all_question = []
        # index为all_question_indexs的下标，all_question_indexs[index]为inaccuracy_question的下标
        for index, question_index in enumerate(all_question_indexs):
            if index == len(all_question_indexs) - 1:
                all_question.append("\n".join(inaccuracy_question[question_index:]))
                break
            # 这一步是将题目分隔开，试卷末尾的答案被暂时分在最后一题里
            all_question.append("\n".join(inaccuracy_question[question_index:all_question_indexs[index + 1]]))

        all_question = find_continuous_sequence(all_question)

        # 判断为standard模式：找到"答案", "参考答案", "试题解析", "参考解答"所在行，并分割。
        answer_split_str = find_answer_split_str(all_question[-1])


        if isinstance(answer_split_str, str):
            print(f"split_str:\n{answer_split_str}")
            try:#如果是答案在最后一题当中，则其长度应远长于前两题之和
                if len(all_question[-1]) > len(all_question[-2]) + len(all_question[-3]):
                    all_answer_area = all_question[-1].split(answer_split_str)[1]
                    all_question[-1] = all_question[-1].split(answer_split_str)[0]
            except:
                return None, None

        else:
            return None,None


        #分割答案
        lines = all_answer_area.splitlines()

        inaccuracy_answers = []

        index = find_next_question_index(0, lines)
        while index < len(lines):
            next_index = find_next_question_index(index, lines)

            inaccuracy_answers.append("\n".join(lines[index: next_index]))
            index = next_index

        inaccuracy_answer_indexes = longest_increasing_subsequence_index(inaccuracy_answers)

        processed_inaccuracy_answers = []
        for index, answer_index in enumerate(inaccuracy_answer_indexes):
            if index == len(inaccuracy_answer_indexes) - 1:
                processed_inaccuracy_answers.append(inaccuracy_answers[answer_index])
                break
            processed_inaccuracy_answers.append(
                "\n".join(inaccuracy_answers[answer_index:inaccuracy_answer_indexes[index + 1]]))
        refine_answer = refine_answers(processed_inaccuracy_answers)[::-1]
        print(f"==题目列表编号==")
        for question in all_question:
            print(question[:10])

        print(f"==答案列表编号==")
        for answer in refine_answer:
            print(answer[:10])

        return all_question,refine_answer




    @staticmethod
    def alignment_answer(all_question, all_answer):
        questions_with_answer = []

        #  倒叙是因为，有的文件出现多个相同的题号，我们确保我们拿到的是准确的
        questions_map = {extract_and_combine_numbers_in_not_start(question): question for question in
                         reversed(all_question)}
        answer_map = {extract_and_combine_numbers_in_not_start(answer): answer for answer in reversed(all_answer)}

        for sequence_number in questions_map:
            questions_with_answer.append({
                "question": questions_map.get(sequence_number),
                "answer": answer_map.get(sequence_number, None)
            })

        return list(reversed(questions_with_answer))


    def align(self):
        """
        对齐
        """
        print(f"【对齐开始】")
        all_question, all_answer = StandardExamParser.extract_questions_and_answers(self.content)
        questions_with_answer=StandardExamParser.alignment_answer(all_question, all_answer)

        # for row in questions_with_answer:
        #     print()
        #     print(row["question"])
        #     print("-------------------------------------------------------")
        #     print(f"{row['answer']}")
        #     print()
        #     print("============================================================")

        return questions_with_answer

