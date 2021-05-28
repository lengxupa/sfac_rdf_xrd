#Python 2.7 code to convert all user input formats into dump files

import sys
import re
import numpy as np
import input2dump
import os
import plotter
import calculation

def detect_format(filename):
    '''Opens the file titled filename and makes a single pass over it to detect
       one of the three possible formats (LAMMPS dump, xyz, data)
       Detects for an xyz file by matching whether the first line is an integer
       Detects for a dump file by searching for the string "ITEM: NUMBER OF ATOMS"
       Detects for a data file by searching for the string "<integer> atoms"
       Once format is detected, return a list containing [fileformat, no of atoms, box info]'''
    infolist = []
    ndimensions = 3
    f = open(filename, 'r')
    lineindex = 0
    for line in f:
        lineindex += 1
        if(lineindex == 1):
            xyzobj = re.match("^[0-9]*$", str(line))
            if xyzobj:
                store = int(line.split()[0])
        dumpobj = re.match("ITEM: NUMBER OF ATOMS\n", str(line))
        dataobj = re.match("[0-9]* atoms", str(line)) #needs work
        if dumpobj:
            infolist.append("dump")
            line = next(f)
            line = line.split()
            infolist.append(int(line[0]))
            f.close()
            box = []
            infolist.append(box)
            return infolist

        if dataobj:
            infolist.append("data")
            line = line.split()
            infolist.append(int(line[0]))
            while "xlo" not in line:
                line = next(f)
            box = np.zeros((ndimensions, 2))
            for i in range(ndimensions):
                line = line.split()
                box[i][0] = float(line[0])
                box[i][1] = float(line[1])
                line = next(f)
            f.close()
            infolist.append(box)
            return infolist
        
        if xyzobj:
            infolist.append("xyz")
            line = line.split()
            infolist.append(int(store))
            f.close()
            box = np.zeros((ndimensions, 2))
            print "Enter box information in the following format:"
            print "xlo xhi\nylo yhi\nzlo zhi"
            for i in range(ndimensions):
                inline = raw_input().split()
                box[i][0] = float(inline[0])
                box[i][1] = float(inline[1])
            infolist.append(box)
            return infolist


def write_dump(filename,infolist,e_flag=0,elementlist=[],atom_style='full'):
    
    columnid = np.zeros(5, dtype='int32') #id type x y z
    regex0 = ' id'; regex1 = ' type'; regex2 = ' x'; regex3 = ' y'; regex4 = ' z'
    dumplist = [regex0, regex1, regex2, regex3, regex4] 
    
    #Infolist structuring [elementlist, fileformat, natoms, box]
    fileformat = infolist[0]
    natoms = infolist[1]
    box = infolist[2]
    print "Writing intermediate dump file"
    print "Input file format :", fileformat
    #g = open('gen.dump', 'w')
    f = open(filename, 'r')
    h = open("numberdensity.dat", 'w') #write number density information
    h.write("Timestep Number density\n")
   
    if (fileformat == "data"):
        input2dump.data2dump(natoms, box, dumplist, columnid, f, g, h, e_flag=e_flag, elementlist=elementlist, atom_style=atom_style)
                
    if (fileformat == "dump"):
        dump_flag=input2dump.dump2dump(natoms, dumplist, columnid, f, h, e_flag=e_flag, elementlist=elementlist)
        if not dump_flag:
            return False
                    
    if (fileformat == "xyz"):
        input2dump.xyz2dump(natoms, box, f, g, h, e_flag=e_flag, elementlist=elementlist)

    f.close(); h.close()

    return True
    
   
def user_decisions(flist,np_flag=0,rnp_flag=0,np=1):
#    print "Which functions do you want to evaluate? (sfac, rdf, xrd)"
#    flist = raw_input().split()
    if 'rdf' in flist:
        print "Evaluating RDF..."
        if 'sfac' in flist:
            if 'xrd' in flist:
                calculation.calculation(np_flag=np_flag,rnp_flag=rnp_flag,np=np,sfac=1,xrd=1)
            else:
                calculation.calculation(np_flag=np_flag,rnp_flag=rnp_flag,np=np,sfac=1)
        else:
            if 'xrd' in flist:
                calculation.calculation(np_flag=np_flag,rnp_flag=rnp_flag,np=np,xrd=1)
            else:
                calculation.calculation(np_flag=np_flag,rnp_flag=rnp_flag,np=np)
        print('Plot Radial distribution function')
        plotter.plotRDF("rdf.dat",'RDF.pdf')
        os.system('cp rdf.dat ..')
        os.system('cp RDF.pdf ..')
    if 'sfac' in flist:
        if 'rdf' in flist:
            print('Plot X-ray weighted Static structure factor')
            plotter.plotSQ("sqtotal_xrd.txt",'sqtotal_xrd.pdf','X-ray weighted Static structure factor')
            os.system('cp sqtotal_xrd.txt ../sfac_xrd.dat')
            os.system('cp sqtotal_xrd.pdf ..')
            print('Plot neutron weighted Static structure factor')
            plotter.plotSQ("sqtotal_neutron.txt",'sqtotal_neutron.pdf','Neutron weighted Static structure factor')
            os.system('cp sqtotal_neutron.txt ../sfac_neutron.dat')
            os.system('cp sqtotal_neutron.pdf ..')
        else:
            print('Calculating structure factor requires RDF inforamtion')
            print('Please add "rdf" keywords in your input script')
            return False
    if 'xrd' in flist:
        print "Evaluating XRD pattern..."
        if 'rdf' not in flist:
            calculation.calculation(np_flag=np_flag,rnp_flag=rnp_flag,np=np,xrd=1)
        print('Plot X-ray diffraction pattern')
        plotter.plotXRD("Deg2Theta.xrd",'XRD.pdf')
        os.system('cp Deg2Theta.xrd ../xrd.dat')
        os.system('cp XRD.pdf ..')
#        calculation.calculation(np_flag=np_flag,rnp_flag=rnp_flag,np=np,xrd=1)


def main(args):
    filename = '../'+args['datafile'][0]

    e_flag=0
    elementlist=[]
    if 'element' in args:
        if len(args['element'])>1:
            ne=int(eval(args['element'][0]))
            print('%d element types:' %ne)
            if len(args['element'])==(1+ne):
                e_flag=1
                elementlist=args['element'][1:]
                print(elementlist)
            else:
                print('please specify %d element types' %ne)
                return False
        else:
            print('Please specify number of element types followed by a sequence of the element(s)')
            return False

    flist=[]
    if 'sfac' in args:
        flist.append('sfac')
    if 'rdf' in args:
        flist.append('rdf')
    if 'xrd' in args:
        flist.append('xrd')
    if not flist:
        print('Please specify what inforamtion you wish to get from the workflow')
        print('sfac ---- Static structure factor')
        print('rdf ---- Radial distribution function')
        print('xrd ---- X-ray powder diffraction')
        return False

    atom_style='full'
    if 'atom_style' in args:
        if len(args)>args.index('atom_style')+1:
            atom_style=args[args.index('atom_style')+1]
            print('LAMMPS data file atom style %s' %atom_style)
        else:
            print('Default LAMMPS data file atom style: full')

    np_flag=0
    rnp_flag=0
    np=1
    if 'parallel' in args:
        np_flag=1
        print('LAMMPS will run in parallel mode')
        if len(args)>args.index('parallel')+1:
            if 'np' in args and args[args.index('parallel')+1]=='np':
                if len(args)>args.index('np')+1:
                    np=int(eval(args[args.index('np')+1]))
                    if np<=0:
                        print('Please input a valid number larger than 0')
                        return False
                    else:
                        print('%d of processors will be in use' %np)
                else:
                    print('Please input a number of processors you want to use')
                    return False
            else:
                rnp_flag=1
                print('Will calculating recommended number of processors after initial polymer configuration generated')
        else:
            rnp_flag=1
            print('Will calculating recommended number of processors after initial polymer configuration generated')

    fileinfo = detect_format(filename)
    if fileinfo[0]=='dump':
        os.system('cp %s gen.dump' %filename)
    write_dump_flag=write_dump(filename,fileinfo,e_flag=e_flag,elementlist=elementlist,atom_style=atom_style)
    if not write_dump_flag:
        return False
    user_decisions(flist,np_flag=np_flag,rnp_flag=rnp_flag,np=np)


infile=sys.argv[1]
ifile=open(infile)
args={}
for line in ifile.readlines():
    ln=line.split('#')[0]
    l=ln.split()
    args[l[0]]=l[1:]
ifile.close()

main(args)

