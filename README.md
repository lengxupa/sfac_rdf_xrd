What is this?
---------------
This set of files and directories contains the code used to analyze structure information for atom trajectory. This code was written by Tongtong Shen (shen276@purdue.edu) at Purdue University, contributed by Saaketh Desai under the guidance of Prof. Alejandro Strachan. Contributions from Dr. Chunyu Li are greatly acknowledged.

What are the contents of this distribution?
-------------------------------------------
README ---- A brief overview of the distribution  
code ---- Directory containing the source code  
examples ---- Directory containing test examples  
analysis.sh ---- Executive file  

Using this code
----------------
This code executes by reading keywords from a input script (text file). Most keywords have default settings, which means you only need to use the keywords if you wish to change the default. For each example provided, copy the file to any location of your choice and cp the code directory and analysis.sh file.

Syntax:
-------

./analysis.sh inputfile

inputfile = name of input script (text file) to read in  
&nbsp;&nbsp;&nbsp;&nbsp;(please refer to *gen.in* in *examples* directory for format)  

zero or more keyword/arg pairs may be appended  
keyword = *element* or *sfac* or *rdf* or *xrd* or *atom_style* or *parallel*  
&nbsp;&nbsp;*element* arg = keyword to specify element information
&nbsp;&nbsp;&nbsp;&nbsp;Syntax: element N type1 type2 ... typeN  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*N* = # of element types  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*type1 type2 … typeN* = chemical symbol of each atom type
&nbsp;&nbsp;*sfac* arg = Static structure factor information to output   
&nbsp;&nbsp;*rdf* arg = Radial distribution function information to output  
&nbsp;&nbsp;*xrd* arg = X-ray powder diffraction information to output  
&nbsp;&nbsp;*atom_style* arg = LAMMPS data file atom style  
&nbsp;&nbsp;&nbsp;&nbsp;keyword = *full* or *charge* or *molecular*  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(See https://lammps.sandia.gov/doc/atom_style.html for more details)  
&nbsp;&nbsp;*parallel* arg = Running LAMMPS in parallel mode  
&nbsp;&nbsp;&nbsp;&nbsp;zero or more keyword/arg pairs may be appended  
&nbsp;&nbsp;&nbsp;&nbsp;keyword = *np*  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*np* value = # of processors request to run in parallel mode  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(This workflow will calculate recommenmded processors based on size of the polymers if this keyword is not used)  

Contacts
---------
If you have questions regarding this distribution or its use, please send an email to Tongtong Shen (shen276@purdue.edu).
