
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
import pandas as pd
import json
import subprocess
import os
import javalang
def get_method_start_end(method_node,tree):
    startpos  = None
    endpos    = None
    startline = None
    endline   = None
    for path, node in tree:
        if startpos is not None and method_node not in path:
            endpos = node.position
            endline = node.position.line if node.position is not None else None
            break
        if startpos is None and node == method_node:
            startpos = node.position
            startline = node.position.line if node.position is not None else None
    return startpos, endpos, startline, endline

def get_method_text(startpos, endpos, startline, endline, last_endline_index,codelines):
    if startpos is None:
        return "", None, None, None
    else:
        startline_index = startline - 1 
        endline_index = endline - 1 if endpos is not None else None 

        # 1. check for and fetch annotations
        if last_endline_index is not None:
            for line in codelines[(last_endline_index + 1):(startline_index)]:
                if "@" in line: 
                    startline_index = startline_index - 1
        meth_text = "<ST>".join(codelines[startline_index:endline_index])
        meth_text = meth_text[:meth_text.rfind("}") + 1] 

        # 2. remove trailing rbrace for last methods & any external content/comments
        # if endpos is None and 
        if not abs(meth_text.count("}") - meth_text.count("{")) == 0:
            # imbalanced braces
            brace_diff = abs(meth_text.count("}") - meth_text.count("{"))

            for _ in range(brace_diff):
                meth_text  = meth_text[:meth_text.rfind("}")]    
                meth_text  = meth_text[:meth_text.rfind("}") + 1]     

        meth_lines = meth_text.split("<ST>")  
        meth_text  = "".join(meth_lines)                   
        last_endline_index = startline_index + (len(meth_lines) - 1) 

        return meth_text, (startline_index + 1), (last_endline_index + 1), last_endline_index

def getTestExactLine(project,bugNo,failingtest):
    cmd = "cd " + project + bugNo + ";"
    cmd += "defects4j coverage -t "+failingtest
    result=''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if 'failing_tests' in str(result):
        with open(project + bugNo+'/failing_tests') as f:
            testlines = f.readlines()
            for x in range(1,len(testlines)):
                if failingtest.replace('::','.') in testlines[x]:
                    return testlines[x][testlines[x].index('(')+1:testlines[x].index(')')].split(':')[1]
    else:
        print('*********************',project,bugNo,failingtest)
        return 

def getTestCode(project,bugNo):
    cmd = "defects4j info -p "+project +"  -b "+bugNo
    result=''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if 'Root cause in triggering tests:' in str(result):
        result=str(result).split('Root cause in triggering tests:')[1]
    if '--------' in str(result):
        result=str(result).split('--------')[0]
    failingtest = ''
    faildiag = ''
    resultLines = str(result).split('\\')
    for l in resultLines:
        if '-' in l and '::' in l and failingtest  in '':
            failingtest = l.split('-')[1]
            failingtest=failingtest.strip()
        if '-->' in l and faildiag  in '':
            faildiag = l.split('-->')[1]
            if '.' in faildiag:
                faildiag_dots = faildiag.split('.')
                if len(faildiag_dots)>2:
                    faildiag=''
                    for i in range(2,len(faildiag_dots)):
                        faildiag+=faildiag_dots[i]
    testCodePath = failingtest.split('::')[0].replace('.','/')
    testFunc = failingtest.split('::')[1]

    if project == 'Math':
        if int(bugNo) >= 85:
            testCodeFullPath = project+bugNo+'/src/test/'+testCodePath+'.java'
        else:
            testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'Lang':
        if int(bugNo) >= 37:
            testCodeFullPath = project+bugNo+'/src/test/'+testCodePath+'.java'
        else:
            testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'Cli':
        if int(bugNo) >= 32:
            testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
        else:
            testCodeFullPath = project+bugNo+'/src/test/'+testCodePath+'.java'
    elif project == 'Closure':
        testCodeFullPath = project+bugNo+'/test/'+testCodePath+'.java'
    elif project == 'Codec':
        if int(bugNo) >= 16:
            testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
        else:
            testCodeFullPath = project+bugNo+'/src/test/'+testCodePath+'.java'
    elif project == 'Mockito':
        testCodeFullPath = project+bugNo+'/test/'+testCodePath+'.java'
    elif project == 'Jsoup':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'JacksonDatabind':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'JacksonCore':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'Compress':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'Collections':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'Time':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'JacksonXml':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'Gson':
        testCodeFullPath = project+bugNo+'/gson/src/test/java/'+testCodePath+'.java'
    elif project == 'Csv':
        testCodeFullPath = project+bugNo+'/src/test/java/'+testCodePath+'.java'
    elif project == 'JxPath':
        testCodeFullPath = project+bugNo+'/src/test/'+testCodePath+'.java'
    else:
        testCodeFullPath = project+bugNo+'/tests/'+testCodePath+'.java'
    testCodeFullPath = 'repos/' + testCodeFullPath
    with open(testCodeFullPath,'r',errors='ignore') as f:
        codelines = f.readlines()
        code_text = ''.join(codelines)
        lex = None
        tree = javalang.parse.parse(code_text) 
        method_text = ''   
        for _, method_node in tree.filter(javalang.tree.MethodDeclaration):
            if method_node.name == testFunc:
                startpos, endpos, startline, endline = get_method_start_end(method_node,tree)
                method_text, startline, endline, lex = get_method_text(startpos, endpos, startline, endline, lex,codelines)
        if method_text:
            codeNo = getTestExactLine('repos/' +project,bugNo,failingtest)
            if codeNo:
                exactCodeline = codelines[int(codeNo)].strip('\n')
                method_text_lines = method_text.split('\n')
                for x in range(len(method_text_lines)):
                    if exactCodeline == method_text_lines[x]:
                        method_text = ''.join(method_text_lines[x-3:x+2])
                        break
                return method_text.replace('    ',' ').replace('     ',' ').replace('\n','')
            else:
                return None
        else:
            print('*********************',project,bugNo)
            return None



df = pd.read_csv('data/test.csv',encoding='latin-1',delimiter='\t')
with open('instruction_of_d4j_withtest_l5_real.json','w') as f:
    output = []
    for x in range(len(df)):
        print(x)
        patch = df['patch'][x]
        bugid = df['bugid'][x]
        buggy_code = df['buggy'][x]
        bid = df['id'][x]
        # bid = 'Cli_3'
        print(bid)

        testCode = getTestCode(bid.split('_')[0],bid.split('_')[1])

        if '[FE]' in buggy_code:
            fe = buggy_code[buggy_code.index('[FE]')+4:buggy_code.index('[CONTEXT]')]
            instruct=f'The following code contains a buggy line with the following test error:{fe}. The original buggy line is given after the special token: [BUGGY]. Please refer to buggy line, its context, error message and tests code to provide the fix code. The tests code which trigger this bug is given here: '
            
        elif '[CE]' in buggy_code:
            ce = buggy_code[buggy_code.index('[CE]')+4:buggy_code.index('[CONTEXT]')]
            instruct=f'The following code contains a buggy line with the following test error:{ce}. The original buggy line is given after the special token: [BUGGY]. Please refer to buggy line, its context, error message to provide the fix code.'
        else:
            # NO WAY
            instruct=f'The following code contains a buggy line. The original buggy line is given after the special token: [BUGGY]. Please refer to buggy line, its context, error message and to provide the fix code.'
        output.append({
            "instruction": instruct + str(testCode),
            "input": buggy_code,
            "output": patch,
            "bugid" : str(bugid)
        })
    f.write(json.dumps(output))
