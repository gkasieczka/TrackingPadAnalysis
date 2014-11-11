import ROOT
import argparse
from root_style import root_style

from os import walk
import copy
import RunInfo

parser = argparse.ArgumentParser(description='Merge the histos')

parser.add_argument('dir')

args = parser.parse_args()

my_style = root_style()
my_style.main_dir=args.dir
width = 1000
my_style.set_style(width,width,1.)
ROOT.gStyle.SetOptStat(0)

frame = None
f = []
f_landau_gaus = []
dir = args.dir+'/root/'
for (dirpath, dirnames, filenames) in walk(dir):
    print dirpath
    print dirnames
    f.extend(filenames)
    for fname in filenames:
        if 'histo_' in fname:
            f_landau_gaus.append(dirpath+fname)
    break

histos = {}
diamond = ''
for f in f_landau_gaus:
    # f = f_landau_gaus[-1]
    print f
    fname = f.split('/')[-1].split('.')[0]
    fname = fname[fname.find('-run-')+5:]
    fname = fname.split('-')

    run = int(fname[0])
    print run
    root_file  = ROOT.TFile.Open(f)
    canvas = root_file.Get('time_canvas')
    ps = {}
    for key in canvas.GetListOfPrimitives():
        print '\t', key.GetName(),key
        prim  = canvas.GetPrimitive(key.GetName()).Clone()
        if 'hSignal' in key.GetName():
            print 'add'
            histos[run] = copy.deepcopy(prim)
        else:
            ps[key.GetName()] = prim
    print histos, ps

c2 = my_style.get_canvas('c_rate_development')
c2.cd()
frame = c2.DrawFrame(0,0,500,1,'')
frame.GetXaxis().SetTitle('Signal / ADC')
frame.SetLineColor(0)
frame.SetTitle('')
frame.Draw()
k = 1

RunInfo.RunInfo.load('runs.json')

maximum = 0

bias = -500
bias_currents = list(set([RunInfo.RunInfo.runs[run].bias_voltage for run in histos]))

print bias_currents
if bias not in bias_currents:
    bias *= -1
ROOT.gStyle.SetOptStat(0)
drawn_histos = []
rates = []
e_rates = []
mps = []
e_mps = []
means = []
e_means = []
is_rate_scan = False
is_bias_scan = False
print args.dir
if 'rate' in args.dir:
    is_rate_scan = True
elif 'bias' in args.dir:
    is_bias_scan = True
print 'bias scan:',is_bias_scan
print 'rate scan:',is_rate_scan

for run in sorted(histos.keys()):
    this_run = RunInfo.RunInfo.runs[run]
    if is_rate_scan:
        print run , this_run.bias_voltage
        if this_run.bias_voltage != bias:
            continue
    elif is_bias_scan:
        pass
    if diamond == '':
        diamond = this_run.diamond
    h = histos[run]
    h.UseCurrentStyle()
    h.SetLineWidth(2)
    integral = 0
    if is_rate_scan:
        h.SetTitle('Run %3d @ %4.2e kHz/cm^{2}'%(run,this_run.get_rate()))
    if is_bias_scan:
        h.SetTitle('Run %3d @ %+5d V'%(run,this_run.bias_voltage))
    h.SetLineColor(k)
    h.SetMarkerColor(k)
    h.SetFillStyle(0)
    h.SetFillColor(0)
    k+=1
    h.SetStats(0)
    h.Draw('same')
    drawn_histos.append(run)
    maximum = max(maximum, h.GetBinContent(h.GetMaximumBin()))
    mps.append(h.GetXaxis().GetBinCenter(h.GetMaximumBin()))
    means.append(h.GetMean())
    e_means.append(h.GetRMS())
    rates.append(this_run.get_rate())
    e_rates.append(rates[-1]*.1)
frame.GetYaxis().SetRangeUser(0,maximum*1.1)

leg = my_style.make_legend(.5,.9,len(drawn_histos))
for run in drawn_histos:
    h = histos[run]
    print 'addding ',run,h.GetTitle()
    leg.AddEntry(h,h.GetTitle())
leg.Draw()
c2.Update()
print 'drawn:',drawn_histos
if is_rate_scan:
    my_style.save_canvas(c2,'rate_scan_landaus')
elif is_bias_scan:
    my_style.save_canvas(c2,'bias_scan_landaus')

my_style.set_style(width,width,.9)
c1 = my_style.get_canvas('rate_scan_development')
g_mp = ROOT.TGraph(len(rates))
g_mp.SetName('g_mp')
g_mp.SetTitle('MP vs rate')
g_mp.SetMarkerStyle(20)
g_mp.SetMarkerColor(ROOT.kBlue)
g_mp.SetFillColor(0)
g_mp.SetFillStyle(0)

g_mean = ROOT.TGraphErrors(len(rates))
g_mean.SetName('g_mean')
g_mean.SetTitle('mean vs rate')
g_mean.SetMarkerStyle(21)
g_mean.SetMarkerColor(ROOT.kGreen)
g_mean.SetFillColor(0)
g_mean.SetFillStyle(0)
for i in range(len(rates)):
    r = rates[i]
    g_mp.SetPoint(i,rates[i],mps[i])
    g_mean.SetPoint(i,rates[i],means[i])
    g_mean.SetPointError(i,e_rates[i],1.)
    #e_means[i])

if is_rate_scan:
    mg = ROOT.TMultiGraph('mg',';rate / #frac{Hz}{cm^{2}}; signal / adc')
    mg.Add(g_mp)
    mg.Add(g_mean)
    mg.Draw('APL')
    leg = my_style.make_legend(.5,.9,2)

    leg.AddEntry(g_mp)
    leg.AddEntry(g_mean)
    leg.Draw()
    c1.Update()
    arrow = ROOT.TArrow()
    arrow_means = []
    arrow_mps = []
    for i in range(len(rates)-1):
        arrow_means.append(arrow.DrawArrow(rates[i],means[i],rates[i+1],means[i+1],0.02,'->-'))
        arrow_mps.append(arrow.DrawArrow(rates[i],mps[i],rates[i+1],mps[i+1],0.02,'->-'))
    c1.Update()

    my_style.save_canvas(c1,'rate_scan_means')
