import json
import time
from pathlib import Path
from openai import OpenAI
from decouple import config


# Configure OpenAI API - new client initialization
openai_api_key = config('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

outfile = 'data/mcwq-optimized-questions.jsonl'

# Read JSONL file
questions = []
with open('data/mcwq-qwen_2.5-eval.jsonl', 'r', encoding='utf-8') as file:
    for line in file:
        data = json.loads(line)
        questions.append(data['question'])

# remove duplicates based
questions = list(set(questions))
# pretty print the first 10 questions
print(json.dumps(questions[:10], indent=4))


# if outfile does not exist, create it
if not Path(outfile).exists():
    with open(outfile, 'w', encoding='utf-8') as file:
        pass

# read the JSON file outfile and remove the questions that are already in the list
questions_already_optimized = []
with open(outfile, 'r', encoding='utf-8') as file:
    for line in file:
        data = json.loads(line)
        questions_already_optimized.append(data['question_original'])

questions = [
    question for question in questions if question not in questions_already_optimized]

# limit the number of questions to 10
# questions = questions[:10]

# Process questions and get OpenAI responses
# send each question to the OpenAI API and get the response
# store the question and the response in a new file

prompt = """
You are a helpful assistant that optimizes questions that need to be answered by a knowledge graph.
You will be given a question and you will need to optimize it, s.t., the question is easier to understand.
However, it is important that the semantics of the question are not changed.

You will need to:
- make the question more specific
- make the question more concise
- make the question more clear

Question: 
"""


for i, question in enumerate(questions, 1):
    print(f"\nProcessing question {i}/{len(questions)}")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt + question}]
    )

    # pretty print the response
    print(f"{i}. Original question:\n{question}")
    print(f"{i}. Optimized question:\n{response.choices[0].message.content}")
    print("-"*30)

    # store the question and the response in a new file
    with open(outfile, 'a', encoding='utf-8') as file:
        # get the response content
        optimized_question = response.choices[0].message.content
        file.write(json.dumps({'question_original': question, 'llm_generated_optimized_question': optimized_question,
                   'final_optimized_question': optimized_question, 'validation_status': "no"}) + '\n')

print(f"Finished processing {len(questions)} questions, written to {outfile}")
