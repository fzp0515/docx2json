#!/bin/bash

INPUT_DIR=$1
OUTPUT_DIR=$2
PANDOC_DIR=$3
ALIGN_NOT_REC_DIR=$4
ALIGN_FAIL_DIR=$5
OUTPUT_JSON_FILE=$6
HANDLE_PICTURE=false # 默认为假


#word文档转成md格式，包含公式转换
python ee2omml/ee_to_omml.py $INPUT_DIR $OUTPUT_DIR $PANDOC_DIR

# 检查是否有 --handle_picture 参数
for arg in "$@"
do
    if [ "$arg" == "--handle_picture" ]; then
        HANDLE_PICTURE=true
        break
    fi
done

#判断是否处理带图片的试题
if [ "$HANDLE_PICTURE" = true ]; then
    # 如果 HANDLE_PICTURE 为真，处理图片
    python extract_and_align_exam.py  $OUTPUT_DIR  $OUTPUT_JSON_FILE  $ALIGN_NOT_REC_DIR  $ALIGN_FAIL_DIR --handle_picture
else
    # 否则，不处理图片
    python extract_and_align_exam.py  $OUTPUT_DIR  $OUTPUT_JSON_FILE  $ALIGN_NOT_REC_DIR  $ALIGN_FAIL_DIR
fi

