import os,string,sys
from math import pi,sin,sqrt,exp

def firstframe(ifile,ofile):
	src=open(ifile)
	des=open(ofile,'w')
	a=0
	for line in src.readlines():
		ln=line.split()
		if a and len(ln)==2 and ln[1]=='TIMESTEP':
			break
		if len(ln)==2 and ln[1]=='TIMESTEP':
			des.write(line)
			a=1
			continue	
		des.write(line)
	src.close()
	des.close()


def read_dump(ifile,multiframe=0):
	Dir={}
	src=open(ifile)
	current=''
	timestep=0
	for line in src.readlines():
		ln=line.split()
		if ln[0]=='ITEM:':
			if ln[1]=='TIMESTEP' or ln[1]=='BOX' or ln[1]=='ATOMS':
				current=ln[1]
				if ln[1]=='BOX':
					Dir[timestep][current]=[]
				if ln[1]=='ATOMS':
					Dir[timestep][current]={}
					Dir[timestep][current]['id']=0
					dump={}
					for i,j in enumerate(ln[2:]):
						dump[i]=j
			if ln[1:]=='NUMBER OF ATOMS'.split():
				current='NUMBER OF ATOMS'
			continue
		if current=='TIMESTEP':
			if multiframe:
				timestep=eval(ln[0])
			if timestep not in Dir:
				Dir[timestep]={}
		if current=='NUMBER OF ATOMS':
			Dir[timestep][current]=eval(ln[0])
		if current=='BOX':
			Dir[timestep][current]+=[eval(i) for i in ln]
		if current=='ATOMS':
			cid=Dir[timestep][current]['id']
			Dir[timestep][current][cid]={}
			for i,j in enumerate([(eval(k) if k[0].isdigit or k[0]=='-' else k) for k in ln]):
				Dir[timestep][current][cid][dump[i]]=j
			Dir[timestep][current]['id']+=1
	return Dir


def write_data(Dir,ofile):
	des=open(ofile,'w')
	des.write('LAMMPS data file via Tongtong\n')
	des.write('\n')
	for i in ['atom','bond','angle','dihedral','improper']:
		if (i+'s') in Dir:
			des.write('%d %s\n' %(Dir[i+'s'],(i+'s')))
			des.write('%d %s\n' %(Dir[i+' types'],(i+' types')))
	des.write('\n')
	for i in ['x','y','z']:
		des.write('%f %f %s %s\n' %(Dir[i+'lo'],Dir[i+'hi'],(i+'lo'),(i+'hi')))
	des.write('\n')
	for key in ['Masses','Pair Coeffs','Bond Coeffs','Angle Coeffs','Dihedral Coeffs','Improper Coeffs','Atoms','Velocities','Bonds','Angles','Dihedrals','Impropers']:
		if key in Dir and len(Dir[key])>0:
			des.write(key+'\n')
			des.write('\n')
			for i in Dir[key]:
				des.write(str(i)+' '+' '.join([str(j) for j in Dir[key][i]])+'\n')
			des.write('\n')
	des.close()


def datafile():
	firstframe('gen.dump','first.dump')
	dumpDir=read_dump('first.dump')
	dataDir={}
	fin2=open('elementinfo','r')
	dataDir['Pair Coeffs']={}
	Dir={}
	Dir2={}
	Dirmirror={}
	for line in fin2.readlines():
		if line:
			ln=line.split()
			Dir[eval(ln[0])]=ln[1]
			if not ln[1] in Dirmirror:
				Dirmirror[ln[1]]=eval(ln[0])
				dataDir['Pair Coeffs'][eval(ln[0])]=[0.0152,2.84642]
			Dir2[eval(ln[0])]=0
	fin2.close()
	atoms=dumpDir[0]['NUMBER OF ATOMS']
	dataDir['atoms']=atoms
	dataDir['atom types']=len(Dir)
	box=[]
	for i in ['x','y','z']:
		for j in ['lo','hi']:
			box.append(i+j)
	for i,j in enumerate(box):
		dataDir[j]=dumpDir[0]['BOX'][i]
	dataDir['Masses']={}
	for key in Dir:		
		dataDir['Masses'][key]=[1]
	dump=[i for i in dumpDir[0]['ATOMS'][0]]
	full=['mol','type','charge','x','y','z']
	dataDir['Atoms']={}
	for i in range(atoms):
		info=dumpDir[0]['ATOMS'][i]
		dataDir['Atoms'][info['id']]=[1]*3+[0]*3
		for j in dump:
			if j in full:
				if j=='type':
					dataDir['Atoms'][info['id']][full.index(j)]=Dirmirror[Dir[info[j]]]
					Dir2[info[j]]+=1
				else:
					dataDir['Atoms'][info['id']][full.index(j)]=info[j]
	write_data(dataDir,'try.data')
	return Dir,Dir2


def read_data(ifile):
	Dir={}
	Box={}
	Masses={}
	src=open(ifile,'r')
	a=1
	s=''
	for line in src.readlines():
		if a:
			a=0
			continue
		ln=line.split('#')[0].split()
		if ln:
			if len(ln)>1 and ln[0].isdigit() and (not ln[1].isdigit()) and (not s):
				Dir[' '.join(ln[1:])]=eval(ln[0])
			if len(ln)==4 and ln[2][1:]=='lo' and ln[3][1:]=='hi':
				Dir[ln[2]]=eval(ln[0])
				Dir[ln[3]]=eval(ln[1])
			if not (ln[0][0].isdigit() or ln[0][0]=='-'):
				s=' '.join(ln)
				Dir[s]={}
			if s and (ln[0][0].isdigit() or ln[0][0]=='-'):
				Dir[s][eval(ln[0])]=[eval(i) for i in ln[1:]]
	src.close()
	return Dir


def grabprocessors(ifile):
	src=open(ifile)
	for line in src.readlines():
		ln=line.split()
		if ln and ln[0]=='read_data':
			datafile=ln[1]
			break
	src.close()
	Dir=read_data(datafile)
	atoms=Dir['atoms']
	if 'bonds' in Dir:
		return atoms/2000+1
	else:
		return atoms/1000+1


def correctppn(ppn):
  nodes=ppn/20+1 if (ppn/20 and ppn%20) else ppn/20 if ppn/20 else 1
  if not ppn/20:
    ppn=20 if ppn>10 else 10 if ppn>8 else 8 if ppn>4 else 4 if ppn>2 else 2 if ppn>1 else 1 
  return nodes,20 if ppn/20 else ppn, nodes*20 if ppn/20 else ppn


def lammpsfile(Dir,Dir2,np_flag=0,rnp_flag=0,np=1,xrd=0):
	fout=open('rdf.in','w')
	fout.write('# General parameters\n')
	fout.write('units	real\n')
	fout.write('atom_style        full\n')
	fout.write('boundary          p p p\n')
#	fout.write('special_bonds     lj/coul 0.0 0.0 1.0 dihedral yes\n')
#	fout.write('dielectric        1.0\n')
	fout.write('pair_style        lj/cut  12.0\n')
#	fout.write('bond_style        harmonic\n')
#	fout.write('angle_style       harmonic\n')
#	fout.write('dihedral_style    harmonic\n')
#	fout.write('improper_style    harmonic\n')
	fout.write('read_data   try.data\n')
#	fout.write('neighbor          2.0 bin\n')
#	fout.write('thermo_style      custom step etotal ke temp pe ebond eangle edihed eimp evdwl ecoul elong press pxx pyy pzz pxy pxz pyz lx ly lz density\n')
#	fout.write('thermo            10\n')
#	fout.write('thermo_modify     flush yes\n')
#	fout.write('neigh_modify	every 1 delay 0 check yes\n')
#	fout.write('pair_style        buck/coul/long  12.0 12.0\n')
#	fout.write('kspace_style      pppm 1e-4\n')
#	fout.write('\n')
	fin=open('numberdensity.dat','r')
	denDir={}
	steps=[]
	for line in fin.readlines():
		ln=line.split()
		if len(ln)==2:
			steps.append(eval(ln[0]))
			denDir[eval(ln[0])]=eval(ln[1])
#	for key in Dir:
#		for key2 in Dir:
#			if key<=key2:
#				fout.write('pair_coeff %d %d 3407.78599213 0.258035858504 31.3691508534\n' %(key,key2))
#	fout.write('\n')
	fout.write('reset_timestep %d\n' %steps[0])
	fout.write('\n')
	Dir3={}
	Dir4={}
	for key in Dir:
		if Dir[key] in Dir3:
			Dir3[Dir[key]].append('%d' %key)
		else:
			Dir3[Dir[key]]=[]
			Dir3[Dir[key]].append('%d' %key)
	s=''
	s1=''
	for key in Dir3:
		for key2 in Dir3:
			s+=str(Dir3[key][0])+' '
			s1+=(key+' ')
			s+=str(Dir3[key2][0])+' '
			s1+=(key2+' ')
		Dir4[key]=0
		for i in Dir3[key]:
			Dir4[key]+=Dir2[eval(i)]
	fout.write('compute 1 all rdf 500\n')
	if len(steps)>1:
		fout.write('fix c1 all ave/time %d %d %d c_1[*] file rdf.dat mode vector\n' %(steps[1]-steps[0],int((steps[-1]-steps[0])/(steps[1]-steps[0])),steps[-1]-steps[0]))
	else:
		fout.write('fix c1 all ave/time 1 1 1 c_1[*] file rdf.dat mode vector\n')
	fout.write('\n')
	fout.write('compute 2 all rdf 500 %s\n' %s)
	if len(steps)>1:
		fout.write('fix c2 all ave/time %d %d %d c_2[*] file rdfpair.dat mode vector\n' %(steps[1]-steps[0],1,steps[1]-steps[0]))
	else:
		fout.write('fix c2 all ave/time 1 1 1 c_2[*] file rdfpair.dat mode vector\n')
	fout.write('\n')
	if xrd:
		fout.write('compute         XRD all xrd 1.54 %s 2Theta 2.5 40 LP 1 echo\n' %(' '.join([Dir[a] for a in sorted(Dir)])))
		if len(steps)>1:
			fout.write('fix f1 all ave/histo %d %d %d 2.5 40 350 c_XRD[1] c_XRD[2] mode vector file Deg2Theta.xrd #1 1 1\n' %(steps[1]-steps[0],int((steps[-1]-steps[0])/(steps[1]-steps[0])),steps[-1]-steps[0]))
		else:
			fout.write('fix f1 all ave/histo 1 1 1 2.5 40 350 c_XRD[1] c_XRD[2] mode vector file Deg2Theta.xrd #1 1 1\n')
		fout.write('\n')
	fout.write('special_bonds     lj/coul 1.0 1.0 1.0 dihedral yes\n')
	fout.write('rerun gen.dump dump type x y z box yes\n')
	fout.write('\n')
	fout.close()
	if rnp_flag:
		print('Calculating recommended number of processors')
		ppn=grabprocessors('minimize.in')
		print(ppn)
		nodes,ppn,np=correctppn(ppn)
		print('%d of processors will be in use' %np)
		ppn=grabprocessors('rdf.in')
		nodes,ppn,np=correctppn(ppn)
#	os.system('module load intel impi/5.1.2.150 lammps/15Feb16')
	print('Running LAMMPS to calculate RDF (Radial distribution function)')
	if np_flag:
		os.system('mpirun -np %d ./lmp_mpi < rdf.in' %np)
	else:
		os.system('./lmp_mpi < rdf.in')
	os.system('cp log.lammps log.rdf')
	return s1,denDir,Dir4


########################################################################################
##calculate 3D S(q)
def getSq(rdfdata,denDir,nq,qmax,numrow,sqfile,qmin=0.):
    r=[]
    g=[]
    fin = open(rdfdata,'r')
    words=string.split(rdfdata,'.')    
    fout = open(sqfile,'w')
    steps=sorted(denDir)
    SqDir={}
    for step in steps:
    	density=denDir[step]
    	dataline=fin.readline()
    	while dataline[0]=='#':
    		dataline=fin.readline()
    	words=string.split(dataline[0:len(dataline)-1])
        nbins=eval(words[1])
    	for i in range(nbins):
        	dataline=fin.readline()
        	words=string.split(dataline[0:len(dataline)-1])
        	ri=eval(words[1])
        	gi =eval(words[numrow])
        	r.append(ri)
        	g.append(gi)
		q=[]
    	Sq=[]
    	dr = r[2]-r[1]
    	dq = (qmax-qmin)/nq    
    	for i in range(nq):
        	qi = (i+0.5)*dq+qmin
        	Sqi = 0.0
        	q.append(qi)
        	Sq.append(Sqi)        
    	for i in range(nq):    
        	for j in range(nbins):
				Sq[i]+=r[j]*(g[j]-1.0)*sin(q[i]*r[j])/q[i]  ##why minus 1.0?
        	Sq[i]=1.0+4.0*pi*density*dr*Sq[i]
    	for i in range(nq):
    		if q[i] not in SqDir:
    			SqDir[q[i]]=0
    		SqDir[q[i]]+=Sq[i]
    l=len(steps)
    for i in range(nq):
    	print >>fout,q[i],SqDir[q[i]]/l
    fout.close()
###################################################################################


def calSq(denDir,pair):
    rdfdata="rdfpair.dat"
    nq=500
    qmax=16
    for i in range(pair):
        numrow=2*(i+1)
        sqdata=('rdfpair_%dsq.txt' %i)
        getSq(rdfdata,denDir,nq,qmax,numrow,sqdata)
#####################################################################################


def f(q,lst):
	fq=lst[8]
	for i in range(4):
		fq+=lst[i*2]*exp(-lst[i*2+1]*q*q/16/pi/pi)
	return fq


def inidatabase():
	database={}
	database['H']=[0.489918,20.6593,0.262003,7.74039,0.196767,49.5519,0.049879,2.20159,0.001305]
	database['H1-']=[0.897661,53.1368,0.565616,15.187,0.415815,186.576,0.116973,3.56709,0.002389]
	database['He']=[0.8734,9.1037,0.6309,3.3568,0.3112,22.9276,0.178,0.9821,0.0064]
	database['Li']=[1.1282,3.9546,0.7508,1.0524,0.6175,85.3905,0.4653,168.261,0.0377]
	database['Li1+']=[0.6968,4.6237,0.7888,1.9557,0.3414,0.6316,0.1563,10.0953,0.0167]
	database['Be']=[1.5919,43.6427,1.1278,1.8623,0.5391,103.483,0.7029,0.542,0.0385]
	database['Be2+']=[6.2603,0.0027,0.8849,0.8313,0.7993,2.2758,0.1647,5.1146,-6.1092]
	database['B']=[2.0545,23.2185,1.3326,1.021,1.0979,60.3498,0.7068,0.1403,-0.1932]
	database['C']=[2.31,20.8439,1.02,10.2075,1.5886,0.5687,0.865,51.6512,0.2156]
	database['Cval']=[2.26069,22.6907,1.56165,0.656665,1.05075,9.75618,0.839259,55.5949,0.286977]
	database['N']=[12.2126,0.0057,3.1322,9.8933,2.0125,28.9975,1.1663,0.5826,-11.529]
	database['O']=[3.0485,13.2771,2.2868,5.7011,1.5463,0.3239,0.867,32.9089,0.2508]
	database['O1-']=[4.1916,12.8573,1.63969,4.17236,1.52673,47.0179,-20.307,-0.01404,21.9412]
	database['F']=[3.5392,10.2825,2.6412,4.2944,1.517,0.2615,1.0243,26.1476,0.2776]
	database['F1-']=[3.6322,5.27756,3.51057,14.7353,1.26064,0.442258,0.940706,47.3437,0.653396]
	database['Ne']=[3.9553,8.4042,3.1125,3.4262,1.4546,0.2306,1.1251,21.7184,0.3515]
	database['Na']=[4.7626,3.285,3.1736,8.8422,1.2674,0.3136,1.1128,129.424,0.676]
	database['Na1+']=[3.2565,2.6671,3.9362,6.1153,1.3998,0.2001,1.0032,14.039,0.404]
	database['Mg']=[5.4204,2.8275,2.1735,79.2611,1.2269,0.3808,2.3073,7.1937,0.8584]
	database['Mg2+']=[3.4988,2.1676,3.8378,4.7542,1.3284,0.185,0.8497,10.1411,0.4853]
	database['Al']=[6.4202,3.0387,1.9002,0.7426,1.5936,31.5472,1.9646,85.0886,1.1151]
	database['Al3+']=[4.17448,1.93816,3.3876,4.14553,1.20296,0.228753,0.528137,8.28524,0.706786]
	database['Siv']=[6.2915,2.4386,3.0353,32.3337,1.9891,0.6785,1.541,81.6937,1.1407]
	database['Sival']=[5.66269,2.6652,3.07164,38.6634,2.62446,0.916946,1.3932,93.5458,1.24707]
	database['Si4+']=[4.43918,1.64167,3.20345,3.43757,1.19453,0.2149,0.41653,6.65365,0.746297]
	database['P']=[6.4345,1.9067,4.1791,27.157,1.78,0.526,1.4908,68.1645,1.1149]
	database['S']=[6.9053,1.4679,5.2034,22.2151,1.4379,0.2536,1.5863,56.172,0.8669]
	database['Cl']=[11.4604,0.0104,7.1964,1.1662,6.2556,18.5194,1.6455,47.7784,-9.5574]
	database['Cl1-']=[18.2915,0.0066,7.2084,1.1717,6.5337,19.5424,2.3386,60.4486,-16.378]
	database['Ar']=[7.4845,0.9072,6.7723,14.8407,0.6539,43.8983,1.6442,33.3929,1.4445]
	database['K']=[8.2186,12.7949,7.4398,0.7748,1.0519,213.187,0.8659,41.6841,1.4228]
	database['K1+']=[7.9578,12.6331,7.4917,0.7674,6.359,-0.002,1.1915,31.9128,-4.9978]
	database['Ca']=[8.6266,10.4421,7.3873,0.6599,1.5899,85.7484,1.0211,178.437,1.3751]
	database['Ca2+']=[15.6348,-0.0074,7.9518,0.6089,8.4372,10.3116,0.8537,25.9905,-14.875]
	database['Sc']=[9.189,9.0213,7.3679,0.5729,1.6409,136.108,1.468,51.3531,1.3329]
	database['Sc3+']=[13.4008,0.29854,8.0273,7.9629,1.65943,-0.28604,1.57936,16.0662,-6.6667]
	database['Ti']=[9.7595,7.8508,7.3558,0.5,1.6991,35.6338,1.9021,116.105,1.2807]
	database['Ti2+']=[9.11423,7.5243,7.62174,0.457585,2.2793,19.5361,0.087899,61.6558,0.897155]
	database['Ti3+']=[17.7344,0.22061,8.73816,7.04716,5.25691,-0.15762,1.92134,15.9768,-14.652]
	database['Ti4+']=[19.5114,0.178847,8.23473,6.67018,2.01341,-0.29263,1.5208,12.9464,-13.28]
	database['V']=[10.2971,6.8657,7.3511,0.4385,2.0703,26.8938,2.0571,102.478,1.2199]
	database['V2+']=[10.106,6.8818,7.3541,0.4409,2.2884,20.3004,0.0223,115.122,1.2298]
	database['V3+']=[9.43141,6.39535,7.7419,0.383349,2.15343,15.1908,0.016865,63.969,0.656565]
	database['V5+']=[15.6887,0.679003,8.14208,5.40135,2.03081,9.97278,-9.576,0.940464,1.7143]
	database['Cr']=[10.6406,6.1038,7.3537,0.392,3.324,20.2626,1.4922,98.7399,1.1832]
	database['Cr2+']=[9.54034,5.66078,7.7509,0.344261,3.58274,13.3075,0.509107,32.4224,0.616898]
	database['Cr3+']=[9.6809,5.59463,7.81136,0.334393,2.87603,12.8288,0.113575,32.8761,0.518275]
	database['Mn']=[11.2819,5.3409,7.3573,0.3432,3.0193,17.8674,2.2441,83.7543,1.0896]
	database['Mn2+']=[10.8061,5.2796,7.362,0.3435,3.5268,14.343,0.2184,41.3235,1.0874]
	database['Mn3+']=[9.84521,4.91797,7.87194,0.294393,3.56531,10.8171,0.323613,24.1281,0.393974]
	database['Mn4+']=[9.96253,4.8485,7.97057,0.283303,2.76067,10.4852,0.054447,27.573,0.251877]
	database['Fe']=[11.7695,4.7611,7.3573,0.3072,3.5222,15.3535,2.3045,76.8805,1.0369]
	database['Fe2+']=[11.0424,4.6538,7.374,0.3053,4.1346,12.0546,0.4399,31.2809,1.0097]
	database['Fe3+']=[11.1764,4.6147,7.3863,0.3005,3.3948,11.6729,0.0724,38.5566,0.9707]
	database['Co']=[12.2841,4.2791,7.3409,0.2784,4.0034,13.5359,2.3488,71.1692,1.0118]
	database['Co2+']=[11.2296,4.1231,7.3883,0.2726,4.7393,10.2443,0.7108,25.6466,0.9324]
	database['Co3+']=[10.338,3.90969,7.88173,0.238668,4.76795,8.35583,0.725591,18.3491,0.286667]
	database['Ni']=[12.8376,3.8785,7.292,0.2565,4.4438,12.1763,2.38,66.3421,1.0341]
	database['Ni2+']=[11.4166,3.6766,7.4005,0.2449,5.3442,8.873,0.9773,22.1626,0.8614]
	database['Ni3+']=[10.7806,3.5477,7.75868,0.22314,5.22746,7.64468,0.847114,16.9673,0.386044]
	database['Cu']=[13.338,3.5828,7.1676,0.247,5.6158,11.3966,1.6735,64.8126,1.191]
	database['Cu1+']=[11.9475,3.3669,7.3573,0.2274,6.2455,8.6625,1.5578,25.8487,0.89]
	database['Cu2+']=[11.8168,3.37484,7.11181,0.244078,5.78135,7.9876,1.14523,19.897,1.14431]
	database['Zn']=[14.0743,3.2655,7.0318,0.2333,5.1652,10.3163,2.41,58.7097,1.3041]
	database['Zn2+']=[11.9719,2.9946,7.3862,0.2031,6.4668,7.0826,1.394,18.0995,0.7807]
	database['Ga']=[15.2354,3.0669,6.7006,0.2412,4.3591,10.7805,2.9623,61.4135,1.7189]
	database['Ga3+']=[12.692,2.81262,6.69883,0.22789,6.06692,6.36441,1.0066,14.4122,1.53545]
	database['Ge']=[16.0816,2.8509,6.3747,0.2516,3.7068,11.4468,3.683,54.7625,2.1313]
	database['Ge4+']=[12.9172,2.53718,6.70003,0.205855,6.06791,5.47913,0.859041,11.603,1.45572]
	database['As']=[16.6723,2.6345,6.0701,0.2647,3.4313,12.9479,4.2779,47.7972,2.531]
	database['Se']=[17.0006,2.4098,5.8196,0.2726,3.9731,15.2372,4.3543,43.8163,2.8409]
	database['Br']=[17.1789,2.1723,5.2358,16.5796,5.6377,0.2609,3.9851,41.4328,2.9557]
	database['Br1-']=[17.1718,2.2059,6.3338,19.3345,5.5754,0.2871,3.7272,58.1535,3.1776]
	database['Kr']=[17.3555,1.9384,6.7286,16.5623,5.5493,0.2261,3.5375,39.3972,2.825]
	database['Rb']=[17.1784,1.7888,9.6435,17.3151,5.1399,0.2748,1.5292,164.934,3.4873]
	database['Rb1+']=[17.5816,1.7139,7.6598,14.7957,5.8981,0.1603,2.7817,31.2087,2.0782]
	database['Sr']=[17.5663,1.5564,9.8184,14.0988,5.422,0.1664,2.6694,132.376,2.5064]
	database['Sr2+']=[18.0874,1.4907,8.1373,12.6963,2.5654,24.5651,-34.193,-0.0138,41.4025]
	database['Y']=[17.776,1.4029,10.2946,12.8006,5.72629,0.125599,3.26588,104.354,1.91213]
	database['Y3+']=[17.9268,1.35417,9.1531,11.2145,1.76795,22.6599,-33.108,-0.01319,40.2602]
	database['Zr']=[17.8765,1.27618,10.948,11.916,5.41732,0.117622,3.65721,87.6627,2.06929]
	database['Zr4+']=[18.1668,1.2148,10.0562,10.1483,1.01118,21.6054,-2.6479,-0.10276,9.41454]
	database['Nb']=[17.6142,1.18865,12.0144,11.766,4.04183,0.204785,3.53346,69.7957,3.75591]
	database['Nb3+']=[19.8812,0.019175,18.0653,1.13305,11.0177,10.1621,1.94715,28.3389,-12.912]
	database['Nb5+']=[17.9163,1.12446,13.3417,0.028781,10.799,9.28206,0.337905,25.7228,-6.3934]
	database['Mo']=[3.7025,0.2772,17.2356,1.0958,12.8876,11.004,3.7429,61.6584,4.3875]
	database['Mo3+']=[21.1664,0.014734,18.2017,1.03031,11.7423,9.53659,2.30951,26.6307,-14.421]
	database['Mo5+']=[21.0149,0.014345,18.0992,1.02238,11.4632,8.78809,0.740625,23.3452,-14.316]
	database['Mo6+']=[17.8871,1.03649,11.175,8.48061,6.57891,0.058881,0,0,0.344941]
	database['Tc']=[19.1301,0.864132,11.0948,8.14487,4.64901,21.5707,2.71263,86.8472,5.40428]
	database['Ru']=[19.2674,0.80852,12.9182,8.43467,4.86337,24.7997,1.56756,94.2928,5.37874]
	database['Ru3+']=[18.5638,0.847329,13.2885,8.37164,9.32602,0.017662,3.00964,22.887,-3.1892]
	database['Ru4+']=[18.5003,0.844582,13.1787,8.12534,4.71304,0.36495,2.18535,20.8504,1.42357]
	database['Rh']=[19.2957,0.751536,14.3501,8.21758,4.73425,25.8749,1.28918,98.6062,5.328]
	database['Rh3+']=[18.8785,0.764252,14.1259,7.84438,3.32515,21.2487,-6.1989,-0.01036,11.8678]
	database['Rh4+']=[18.8545,0.760825,13.9806,7.62436,2.53464,19.3317,-5.6526,-0.0102,11.2835]
	database['Pd']=[19.3319,0.698655,15.5017,7.98929,5.29537,25.2052,0.605844,76.8986,5.26593]
	database['Pd2+']=[19.1701,0.696219,15.2096,7.55573,4.32234,22.5057,0,0,5.2916]
	database['Pd4+']=[19.2493,0.683839,14.79,7.14833,2.89289,17.9144,-7.9492,0.005127,13.0174]
	database['Ag']=[19.2808,0.6446,16.6885,7.4726,4.8045,24.6605,1.0463,99.8156,5.179]
	database['Ag1+']=[19.1812,0.646179,15.9719,7.19123,5.27475,21.7326,0.357534,66.1147,5.21572]
	database['Ag2+']=[19.1643,0.645643,16.2456,7.18544,4.3709,21.4072,0,0,5.21404]
	database['Cd']=[19.2214,0.5946,17.6444,6.9089,4.461,24.7008,1.6029,87.4825,5.0694]
	database['Cd2+']=[19.1514,0.597922,17.2535,6.80639,4.47128,20.2521,0,0,5.11937]
	database['In']=[19.1624,0.5476,18.5596,6.3776,4.2948,25.8499,2.0396,92.8029,4.9391]
	database['In3+']=[19.1045,0.551522,18.1108,6.3247,3.78897,17.3595,0,0,4.99635]
	database['Sn']=[19.1889,5.8303,19.1005,0.5031,4.4585,26.8909,2.4663,83.9571,4.7821]
	database['Sn2+']=[19.1094,0.5036,19.0548,5.8378,4.5648,23.3752,0.487,62.2061,4.7861]
	database['Sn4+']=[18.9333,5.764,19.7131,0.4655,3.4182,14.0049,0.0193,-0.7583,3.9182]
	database['Sb']=[19.6418,5.3034,19.0455,0.4607,5.0371,27.9074,2.6827,75.2825,4.5909]
	database['Sb3+']=[18.9755,0.467196,18.933,5.22126,5.10789,19.5902,0.288753,55.5113,4.69626]
	database['Sb5+']=[19.8685,5.44853,19.0302,0.467973,2.41253,14.1259,0,0,4.69263]
	database['Te']=[19.9644,4.81742,19.0138,0.420885,6.14487,28.5284,2.5239,70.8403,4.352]
	database['I']=[20.1472,4.347,18.9949,0.3814,7.5138,27.766,2.2735,66.8776,4.0712]
	database['I1-']=[20.2332,4.3579,18.997,0.3815,7.8069,29.5259,2.8868,84.9304,4.0714]
	database['Xe']=[20.2933,3.9282,19.0298,0.344,8.9767,26.4659,1.99,64.2658,3.7118]
	database['Cs']=[20.3892,3.569,19.1062,0.3107,10.662,24.3879,1.4953,213.904,3.3352]
	database['Cs1+']=[20.3524,3.552,19.1278,0.3086,10.2821,23.7128,0.9615,59.4565,3.2791]
	database['Ba']=[20.3361,3.216,19.297,0.2756,10.888,20.2073,2.6959,167.202,2.7731]
	database['Ba2+']=[20.1807,3.21367,19.1136,0.28331,10.9054,20.0558,0.77634,51.746,3.02902]
	database['La']=[20.578,2.94817,19.599,0.244475,11.3727,18.7726,3.28719,133.124,2.14678]
	database['La3+']=[20.2489,2.9207,19.3763,0.250698,11.6323,17.8211,0.336048,54.9453,2.4086]
	database['Ce']=[21.1671,2.81219,19.7695,0.226836,11.8513,17.6083,3.33049,127.113,1.86264]
	database['Ce3+']=[20.8036,2.77691,19.559,0.23154,11.9369,16.5408,0.612376,43.1692,2.09013]
	database['Ce4+']=[20.3235,2.65941,19.8186,0.21885,12.1233,15.7992,0.144583,62.2355,1.5918]
	database['Pr']=[22.044,2.77393,19.6697,0.222087,12.3856,16.7669,2.82428,143.644,2.0583]
	database['Pr3+']=[21.3727,2.6452,19.7491,0.214299,12.1329,15.323,0.97518,36.4065,1.77132]
	database['Pr4+']=[20.9413,2.54467,20.0539,0.202481,12.4668,14.8137,0.296689,45.4643,1.24285]
	database['Nd']=[22.6845,2.66248,19.6847,0.210628,12.774,15.885,2.85137,137.903,1.98486]
	database['Nd3+']=[21.961,2.52722,19.9339,0.199237,12.12,14.1783,1.51031,30.8717,1.47588]
	database['Pm']=[23.3405,2.5627,19.6095,0.202088,13.1235,15.1009,2.87516,132.721,2.02876]
	database['Pm3+']=[22.5527,2.4174,20.1108,0.185769,12.0671,13.1275,2.07492,27.4491,1.19499]
	database['Sm']=[24.0042,2.47274,19.4258,0.196451,13.4396,14.3996,2.89604,128.007,2.20963]
	database['Sm3+']=[23.1504,2.31641,20.2599,0.174081,11.9202,12.1571,2.71488,24.8242,0.954586]
	database['Eu']=[24.6274,2.3879,19.0886,0.1942,13.7603,13.7546,2.9227,123.174,2.5745]
	database['Eu2+']=[24.0063,2.27783,19.9504,0.17353,11.8034,11.6096,3.87243,26.5156,1.36389]
	database['Eu3+']=[23.7497,2.22258,20.3745,0.16394,11.8509,11.311,3.26503,22.9966,0.759344]
	database['Gd']=[25.0709,2.25341,19.0798,0.181951,13.8518,12.9331,3.54545,101.398,2.4196]
	database['Gd3+']=[24.3466,2.13553,20.4208,0.155525,11.8708,10.5782,3.7149,21.7029,0.645089]
	database['Tb']=[25.8976,2.24256,18.2185,0.196143,14.3167,12.6648,2.95354,115.362,3.58324]
	database['Tb3+']=[24.9559,2.05601,20.3271,0.149525,12.2471,10.0499,3.773,21.2773,0.691967]
	database['Dy']=[26.507,2.1802,17.6383,0.202172,14.5596,12.1899,2.96577,111.874,4.29728]
	database['Dy3+']=[25.5395,1.9804,20.2861,0.143384,11.9812,9.34972,4.50073,19.581,0.68969]
	database['Ho']=[26.9049,2.07051,17.294,0.19794,14.5583,11.4407,3.63837,92.6566,4.56796]
	database['Ho3+']=[26.1296,1.91072,20.0994,0.139358,11.9788,8.80018,4.93676,18.5908,0.852795]
	database['Er']=[27.6563,2.07356,16.4285,0.223545,14.9779,11.3604,2.98233,105.703,5.92046]
	database['Er3+']=[26.722,1.84659,19.7748,0.13729,12.1506,8.36225,5.17379,17.8974,1.17613]
	database['Tm']=[28.1819,2.02859,15.8851,0.238849,15.1542,10.9975,2.98706,102.961,6.75621]
	database['Tm3+']=[27.3083,1.78711,19.332,0.136974,12.3339,7.96778,5.38348,17.2922,1.63929]
	database['Yb']=[28.6641,1.9889,15.4345,0.257119,15.3087,10.6647,2.98963,100.417,7.56672]
	database['Yb2+']=[28.1209,1.78503,17.6817,0.15997,13.3335,8.18304,5.14657,20.39,3.70983]
	database['Yb3+']=[27.8917,1.73272,18.7614,0.13879,12.6072,7.64412,5.47647,16.8153,2.26001]
	database['Lu']=[28.9476,1.90182,15.2208,9.98519,15.1,0.261033,3.71601,84.3298,7.97628]
	database['Lu3+']=[28.4628,1.68216,18.121,0.142292,12.8429,7.33727,5.59415,16.3535,2.97573]
	database['Hf']=[29.144,1.83262,15.1726,9.5999,14.7586,0.275116,4.30013,72.029,8.58154]
	database['Hf4+']=[28.8131,1.59136,18.4601,0.128903,12.7285,6.76232,5.59927,14.0366,2.39699]
	database['Ta']=[29.2024,1.77333,15.2293,9.37046,14.5135,0.295977,4.76492,63.3644,9.24354]
	database['Ta5+']=[29.1587,1.50711,18.8407,0.116741,12.8268,6.31524,5.38695,12.4244,1.78555]
	database['W']=[29.0818,1.72029,15.43,9.2259,14.4327,0.321703,5.11982,57.056,9.8875]
	database['W6+']=[29.4936,1.42755,19.3763,0.104621,13.0544,5.93667,5.06412,11.1972,1.01074]
	database['Re']=[28.7621,1.67191,15.7189,9.09227,14.5564,0.3505,5.44174,52.0861,10.472]
	database['Os']=[28.1894,1.62903,16.155,8.97948,14.9305,0.382661,5.67589,48.1647,11.0005]
	database['Os4+']=[30.419,1.37113,15.2637,6.84706,14.7458,0.165191,5.06795,18.003,6.49804]
	database['Ir']=[27.3049,1.59279,16.7296,8.86553,15.6115,0.417916,5.83377,45.0011,11.4722]
	database['Ir3+']=[30.4156,1.34323,15.862,7.10909,13.6145,0.204633,5.82008,20.3254,8.27903]
	database['Ir4+']=[30.7058,1.30923,15.5512,6.71983,14.2326,0.167252,5.53672,17.4911,6.96824]
	database['Pt']=[27.0059,1.51293,17.7639,8.81174,15.7131,0.424593,5.7837,38.6103,11.6883]
	database['Pt2+']=[29.8429,1.32927,16.7224,7.38979,13.2153,0.263297,6.35234,22.9426,9.85329]
	database['Pt4+']=[30.9612,1.24813,15.9829,6.60834,13.7348,0.16864,5.92034,16.9392,7.39534]
	database['Au']=[16.8819,0.4611,18.5913,8.6216,25.5582,1.4826,5.86,36.3956,12.0658]
	database['Au1+']=[28.0109,1.35321,17.8204,7.7395,14.3359,0.356752,6.58077,26.4043,11.2299]
	database['Au3+']=[30.6886,1.2199,16.9029,6.82872,12.7801,0.212867,6.52354,18.659,9.0968]
	database['Hg']=[20.6809,0.545,19.0417,8.4484,21.6575,1.5729,5.9676,38.3246,12.6089]
	database['Hg1+']=[25.0853,1.39507,18.4973,7.65105,16.8883,0.443378,6.48216,28.2262,12.0205]
	database['Hg2+']=[29.5641,1.21152,18.06,7.05639,12.8374,0.284738,6.89912,20.7482,10.6268]
	database['Tl']=[27.5446,0.65515,19.1584,8.70751,15.538,1.96347,5.52593,45.8149,13.1746]
	database['Tl1+']=[21.3985,1.4711,20.4723,0.517394,18.7478,7.43463,6.82847,28.8482,12.5258]
	database['Tl3+']=[30.8695,1.1008,18.3481,6.53852,11.9328,0.219074,7.00574,17.2114,9.8027]
	database['Pb']=[31.0617,0.6902,13.0637,2.3576,18.442,8.618,5.9696,47.2579,13.4118]
	database['Pb2+']=[21.7886,1.3366,19.5682,0.488383,19.1406,6.7727,7.01107,23.8132,12.4734]
	database['Pb4+']=[32.1244,1.00566,18.8003,6.10926,12.0175,0.147041,6.96886,14.714,8.08428]
	database['Bi']=[33.3689,0.704,12.951,2.9238,16.5877,8.7937,6.4692,48.0093,13.5782]
	database['Bi3+']=[21.8053,1.2356,19.5026,6.24149,19.1053,0.469999,7.10295,20.3185,12.4711]
	database['Bi5+']=[33.5364,0.91654,25.0946,0.39042,19.2497,5.71414,6.91555,12.8285,-6.7994]
	database['Po']=[34.6726,0.700999,15.4733,3.55078,13.1138,9.55642,7.02588,47.0045,13.677]
	database['At']=[35.3163,0.68587,19.0211,3.97458,9.49887,11.3824,7.42518,45.4715,13.7108]
	database['Rn']=[35.5631,0.6631,21.2816,4.0691,8.0037,14.0422,7.4433,44.2473,13.6905]
	database['Fr']=[35.9299,0.646453,23.0547,4.17619,12.1439,23.1052,2.11253,150.645,13.7247]
	database['Ra']=[35.763,0.616341,22.9064,3.87135,12.4739,19.9887,3.21097,142.325,13.6211]
	database['Ra2+']=[35.215,0.604909,21.67,3.5767,7.91342,12.601,7.65078,29.8436,13.5431]
	database['Ac']=[35.6597,0.589092,23.1032,3.65155,12.5977,18.599,4.08655,117.02,13.5266]
	database['Ac3+']=[35.1736,0.579689,22.1112,3.41437,8.19216,12.9187,7.05545,25.9443,13.4637]
	database['Th']=[35.5645,0.563359,23.4219,3.46204,12.7473,17.8309,4.80703,99.1722,13.4314]
	database['Th4+']=[35.1007,0.555054,22.4418,3.24498,9.78554,13.4661,5.29444,23.9533,13.376]
	database['Pa']=[35.8847,0.547751,23.2948,3.41519,14.1891,16.9235,4.17287,105.251,13.4287]
	database['U']=[36.0228,0.5293,23.4128,3.3253,14.9491,16.0927,4.188,100.613,13.3966]
	database['U3+']=[35.5747,0.52048,22.5259,3.12293,12.2165,12.7148,5.37073,26.3394,13.3092]
	database['U4+']=[35.3715,0.516598,22.5326,3.05053,12.0291,12.5723,4.7984,23.4582,13.2671]
	database['U6+']=[34.8509,0.507079,22.7584,2.8903,14.0099,13.1767,1.21457,25.2017,13.1665]
	database['Np']=[36.1874,0.511929,23.5964,3.25396,15.6402,15.3622,4.1855,97.4908,13.3573]
	database['Np3+']=[35.7074,0.502322,22.613,3.03807,12.9898,12.1449,5.43227,25.4928,13.2544]
	database['Np4+']=[35.5103,0.498626,22.5787,2.96627,12.7766,11.9484,4.92159,22.7502,13.2116]
	database['Np6+']=[35.0136,0.48981,22.7286,2.81099,14.3884,12.33,1.75669,22.6581,13.113]
	database['Pu']=[36.5254,0.499384,23.8083,3.26371,16.7707,14.9455,3.47947,105.98,13.3812]
	database['Pu3+']=[35.84,0.484938,22.7169,2.96118,13.5807,11.5331,5.66016,24.3992,13.1991]
	database['Pu4+']=[35.6493,0.481422,22.646,2.8902,13.3595,11.316,5.18831,21.8301,13.1555]
	database['Pu6+']=[35.1736,0.473204,22.7181,2.73848,14.7635,11.553,2.28678,20.9303,13.0582]
	database['Am']=[36.6706,0.483629,24.0992,3.20647,17.3415,14.3136,3.49331,102.273,13.3592]
	database['Cm']=[36.6488,0.465154,24.4096,3.08997,17.399,13.4346,4.21665,88.4834,13.2887]
	database['Bk']=[36.7881,0.451018,24.7736,3.04619,17.8919,12.8946,4.23284,86.003,13.2754]
	database['Cf']=[36.9185,0.437533,25.1995,3.00775,18.3317,12.4044,4.24391,83.7881,13.2674]
	return database


def inineutronbase():
	database={}
	database['H']=-3.7390
	database['1H']=-3.7406
	database['2H']=6.671
	database['3H']=4.792
	database['He']=3.26
	database['3He']=5.74-1.483j
	database['4He']=3.26
	database['Li']=-1.90
	database['6Li']=2.00-0.261j
	database['7Li']=-2.22
	database['Be']=7.79
	database['B']=5.30-0.213j
	database['10B']=-0.1-1.066j
	database['11B']=6.65
	database['C']=6.6460
	database['12C']=6.6511
	database['13C']=6.19
	database['N']=9.36
	database['14N']=9.37
	database['15N']=6.44
	database['O']=5.803
	database['16O']=5.803
	database['17O']=5.78
	database['18O']=5.84
	database['F']=5.654
	database['Ne']=4.566
	database['20Ne']=4.631
	database['21Ne']=6.66
	database['22Ne']=3.87
	database['Na']=3.63
	database['Mg']=5.375
	database['24Mg']=5.66
	database['25Mg']=3.62
	database['26Mg']=4.89
	database['Al']=3.449
	database['Si']=4.1491
	database['28Si']=4.107
	database['29Si']=4.70
	database['30Si']=4.58
	database['P']=5.13
	database['S']=2.847
	database['32S']=2.804
	database['33S']=4.74
	database['34S']=3.48
	database['36S']=3.
	database['Cl']=9.5770
	database['35Cl']=11.65
	database['37Cl']=3.08
	database['Ar']=1.909
	database['36Ar']=24.90
	database['38Ar']=3.5
	database['40Ar']=1.830
	database['K']=3.67
	database['39K']=3.74
	database['40K']=3.
	database['41K']=2.69
	database['Ca']=4.70
	database['40Ca']=4.80
	database['42Ca']=3.36
	database['43Ca']=-1.56
	database['44Ca']=1.42
	database['46Ca']=3.6
	database['48Ca']=0.39
	database['Sc']=12.29
	database['Ti']=-3.438
	database['46Ti']=4.93
	database['47Ti']=3.63
	database['48Ti']=-6.08
	database['49Ti']=1.04
	database['50Ti']=6.18
	database['V']=-0.3824
	database['50V']=7.6
	database['51V']=-0.402
	database['Cr']=3.635
	database['50Cr']=-4.50
	database['52Cr']=4.920
	database['53Cr']=-4.20
	database['54Cr']=4.55
	database['Mn']=-3.73
	database['Fe']=9.45
	database['54Fe']=4.2
	database['56Fe']=9.94
	database['57Fe']=2.3
	database['58Fe']=15.
	database['Co']=2.49
	database['Ni']=10.3
	database['58Ni']=14.4
	database['60Ni']=2.8
	database['61Ni']=7.60
	database['62Ni']=-8.7
	database['64Ni']=-0.37
	database['Cu']=7.718
	database['63Cu']=6.43
	database['65Cu']=10.61
	database['Zn']=5.680
	database['64Zn']=5.22
	database['66Zn']=5.97
	database['67Zn']=7.56
	database['68Zn']=6.03
	database['70Zn']=6.
	database['Ga']=7.288
	database['69Ga']=7.88
	database['71Ga']=6.40
	database['Ge']=8.185
	database['70Ge']=10.0
	database['72Ge']=8.51
	database['73Ge']=5.02
	database['74Ge']=7.58
	database['76Ge']=8.2
	database['As']=6.58
	database['Se']=7.970
	database['74Se']=0.8
	database['76Se']=12.2
	database['77Se']=8.25
	database['78Se']=8.24
	database['80Se']=7.48
	database['82Se']=6.34
	database['Br']=6.795
	database['79Br']=6.80
	database['81Br']=6.79
	database['Kr']=7.81
	database['86Kr']=8.1
	database['Rb']=7.09
	database['85Rb']=7.03
	database['87Rb']=7.23
	database['Sr']=7.02
	database['84Sr']=7.
	database['86Sr']=5.67
	database['87Sr']=7.40
	database['88Sr']=7.15
	database['Y']=7.75
	database['Zr']=7.16
	database['90Zr']=6.4
	database['91Zr']=8.7
	database['92Zr']=7.4
	database['94Zr']=8.2
	database['96Zr']=5.5
	database['Nb']=7.054
	database['Mo']=6.715
	database['92Mo']=6.91
	database['94Mo']=6.80
	database['95Mo']=6.91
	database['96Mo']=6.20
	database['97Mo']=7.24
	database['98Mo']=6.58
	database['100Mo']=6.73
	database['Tc']=6.8
	database['Ru']=7.03
	database['Rh']=5.88
	database['Pd']=5.91
	database['102Pd']=7.7
	database['104Pd']=7.7
	database['105Pd']=5.5
	database['106Pd']=6.4
	database['108Pd']=4.1
	database['110Pd']=7.7
	database['Ag']=5.922
	database['107Ag']=7.555
	database['109Ag']=4.165
	database['Cd']=4.87-0.70j
	database['106Cd']=5.
	database['108Cd']=5.4
	database['110Cd']=5.9
	database['111Cd']=6.5
	database['112Cd']=6.4
	database['113Cd']=-8.0-5.73j
	database['114Cd']=7.5
	database['116Cd']=6.3
	database['In']=4.065-0.0539j
	database['113In']=5.39
	database['115In']=4.01-0.0562j
	database['Sn']=6.225
	database['112Sn']=6.
	database['114Sn']=6.2
	database['115Sn']=6.
	database['116Sn']=5.93
	database['117Sn']=6.48
	database['118Sn']=6.07
	database['119Sn']=6.12
	database['120Sn']=6.49
	database['122Sn']=5.74
	database['124Sn']=5.97
	database['Sb']=5.57
	database['121Sb']=5.71
	database['123Sb']=5.38
	database['Te']=5.80
	database['120Te']=5.3
	database['122Te']=3.8
	database['123Te']=-0.05-0.116j
	database['124Te']=7.96
	database['125Te']=5.02
	database['126Te']=5.56
	database['128Te']=5.89
	database['130Te']=6.02
	database['I']=5.28
	database['Xe']=4.92
	database['Cs']=5.42
	database['Ba']=5.07
	database['130Ba']=-3.6
	database['132Ba']=7.8
	database['134Ba']=5.7
	database['135Ba']=4.67
	database['136Ba']=4.91
	database['137Ba']=6.83
	database['138Ba']=4.84
	database['La']=8.24
	database['138La']=8.
	database['139La']=8.24
	database['Ce']=4.84
	database['136Ce']=5.80
	database['138Ce']=6.70
	database['140Ce']=4.84
	database['142Ce']=4.75
	database['Pr']=4.58
	database['Nd']=7.69
	database['142Nd']=7.7
	database['143Nd']=14.
	database['144Nd']=2.8
	database['145Nd']=14.
	database['146Nd']=8.7
	database['148Nd']=5.7
	database['150Nd']=5.3
	database['Pm']=12.6
	database['Sm']=0.80-1.65j
	database['144Sm']=-3.
	database['147Sm']=14.
	database['148Sm']=-3.
	database['149Sm']=-19.2-11.7j
	database['150Sm']=14.
	database['152Sm']=-5.0
	database['154Sm']=9.3
	database['Eu']=7.22-1.26j
	database['151Eu']=6.13-2.53j
	database['153Eu']=8.22
	database['Gd']=6.5-13.82j
	database['152Gd']=10.
	database['154Gd']=10.
	database['155Gd']=6.0-17.0j
	database['156Gd']=6.3
	database['157Gd']=-1.14-71.9j
	database['158Gd']=9.
	database['160Gd']=9.15
	database['Tb']=7.38
	database['Dy']=16.9-0.276j
	database['156Dy']=6.1
	database['158Dy']=6.
	database['160Dy']=6.7
	database['161Dy']=10.3
	database['162Dy']=-1.4
	database['163Dy']=5.0
	database['164Dy']=49.4-0.79j
	database['Ho']=8.01
	database['Er']=7.79
	database['162Er']=8.8
	database['164Er']=8.2
	database['166Er']=10.6
	database['167Er']=3.0
	database['168Er']=7.4
	database['170Er']=9.6
	database['Tm']=7.07
	database['Yb']=12.43
	database['168Yb']=-4.07-0.62j
	database['170Yb']=6.77
	database['171Yb']=9.66
	database['172Yb']=9.43
	database['173Yb']=9.56
	database['174Yb']=19.3
	database['176Yb']=8.72
	database['Lu']=7.21
	database['175Lu']=7.24
	database['176Lu']=6.1-0.57j
	database['Hf']=7.7
	database['174Hf']=10.9
	database['176Hf']=6.61
	database['177Hf']=0.8
	database['178Hf']=5.9
	database['179Hf']=7.46
	database['180Hf']=13.2
	database['Ta']=6.91
	database['180Ta']=7.
	database['181Ta']=6.91
	database['W']=4.86
	database['180W']=5.
	database['182W']=6.97
	database['183W']=6.53
	database['184W']=7.48
	database['186W']=-0.72
	database['Re']=9.2
	database['185Re']=9.0
	database['187Re']=9.3
	database['Os']=10.7
	database['184Os']=10.
	database['186Os']=11.6
	database['187Os']=10.
	database['188Os']=7.6
	database['189Os']=10.7
	database['190Os']=11.0
	database['192Os']=11.5
	database['Ir']=10.6
	database['Pt']=9.60
	database['190Pt']=9.0
	database['192Pt']=9.9
	database['194Pt']=10.55
	database['195Pt']=8.83
	database['196Pt']=9.89
	database['198Pt']=7.8
	database['Au']=7.63
	database['Hg']=12.692
	database['196Hg']=30.3
	database['199Hg']=16.9
	database['Tl']=8.776
	database['203Tl']=6.99
	database['205Tl']=9.52
	database['Pb']=9.405
	database['204Pb']=9.90
	database['206Pb']=9.22
	database['207Pb']=9.28
	database['208Pb']=9.50
	database['Bi']=8.532
	database['Ra']=10.0
	database['Th']=10.31
	database['Pa']=9.1
	database['U']=8.417
	database['233U']=10.1
	database['234U']=12.4
	database['235U']=10.47
	database['238U']=8.402
	database['Np']=10.55
	database['238Pu']=14.1
	database['239Pu']=7.7
	database['240Pu']=3.5
	database['242Pu']=8.1
	database['Am']=8.3
	database['244Cm']=9.5
	database['246Cm']=9.3
	database['248Cm']=7.7
	return database


def calWeiSqneutron(s1,Dir4):
	fout=open('sqtotal_neutron.txt','w')
	database=inineutronbase()
	Dir={}
	s=s1.split()
	for i in range(len(s)/2):
		a=s[i*2]
		l=len(a)
		j=0
		t=''
		while j<l:
			while a[j].isdigit():
				t+=a[j]
				j+=1
			while j<l and a[j].isalpha():
				t+=a[j]
				j+=1
			break
		a=t
		b=s[i*2+1]
		l=len(b)
		j=0
		t=''
		while j<l:
			while b[j].isdigit():
				t+=b[j]
				j+=1
			while j<l and b[j].isalpha():
				t+=b[j]
				j+=1
			break
		b=t
		sqdata=('rdfpair_%dsq.txt' %i)
		fin = open(sqdata,'r')
		for line in fin.readlines():
			ln=line.split()
			if ln:
				if i==0:
					Dir[eval(ln[0])]=[]
					lala=Dir4[s[i*2]]*Dir4[s[i*2+1]]*database[a]*database[b]
					Dir[eval(ln[0])].append(lala)
					Dir[eval(ln[0])].append(eval(ln[1])*lala)
				else:
					lala=Dir4[s[i*2]]*Dir4[s[i*2+1]]*database[a]*database[b]
					Dir[eval(ln[0])][0]+=lala
					Dir[eval(ln[0])][1]+=eval(ln[1])*lala
		fin.close()
	Dir2=sorted(Dir)
	for key in Dir2:
		fout.write('%f %f\n' %(key,(Dir[key][1]/Dir[key][0]).real))
	fout.close()


def calWeiSqxrd(s1,Dir4):
	fout=open('sqtotal_xrd.txt','w')
	database=inidatabase()
	Dir={}
	s=s1.split()
	for i in range(len(s)/2):
		a=s[i*2]
		l=len(a)
		j=0
		t=''
		while a[j].isdigit():
			j+=1
		t=a[j:]
		a=t
		b=s[i*2+1]
		l=len(b)
		j=0
		t=''
		while b[j].isdigit():
			j+=1
		t=b[j:]
		b=t
		sqdata=('rdfpair_%dsq.txt' %i)
		fin = open(sqdata,'r')
		for line in fin.readlines():
			ln=line.split()
			if ln:
				if i==0:
					Dir[eval(ln[0])]=[]
					lala=Dir4[s[i*2]]*Dir4[s[i*2+1]]*f(eval(ln[0]),database[a])*f(eval(ln[0]),database[b])
					Dir[eval(ln[0])].append(lala)
					Dir[eval(ln[0])].append(eval(ln[1])*lala)
				else:
					lala=Dir4[s[i*2]]*Dir4[s[i*2+1]]*f(eval(ln[0]),database[a])*f(eval(ln[0]),database[b])
					Dir[eval(ln[0])][0]+=lala
					Dir[eval(ln[0])][1]+=eval(ln[1])*lala
		fin.close()
	Dir2=sorted(Dir)
	for key in Dir2:
		fout.write('%f %f\n' %(key,Dir[key][1]/Dir[key][0]))
	fout.close()


def calWeixrd(s1,Dir4):
	fout=open('xrdtotal.txt','w')
	database=inidatabase()
	Dir={}
	s=s1.split()
	for i in range(len(s)/2):
		sqdata=('rdfpair_%dxrd.txt' %i)
		fin = open(sqdata,'r')
		for line in fin.readlines():
			ln=line.split()
			if ln:
				if i==0:
					Dir[eval(ln[0])]=[]
					lala=Dir4[s[i*2]]*Dir4[s[i*2+1]]*f(eval(ln[0]),database[s[i*2]])*f(eval(ln[0]),database[s[i*2+1]])
					Dir[eval(ln[0])].append(lala)
					Dir[eval(ln[0])].append(eval(ln[1])*lala)
				else:
					lala=Dir4[s[i*2]]*Dir4[s[i*2+1]]*f(eval(ln[0]),database[s[i*2]])*f(eval(ln[0]),database[s[i*2+1]])
					Dir[eval(ln[0])][0]+=lala
					Dir[eval(ln[0])][1]+=eval(ln[1])*lala
	Dir2=sorted(Dir)
	for key in Dir2:
		fout.write('%f %f\n' %(key,Dir[key][1]))
	fout.close()


def calculation(np_flag=0,rnp_flag=0,np=1,sfac=0,xrd=0):
	print('Writing intermediate files to run LAMMPS')
	print('Writing LAMMPS data file')
	Dir,Dir2=datafile()
	print('Writing LAMMPS input file')
	s1,denDir,Dir4=lammpsfile(Dir,Dir2,np_flag=np_flag,rnp_flag=rnp_flag,np=np,xrd=xrd)
	if sfac:
		print('Doing fast Fourier transform')
		calSq(denDir,len(s1.split())/2)
		print('Calculating X-ray weighted Static structure factor')
		calWeiSqxrd(s1,Dir4)
		print('Calculating neutron weighted Static structure factor')
		calWeiSqneutron(s1,Dir4)
#	if xrd:
#		calxrd(den,len(s1.split())/2)
#	calWeixrd(s1,Dir4)


def calxrd(den,pair):
    rdfdata="rdfpair.dat"
    nq=350
    qmax=3.449
    qmin=0.284
    for i in range(pair):
        numrow=2*(i+1)
        sqdata=('rdfpair_%dxrd.txt' %i)
        getSq(rdfdata,den,nq,qmax,numrow,sqdata,qmin)


#calculation()

