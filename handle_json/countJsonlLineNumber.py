import json
input_file='output\\other_pic_05.jsonl'
def read_jsonl(file_name):
    with open(file_name, 'r',encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)

counter = 0
for data in read_jsonl(input_file):
    counter += 1

print(f'There are {counter} JSON objects in the file.')