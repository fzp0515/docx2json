from exam_alignment.type_exam_parser.abstract_exam_parser import AbstractExamParser

from exam_alignment.type_exam_parser.annotated_exam_parser import AnnotatedExamParser
from exam_alignment.type_exam_parser.standard_exam_parser import StandardExamParser
from exam_alignment.type_exam_parser.split_exam_parser import SplitExamParser


file_path = r"C:\Users\Zhipeng\Desktop\test\input\2008年山西公务员考试《行测》真题及参考解析.md"
import re
regex_pattern = r"!\[\]\(media/(.+?)\)"
with open(file_path, 'r', encoding='utf-8') as file:
    md_content = file.read()
    modified_text = re.sub(regex_pattern, r"![](media/\1)\n", md_content)

if StandardExamParser.detect_this_exam_type(modified_text):
    print("StandardExamParser success!")


if AnnotatedExamParser.detect_this_exam_type(modified_text):
    print("AnnotatedExamParser success!")
