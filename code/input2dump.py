#Python 2.7 code to convert all user input formats into dump files

import sys
import re
import numpy as np

def data2dump(natoms, box, dumplist, columnid, f, g, h, lineindex=0, switch=False, ndimensions=3, e_flag=0, elementlist=[], atom_style='full'):
    if not e_flag:
        print('Please specify number of element types followed by a sequence of the element(s)')
        return False
    #print "Enter elements corresponding to atom types"
    #elementlist = raw_input().split()
    l = open("elementinfo", 'w')
    for elementindex, element in enumerate(elementlist):
        l.write(str(elementindex+1) + " " + element + "\n")
    l.close()
    formatstring = detect_datatype()
    for i in range(len(dumplist)):
        mobj = re.search(dumplist[i], formatstring) 
        columnid[i] = formatstring.count(' ', 0, mobj.start())
    g.write('ITEM: TIMESTEP\n')
    g.write(str(0) + "\n")
    g.write('ITEM: NUMBER OF ATOMS\n')
    g.write(str(natoms) + "\n")
    g.write('ITEM: BOX BOUNDS\n')
    for i in range(ndimensions):
        g.write(str(float(box[i][0])) + " " + str(float(box[i][1])) + "\n")
    g.write('ITEM: ATOMS id type x y z\n')
    volume = (box[0][1]-box[0][0])*(box[1][1]-box[1][0])*(box[2][1]-box[2][0])
    h.write(str(0) + " " + str(natoms/volume) + "\n")
    for line in f:
        lineindex += 1
        if ("Atoms" in line):
            startindex = lineindex+2
            switch = True
        if (switch and lineindex >= startindex and lineindex < startindex+natoms):
            line = line.split()
            g.write(str(line[columnid[0]]) + " " + str(line[columnid[1]]) + " " + str(line[columnid[2]]) 
                    + " " + str(line[columnid[3]]) + " " + str(line[columnid[4]]))
            g.write("\n")  
    return 1


def xyz2dump(natoms, box, f, g, h, lineindex=0, ndimensions=3, e_flag=0, elementlist=[]):
    typeflag = 0
    elemflag = 0
    switch = 1
    l = open("elementinfo", 'w')
    for line in f:
        lineindex += 1
        remainder = (lineindex-1) % (natoms + 2)
        if (remainder == 1):
            counter = 0
            g.write('ITEM: TIMESTEP\n')
            line = line.split()
            g.write(str(line[-1]) + "\n") #build in error checking
            g.write('ITEM: NUMBER OF ATOMS\n')
            g.write(str(natoms) + "\n")
            g.write('ITEM: BOX BOUNDS\n')
            for i in range(ndimensions):
                g.write(str(float(box[i][0])) + " " + str(float(box[i][1])) + "\n")
            g.write('ITEM: ATOMS id type x y z\n')
            volume = (box[0][1]-box[0][0])*(box[1][1]-box[1][0])*(box[2][1]-box[2][0])
            h.write(str(0) + " " + str(natoms/volume) + "\n")
        if (remainder > 1):
            counter += 1
            typeobj = re.match('[0-9] ', line)
            elementobj = re.search('[a-zA-Z] ', line)
            line = line.split()
            if (typeobj):
                typeflag = 1
                if not e_flag:
                    print('Please specify number of element types followed by a sequence of the element(s)')
                    return False
                #print "Enter elements corresponding to atom types"
                #elementlist = raw_input().split()
                for elementindex, element in enumerate(elementlist):
                    l.write(str(elementindex+1) + " " + element + "\n")
            if (elementobj): 
                elemflag = 1; typeflag = 0
                currelem = str(line[0])
                if currelem not in elementlist:
                    elementlist.append(currelem)
                typeindex = [i+1 for i in range(len(elementlist)) if (elementlist[i] == currelem)][0]
            
            g.write(str(counter) + " " + str(typeindex) + " " + str(line[1]) + " " + str(line[2]) + " " + str(line[3]))
            g.write("\n")
    if (elemflag == 1):
        for elementindex, element in enumerate(elementlist):
            l.write(str(elementindex+1) + " " + element + "\n")
    l.close()
    return 1


def dump2dump(natoms, dumplist, columnid, f, h, lineindex=0, ndimensions=3, e_flag=0, elementlist=[]):
    currvol = 1 #vol init
    typeflag = 0
    elemflag = 0
    switch = 1
    l = open("elementinfo", 'w')
    for line in f:
        lineindex += 1
        remainder = (lineindex-1) % (natoms + 9)
        #if (remainder < 8):
            #g.write(line)
        if (remainder == 1):
            tstep = int(line.split()[0])
        if (remainder >= 5 and remainder <= 7):
            line = line.split()
            currvol  = currvol*(float(line[1])-float(line[0]))
        if (remainder == 8):
            volume = currvol
            currvol = 1
            h.write(str(tstep) + " " + str(natoms/volume) + "\n")
            #g.write('ITEM: ATOMS id type x y z\n')
            if (switch == 1): #to make sure searching is done once
                typeobj = re.search(' type ', line)
                elementobj = re.search(' element ', line)
                if (typeobj):
                    typeflag = 1
                    if not e_flag:
                        print('Please specify number of element types followed by a sequence of the element(s)')
                        return False
                    #print "Enter elements corresponding to atom types"
                    #elementlist = raw_input().split()
                    for elementindex, element in enumerate(elementlist):
                        l.write(str(elementindex+1) + " " + element + "\n")
                if (elementobj): dumplist[1] = ' element '; elemflag = 1; typeflag = 0
            for i in range(len(dumplist)):
                mobj = re.search(dumplist[i], line) 
                columnid[i] = line.count(' ', 0, mobj.start())-1
            switch = 0
        if (remainder > 8):
            line = line.split()
            if (typeflag == 1):
                typeindex = int(line[columnid[1]])
            if (elemflag == 1):
                currelem = str(line[columnid[1]])
                #if currelem not in elementlist:
                    #elementlist.append(currelem)
                #typeindex = [i+1 for i in range(len(elementlist)) if (elementlist[i] == currelem)][0]
            #g.write(str(line[columnid[0]]) + " " + str(typeindex) + " " + str(line[columnid[2]]) 
                    #+ " " + str(line[columnid[3]]) + " " + str(line[columnid[4]]))
            #g.write("\n")
    if (elemflag == 1):
        for elementindex, element in enumerate(elementlist):
            l.write(str(elementindex+1) + " " + element + "\n")
    l.close()
    return 1


def detect_datatype(atom_style='full'):
    #print "Enter atom style:"
    #atom_style = raw_input() #1 for full
    formatstring = {"full": " id molid type q x y z", "charge": " id type q x y z", "molecular": " id molid type x y z"}
    if (formatstring[atom_style]):
        return formatstring[atom_style]
    else:
        print "Unknown atom style"
        return null

