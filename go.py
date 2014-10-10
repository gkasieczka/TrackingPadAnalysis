#!/usr/bin/python

import math, sys, os
from RunInfo import RunInfo
from subprocess import call


do_pedestal = False
do_data     = False

args = sys.argv

if 'pedestal' in args or 'ped' in args or 'p' in args:
    do_pedestal = True
if 'data' in args or 'dat' in args or 'd' in args:
    do_data = True

if do_pedestal and do_data:
    print 'you can do either pedestal or data, not both!'
    print 'don\'t be greedy'
    sys.exit()

if not do_pedestal and not do_data:
    print 'you have to specify either \'data\' or \'pedestal\''
    print 'don\'t be modest'
    sys.exit()

RunInfo.load('runs.json')


if do_pedestal:
    ped_not = []
    ped_all = []
    
    for rn, r in RunInfo.runs.items():
        if r.data_type == 1:
            ped_all.append(rn)
            if math.isnan(r.pedestal) and r.calibration_event_fraction > 0.:
                ped_not.append(rn)
    
    
    print 'these are the unanalyzed pedestal runs:'
    print ped_not
    
    for run in ped_not:
        cmd = 'python Analyze.py '+str(run)
        print 'calling', cmd
        call('python Analyze.py '+str(run), shell=True)

if do_data:
    dat_not = []
    dat_all = []
    
    for rn, r in RunInfo.runs.items():
        if r.data_type == 0:
            dat_all.append(rn)
            has_pedestal = not math.isnan(r.pedestal)
            has_timing   = r.calibration_event_fraction > 0.
            has_plots    = os.path.isfile('results/run_'+str(rn)+'/plots.pdf') # check if a file already exists

            if (has_pedestal and has_timing) and not has_plots:
                dat_not.append(rn)
    
    
    print 'these are the unanalyzed data runs:'
    print dat_not
    
    for run in dat_not:
        cmd = 'python Analyze.py '+str(run)
        print 'calling', cmd
        call('python Analyze.py '+str(run), shell=True)
