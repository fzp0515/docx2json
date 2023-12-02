#!/bin/bash

INPUT_DIR=$1
OUTPUT_DIR=$2
PANDOC_DIR=$3
ALIGN_NOT_DIR=$4
ALIGN_FAIL_DIR=$5
OUTPUT_JSON_FILE=$6

# 调用第一个Python文件
python ee2omml/ee_to_omml.py  $INPUT_DIR  $OUTPUT_DIR $PANDOC_DIR

# 调用第二个Python文件
python extract_and_align_exam.py  $OUTPUT_DIR  $OUTPUT_JSON_FILE  $ALIGN_NOT_DIR  $ALIGN_FAIL_DIR
