#Python 2.7 code to plot the required functions

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def plotXRD(filename,ofile):
    src=open(filename)
    des=open('tmp_'+filename,'w')
    for line in src.readlines():
        if len(line.split('#')[0].split())>2:
            if eval(line.split()[1])==350:
                continue
            des.write(line)
    src.close()
    des.close()
    fig = plt.figure()
    fig.add_axes()
    x,y = np.loadtxt('tmp_'+filename, usecols=(1,2), unpack=True)
    plt.title('Powder X-Ray Diffraction Pattern')
    plt.xlabel(r'$2\theta$ (degrees)')
    plt.ylabel('Intensity')
    plt.yticks([])
    plt.plot(x,y)
    pp = PdfPages(ofile)
    pp.savefig()
    pp.close()
    return


def plotSQ(filename,ofile,head):
    fig = plt.figure()
    fig.add_axes()
    x,y = np.loadtxt(filename, usecols=(0,1), unpack=True)
    plt.title(head)
    plt.xlabel('q')
    plt.ylabel('S(q)')
    plt.yticks([])
    plt.plot(x,y)
    pp = PdfPages(ofile)
    pp.savefig()
    pp.close()
    return


def plotRDF(filename,ofile):
    src=open(filename)
    des=open('tmp_'+filename,'w')
    for line in src.readlines():
        if len(line.split('#')[0].split())>2:
            des.write(line)
    src.close()
    des.close()
    fig = plt.figure()
    fig.add_axes()
    x,y = np.loadtxt('tmp_'+filename, usecols=(1,2), unpack=True)
    plt.title('Radial distribution function')
    plt.xlabel('Angstrom')
    plt.ylabel('Intensity')
    plt.yticks([])
    plt.plot(x,y)
    pp = PdfPages(ofile)
    pp.savefig()
    pp.close()

