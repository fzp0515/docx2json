import json
import jsonlines
import ijson
# 定义输入和输出文件名
input_file = 'all\\other_pic_b.json'
output_noPic_file = 'output\\other_noPic_05.jsonl'
output_Pic_file='output\\other_pic_05.jsonl'


with open(input_file, 'r',encoding='utf-8') as f, open(output_noPic_file, 'w',encoding='utf-8') as f1 ,open(output_Pic_file, 'w',encoding='utf-8') as f2:
    for line in f:
        item = json.loads(line)
        # 如果item的'detail_data'属性存在且'pic_count'属性为0
        if 'detail_data' in item and item['detail_data']['pic_count'] == 0:
            # 如果'question'和'answer'属性都不为空
            if item['question'] != '' and item['answer'] != '':
                # 将整个对象写入JSONL文件
                f1.write(json.dumps(item, ensure_ascii=False) + '\n')
        else:
            # 将整个对象写入other_data.jsonl文件
            f2.write(json.dumps(item, ensure_ascii=False) + '\n')
