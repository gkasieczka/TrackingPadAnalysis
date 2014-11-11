#!/usr/bin/python

import ROOT
import math, sys, os
from RunInfo import RunInfo
from subprocess import call

def modification_date(filename):
    t = os.path.getmtime(filename)
    return t
    return datetime.datetime.fromtimestamp(t)
d = modification_date('TimingAlignmentClass.py')

RunInfo.load('runs.json')
fsh13 = set()
fs11 = set()
for rn,r in RunInfo.runs.items():
    fsh13.add(abs(r.fsh13))
    fs11.add(r.fs11)
fsh13 = sorted(list(fsh13))
fs11 = sorted(list(fs11))
print 'fsh13: ',fsh13
print 'fs11:  ',fs11
h_event_fraction = ROOT.TH1F('hEventFraction','hEventFraction',103,-2.5,100.5)
bin_width = 4.
xbins = int((100+bin_width)/bin_width)
xmin = -bin_width/2.
xmax = 100+bin_width/2.
h_event_fraction_vs_type = ROOT.TH2F('hEventFractionVsType','hEventFractionVsType',xbins,xmin,xmax,6,-.5,5.5)
h_analysis_status = ROOT.TH1F('hAnalysisStatus','hAnalysisStatus',8,-6.5,1.5)
ymin = 0.
ybin = int(len(fs11)*len(fsh13))
ymax = ybin
h_event_fraction_vs_rate = \
    ROOT.TH2F('hEventFractionVsRate','hEventFractionVsRate',xbins,xmin,xmax,ybin,ymin,ymax)
print ybin,ymin,ymax
for f13 in fsh13:
    for f11 in fs11:
        bin = fs11.index(f11)*len(fsh13)+fsh13.index(abs(f13))+1
        h_event_fraction_vs_rate.GetYaxis().SetBinLabel(bin,"%3d / %2d"%(f11,-1.*f13))
        print bin, f11, f13
h_event_fraction_vs_rate.GetXaxis().SetTitle('Fraction')
h_event_fraction_vs_rate.GetYaxis().SetTitle('Rate')

bad_events  = {0: [], 1:[]}
old_runs = []
for rn, r in RunInfo.runs.items():
    if r.test_campaign !="PSI_Sept14":
        continue
    if r.time_timing_alignment < d:
        old_runs.append(rn)
    event_fraction = r.calibration_event_fraction
    data_type = r.data_type
    rate = fs11.index(r.fs11)*len(fsh13)+fsh13.index(abs(r.fsh13))
    if event_fraction < 0:
        h_analysis_status.Fill(event_fraction)
        if event_fraction not in bad_events:
            bad_events[event_fraction] = []
        bad_events[event_fraction].append(rn)
    else:

        if event_fraction < 50:
            h_analysis_status.Fill(event_fraction)
            bad_events[0].append([rn,r.diamond])
            h_analysis_status.Fill(0)
        else:
            bad_events[1].append(rn)
            h_analysis_status.Fill(1)
        h_event_fraction_vs_rate.Fill(event_fraction,rate)
        h_event_fraction.Fill(event_fraction)
        h_event_fraction_vs_type.Fill(event_fraction,data_type)
x_labels = {-6:'no alignment events',
            -5:'no mask file',
            -4:'no pixel data',
            -3:'no pad data',
            -2:'no calib data',
            -1:'not analyzed',
             0:'not aligned',
             1:'good aligned'}
for i in x_labels:
    bin = h_analysis_status.GetXaxis().FindBin(i)
    h_analysis_status.GetXaxis().SetBinLabel(bin,x_labels[i])
print 'old_runs',old_runs

for ev in sorted(bad_events.keys()):
    print x_labels[ev],': ',sorted(bad_events[ev]),'\n'
ROOT.gStyle.SetOptStat(0)
c1 = ROOT.TCanvas()
c1.cd()

h_event_fraction.Draw()
c1.SaveAs('evenfraction.png')

h_event_fraction_vs_type.Draw('colz')
c1.SaveAs('eventfraction_vs_type.png')

h_analysis_status.SetMarkerSize(h_analysis_status.GetMarkerSize()*2.)
h_analysis_status.SetMaximum(1.2*h_analysis_status.GetMaximum())
h_analysis_status.Draw('text00hist')
c1.SaveAs('h_analysis_status.png')
h_event_fraction_vs_rate.Draw('colztext')
c1.SaveAs('h_event_fraction_vs_rate.png')
# print 'no data: ',n_no_data,'of',len(RunInfo.runs)
#
# print 'No data (-2): ',sorted(a_minus_one)
#
# print '\nnot Analyzed (-1): ', sorted(a_minus_two)
#
# print '\nlow Fraction(<50%): ', sorted(a_low)
#
#-6: cannot find a matching start point
#-5: no masked assigned
#-4: no pad file
#-3: no pixel file
#-2: no calibration events
#-1: not analyzed
# 0: timing alignment failed
# 1: timing alignment good (calibration_event_fraction > 50%)
#
