
from openai import OpenAI

from datetime import datetime

def gpt_alignment_process(text,key):
    prompt = ("""你将得到一份试卷，请拆分问题，返回json格式，遵循以下规则：
    1.problem里填入问题,options填入选项，若主观题则options为空，ground_truth_solution填入解析，没有解析则空着，ground_truth_answer填入回答，没有回答则空着
    2.在试卷原文中保留形如![](media/image1.png)的图片插入标志，不要删去
    3.严格遵守给定的试卷，不得增加或者减少原文中的信息，保留图片插入标志

    返回格式如下：
    [
    {
        "problem": "4. 与全国平均水平相比，人均GDP高、人均CO2排放量低的是",
        "options":"A．上海、天津 B．广东、福建 C．海南、贵州 D．辽宁、山东",#选择题包含options
        "ground_truth_solution": "",
        "ground_truth_answer": "C"
    },
    {
        "problem": "41.（28分）石羊河流经甘肃省中部，流域内灌溉农业较发达、生态环境问题严重。根据下列材料，结合所学知识。完成（1）\~（4）题。（1）石羊河的总体流向为 。从内、外流河类型看，该河为 河，判断理由是。（6分）",
        "options":"",# 主观题的options为空
        "ground_truth_solution": "",
        "ground_truth_answer": "41、（1）自西南向东北 内流河 没有流入海洋 (每空2分,共6分)
        }]
    """)


    client = OpenAI(
        api_key=key,

        base_url="https://api.moonshot.cn/v1",
    )



    query_str=prompt + "input:" + text + "output:"

    completion = client.chat.completions.create(
        model="moonshot-v1-128k",
        messages=[
            {"role": "system",
             "content": "你是人工智能助手。你会为用户提供安全，有帮助，准确的回答。"},
            {"role": "user", "content": query_str}
        ],
        temperature=0.3,
        max_tokens=10240
    )


    #把gpt生成的数据归档一下
    current_time = datetime.now()
    formatted_time = current_time.strftime('%Y%m%d%H%M')
    file_path = formatted_time+'GPTGenerateData.txt'  # 指定文件路径
    generate_data=prompt + "input:" + text + "output:"+completion.choices[0].message.content
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(generate_data)

    return completion.choices[0].message.content










