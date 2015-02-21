#!/usr/bin/env python

"""
Study timing between pixel and pad detectors.

Also produce tracking based analysis plots.
"""

# ##############################
# Imports
# ##############################

import sys
import argparse
import ConfigParser

import ROOT
from RunInfo import RunInfo

import TimingAlignmentClass
import ConfigParser

# ##############################
# Configuration
# ##############################

parser = argparse.ArgumentParser(description='Timing Alignment of DRS4-Board with CMS - Pixel testboard.',
                                 epilog="Example  python {0} 70 0".format(sys.argv[0]))

parser.add_argument('run', metavar='R', type=int, help='run: run number (int)')
parser.add_argument('action', metavar='A', type=int,
                    help='action: 0=analyze    1=run on small sample     2=find alignment    3=do everything')
parser.add_argument('-diamond', type=str, help='only needed for action=3')
parser.add_argument('-voltage', type=int, help='only needed for action=3')
parser.add_argument('--output-dir', '-o', dest='output', help='output directory', default='./results/runs/')
args = parser.parse_args()

run = args.run
action = args.action

config = ConfigParser.ConfigParser()
config.read('TimingAlignment.cfg')

# print 'Run', args.run
# print 'action', args.action
# print 'diamond', args.diamond
# print 'voltage', args.voltage


# ##############################
# Init ROOT
# ##############################

ROOT.gStyle.SetPalette(53)

ROOT.gStyle.SetPadLeftMargin(0.15)
ROOT.gStyle.SetPadRightMargin(0.14)
ROOT.gStyle.SetPadBottomMargin(0.12)
ROOT.gStyle.SetPadTopMargin(0.05)
ROOT.gROOT.ForceStyle()
c = ROOT.TCanvas("", "", 800, 800)

print "Going to process run {0} with action = {1}".format(run, action)

# ##############################
# Branch names
# ##############################

branch_names = {
    # Event Numbers
    "n_pad": "n",
    "n_pixel": "ievent",
    # Time
    "t_pad": "time_stamp",  # [seconds]
    "t_pixel": "time",  # clock-ticks (25 ns spacing)
    # Pixel only:
    # - Hit plane bits 
    "plane_bits_pixel": "hit_plane_bits",
    # -Tracks
    "track_x": "track_x",
    "track_y": "track_y",

    # Pad only:
    # - Calibration flag
    "calib_flag_pad": "calibflag",
    # - Integral50
    "integral_50_pad": "Integral50"
}


# ##############################
# Get Trees
# ##############################
#

basedir_pad = config.get('INPUT','basedir_pad')
#"/scratch/PAD-testbeams/PSI_sept_14/pad_out/"
basedir_pixel = config.get('INPUT','basedir_pixel')
#"/scratch/PAD-testbeams/PSI_sept_14/software/DHidasPLT/plots/"

format_pad = config.get('INPUT','format_pad')
#"{0}run_2014_09r{1:06d}.root"
format_pixel = config.get('INPUT','format_pixel')
#"{0}{1:06d}/histos.root"

filename_pad = format_pad.format(basedir_pad, run)
print filename_pad
filename_pixel = format_pixel.format(basedir_pixel, run)

f_pad = ROOT.TFile.Open(filename_pad)
f_pixel = ROOT.TFile.Open(filename_pixel)
if not f_pad:
    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    RunInfo.load(parser.get('JSON','runs'))
    run_info = RunInfo.runs[run]
    run_info.calibration_event_fraction = -3.0
    RunInfo.update_run_info(run_info)
    raise Exception('Cannot find Pad File')
if not f_pixel:
    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    RunInfo.load(parser.get('JSON','runs'))
    run_info = RunInfo.runs[run]
    run_info.calibration_event_fraction = -4.0
    RunInfo.update_run_info(run_info)
    # raise Exception('Cannot find Pixel File')



# ##############################
# Actual work
# ##############################

TA = TimingAlignmentClass.TimingAlignment(run, f_pixel, f_pad, branch_names)
if True:
    if (action == 0) or (action == 1):
        # TaH.print_run_info(run, tree_pixel, tree_pad, branch_names)
        TA.set_action(action)
        TA.analyse()
    elif action == 2:
        # TaH.print_run_info(run, tree_pixel, tree_pad, branch_names)
        TA.set_action(action)
        TA.find_first_alignment()
    elif action == 3:
        diamond = args.diamond
        bias_voltage = args.voltage
        # TaH.RunTiming(run, diamond_name=diamond, bias_voltage=bias_voltage)
        TA.set_action(action)
        if f_pixel:
            TA.find_first_alignment()
        TA.set_action(1)
        TA.analyse()
        TA.set_action(0)
        TA.analyse()
