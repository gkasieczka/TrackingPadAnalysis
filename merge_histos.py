import ROOT
import argparse
from root_style import root_style
from merge_histos_helper import *
import RunInfo

parser = argparse.ArgumentParser(description='Merge the histos')

parser.add_argument('dir')

args = parser.parse_args()

my_style = root_style()
my_style.main_dir=args.dir+'/output/'
width = 1000
my_style.set_style(width,width,1.)
ROOT.gStyle.SetOptStat(0)

frame = None
dir = args.dir+'/root/'

diamond = ''

histos = get_histos(dir)

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
bias_voltages= list(set([RunInfo.RunInfo.runs[run].bias_voltage for run in histos]))

print bias_voltages
if bias not in bias_voltages:
    bias *= -1
ROOT.gStyle.SetOptStat(0)
drawn_histos = []
rates = []
e_rates = []
mps = []
e_mps = []
means = []
pedestals = []
e_means = []
ratios = []
v_bias = []
is_rate_scan = False
is_bias_scan = False
print args.dir
if 'rate' in args.dir:
    is_rate_scan = True
elif 'bias' in args.dir or 'voltage' in args.dir:
    is_bias_scan = True
print 'bias scan:',is_bias_scan
print 'rate scan:',is_rate_scan

for b in bias_voltages:
    print b, filter(lambda i: RunInfo.RunInfo.runs[i].bias_voltage == b,histos.keys())

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
    h = histos[run][1]
    h.UseCurrentStyle()
    h.SetLineWidth(2)
    integral = 0
    if is_rate_scan:
        #todo make nice format
        title = 'Run %3d @ %s'%(run,this_run.get_rate_string())
        h.SetTitle(title)
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
    rs,m, mpp = divide_histo(histos[run][0],this_run.get_rate(),5)
    print len(m),len(mpp),len(rs)
    h.Scale(1/h.GetBinContent(h.GetMaximumBin()))
    maximum = max(maximum, h.GetBinContent(h.GetMaximumBin()))
    # h.Scale(1./float(maximum))
    mps.extend(mpp)
    means.extend(m)
    ratios.extend(map(lambda x,y: x/y, m,mpp))
    e_means.append(h.GetRMS())
    rates.extend(rs)
    e_rates.extend(map(lambda r: r*.1,rs))
    v_bias.extend([this_run.bias_voltage]*len(mpp))
    pedestals.extend([this_run.pedestal]*len(mpp))
    print len(mps),len(rates),len(means)


frame.GetYaxis().SetRangeUser(0,maximum*1.1)
leg = my_style.make_legend(.5,.9,len(drawn_histos))
for run in drawn_histos:
    h = histos[run][1]
    print 'adding ',run,h.GetTitle()
    leg.AddEntry(h,h.GetTitle())
leg.Draw()
c2.Update()
print 'drawn:',drawn_histos,is_rate_scan,is_bias_scan
if is_rate_scan:
    my_style.save_canvas(c2,'rate_scan_landaus')
elif is_bias_scan:
    my_style.save_canvas(c2,'bias_scan_landaus')

my_style.set_style(width,width,.9)

c1 = my_style.get_canvas('rate_scan_development')
pad_plot  = my_style.make_pad('plot','logx')
pad_ratio = my_style.make_pad('ratio','logx')
pad_plot.SetTicks(1,1)
pad_ratio.SetTicks(1,1)


print 'klength rates: ', len(rates),len(mps),len(means)   ,len(pedestals)
print rates
print mps
print means

g_mp = ROOT.TGraph(len(rates))
g_mp.SetName('g_mp')
g_mp.SetTitle('MP')
g_mp.SetMarkerStyle(20)
g_mp.SetMarkerColor(ROOT.kBlue)
g_mp.SetFillColor(0)
g_mp.SetFillStyle(0)

g_mean = ROOT.TGraphErrors(len(rates))
g_mean.SetName('g_mean')
g_mean.SetTitle('mean')
g_mean.SetMarkerStyle(21)
g_mean.SetMarkerColor(ROOT.kGreen)
g_mean.SetFillColor(0)
g_mean.SetFillStyle(0)

g_ratio = ROOT.TGraphErrors(len(rates))
g_ratio.SetName('g_ratio')
g_ratio.SetTitle('mean / mpv')
g_ratio.SetMarkerStyle(22)
g_ratio.SetMarkerColor(ROOT.kRed)
g_ratio.SetFillColor(0)
g_ratio.SetFillStyle(0)

g_pedestal = ROOT.TGraph(len(rates))
g_pedestal.SetName('g_pedestals')
g_pedestal.SetTitle('Pedestal')
g_pedestal.SetMarkerStyle(20)
g_pedestal.SetMarkerColor(ROOT.kViolet)
g_pedestal.SetFillColor(0)
g_pedestal.SetFillStyle(0)

for i in range(len(rates)):
    r = rates[i]
    g_mp.SetPoint(i,rates[i],mps[i])
    g_mean.SetPoint(i,rates[i],means[i])
    g_ratio.SetPoint(i,rates[i],ratios[i])
    g_mean.SetPointError(i,e_rates[i],1.)
    g_pedestal.SetPoint(i,rates[i],pedestals[i])
    #e_means[i])

if is_rate_scan:
    pad_plot.cd()
    xmin = min(rates)
    xmax = max(rates)
    xmin = (xmin/10**int(math.log10(xmin))-1)*10**int(math.log10(xmin))
    xmax = (xmax/10**int(math.log10(xmax))+1)*10**int(math.log10(xmax))
    ymax = max(means+mps+pedestals)
    ymin = min(means+mps+pedestals)
    delta = ymax - ymin
    ymax = ymax + delta*.1
    ymin = ymin - delta*.1
    frame_plot = pad_plot.DrawFrame(xmin,ymin,xmax,ymax)
    mg = ROOT.TMultiGraph('mg',';rate / #frac{Hz}{cm^{2}}; signal / adc')
    mg.Add(g_mp)
    mg.Add(g_mean)
    mg.Add(g_pedestal)
    mg.Draw('PL')
    frame_plot.GetYaxis().SetTitle('signal / adc')
    frame_plot.GetXaxis().SetTitle(' #frac{Hz}{cm^{2}}')
    # mg.GetXaxis().SetRangeUser(1,2.2e6)
    leg = my_style.make_legend(.7,.65,3)

    leg.AddEntry(g_mp)
    leg.AddEntry(g_mean)
    leg.AddEntry(g_pedestal)
    leg.Draw()
    c1.Update()

    pad_ratio.cd()

    ymin = min(ratios)-.1
    ymax = max(ratios)+.1
    frame_ratio = pad_ratio.DrawFrame(xmin,ymin,xmax,ymax)
    frame_ratio.GetXaxis().SetLabelColor(0)
    frame_ratio.GetYaxis().SetNdivisions(505)
    frame_ratio.GetYaxis().SetLabelSize(.2)
    frame_ratio.GetYaxis().SetTitle('ratio #frac{mean}{mp}')
    frame_ratio.GetYaxis().SetTitleSize(.2)
    frame_ratio.GetYaxis().SetTitleOffset(0.2)
    g_ratio.Draw('PL')

    pad_plot.cd()
    arrow = ROOT.TArrow()
    arrow_means = []
    arrow_mps = []
    for i in range(len(rates)-1):
        arrow_means.append(arrow.DrawArrow(rates[i],means[i],rates[i+1],means[i+1],0.02,'->-'))
        arrow_mps.append(arrow.DrawArrow(rates[i],mps[i],rates[i+1],mps[i+1],0.02,'->-'))
    c1.Update()
    my_style.save_canvas(c1,'rate_scan_means')
