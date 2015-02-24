#!/usr/bin/python

import ROOT
import math, sys, os
from RunInfo import RunInfo
from subprocess import call
import root_style
import ConfigParser
import DataTypes

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
    fsh13.add(abs(r.fsh13))
    fs11.add(r.fs11)
    diamonds.add(r.diamond)
fsh13 = sorted(list(fsh13))
fs11 = sorted(list(fs11))
bad_events  = {0: [], 1:[]}
old_runs = []
infos = {}
for rn, r in RunInfo.runs.items():
    if r.test_campaign !="PSI_Sept14":
        continue
    dia = r.diamond
    data_type = r.data_type
    bias = r.bias_voltage
    if data_type == 2:
        bias = math.copysign(1,r.bias_voltage)
    if data_type == 2:
        if bias > 0:
            key = '%s_pos'%(DataTypes.data_types[data_type])
        else:
            key = '%s_neg'%(DataTypes.data_types[data_type])
    else:
        if bias >0:
            key = '%s_pos%s'%(DataTypes.data_types[data_type],abs(bias))
        else:
            key = '%s_neg%s'%(DataTypes.data_types[data_type],abs(bias))

    if dia != 'S129':
        continue
    if not infos.has_key(key):
        infos[key] = []
    infos[key].append(r.number)
for key in infos:
    print key, infos[key]

        #print r.diamond,r,r.number,rate,r.data_type,r.fsh13,r.fs11
    #event_fraction = r.calibration_event_fraction
#    data_type = r.data_type
#    rate = fs11.index(r.fs11)*len(fsh13)+fsh13.index(abs(r.fsh13))
#    if event_fraction < 0:
#        h_analysis_status.Fill(event_fraction)
#        if event_fraction not in bad_events:
#            bad_events[event_fraction] = []
#        bad_events[event_fraction].append(rn)
#    else:
#
#        if event_fraction < 50:
#            h_analysis_status.Fill(event_fraction)
#            bad_events[0].append([rn,r.diamond])
#            h_analysis_status.Fill(0)
#        else:
#            bad_events[1].append(rn)
#            h_analysis_status.Fill(1)
#        h_event_fraction_vs_rate.Fill(event_fraction,rate)
#        h_event_fraction.Fill(event_fraction)
#        h_event_fraction_vs_type.Fill(event_fraction,data_type)
#x_labels = {-6:'no alignment events',
#            -5:'no mask file',
#            -4:'no pixel data',
#            -3:'no pad data',
#            -2:'no calib data',
#            -1:'not analyzed',
#             0:'not aligned',
#             1:'good aligned'}
#for i in x_labels:
#    bin = h_analysis_status.GetXaxis().FindBin(i)
#    h_analysis_status.GetXaxis().SetBinLabel(bin,x_labels[i])
#print 'old_runs',len(old_runs),old_runs
#
#for ev in sorted(bad_events.keys()):
#    print len(bad_events[ev]),x_labels[ev],': ',sorted(bad_events[ev]),'\n'
#ROOT.gStyle.SetOptStat(0)
#c1 = this_style.get_canvas('timimng_analysis')
#c1.cd()
#
#h_event_fraction.Draw()
#this_style.main_dir = './output/'
#this_style.save_canvas(c1,'eventfraction')
#
#h_event_fraction_vs_type.Draw('colz')
#this_style.save_canvas(c1,'eventfraction_vs_type')
#
#h_analysis_status.SetMarkerSize(h_analysis_status.GetMarkerSize()*2.)
#h_analysis_status.SetMaximum(1.2*h_analysis_status.GetMaximum())
#h_analysis_status.Draw('text00hist')
#
#this_style.save_canvas(c1,'analysis_status')
#
#h_event_fraction_vs_rate.Draw('colztext')
#this_style.save_canvas(c1,'event_fraction_vs_rate')
#c1.SaveAs('output/h_event_fraction_vs_rate.png')
## print 'no data: ',n_no_data,'of',len(RunInfo.runs)
##
## print 'No data (-2): ',sorted(a_minus_one)
##
## print '\nnot Analyzed (-1): ', sorted(a_minus_two)
##
## print '\nlow Fraction(<50%): ', sorted(a_low)
##
##-6: cannot find a matching start point
##-5: no masked assigned
##-4: no pad file
##-3: no pixel file
##-2: no calibration events
##-1: not analyzed
## 0: timing alignment failed
## 1: timing alignment good (calibration_event_fraction > 50%)
##
