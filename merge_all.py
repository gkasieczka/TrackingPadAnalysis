#!/usr/bin/python

import ROOT
import math, sys, os
from RunInfo import RunInfo
from subprocess import call
import root_style
import ConfigParser
import subprocess

this_style = root_style.root_style()
this_style.set_style(1000,1000,1)

def modification_date(filename):
    t = os.path.getmtime(filename)
    return t
    return datetime.datetime.fromtimestamp(t)
d = modification_date('TimingAlignmentClass.py')

parser = ConfigParser.ConfigParser()
parser.read('TimingAlignment.cfg')
RunInfo.load(parser.get('JSON','runs'))
fsh13 = set()
fs11 = set()
diamonds = set()
for rn,r in RunInfo.runs.items():
    diamonds.add(r.diamond)
print diamonds
scans = ['rate-scan','voltage-scan']
for dia in list(diamonds):
    print dia
    for scan in scans:
        fdir = 'results/'+dia+'/'+scan+'/'
        print fdir
        command = 'python merge_histos.py %s --batch'%fdir
        print command
        #raw_input()
        subprocess.call(command, shell=True)
