#!/usr/bin/python

import math, sys, os
from RunInfo import RunInfo
from subprocess import call
from functools import partial
from subprocess import call
from multiprocessing.dummy import Pool
from subprocess import call
import subprocess
import multiprocessing
import datetime
import ROOT
ROOT.gROOT.SetBatch()

reanalyze = False
do_pedestal = False
do_data     = False
reload = False
nProcesses = 12

args = sys.argv

if 'reload' in args:
    reload = True
if 'reanalyze' in args:
    reanalyze = True

if 'pedestal' in args or 'ped' in args or 'p' in args:
    do_pedestal = True
if 'data' in args:
    do_data = True
if 'both' in args:
    do_data = True
    do_pedestal = True

# if do_pedestal and do_data:
#     print 'you can do either pedestal or data, not both!'
#     print 'don\'t be greedy'
#     sys.exit()

print 'pedestal: ',do_pedestal
print 'data: ',do_data
print 'reload: ',reload
print 'reanalyze:',reanalyze

if not do_pedestal and not do_data:
    print 'you have to specify either \'data\' or \'pedestal\''
    print 'don\'t be modest'
    sys.exit()

RunInfo.load('runs.json')

dat_not = []
dat_all = []
ped_not = []
ped_all = []
commands = []
if do_pedestal:
    ped_fail = []
    for rn, r in RunInfo.runs.items():
        if r.data_type == 1:
            ped_all.append(rn)
            if math.isnan(r.pedestal):
                ped_not.append(rn)
            else:
                ped_fail.append(rn)

    print 'failues',ped_fail
    print 'these are the unanalyzed pedestal runs:'
    print ped_not

    for run in ped_not:
        cmd = 'python Analyze.py reload '+str(run)
        commands.append(cmd)
        # print 'calling', cmd
        # call('python Analyze.py reload '+str(run), shell=True)
if do_data:
    dat_fail_no_timing = []
    dat_fail_no_pedestal = []
    for rn, r in RunInfo.runs.items():
        if r.data_type == 0:
            dat_all.append(rn)
            has_pedestal = not math.isnan(r.pedestal)
            has_timing   = r.calibration_event_fraction > 0.
            has_plots    = os.path.isfile('results/run_'+str(rn)+'/plots.pdf') # check if a file already exists
            if (has_pedestal and has_timing) and (not has_plots or reanalyze):
                dat_not.append(rn)
            else:
                if not has_pedestal:
                    dat_fail_no_pedestal.append(rn)
                if not  has_timing:
                    dat_fail_no_timing.append(rn)
    print
    print 'cannot analyze: due to missing pedestal',dat_fail_no_pedestal
    print 'and due to missing timing',dat_fail_no_timing
    print '\nthese are the unanalyzed data runs:'
    print dat_not
    
    for run in dat_not:
        cmd = 'python Analyze.py '
        if reload:
            cmd += 'reload '
        cmd += str(run)
        commands.append(cmd)
        # print 'calling', cmd
        # call('python Analyze.py '+str(run), shell=True)
raw_input('start analysis. press enter')
pool = Pool(nProcesses)
it = pool.imap_unordered(partial(call, shell=True), commands)
failures = []
complete = []
for i, returncode in enumerate(it):
    # print multiprocessing.active_children()
    if returncode != 0:
        print("Command '%s'  failed: %d" % (commands[i], returncode))
        failures.append(i)
    else:
        complete.append(i)
        print("Command '%s'  completed: %d" % (commands[i], returncode))
print 'completed:',complete

print 'Failures:',failures

print 'finished'
