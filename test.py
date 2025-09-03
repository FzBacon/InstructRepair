import numpy as np
import pandas as pd
import torch,sys
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler
import warnings
from torch import cuda
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, EncoderDecoderConfig
import loader
import torch.autograd as autograd
import csv
import os, gc
import sys, subprocess,fnmatch, shutil, csv,re, datetime
from datasets import load_dataset, load_from_disk, Dataset
import logging
from accelerate import init_empty_weights, infer_auto_device_map


PROMPT_DICT = {
    "prompt_input": (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:"
    ),
    "prompt_no_input": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Response:"
    ),
}
os.environ["HF_ENDPOINT"]="https://hf-mirror.com"

prompt_input, prompt_no_input = PROMPT_DICT["prompt_input"], PROMPT_DICT["prompt_no_input"]

def getBugName(bugid):
    bugid=str(bugid).replace(' ','')
    buginfo=''
    startNo=''
    removeNo=''
    filepath=''
    with open(TEST_PATH) as testfile:
        lines = testfile.readlines()
        for l in lines:
            bid=l.split('\t')[0]
            bid=bid.replace(' ','')
            if bid in bugid and bugid in bid:
                buginfo=l.split('\t')[3]
                buginfo=buginfo.replace('\n','').replace('\t','').replace('\r','')
                startNo=l.split('\t')[4]
                removeNo=l.split('\t')[5]
                infos = l.split('\t')
                if len(infos) > 6:
                    filepath=l.split('\t')[6]
                    filepath=filepath.replace('\n','').replace('\t','').replace('\r','')
                else:
                    filepath=''
                break
    
    
    return buginfo,startNo,removeNo,filepath


        
def test( model, tokenizer, device, loader,epoch):
    
    return_sequences = 20
    model.eval()
    identicalset=[]
    torch.cuda.empty_cache()
    with torch.no_grad():
        for _,data in enumerate(loader, 0):
            if _>-1:
                bugid = data['bugid']
                logging.info("====bugid==="+bugid)
                formated_prompt = prompt_input.format_map({"instruction": data["instruction"], "input": data["input"]})
                encoding = tokenizer(formated_prompt, return_tensors="pt", max_length=768, truncation=True).to(device)
                encoding["decoder_input_ids"] = encoding["input_ids"]
                try:
                    generated_ids = model.generate(**encoding, #decoder_input_ids=encoding['input_ids'],
                                            max_length=1024,
                                            decoder_start_token_id=tokenizer.pad_token_id,
                                            eos_token_id=tokenizer.eos_token_id,
                                            num_return_sequences=return_sequences,
                                            num_beam_groups = 1,
                                            repetition_penalty=3.0,
                                            num_beams=return_sequences,
                                            # top_k=5
                                            )
                except Exception as e:
                    logging.error(e)
                    continue
                generated_ids = generated_ids[:, encoding['input_ids'].shape[-1]+2:]
                preds = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]

                target = data['output']
                bugname,startNo,removeNo,filepath  = getBugName(bugid)
                with open('./raw_results.csv', 'a') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter='\t',escapechar=' ',quoting=csv.QUOTE_NONE)
                    for i in range(0,return_sequences):
                        filewriter.writerow([bugname, startNo,removeNo,filepath,preds[i],target])

def getGeneratorDataLoader(filepatch,tokenizer,batchsize):
    df = pd.read_csv(filepatch,encoding='latin-1',delimiter='\t')
    print(df.head(1))
    
    df = df[['bugid','patch','buggy']]

    params = {
        'batch_size': batchsize,
        'shuffle': True,
        'num_workers': 0
        }

    dataset=df.sample(frac=1.0, random_state = SEED).reset_index(drop=True)
    target_set = loader.GeneratorDataset(dataset, tokenizer, MAX_LEN, PATCH_LEN)
    target_loader = DataLoader(target_set, **params)
    return target_loader


from peft import PeftModel,PeftConfig,AutoPeftModelForSeq2SeqLM

def run_test(epoch):
    checkpoints = ['final_checkpoint']
    for eve in checkpoints:
        checkpoint = f'./saved_models/prompt-tuning/{eve}'
        print(f'Using checkpoints:{checkpoint}')
        original = 'Salesforce/codet5p-2b'
        
        gen  = AutoPeftModelForSeq2SeqLM.from_pretrained(checkpoint,device_map='auto',output_hidden_states=True,torch_dtype=torch.float16,low_cpu_mem_usage=True,trust_remote_code=True,local_files_only=True)

        gen_tokenizer = AutoTokenizer.from_pretrained(original,truncation=True,trust_remote_code=True)
        gen_tokenizer.add_tokens(['{', '}','<','^','>','<=','>=','==','!=','<<','>>','[PATCH]','[BUG]','[CE]','[FE]','[CONTEXT]','[BUGGY]','[CLASS]','[METHOD]','[RETURN_TYPE]','[VARIABLES]','[Delete]'])
            
        test_loader = load_dataset('json', data_files='tests_with_instructions.json')
        test(gen, gen_tokenizer, device, test_loader, epoch+1)
        logging.info('Fix done!')
          
if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    SEED=42
    LEARNING_RATE = 1e-4
    VALID_BATCH_SIZE = 1
    MAX_LEN = 384
    PATCH_LEN = 76 
    os.environ['CUDA_VISIBLE_DEVICES']='0,1,2,3'
    device = 'cuda:0' if cuda.is_available() else 'cpu'
    # device =torch.device("cuda")

    TEST_PATH='./data/test.csv'  
    run_test(0)

