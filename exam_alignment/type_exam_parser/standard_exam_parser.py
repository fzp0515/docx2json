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
from exam_alignment.utils.alignment_utils import answer_area_str_process
from exam_alignment.utils.alignment_utils import generate_answer_area_string
from exam_alignment.utils.alignment_utils import align_answers_in_questions
from exam_alignment.utils.alignment_utils import match_specific_from_start
from exam_alignment.utils.alignment_utils import type_of_judgment
from exam_alignment.utils.alignment_utils import split_question
from exam_alignment.utils.alignment_utils import find_continuous_sequence
from exam_alignment.utils.alignment_utils import extract_and_combine_numbers_in_not_start_by_number
class StandardExamParser(AbstractExamParser):
    def __init__(self, content):
        super().__init__(content)

    
    @staticmethod
    def detect_this_exam_type(content):
        """
        检测是否试卷形式为
        题目
        题目答案分割标志词：e.g. 参考答案
        答案

        """

        print(f"【StandardExamParser开始】")
        all_question, split_str = StandardExamParser.extract_questions(content)

        # answer_split_str = StandardExamParser.get_answer_split_str(lines[5:])
        # if answer_split_str is None:
        #     print(f"【未找到题目答案分割行】")
        #     print(f"【StandardExamParser匹配失败】")
        #     return False
        # answer_split_str_index = 0
        #
        # for i in range(len(lines)):
        #     if lines[i] == answer_split_str:
        #         answer_split_str_index = i
        #         print(f"【找到题目答案分割行：'{i}''{answer_split_str}'】")
        #         break

        print(f"split_str:\n{split_str}")
        if split_str in [-1, 0]:
            print("【未找到答案关键字】")
            return False
        if split_str ==1:
            print("【非standard_exam_parser】")
            return False

        answer_str_area = generate_answer_area_string(content, split_str)
        answer_str= StandardExamParser.extract_answers(answer_area_str_process(answer_str_area))

        question_count = len(all_question)
        answer_count = len(answer_str)
        print(f"question_list:'{question_count}'")
        print(f"answer_list:'{answer_count}'")
        is_match = question_count == answer_count

        if is_match:
            print(f"【题干答案已匹配】")
            print(f"【StandardExamParser匹配成功】")
        else:
            print(f"【题干答案不匹配】")
            print(f"【StandardExamParser匹配失败】")
        return is_match


    @staticmethod
    def extract_questions(text):
        # 拆分成行
        lines = text.splitlines()

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

            all_question.append("\n".join(inaccuracy_question[question_index:all_question_indexs[index + 1]]))

        if not all_question:
            return None, None

        all_question = find_continuous_sequence(all_question)

        if text.splitlines()[0] in all_question[-1]:
            answer_split_str = text.splitlines()[0]
            # 看看试卷的title是否出现在"all_question[-1]"位置，如果出现则删除
            all_question[-1] = all_question[-1].split(text.splitlines()[0], 1)[0]
        else:
            # 尝试寻找用于分割答题区与答案区的字符串，返回值为int/str，如果是str则是分割的字符串
            # 本质是在"all_question[-1]"寻找答案关键字等字样
            answer_split_str = find_answer_split_str(all_question)

            if isinstance(answer_split_str, str):
                # 如果找到这个拆分的字符串了，则先把最后一道题的内容进行拆分
                all_question[-1] = all_question[-1].split(answer_split_str)[0]

        return all_question, answer_split_str

    @staticmethod
    def extract_answers(answer_area_string):
        lines = answer_area_string.splitlines()

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

        return refine_answers(processed_inaccuracy_answers)[::-1]

    @staticmethod
    def alignment_answer(all_question, answer_str):
        questions_with_answer = []
        if not answer_str:
            return [{"question": question, "answer": None} for question in all_question]
        all_answer = StandardExamParser.get_all_answer_sequence(answer_area_str_process(answer_str))

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
        all_question, split_str = StandardExamParser.get_all_question(self.content)
        answer_str = generate_answer_area_string(self.content, split_str)
        questions_with_answer=StandardExamParser.alignment_answer(all_question, answer_str)
        for row in questions_with_answer:
            print()

            print(row["question"])
            print("-------------------------------------------------------")
            print(f"{row['answer']}")
            print()
            print("============================================================")

        return questions_with_answer

