#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
Created on 27-04-2012 18:43:25
@author: Maciej Chudak

Extracts band structure data from an Abinit .out file and writes it out
in csv format to stdout.  
Output data order:
path length, kx, ky, kz, one or more band energy values
'''
import re

# raw ('r') strings as regular expressions
regexps={"header":r"Eigenvalues \( *(\w+) *\) for nkpt= *([0-9]+) *k points:",
         "coords":r"kpt= +([\-0-9\.]+) +([\-0-9\.]+) +([\-0-9\.]+)",
         "value" :r"([\-0-9\.]+)"}


def find_datasets(file):
    '''
    Find each band structure dataset in a file and return it as a list of:
        1) the unit used (str, e.g. "Hartree"),
        2) number of k-points (str, e.g. "40"),
        3) list of lines of data, copied from the file.
    '''
    datasets=[]
    data_lines_ahead=0
    for line in file:
        if data_lines_ahead==0: # if not in a data block
            header=re.search(regexps["header"], line)
            if header:
                datasets.append(list(header.groups()))
                datasets[-1].append(list())
                # int()*2 because there are 2 lines per k point
                data_lines_ahead=int(header.groups()[1])*2
        else:                   # if in a data block
            datasets[-1][2].append(line)
            data_lines_ahead-=1
    return datasets


def convert_to_csv(dataset, ostream, name=None):
    from math import sqrt
    '''
    Converts the "dataset" object to csv and writes to "ostream", mentions
    the original file "name" in the first line.
    Arguments:
        - "dataset" should be returned by the "find_datasets" function,
        - "ostream" should be a csv.writer object.
    '''
    # write initial descriptive lines
    ostream.writerow([
" Band structure: file generated from Abinit "+name+" file. "])
    ostream.writerow([
" Eigenvalues ("+dataset[0]+") for nkpt= "+dataset[1]+" k points. "])
    ostream.writerow([
" Format: total path length, kx, ky, kz, one or more energy eigenvalues. "])

    # helper variables
    path_length=0.0     # total length of path in k-space
    out_line=[]         # temporal container for the next row to be written
    k=[0.0, 0.0, 0.0]   # value of current k, to compute the path_length
    k_old=None          # value of last k, also to compute the path_length

    # for each line of the extracted dataset
    for line in dataset[2]:
        coords=re.search(regexps['coords'], line)

        # if the processed line contains coordinates in k-space
        if coords:
            step_squared=0.0    # sum of squares of step components

            # initialise k_old variable (occurs once)
            if k_old is None:
                k_old=[0.0, 0.0, 0.0]
                for i in range(3):
                    k_old[i]=float(coords.groups()[i])

            # read current coordinates
            for i in range(3):
                k[i]=float(coords.groups()[i])
                step_squared+=(k[i]-k_old[i])**2

            path_length+=sqrt(step_squared)
            k_old=list(k)

            # write out to the temporal row container
            out_line.append(path_length)
            for i in range(3):
                out_line.append(k[i])

        # if not, then it should contain the energy eigenvalues
        else:
            for match in re.findall(regexps['value'], line):
                out_line.append(match)
            ostream.writerow(out_line)
            out_line=[]


if __name__=="__main__":
    import argparse, sys, csv
    
    # command line arguments parsing
    parser=argparse.ArgumentParser(description='Extract band structure data from '+
                                   'Abinit .out file as convenient .csv. Outputs '+
                                   'to stdout.')
    parser.add_argument('input_file', type=str, nargs=1,
                        help='path of the .out file')
    parser.add_argument('-c', type=str, nargs=1, metavar="choice", default="b",
    help='''method of choosing the dataset to process, possible values are:\n
    b - biggest (most k-points, last biggest is used in the case of a draw),\n
    l - last dataset (same as "-1"),\n
    any positive integer - dataset of this number will be used, 0 is the first\
    encountered in the file
    any negative integer - dataset of this number, counting from the end, will \
    be used: -1 is last, -2 previous, etc.
    Default is b.''')
    args=parser.parse_args()

    # find all the datasets
    with open(args.input_file[0], "r") as inf:
        datasets=find_datasets(inf)

    # check which dataset user requested
    if args.c=="b":
        # find the dataset with most k points
        requested_set=0
        for i in range(len(datasets)):
            if datasets[i][1]>datasets[requested_set][1]:
                requested_set=i
    elif args.c=="l":
        # choose the last one
        requested_set=-1
    else:
        # check if it's a number
        error_string="No such dataset: "+args.c[0]+\
            ". There are "+str(len(datasets))+" sets, so correct -c "+\
            "values are:"+"'b', 'l', or any number from "+\
            str(-len(datasets))+" to "+str(len(datasets)-1)+"."
        try:
            # if yes, choose that dataset
            requested_set=int(args.c[0])
        except ValueError:
            # if not, fail
            raise IndexError(error_string)
        # check if it's not out of range:
        if not-len(datasets)<=requested_set<=len(datasets)-1:
            raise IndexError(error_string)

    # initialise writing object
    ostream=csv.writer(sys.stdout, delimiter=' ', escapechar='\\',
                      quoting=csv.QUOTE_MINIMAL, quotechar='#')

    # convert and write out requested data
    convert_to_csv(datasets[requested_set], ostream, args.input_file[0])









