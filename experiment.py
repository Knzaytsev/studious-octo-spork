import torch
from transformers import BloomTokenizerFast
from petals import DistributedBloomForCausalLM
from tqdm import tqdm
import json
from os.path import join, exists
import subprocess
from constants import PATH, EXPERIMENT_PATH, EXPERIMENT, SELF_CONSISTENCY

def read_jsonl(path: str):
    with open(path) as fh:
        return [json.loads(line) for line in fh.readlines() if line]

def read_json(path: str):
    with open(path) as fh:
        return json.loads(fh.read())

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(device)

model = DistributedBloomForCausalLM.from_pretrained("bigscience/bloom-petals", tuning_mode="ptune", pre_seq_len=16, request_timeout=1800).to(device)
tokenizer = BloomTokenizerFast.from_pretrained("bigscience/bloom-petals")

print('model is ready')

data = read_jsonl(PATH)

outputs = dict()
if exists(EXPERIMENT_PATH):
    outputs = read_json(EXPERIMENT_PATH)

start_position = len(outputs)

print('data is read')

input_prompt = """Q: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?
A: We start with 15 trees. Later we have 21 trees. The difference must be the number of trees they planted. So, they must have planted 21 - 15 = 6 trees. The answer is 6.

Q: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?
A: There are 3 cars in the parking lot already. 2 more arrive. Now there are 3 + 2 = 5 cars. The answer is 5.

Q: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total? 
A: Leah had 32 chocolates and Leah’s sister had 42. That means there were originally 32 + 42 = 74 chocolates. 35 have been eaten. So in total they still have 74 - 35 = 39 chocolates. The answer is 39.

Q: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?
A: Jason had 20 lollipops. Since he only has 12 now, he must have given the rest to Denny. The number of lollipops he has given to Denny must have been 20 - 12 = 8 lollipops. The answer is 8.

Q: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?
A: He has 5 toys. He got 2 from mom, so after that he has 5 + 2 = 7 toys. Then he got 2 more from dad, so in total he has 7 + 2 = 9 toys. The answer is 9.

Q: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
A: There are 4 days from monday to thursday. 5 computers were added each day. That means in total 4 * 5 = 20 computers were added. There were 9 computers in the beginning, so now there are 9 + 20 = 29 computers. The answer is 29.

Q: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
A: Michael initially had 58 balls. He lost 23 on Tuesday, so after that he has 58 - 23 = 35 balls. On Wednesday he lost 2 more so now he has 35 - 2 = 33 balls. The answer is 33.

Q: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
A: She bought 5 bagels for $3 each. This means she spent 5 * $3 = $15 on the bagels. She had $23 in beginning, so now she has $23 - $15 = $8. The answer is 8."""


for row in tqdm(data[start_position:]):
    question, answer = row['question'], row['answer']

    input_text = input_prompt + '\n\nQ: ' + question + '\nA:'
    inputs = tokenizer(input_text, return_tensors="pt", )["input_ids"].to(device)

    answers = []
    if EXPERIMENT == SELF_CONSISTENCY:
        for _ in tqdm(range(5)):
            output = model.generate(inputs, max_new_tokens=128, temperature=0.9, 
                                        top_k=32, do_sample=True)
            answers.append(tokenizer.decode(output[0]))
    else:
        output = model.generate(inputs, max_new_tokens=128, temperature=0.9, do_sample=False)
        answers.append(tokenizer.decode(output[0]))
        
        
    outputs[question] = {'correct_answer': answer, 'model_answer': answers}

    with open(EXPERIMENT_PATH, 'w') as f:
        json.dump(outputs, f)
    
    subprocess.run(['dvc', 'add', 'data'])
    subprocess.run(['git', 'commit', 'data.dvc', '-m', '"answers updates"'])
    subprocess.run(['dvc', 'push'])
    subprocess.run(['git', 'push'])