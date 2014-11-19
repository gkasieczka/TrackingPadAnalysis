import ROOT
import argparse
from root_style import root_style
from merge_histos_helper import *
import RunInfo
import ConfigParser

parser = argparse.ArgumentParser(description='Merge the histos')

parser.add_argument('dir')
parser.add_argument('-b','--batch',action='store_true')

args = parser.parse_args()

my_style = root_style()
if args.batch:
    ROOT.gROOT.SetBatch()
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
frame = c2.DrawFrame(-50,0,500,1,'')
frame.GetXaxis().SetTitle('Signal / ADC')
frame.SetLineColor(0)
frame.SetTitle('')
frame.Draw()
k = 1


parser = ConfigParser.ConfigParser()
parser.read('TimingAlignment.cfg')
RunInfo.RunInfo.load(parser.get('JSON','runs'))

maximum = 0

bias = -500
bias_voltages= list(set([RunInfo.RunInfo.runs[run].bias_voltage for run in histos]))

print bias_voltages
if bias not in bias_voltages:
    bias *= -1
ROOT.gStyle.SetOptStat(0)
is_rate_scan = False
is_bias_scan = False
print args.dir
if 'rate' in args.dir:
    is_rate_scan = True
elif 'bias' in args.dir or 'voltage' in args.dir:
    is_bias_scan = True
print 'bias scan:',is_bias_scan
print 'rate scan:',is_rate_scan


def create_histos(keys, is_bias_scan,is_rate_scan, bias):
    frame = c2.DrawFrame(-50,0,500,1,'')
    frame.GetXaxis().SetTitle('Signal / ADC')
    frame.SetLineColor(0)
    frame.SetTitle('')
    frame.Draw()
    drawn_histos = []
    rates = []
    e_rates = []
    mps = []
    e_mps = []
    means = []
    pedestals = []
    e_pedestals = []
    e_means = []
    ratios = []
    v_bias = []
    raw_bias = []
    raw_rates = []
    diamond = ''
    k = 1
    maximum = 0
    all_histos = []
    run_infos = []
    last_means = []
    runs = []
    for run in sorted(keys):
        print run
        this_run = RunInfo.RunInfo.runs[run]
        runs.append(run)
        pedestal_histo = get_pedestal_histo(args.dir,this_run)
        # if is_rate_scan:
        #     print run , this_run.bias_voltage
        #     if this_run.bias_voltage != bias:
        #         continue
        # elif is_bias_scan:
        #     pass
        if diamond == '':
            diamond = this_run.diamond
        h = histos[run][1]
        all_histos.append([copy.deepcopy(h),copy.deepcopy(pedestal_histo)])
        run_infos.append(this_run)
        h.UseCurrentStyle()
        h.SetLineWidth(2)
        integral = 0
        if is_rate_scan:
            title = 'Run %3d @ %s'%(run,this_run.get_rate_string())
            h.SetTitle(title)
        if is_bias_scan:
            if -1<= this_run.bias_voltage <= 1:
                bias = 0
            else:
                bias = this_run.bias_voltage
            h.SetTitle('Run %3d @ %+5d V'%(run,bias))
        h.SetLineColor(k)
        h.SetMarkerColor(k)
        h.SetFillStyle(0)
        h.SetFillColor(0)
        h.SetStats(0)
        k+=1
        drawn_histos.append(run)
        if h.GetBinContent(h.GetMaximumBin()) != 0:
            h.Scale(1/h.GetBinContent(h.GetMaximumBin()))
        maximum = max(maximum, h.GetBinContent(h.GetMaximumBin()))
        c2.cd()
        h.Draw('same')

        rate = this_run.get_rate()
        if rate > 1e6 and 'IIa' in this_run.diamond:
            continue
        if is_rate_scan:
            raw_rates.append(rate)
        else:
            raw_rates = [rate]
        rs,m, mpp = divide_histo(histos[run][0],raw_rates,5)
        # h.Scale(1./float(maximum))
        if len(rs) > 0:

            mps.extend(mpp)
            means.extend(m)
            last_means.append(m[-1])
            ratios.extend(map(lambda x,y: x/y, m,mpp))
            e_means.append(h.GetRMS())
            rates.extend(rs)
            e_rates.extend(map(lambda r: r*.1,rs))
            if is_rate_scan:
                v_bias.extend([this_run.bias_voltage]*len(mpp))
                raw_bias.append(this_run.bias_voltage)
            else:
                bias = this_run.bias_voltage
                if bias == 1:
                    bias = +0.0
                elif bias == -1:
                    bias = -0.0
                raw_bias.append(bias)
                v_bias.extend([bias+math.copysign(3, bias)*i for i in range(len(mpp))])
            pedestals.extend([this_run.pedestal]*len(mpp))
            e_pedestals.extend([this_run.pedestal_sigma]*len(mpp))
            print len(mps),len(rates),len(means)

    if is_bias_scan:
        print 'is BIAS scan'
        print v_bias
        print sorted(raw_bias)

    frame.GetYaxis().SetRangeUser(0,maximum*1.1)
    leg = my_style.make_legend(.5,.94,len(drawn_histos))
    for run in drawn_histos:
        h = histos[run][1]
        print 'adding ',run,h.GetTitle()
        leg.AddEntry(h,h.GetTitle())
    leg.Draw()
    c2.Update()
    print 'drawn:',drawn_histos,is_rate_scan,is_bias_scan
    if is_rate_scan:
        my_style.save_canvas(c2,'rate_scan_%s_landaus'%get_voltage_string(bias))
    elif is_bias_scan:
        print bias_voltages
        if min(bias_voltages) < -1:
            if max(bias_voltages) > +1:
                sign = 'all'
            else:
                sign = 'neg'
        else:
            sign = 'pos'
        #bias_scan_%s_means_rate_%1.0E'%(sign,rate))
        my_style.save_canvas(c2,'bias_scan_%s_landaus_rate_%1.0E'%(sign,rate))
        if sign == 'all':
            print 'all',sorted(list(set(raw_bias))),
    my_style.set_style(width,width,.9)
    is_IIa_diamond = ('IIa-' in this_run.diamond)
    e_vbias = [0]*len(rates)
    if is_rate_scan:
        create_graph(this_run.diamond,my_style,[rates,e_rates],[mps,e_mps],[means,e_means],[pedestals,e_pedestals],bias,draw_mp=not is_IIa_diamond)
    else:
        print sign
        if sign == 'all':
            print map(lambda x,y: (x,y),runs,raw_bias)
            print raw_bias
            print 'all means:',len(raw_bias),len(last_means)
            print map(lambda x,y: (x,y),raw_bias,last_means)
            draw_voltage_scan(my_style,raw_bias,last_means,raw_rates[-1])
        create_graph(this_run.diamond,my_style,[v_bias,e_vbias],[mps,e_mps],[means,e_means],[pedestals,e_pedestals],0,raw_rates[-1],draw_mp=not is_IIa_diamond)

    create_pedestal_histos(my_style,all_histos,raw_bias,raw_rates,run_infos)

if is_rate_scan:
    for b in bias_voltages:
        keys = filter(lambda i: RunInfo.RunInfo.runs[i].bias_voltage == b,histos.keys())
        print b, keys
        create_histos(sorted(keys),is_bias_scan,is_rate_scan,b)
else:
    create_histos(sorted(histos.keys()),is_bias_scan,is_rate_scan,0)
    bias_signs = map(lambda b: math.copysign(1,b),bias_voltages)
    print 'bias'
    print bias_voltages
    print bias_signs
    print map(lambda key: (key,math.copysign(1,RunInfo.RunInfo.runs[key].bias_voltage)),histos.keys())
    for sign in list(set(bias_signs)):
        print 'checking',sign
        keys = filter(lambda key: math.copysign(1,RunInfo.RunInfo.runs[key].bias_voltage) == sign,histos.keys())
        print 'keys: '
        print keys
        # print map(lambda b: math.copysign(1,b),keys)
        print map(lambda key: (key,RunInfo.RunInfo.runs[key].bias_voltage),sorted(keys))
        # keys = sorted(histos.keys())
        create_histos(sorted(keys),is_bias_scan,is_rate_scan,0)
