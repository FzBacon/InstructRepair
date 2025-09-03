#!/usr/bin/python
import sys, os, time, subprocess,fnmatch, shutil, csv,re, datetime,random
from multiprocessing import Process,Pool

def executePatch(projectId,bugId,startNo,removedNo,fpath,predit,repodir):
    #first checkout buggy project
    random_number = str(random.randint(1, 10000)).zfill(5)
    os.system("cp -r "+ repodir+'/'+projectId+bugId +"  "+repodir+'/tmp_exec/'+projectId+bugId+random_number)

    #keep a copy of the buggy file
    originFile = repodir+'/tmp_exec/'+projectId+bugId+random_number+'/'+fpath
    filename = originFile.split('/')[-1]

    newStr=''
    endNo=int(startNo)+int(removedNo)
    try:
        with open(originFile,'r') as of:
            lines=of.readlines()
            for i in range(0,len(lines)):
                l=lines[i]
                if i+1 < int(startNo):
                    newStr+=l 
                if i+1 == int(startNo):
                    newStr+=predit+'\n'
                if i+1 >= endNo:
                    newStr+=l
        with open(originFile,'w') as wof:
            wof.write(newStr)
    except Exception as e:
        return '[exception]'+str(e)
    exeresult = execute(projectId+bugId,repodir,originFile,repodir+'/tmp_exec/'+projectId+bugId+random_number)
        
    os.system("rm -rf "+repodir+"/tmp_exec/"+projectId+bugId+random_number)
    # print(predit)
    return exeresult


def execute(patchId,repodir,originFile,rootdir):
    compile_error_flag = True

    # program_path=repodir+'/'+patchId
    program_path=rootdir
    print('****************'+program_path+'******************')
    #get compile result
    cmd = "cd " + program_path + ";"
    cmd += "timeout 300 defects4j compile"
    exectresult='[timeout]'
    symbolVaraible=''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print(result)
    
    # evaluate compilable
    if 'Running ant (compile)' in str(result):
        result = str(result).split("Running ant (compile)")[1]
        result=result.split('\n')
        for i in range(0,len(result)):
            if 'error: ' in result[i]:
                firstError=result[i].split('error: ')[1]
                exectresult=firstError.split('[javac]')[0]
                if '\\' in exectresult:
                    exectresult=exectresult.split('\\')[0]
                # print('=======First Error========='+firstError)
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
                exectresult='OK'
                compile_error_flag=False

    # evaluate plausible
    if not compile_error_flag:
        #get test result
        cmd = "cd " + program_path + ";"
        cmd += "timeout 600 defects4j test"
        result=''
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # print(result)
        if 'Failing tests: 0' in str(result):
            exectresult='[Plausible]'
        elif 'Failing tests' in str(result):
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


    return exectresult


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


if __name__ == '__main__':

    patchFromPath='./raw_results.csv'
    patchToPath='./results.csv'
    repodir = '/home/instructrepair/repos'    
    with open(patchFromPath,'r') as patchFile:
        patches = patchFile.readlines()
        for i in range(0,len(patches)): # len(patches)15,18
            try:
                print(i)
                patch=patches[i]
                pid=patch.split('\t')[0]
                projectId =pid.split('_')[0]
                bugId =pid.split('_')[1]
                startNo=patch.split('\t')[1]
                removedNo=patch.split('\t')[2]
                path=patch.split('\t')[3]
                predit = patch.split('\t')[4]
                groundtruth = patch.split('\t')[5]
                print(projectId)
                print(bugId)
                preditNoSpace = predit.replace(' ','').replace('\n','').replace('\r','').replace('[Delete]','')
                groundtruthNoSpace = groundtruth.replace(' ','').replace('\n','').replace('\r','').replace('[PATCH]','').replace('[Delete]','')
                if groundtruthNoSpace in 'nan':
                    groundtruthNoSpace=''
                if preditNoSpace in groundtruthNoSpace and groundtruthNoSpace in preditNoSpace:
                    with open(repodir + '/' + patchToPath,'a') as targetFile:
                        targetFile.write('Identical\t'+str(i)+'\t'+patch)
                else:
                    exeresult = executePatch(projectId,bugId,startNo,removedNo,path,predit,repodir)
            except Exception as e:
                print(e)
    

                



