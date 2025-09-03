#!/usr/bin/python
import sys, os, time, subprocess,fnmatch, shutil, csv,re, datetime

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

def getTestExactLine(program_path,failingtest):
    cmd = "cd " + program_path + ";"
    cmd += "defects4j coverage -t "+failingtest
    print(cmd)
    result=''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    print(result)
    if 'failing_tests' in str(result):
        # fail_test = subprocess.run('defects4j test', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        with open(program_path+'/failing_tests') as f:
            testlines = f.readlines()
            print(testlines)
            for x in range(1,len(testlines)):
                if failingtest.replace('::','.') in testlines[x]:
                    return testlines[x][testlines[x].index('(')+1:testlines[x].index(')')].split(':')[1]
    else:
        # print('*********************',program_path,failingtest)
        return 

def getTestCode(program_path,project,bugNo):
    cmd = "defects4j info -p "+project +"  -b "+bugNo
    # print(cmd)
    result=''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if 'Root cause in triggering tests:' in str(result):
        result=str(result).split('Root cause in triggering tests:')[1]
    if '--------' in str(result):
        result=str(result).split('--------')[0]
    # print(result)
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
    print('==========failingtest======='+failingtest)
    print('==========faildiag======='+faildiag)
    testCodePath = failingtest.split('::')[0].replace('.','/')
    testFunc = failingtest.split('::')[1]

    if project == 'Math':
        if int(bugNo) >= 85:
            testCodeFullPath = '/src/test/'+testCodePath+'.java'
            #project+bugNo+
        else:
            testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'Lang':
        if int(bugNo) >= 37:
            testCodeFullPath = '/src/test/'+testCodePath+'.java'
        else:
            testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'Cli':
        if int(bugNo) >= 32:
            testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
        else:
            testCodeFullPath = '/src/test/'+testCodePath+'.java'
    elif project == 'Closure':
        testCodeFullPath = '/test/'+testCodePath+'.java'
    elif project == 'Codec':
        if int(bugNo) >= 16:
            testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
        else:
            testCodeFullPath = '/src/test/'+testCodePath+'.java'
    elif project == 'Mockito':
        testCodeFullPath = '/test/'+testCodePath+'.java'
    elif project == 'Jsoup':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'JacksonDatabind':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'JacksonCore':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'Compress':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'Collections':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'Time':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'JacksonXml':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'Gson':
        testCodeFullPath = '/gson/src/test/java/'+testCodePath+'.java'
    elif project == 'Csv':
        testCodeFullPath = '/src/test/java/'+testCodePath+'.java'
    elif project == 'JxPath':
        testCodeFullPath = '/src/test/'+testCodePath+'.java'
    else:
        testCodeFullPath = '/tests/'+testCodePath+'.java'
    # program_path = program_path.replace("Perturbation-",'')
    testCodeFullPath = program_path + testCodeFullPath

    if os.path.exists((program_path+'/tests')):
        testCodeFullPath = program_path+'/tests/'
    elif os.path.exists(program_path+'/test'):
        testCodeFullPath = program_path+'/test/'
    elif os.path.exists(program_path+'/src/test/java'):
        testCodeFullPath = program_path+'/src/test/java/'
    elif os.path.exists(program_path+'/src/test'):
        testCodeFullPath = program_path+'/src/test/'
    elif os.path.exists(program_path+'/gson/src/test/java'):
        testCodeFullPath = program_path+'/gson/src/test/java/'
    testclass = failingtest.split("::")[0]
    testmethod = failingtest.split("::")[1]
    testclass=testclass.replace('.','/')
    testclass = testclass+'.java'

    testCodeFullPath = testCodeFullPath+testclass
        
    # if not os.path.exists(testCodeFullPath):
    #     os.system('defects4j checkout -p '+ str(project)+' -v '+str(bugNo)+'b   -w '+'repos/'+ project+bugNo)

    with open(testCodeFullPath,'r',errors='ignore') as f:
        codelines = f.readlines()
        code_text = ''.join(codelines)
        lex = None
        tree = javalang.parse.parse(code_text) 
        method_text = ''   
        # methods = {}
        for _, method_node in tree.filter(javalang.tree.MethodDeclaration):
            if method_node.name == testFunc:
                startpos, endpos, startline, endline = get_method_start_end(method_node,tree)
                method_text, startline, endline, lex = get_method_text(startpos, endpos, startline, endline, lex,codelines)
        if method_text:
            codeNo = getTestExactLine(program_path ,failingtest)
            if codeNo:
                exactCodeline = codelines[int(codeNo)].strip('\n')
                method_text_lines = method_text.split('\n')
                for x in range(len(method_text_lines)):
                    if exactCodeline == method_text_lines[x]:
                        method_text = ''.join(method_text_lines[x-5:x])
                        break
                return method_text.replace('    ',' ').replace('     ',' ').replace('\n','')
            else:
                return 'codeNo NOT FOUND'
        else:
            return 'method_text NOT FOUND'

def start(bugId,repodir,rootdir):
    projectPath=repodir+'/'+bugId
    traveProject(bugId, projectPath,repodir)

def traveProject(bugId,projectPath,repodir):
    listdirs = os.listdir(projectPath)
    for x in range(0,len(listdirs)):
        print(bugId+':'+str(x)+"of"+str(len(listdirs)))
        pattern = '*.java'
        p = os.path.join(projectPath, listdirs[x])
        if os.path.isfile(p):
            if fnmatch.fnmatch(listdirs[x], pattern) and ('Test' not in p and 'test' not in p) :
                print(p)
                with open(p,'r') as perturbFile:
                    lines = perturbFile.readlines()
                    if len(lines)>0:
                        for k in range(0,len(lines)):
                            constructTrainSample(bugId, lines[k], p, repodir, True, rootdir)
        else:
            traveProject(bugId,p,repodir)


def constructTrainSample(bugId,line,targetfile,repodir,diagnosticFlag,rootdir):
    project = bugId.split('-')[0]
    # print(line)
    sample=''
    cxt=''
    filename = targetfile.split('/')[-1]
    originFile = targetfile.replace("Perturbation-","")

    if not '^' in line:
        return
    infos = line.split('^')
    if len(infos) < 11:
        return
    if len(infos) > 11:
        return
    curruptCode =  infos[1]


    lineNo1 =  infos[2] 
    lineNo2 =  infos[3] 
    lineNo3 =  infos[4] 
    lineNo4 =  infos[5]
    lineNo5 =  infos[6]
    cxtStart = infos[7]
    cxtEnd = infos[8]
    groundTruth = infos[9]
    metaInfo = infos[10]
    groundTruth = groundTruth.replace('  ',' ').replace('\r','').replace('\n','')
    action = infos[0] 

    try:
        string_int = int(lineNo1)
    except ValueError:
        return
    

    curruptCode = curruptCode.replace(' (','(').replace(' )',')')
    curruptCode = curruptCode.replace('(  )','()')
    curruptCode = curruptCode.replace(' .','.')
    
    # get diagnostic by execution
    diagnosticMsg,testCode = diagnostic(bugId,line,targetfile,repodir,action,diagnosticFlag,rootdir)
    
    #get context info
    if cxtStart not in '' and cxtEnd not in '':
        with open(originFile,'r') as perturbFile:
            lines = perturbFile.readlines()
            for i in range(0,len(lines)):
                if i > int(cxtStart)-2 and i < int(cxtEnd):
                    l = lines[i]
                    l = l.strip()
                    #remove comments
                    if  l.startswith('/') or l.startswith('*'):
                        l = ' '
                    l = l.replace('  ','').replace('\r','').replace('\n','')
                    if i == int(lineNo1)-1:
                        l='[BUGGY] '+curruptCode + ' [BUGGY] '
                    cxt+=l+' '


    os.system("mv "+repodir+"/"+filename +"  "+originFile)
    sample+='[BUG] [BUGGY] ' + curruptCode + diagnosticMsg+ ' [CONTEXT] ' + cxt +' '+'  '+ metaInfo + ' [TESTS] ' + str(testCode)
    sample = sample.replace('\t',' ').replace('\n',' ').replace('\r',' ').replace('  ',' ')
    groundTruth = '[PATCH] '+groundTruth.replace('\t',' ').replace('\n',' ').replace('\r',' ').replace('  ',' ')
    
    # print("*****sample**** :"+sample)


    with open(repodir+'/train-'+bugId+'.csv','a')  as csvfile:
        filewriter = csv.writer(csvfile, delimiter='\t',  escapechar=' ', 
                                quoting=csv.QUOTE_NONE)               
        filewriter.writerow([groundTruth,sample,action])




def diagnostic(bugId,line,targetfile,repodir,action,executeFlag,rootdir):
    project = bugId.split('-')[0]
    line=line.replace('\r',' ').replace('\n',' ')
    filename = targetfile.split('/')[-1]
    originFile = targetfile.replace("Perturbation-","")
    # print("*****originFile originFile**** :"+originFile)
    # print("*****diagnostics**** :")


    #copy the origin file outside the project
    os.system("cp "+originFile+"  "+repodir)
    # initial perturb string
    perturbStr=''
    
    # print("target line:"+line)
    infos = line.split('^')
    curruptCode =  infos[1]  
    lineNo1 =  infos[2] 
    lineNo2 =  infos[3] 
    lineNo3 =  infos[4] 
    lineNo4 =  infos[5]
    lineNo5 =  infos[6]

    # print('**************Currupt Code*************'+curruptCode)
    
    
    if "Transplant" in action or "Replace" in action or "Move" in action or  "Insert" in action:
        # read and perturb code 
        with open(originFile,'r') as perturbFile:
            lines = perturbFile.readlines()
            for i in range(0,len(lines)):
                if i+1< int(lineNo1) or i+1> int(lineNo1)+4:
                    perturbStr+=lines[i]
                elif i+1==int(lineNo1):
                    perturbStr+=curruptCode+"\n"
                elif i+1==int(lineNo1)+1: 
                    if lineNo2=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
                elif i+1==int(lineNo1)+2:
                    if lineNo3=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
                elif i+1==int(lineNo1)+3:  
                    if lineNo4=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
                elif i+1==int(lineNo1)+4:
                    if lineNo5=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
    #REMOVE actions
    elif "P14_" in action or 'P15_' in action or 'P16_' in action:
        with open(originFile,'r') as perturbFile:
            lines = perturbFile.readlines()
            for i in range(0,len(lines)):
                if i+1< int(lineNo1) or i+1> int(lineNo1)+4:
                    perturbStr+=lines[i]
                elif i+1==int(lineNo1):
                    perturbStr+= lines[i]+" \n" +curruptCode
                elif i+1==int(lineNo1)+1: 
                    if lineNo2=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
                elif i+1==int(lineNo1)+2:
                    if lineNo3=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
                elif i+1==int(lineNo1)+3:  
                    if lineNo4=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"
                elif i+1==int(lineNo1)+4:
                    if lineNo5=='':
                        perturbStr+=lines[i]
                    else:
                        perturbStr+=" \n"


  
    # write back the perturb code to class file
    with open(originFile,'w') as perturbFileWrite:
        perturbFileWrite.write(perturbStr)

    if executeFlag:
        execute_result,testCode = executePerturbation(bugId,repodir,originFile,action,line,rootdir)
    else:
        execute_result=''
        testCode = 'None'
    
    return execute_result,testCode




def executePerturbation(bugId,repodir,originFile,action,line,rootdir):
    bugId = bugId.replace('Perturbation-','')
    compile_error_flag = True

    program_path=repodir+'/'+bugId
    # print('****************'+program_path+'******************')
    #get compile result
    cmd = "cd " + program_path + ";"
    cmd += "timeout 90 defects4j compile"
    exectresult='[TIMEOUT]'
    testCode = 'None'
    symbolVaraible=''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print(result)
    # Running ant (compile.tests)
    if 'Running ant (compile)' in str(result):
        result = str(result).split("Running ant (compile)")[1]
        # print('===result==='+str(result))

        result=result.split('\n')
        for i in range(0,len(result)):
            if 'error: ' in result[i]:
                firstError=result[i].split('error: ')[1]
                exectresult=firstError.split('[javac]')[0]
                if '\\' in exectresult:
                    exectresult=exectresult.split('\\')[0]
                # print('===FirstError==='+firstError)
                # 'cannot  find  symbol      
                if 'symbol' in firstError and 'cannot' in firstError and 'find' in firstError:       
                    if '[javac]' in firstError:
                        lines = firstError.split('[javac]')
                        for l in lines:
                            if 'symbol:'in l and 'variable' in l:
                                symbolVaraible=l.split('variable')[1]
                                if '\\' in symbolVaraible:
                                    symbolVaraible=symbolVaraible.split('\\')[0]
                                break



                exectresult='[CE] '+exectresult+symbolVaraible
                break
            elif 'OK' in result[i]:
                exectresult='[FE]'
                compile_error_flag=False



    if not compile_error_flag:
        #get test result
        cmd = "cd " + program_path + ";"
        cmd += "timeout 180 defects4j test"
        result=''
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # print(result)
        if 'Failing tests: 0' in str(result):
            exectresult='[NO-ERROR]'
        elif 'Failing tests' in str(result):
            testCode = getTestCode(program_path,bugId.split('-')[0],bugId.split('-')[1])
            # print(str(testCode))
            result=str(result).split('Failing tests:')[1]
            result=str(result).split('-')
            for i in range(1,len(result)):
                failingtest = result[i]
                if '::' not in failingtest and i+1<len(result):
                    failingtest = result[i+1]
                if '\\' in failingtest:
                    failingtest = failingtest.split('\\')[0]
                failingtest=failingtest.strip()

                if '::' in failingtest:
                    failingTestMethod=failingtest.split('::')[1]
                    faildiag = getFailingTestDiagnostic(failingtest,program_path)
                    exectresult = '[FE] ' + faildiag +' '+failingTestMethod
                else:
                    exectresult = '[FE] '
                break



    os.chdir(rootdir)

    with open(repodir+'/diagnostic.csv','a')  as csvfile:
        filewriter = csv.writer(csvfile, delimiter='\t',  escapechar=' ', 
                                quoting=csv.QUOTE_NONE)               
        filewriter.writerow([exectresult+' [TESTS] '+str(testCode),line])

    return exectresult,testCode



def getFailingTestDiagnostic(failingtest,program_path):
    testclass = failingtest.split("::")[0]

    cmd = "cd " + program_path + ";"
    cmd += "timeout 120 defects4j monitor.test -t "+failingtest
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print('====result===='+str(result))
    if 'failed!' in str(result) :
        result = str(result).split('failed!')[1]
        if testclass in str(result):
            result = str(result).split(testclass)[1]
            if '):' in str(result):
                result = str(result).split('):')[1]
                if '\\' in str(result):
                    result = str(result).split('\\')[0]
    else:
        result =''
    
    return str(result)




def getFailingTestSourceCode(failingtest,program_path):
    code=''
    if os.path.exists((program_path+'/tests')):
        program_path = program_path+'/tests/'
    elif os.path.exists(program_path+'/test'):
        program_path = program_path+'/test/'
    elif os.path.exists(program_path+'/src/test/java'):
        program_path = program_path+'/src/test/java/'
    elif os.path.exists(program_path+'/src/test'):
        program_path = program_path+'/src/test/'
    elif os.path.exists(program_path+'/gson/src/test/java'):
        program_path = program_path+'/gson/src/test/java/'

    # print(failingtest+'&&&&&&&&failingtest')
    testclass = failingtest.split("::")[0]
    testmethod = failingtest.split("::")[1]
    testclass=testclass.replace('.','/')
    testclass = testclass+'.java'

    fullpath = program_path+testclass

    if os.path.exists(fullpath):    
        startflag=False
        code =''
        with open(fullpath,'r') as codefile:
            lines=codefile.readlines()
            for l in lines:
                if 'public' in l  and 'void' in l and testmethod in l:
                    startflag=True
                if 'public' in l and 'void' in l and testmethod not in l:
                    startflag=False
                if startflag:
                    if 'assert' in l:
                        l = l.strip()
                        if l not in code:
                            code=l
    return code


if __name__ == '__main__': 
    bugIds = ['Closure-134','Lang-65','Chart-26','Math-106','Mockito-38','Time-26','Cli-1','Collections-25','Codec-1','Compress-1','Csv-1','Gson-1','JacksonCore-1','JacksonDatabind-1','JacksonXml-1','Jsoup-1','JxPath-1']
    rootdir= '/home/instructrepair'   
    repodir = rootdir+'/Perturbation_Samples'
    
    for bugId in bugIds:
        exeresult_list = []
        project=bugId.split('-')[0]
        bugNo = bugId.split('-')[1]
        if os.path.exists(repodir+'/'+bugId):
            os.system('rm -rf '+repodir+'/'+bugId)
        os.system('defects4j checkout -p '+ str(project)+' -v '+str(bugNo)+'f   -w '+repodir+'/'+bugId)
        bugId = bugId.replace(project, "Perturbation-"+project)
        start(bugId,repodir,rootdir)

        
        
