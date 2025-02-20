import requests
import json
import jsonlines

from pydantic import BaseModel
from typing import List


class SPARQL(BaseModel):
    query: List[str]


def add_suffix(s: str, suffix: str):
    """Adds suffix to the string s if s is not ending with it, else returns s"""
    return s if len(suffix) == 0 or s.endswith(suffix) else s + suffix


def json_load(name: str, encoding: str='utf-8', suffix='.json'):
    with open(add_suffix(name, suffix), 'r', encoding=encoding) as f:
        return json.load(f)


url = 'http://localhost:11434/api/generate'

headers = {
    'conent-type': 'application/json'
}

models = {
#    'qwen_2.5': ['qwen2.5:latest', 'qwen2.5:14b', 'qwen2.5:32b', 'qwen2.5:72b',],
#    'deepseek_r1': ['deepseek-r1:7b', 'deepseek-r1:14b', 'deepseek-r1:32b', 'deepseek-r1:70b',],
    'llama_3.3': ['llama3.3:70b'],
    'mistral': ['mistral-small:latest', 'mistral-large:latest'],
}

processes = ['direct', 'NER', 'masked',]

qald = json_load('benchmarks/qald9plus.json')
mcwq = json_load('benchmarks/mcwq.json')

datasets = {
    'qald9': qald,
    'mcwq': mcwq,
}


def main():
    for family, model_list in models.items():
        for dataset_name, dataset in datasets.items():
            print(family, dataset_name)
            out_file = f'results/{dataset_name}-{family}.jsonl'
            for model in model_list:
                print(' ', model)
                for x, item in enumerate(dataset):
                    print(f'  {x+1:>5}/{len(dataset)}'.ljust(100), end='\r')
                    for process in processes:
                        print(f'  {x+1:>5}/{len(dataset)} - {process}'.ljust(100), end='\r')

                        if not process in item:
                            continue
                        prompt = item[process]

                        data = {
                            'model': model,
                            'prompt': prompt,
                            'stream': False,
                            'options': {
                                'temperature': 0,
                                'num_predict': 4000,
                            },
                            'format': SPARQL.model_json_schema(),
                        }
                        try:
                            response = requests.post(url, headers=headers, data=json.dumps(data))

                            response = {
                                'question': item['en'],
                                'model': model,
                                'process': process,
                                'prompt': prompt,
                                'response': response.json()['response'],
                            }
                        except Exception as e:
                            print(f'Error: {e}')
                            continue

                        with jsonlines.open(out_file, 'a') as writer:
                            writer.write(response)

                print(f'  {x+1:>5}/{len(dataset)}'.ljust(100))


if __name__ == "__main__":
    main()
