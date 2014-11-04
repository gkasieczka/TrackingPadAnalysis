#!/usr/bin/python

import math, sys, os
from RunInfo import RunInfo
from subprocess import call
from functools import partial
from multiprocessing.dummy import Pool
from subprocess import call
import subprocess
import multiprocessing
import datetime

do_pedestal = False
do_data     = False
do_timing   = True
args = sys.argv

def modification_date(filename):
    t = os.path.getmtime(filename)
    return t
    return datetime.datetime.fromtimestamp(t)
d = modification_date('TimingAlignmentClass.py')
print d

RunInfo.load('runs.json')

print 'There are in total {n_runs} runs in the DB'.format(n_runs=len(RunInfo.runs))

nProcesses = 10
if do_timing:
    timing_not = []
    timing_all = []

    for rn, r in RunInfo.runs.items():
        if r.calibration_event_fraction < 0 or r.time_timing_alignment < d:
            timing_all.append(rn)
            # if math.isnan(r.pedestal) and r.calibration_event_fraction > 0.:
            #     ped_not.append(rn)

    print 'these are the unanalyzed pedestal runs:'
    print timing_all
    errors = []
    commands = []
    for run in timing_all:
        cmd = './TimingAlignment.py {run} 3'.format(run=run)
        commands.append(cmd)
    pool = Pool(nProcesses)
    it = pool.imap_unordered(partial(call, shell=True), commands)
    for i, returncode in enumerate(it):
        # print multiprocessing.active_children()
        if returncode != 0:
            print("Command '%s'  failed: %d" % (commands[i], returncode))
        else:
            print("Command '%s'  completed: %d" % (commands[i], returncode))
        # call(cmd, shell=True)

# if do_data:
#     dat_not = []
#     dat_all = []
#
#     for rn, r in RunInfo.runs.items():
#         if r.data_type == 0:
#             dat_all.append(rn)
#             has_pedestal = not math.isnan(r.pedestal)
#             has_timing   = r.calibration_event_fraction > 0.
#             has_plots    = os.path.isfile('results/run_'+str(rn)+'/plots.pdf') # check if a file already exists
#
#             if (has_pedestal and has_timing) and not has_plots:
#                 dat_not.append(rn)
#
#
#     print 'these are the unanalyzed data runs:'
#     print dat_not
#
#     for run in dat_not:
#         cmd = 'python Analyze.py '+str(run)
#         print 'calling', cmd
#         call('python Analyze.py '+str(run), shell=True)
