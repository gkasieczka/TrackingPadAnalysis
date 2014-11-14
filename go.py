#!/usr/bin/python

import argparse
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
import DataTypes
ROOT.gROOT.SetBatch()

parser = argparse.ArgumentParser()
parser.add_argument('-p','--pedestal', dest='do_pedestal', action='store_true',
                   default = False,
                   help='Analyse pedestals')
parser.add_argument('-d','--data', dest='do_data', action='store_true',
                   default = False,
                   help='Analyse data')
parser.add_argument('-b','--bias', dest='do_bias', action='store_true',
                   default = False,
                   help='Analyse bias')
parser.add_argument('-f','--reanalyze', dest='reanalyze', action='store_true',
                   default = False,
                   help='Reanalyze')
parser.add_argument('-ff','--reload', dest='reload', action='store_true',
                   default = False,
                   help='Reload')
parser.add_argument('-a','--all', action='store_true',
                   default = False,
                   help='Analyse all')
parser.add_argument('-j','--jobs', default = 10,
                   help='Set jobs')


args = parser.parse_args()
if args.all:
    args.do_pedestal = True
    args.do_data = True
    args.do_bias = True
print args
reanalyze = args.reanalyze
do_pedestal = args.do_pedestal
do_data     = args.do_data
do_bias = args.do_bias
reload = args.reload
print args.jobs,type(args.jobs)
nProcesses = int(args.jobs)
print nProcesses, type(nProcesses)

print 'pedestal: ',do_pedestal
print 'data:     ',do_data
print 'bias:     ',do_bias
print 'reload:   ',reload
print 'reanalyze:',reanalyze

if not do_pedestal and not do_data and not do_bias:
    print 'you have to specify either \'data\' or \'pedestal\''
    print 'don\'t be modest'
    sys.exit()

RunInfo.load('runs.json')

dat_not = []
dat_all = []
ped_not = []
ped_all = []
commands = []
runs = {}
for rn, r in RunInfo.runs.items():
    if r.data_type not in runs:
        runs[r.data_type]=0
    runs[r.data_type]+=1
print '\nThere are the following runs in the json file:'
for data_type in runs:
    print '\t- %12s: %4d'%(DataTypes.data_types[data_type],runs[data_type])
print '\t'+'-'*20
print '\t- %12s: %4d'%('TOTAL',reduce(lambda x,y: x+y,runs.values()))
print

if do_pedestal:
    ped_fail = []
    data_type = DataTypes.data_types.keys()[DataTypes.data_types.values().index('PEDESTAL')]
    #find all pedestal runs whcih must be analyzed
    for rn, r in RunInfo.runs.items():
        if r.data_type == data_type:
            ped_all.append(rn)
            if math.isnan(r.pedestal) or reload:
                ped_not.append(rn)
            else:
                ped_fail.append(rn)
    print 'PEDESTAL'
    print 'these are the %d / %d  pedestal runs which will NOT be analyzed:\n\t'%(len(ped_fail),runs[data_type]),ped_fail
    print 'these are the %d / %d unanalyzed pedestal runs:\n\t'%(len(ped_not),runs[data_type]), ped_not
    raw_input('Press enter to continue.')

    for run in ped_not:
        cmd = 'python Analyze.py reload '+str(run)
        commands.append((run,cmd))

if do_data:
    dat_fail_no_timing = []
    dat_fail_no_pedestal = []
    data_types = [DataTypes.data_types.keys()[DataTypes.data_types.values().index('DATA')],
                 DataTypes.data_types.keys()[DataTypes.data_types.values().index('LONG_RUN')]]
    for rn, r in RunInfo.runs.items():
        if r.data_type in data_types:
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
    print 'DATA'
    print 'cannot analyze %3d / %3d runs,  due to missing pedestal:\n\t'%(len(dat_fail_no_pedestal),runs[data_type]),dat_fail_no_pedestal
    print 'and %3d / %3d  runs due to missing timing:\n\t'%(len(dat_fail_no_timing),runs[data_type]),dat_fail_no_timing
    print '\nthese are the %3d / %3d  data runs which will be analyzed:\n\t'%(len(dat_not),runs[data_type]),dat_not
    raw_input('Press enter to continue.')

    for run in dat_not:
        cmd = 'python Analyze.py '
        if reload:
            cmd += 'reload '
        cmd += str(run)
        commands.append((run,cmd))
if do_bias:
    bias_fail_no_pedestal = []
    bias_fail_no_timing = []
    bias_not = []
    bias_all = []
    data_type = DataTypes.data_types.keys()[DataTypes.data_types.values().index('VOLTAGESCAN')]
    for rn, r in RunInfo.runs.items():
        if r.data_type == data_type:
            bias_all.append(rn)
            has_pedestal = not math.isnan(r.pedestal)
            has_timing   = r.calibration_event_fraction > 0.
            has_plots    = os.path.isfile('results/run_'+str(rn)+'/plots.pdf') # check if a file already exists
            if (has_pedestal and has_timing) and (not has_plots or reanalyze):
                bias_not.append(rn)
            else:
                if not has_pedestal:
                    bias_fail_no_pedestal.append(rn)
                if not  has_timing:
                    bias_fail_no_timing.append(rn)
    print
    print 'VOLTAGESCAN'
    print 'cannot analyze %3d / %3d runs,  due to missing pedestal:\n\t'%(len(bias_fail_no_pedestal),runs[data_type]),bias_fail_no_pedestal
    print 'and %3d / %3d  runs due to missing timing:\n\t'%(len(bias_fail_no_timing),runs[data_type]),bias_fail_no_timing
    print '\nthese are the %3d / %3d  data runs which will be analyzed:\n\t'%(len(bias_not),runs[data_type]), bias_not
    raw_input('Press enter to continue.')

    for run in bias_not:
        cmd = 'python Analyze.py '
        if reload:
            cmd += 'reload '
        cmd += str(run)
        commands.append((run,cmd))

raw_input('start analysis with %d commands. press enter'%len(commands))
pool = Pool(nProcesses)
it = pool.imap_unordered(partial(call, shell=True), [c[1] for c in commands])
failures = []
complete = []
for i, returncode in enumerate(it):
    # print multiprocessing.active_children()
    if returncode != 0:
        print("Command '%s'  failed: %d" % (commands[i], returncode))
        failures.append(commands[i][0])
    else:
        complete.append(commands[i][0])
        print("Command '%s'  completed: %d" % (commands[i], returncode))
print 'completed:',complete

print 'Failures:',failures

print 'finished'
