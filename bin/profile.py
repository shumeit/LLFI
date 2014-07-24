#! /usr/bin/env python3

"""

%(prog)s takes a profiling executable and executes it

Usage: %(prog)s <profiling executable> <the same options that you use to run the excutable before>

       %(prog)s --help(-h): show help information

Prerequisite:
1. You need to be at the parent directory of the <profiling executable> to invoke %(prog)s. This is to make it easier for LLFI to track the outputs generated by <profiling executable>
2. (prog)s only checks recursively at the current directory for possible outputs, if your output is not under current directory, you need to store that output by yourself
3. You need to put your input files (if any) under current directory
4. You need to have 'input.yaml' under your current directory, which contains appropriate options for LLFI. 
"""

# This script profiles the program to produce llfi.stat.prof.txt

import sys
import yaml
import os
import time
import subprocess
import shutil

optionlist = []
prog = os.path.basename(sys.argv[0])

basedir = os.getcwd()
profiling_exe = ""

def usage(msg = None):
  retval = 0
  if msg is not None:
    retval = 1
    msg = "ERROR: " + msg
    print(msg, file=sys.stderr)
  print(__doc__ % globals(), file=sys.stderr)
  sys.exit(retval)


def parseArgs(args):
  global optionlist, profiling_exe, env
  #print("args:")
  #print(args)
  profiling_exe = os.path.realpath(args[1])
  env= args[0]
  optionlist = args[2:]
 # print("exe: ")
 # print(profiling_exe)
 # print("opts: ")
 # print(optionlist)

  if env=="-e" or env== "--CLI":
   
    if os.path.dirname(os.path.dirname(profiling_exe)) != basedir:
      usage("You need to invoke %s at the parent directory of profiling executable" %prog)
      # "program should launch in CLI"
  elif env=="-u" or env== "--GUI": 
    if os.path.dirname(os.path.dirname(os.path.dirname(profiling_exe))) != basedir:
     # "program should launch in GUI"	
      usage("You need to invoke %s at the parent of parent directory of profiling executable" %prog)
  else: 
      usage("You need to enable optiones for GUI/CLI")
  

  # remove the directory prefix for input files, this is to make it easier for the program
  # to take a snapshot
  for index, opt in enumerate(optionlist):
    if os.path.isfile(opt):
      if os.path.realpath(os.path.dirname(opt)) != basedir:
        usage("File %s passed through option is not under current directory" % opt)
      else:
        optionlist[index] = os.path.basename(opt)


def checkInputYaml():
  #Check for input.yaml's presence
  yamldir = os.path.dirname(os.path.dirname(profiling_exe))
  try:
    f = open(os.path.join(yamldir, 'input.yaml'), 'r')
  except:
    usage("No input.yaml file in the parent directory of profiling executable")
    exit(1)
  
  #Check for input.yaml's correct formmating
  try:
    doc = yaml.load(f)
    f.close()
  except:
    usage("input.yaml is not formatted in proper YAML (reminder: use spaces, not tabs)")
    exit(1)
  
 
################################################################################
def config():
  global inputdir, outputdir, baselinedir, errordir
  # config
  llfi_dir = os.path.dirname(profiling_exe)

  inputdir = os.path.join(llfi_dir, "prog_input")
  outputdir = os.path.join(llfi_dir, "prog_output")
  baselinedir = os.path.join(llfi_dir, "baseline")
  errordir = os.path.join(llfi_dir, "error_output")

  if not os.path.isdir(outputdir):
    os.mkdir(outputdir)
  if not os.path.isdir(baselinedir):
    os.mkdir(baselinedir)
  if not os.path.isdir(errordir):
    os.mkdir(errordir)
  if not os.path.isdir(inputdir):
    os.mkdir(inputdir)

################################################################################
def execute(execlist):
  #print "Begin"
  #inputFile = open(inputfile, "r")
  global outputfile
  print('\t' + ' '.join(execlist))
  #get state of directory
  dirSnapshot()
  p = subprocess.Popen(execlist, stdout=subprocess.PIPE)
  elapsetime = 0
  while True:
    elapsetime += 1
    time.sleep(1)
    #print p.poll()
    if p.poll() is not None:
      moveOutput()
      print("\t program finish", p.returncode)
      print("\t time taken", elapsetime,"\n")
      outputFile = open(outputfile, "wb")
      
      outputFile.write(p.communicate()[0])
      outputFile.close()
      replenishInput() #for cases where program deletes input or alters them each run
      #inputFile.close()
      return p.returncode

################################################################################
def storeInputFiles():
  global inputList
  inputList=[]
  for opt in optionlist:
    if os.path.isfile(opt):#stores all files in inputList and copy over to inputdir
      shutil.copy2(opt, os.path.join(inputdir, opt))
      inputList.append(opt)

################################################################################
def replenishInput():#TODO make condition to skip this if input is present
  for each in inputList:
    if not os.path.isfile(each):#copy deleted inputfiles back to basedir
      shutil.copy2(os.path.join(inputdir, each), each)

################################################################################
def moveOutput():
  #move all newly created files that are not "llfi.stat.prof.txt" < -- since this is a product of profiling
  newfiles = [_file for _file in os.listdir(".")]
  for each in newfiles:
    if each not in dirBefore and each != "llfi.stat.prof.txt":
      fileSize = os.stat(each).st_size
      if fileSize == 0 and each.startswith("llfi"):
        #empty library output, can delete
        print(each + " is going to be deleted for having size of " + str(fileSize))
        os.remove(each)
      else:
        flds = each.split(".")
        newName = '.'.join(flds[0:-1])
        newName+='.prof.'+flds[-1]
        os.rename(each, os.path.join(baselinedir, newName))

################################################################################
def dirSnapshot():
  #snapshot of directory before each execute() is performed
  global dirBefore
  dirBefore = [_file for _file in os.listdir(".")]

################################################################################
def main(args):
  global optionlist, outputfile

  parseArgs(args)
  checkInputYaml()
  config()

  storeInputFiles()
  # baseline
  outputfile = os.path.join(baselinedir, "golden_std_output")
  execlist = [profiling_exe]
  execlist.extend(optionlist)
   
  return execute(execlist)


################################################################################

if __name__=="__main__":
  if len(sys.argv) == 1:
    usage('Must provide the profiling executable and its options')
    exit(1)
  exit(main(sys.argv[1:]))
