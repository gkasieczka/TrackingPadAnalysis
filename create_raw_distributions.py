
import ROOT
import math, sys, os
import AnalyzeHelpers
from RunInfo import RunInfo
from subprocess import call
import root_style
import ConfigParser
import DataTypes
import argparse
import copy

def makePave(x1, y1, x2, y2):
    pave = ROOT.TPaveText(x1, y1, x2, y2, 'NDC NB')
    pave.SetTextAlign(12)
    pave.SetTextFont(82)
    pave.SetFillColor(0)
    pave.SetFillStyle(0)
    pave.SetShadowColor(0)
    pave.SetBorderSize(0)
    pave.SetTextFont(62)
    return pave

this_style = root_style.root_style()
this_style.set_style(1000,1000,1)
this_style.main_dir='./output/Raw_To_Signal/'
parser = ConfigParser.ConfigParser()
parser.read('TimingAlignment.cfg')
RunInfo.load(parser.get('JSON','runs'))

parser = argparse.ArgumentParser()
parser.add_argument('run', metavar='R', type=int, help='run: run number (int)')
args = parser.parse_args()

print 'Analyze RUN', args.run

if not RunInfo.runs.has_key(args.run):
    print 'Cannot find key',args.run
    exit()
if RunInfo.runs[args.run].data_type == 1:
    print 'Cannot create plot for only Pedestal run'
    exit()

pedestal_run = RunInfo.runs[args.run].pedestal_run

print 'Taking Pedestal Run: ', pedestal_run

directory = './results/runs/run_{0}/track_info.root'

print 'get files'
ped_file_name = directory.format(pedestal_run)
print ped_file_name
pedestal_file = ROOT.TFile.Open(ped_file_name)

data_file_name = directory.format(args.run)
print data_file_name

data_file = ROOT.TFile.Open(data_file_name)
print 'get canvas'
c1 = this_style.get_canvas('Distribution')
c1.Divide(1,3)
c1.cd(1)
c1.cd(1).SetGridx()
ped_raw = copy.deepcopy(pedestal_file.Get('h_raw'))
data_raw = copy.deepcopy(data_file.Get('h_raw'))
ped_raw.SetLineColor(ROOT.kBlue)
frame1 = c1.cd(1).DrawFrame(-500,0,500,1.1)
frame1.GetXaxis().SetTitle('raw / ADC')
ped_raw.Scale(1/ped_raw.GetBinContent(ped_raw.GetMaximumBin()))
ped_raw.Draw('same')
data_raw.Scale(1/data_raw.GetBinContent(data_raw.GetMaximumBin()))
data_raw.Draw('same')

pave_raw = makePave(0.00, 0.3, 0.15, 0.9)
pave_raw.AddText('mean_sig: %.2f' %(data_raw.GetMean() ))
pave_raw.AddText('mpv_sig : %.2f' %(data_raw.GetXaxis().GetBinCenter(data_raw.GetMaximumBin())) )
pave_raw.AddText('mean_ped: %.2f' %(ped_raw .GetMean() ))
pave_raw.AddText('mpv_ped : %.2f' %(ped_raw .GetXaxis().GetBinCenter(ped_raw.GetMaximumBin()) ))
pave_raw.SetTextSize(0.05)
pave_raw.Draw('same')




c1.cd(2)
c1.cd(2).SetGridx()
ped_raw_factor = copy.deepcopy(pedestal_file.Get('h_raw_factor'))
data_raw_factor = copy.deepcopy(data_file.Get('h_raw_factor'))
ped_raw_factor.SetLineColor(ROOT.kBlue)
frame2 = c1.cd(2).DrawFrame(-500,0,500,1.1)
frame2.GetXaxis().SetTitle('converted raw / ADC')
ped_raw_factor.Scale(1/ped_raw_factor.GetBinContent(ped_raw_factor.GetMaximumBin()))
ped_raw_factor.Draw('same')
data_raw_factor.Scale(1/data_raw_factor.GetBinContent(data_raw_factor.GetMaximumBin()))
data_raw_factor.Draw('same')

pave_raw_factor = makePave(0.00, 0.3, 0.15, 0.9)
pave_raw_factor.AddText('mean_sig: %.2f' %(data_raw_factor.GetMean() ))
pave_raw_factor.AddText('mpv_sig : %.2f' %(data_raw_factor.GetXaxis().GetBinCenter(data_raw_factor.GetMaximumBin())) )
pave_raw_factor.AddText('mean_ped: %.2f' %(ped_raw_factor .GetMean() ))
pave_raw_factor.AddText('mpv_ped : %.2f' %(ped_raw_factor .GetXaxis().GetBinCenter(ped_raw_factor.GetMaximumBin()) ))
pave_raw_factor.SetTextSize(0.05)
pave_raw_factor.Draw('same')

c1.cd(3)
c1.cd(3).SetGridx()
ped_signal = copy.deepcopy(pedestal_file.Get('h_signal'))
data_signal = copy.deepcopy(data_file.Get('h_signal'))
ped_signal.SetLineColor(ROOT.kBlue)
frame3 = c1.cd(3).DrawFrame(-500,0,500,1.1)
frame3.GetXaxis().SetTitle('signal / ADC')
ped_signal.Scale(1/ped_signal.GetBinContent(ped_signal.GetMaximumBin()))
ped_signal.Draw('same')
data_signal.Scale(1/data_signal.GetBinContent(data_signal.GetMaximumBin()))
data_signal.Draw('same')
pt = AnalyzeHelpers.addDiamondInfo(.01,.01,.2,.2,RunInfo.runs[args.run])
pt.SetTextSize(.06)
pt.Draw('same')

pave_signal = makePave(0.00, 0.3, 0.15, 0.9)
pave_signal.AddText('mean_sig: %.2f' %(data_signal.GetMean() ))
pave_signal.AddText('mpv_sig : %.2f' %(data_signal.GetXaxis().GetBinCenter(data_signal.GetMaximumBin())) )
pave_signal.AddText('mean_ped: %.2f' %(ped_signal .GetMean() ))
pave_signal.AddText('mpv_ped : %.2f' %(ped_signal .GetXaxis().GetBinCenter(ped_signal.GetMaximumBin()) ))
pave_signal.SetTextSize(0.05)
pave_signal.Draw('same')

##this_style.save_canvas(c1, 'Raw_To_Signal_run%03d'%args.run)
c1.SaveAs('/scratch/PAD-testbeams/PSI_sept_14/software/TrackingPadAnalysis/outputMarc/Raw_To_Signal_run%03d_marc.pdf'%args.run)
