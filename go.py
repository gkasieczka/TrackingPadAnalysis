#!/usr/bin/python

from RunInfo import RunInfo
import math
from subprocess import call

RunInfo.load('runs.json')


ped_not = []
ped_all = []

for rn, r in RunInfo.runs.items():
    if r.data_type == 1:
        ped_all.append(rn)
        if math.isnan(r.pedestal):
            ped_not.append(rn)


print 'these are the unanalyzed pedestal runs:'
print ped_not

for run in ped_not:
    call('python Analyze.py '+str(run), shell=True)
