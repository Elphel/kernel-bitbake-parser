# Author: Yuri Nenakhov, Elphel. Inc
# License: GPLv2+

# TODO: makefiles with multiple workdirs not supported
import sys
import os
import re

proj_dir = '/linux-elphel'
src_dir = '/linux'
abs_path1 = re.compile('/home.*r1/git/')
wrk_link1 = proj_dir+'/linux/'
abs_path2 = re.compile('/home.*tmp/sysroots/')
wrk_link2 = proj_dir+'/sysroots/'

is_inc_start = re.compile('^\#include\ <\.\.\.>\ search\ starts\ here\:$')
is_inc_end = re.compile('^End\ of\ search\ list\.$')
is_inc_abspath = re.compile('^\s\/[^\s]*$')
is_inc_relpath = re.compile('^\s[\w][^\s]*$')
is_workdir = re.compile('Entering directory')
is_def_symbol = re.compile('\s-D[\s]*([^\s\n]+)')
is_src_path = re.compile('\s([^\s]+\/[\w]+\.c)\s')
is_extra_include = re.compile('-include[\s]+([^\s]+\.h)[\s\n]')
is_src_file = re.compile('.*\.c$')
inc_receiving = 0
inc_paths = []
workdirs = []
srcdirs = []
defsyms = []
extraincs = []
defsymnames = []
all_paths = []

def abs2wrklink(path):
    path = re.sub(abs_path1,wrk_link1,path)
    path = re.sub(abs_path2,wrk_link2,path)
    return path

print(" ╔═══════════════════════════════════════════════════════╗ ")
print(" ║ Required output is produced by a recipe modified with ║ ")
print(" ║    EXTRA_OEMAKE = \"-s -w -j1 -B KCFLAGS='-v'\"         ║ ")
print(" ╚═══════════════════════════════════════════════════════╝ ")

for line in sys.stdin:
    # searching for workdir
    if(is_workdir.search(line)): 
        line = line.split('`')[1]
        line = re.sub("[\s\'\n]","",line)
        if (line not in workdirs):
            workdirs.append(line)
            workdir = line
            cmd = 'find -L '+workdir+' -type d'
            for i in os.popen(cmd):
                i = abs2wrklink(i)[:-1]
                if workdir not in i:
                    all_paths.append(i)
            cmd = 'find -L '+workdir+' -path \"*.c\"'
            for i in os.popen(cmd):
                i = abs2wrklink(i)[:-1]
                if workdir not in i:
                    all_paths.append(i)
        pass
    #searching for inc paths start
    if(is_inc_start.search(line)): 
        inc_receiving+=1
        pass
    # searching for inc paths
    if(inc_receiving): 
        if(is_inc_end.search(line)):
            inc_receiving-=1
        else:
            if(is_inc_relpath.search(line)):
                line = " "+workdir+"/"+str(line)[1:]
            if(is_inc_abspath.search(line)):
                line = abs2wrklink(line)
                line = re.sub("[ \n]","",line)
                if(line not in inc_paths):
                    inc_paths.append(line)
        pass
    # searching for define symbols
    clearedline = re.sub("[\']*","",line)
    for defsym in re.finditer(is_def_symbol,clearedline):
        defsymname = defsym.group(1).split("=")[0]
        if defsymname not in defsymnames:
            defsymnames.append(defsymname)
            defsyms.append(defsym.group(1))
    # searching for extra includes
    for extrainc in re.finditer(is_extra_include,clearedline):
        if extrainc.group(1) not in extraincs:
            extraincs.append(extrainc.group(1))
    # searching for source paths
    for srcpath in re.finditer(is_src_path,clearedline):
        srcdir = abs2wrklink(workdir+"/"+ srcpath.group(1))
        if srcdir not in srcdirs:
            srcdirs.append(srcdir)
            for i in all_paths:
                if i in srcdir:
                    all_paths.remove(i)
print(" ╔════════════════════╗\n ║   define symbols   ║\n ╚════════════════════╝")
xml_defs = ""
for i in defsyms:
    i=i.split("=")
    xml_defs += "<listOptionValue builtIn=\"false\" value=\""+i[0]+"="
    try:
        xml_defs += i[1]
    except IndexError:
        xml_defs += "1"
    xml_defs += "\"/>\n"
xml_defs = xml_defs[:-1]
print(xml_defs)

print(" ╔════════════════════╗\n ║   include paths    ║\n ╚════════════════════╝")
for i in inc_paths:
    print("<listOptionValue builtIn=\"false\" value=\"&quot;${workspace_loc:"+i+"}&quot;\"/>")

print(" ╔════════════════════╗\n ║   extra includes   ║\n ╚════════════════════╝")
for i in extraincs:
    print(abs2wrklink(i))

all_paths.sort()
for i in range(len(all_paths)):
    try:
        while all_paths[i+1].startswith(all_paths[i]):
            #print("removing "+all_paths[i+1]+" because of "+all_paths[i])
            all_paths.pop(i+1)
    except IndexError:
        pass
print(" ╔════════════════════╗\n ║    source paths    ║\n ╚════════════════════╝")
xml_src = "<entry excluding=\""
all_paths.sort()
for i in all_paths:
    i=i.replace(proj_dir+src_dir+"/","")
    if not is_src_file.search(i):
        i += "/"
    xml_src += i
    xml_src += "|"
xml_src = xml_src[:-1]+"\" flags=\"VALUE_WORKSPACE_PATH\" kind=\"sourcePath\" name=\""+src_dir[1:]+"\"/>"
print(xml_src)
