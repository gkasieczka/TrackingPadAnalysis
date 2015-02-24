import datetime
import ROOT
import warnings
import RunInfo
import os
import math
from os import walk
import copy
import ConfigParser
import time

def get_voltage_string(bias):
    if bias <0:
        retVal = 'm'
        bias *= -1
    else:
        retVal = 'p'
    retVal+='%04dV'%bias
    return retVal

def get_mean(h):
    return [h.GetMean(),h.GetRMS()]

def get_mp(h):
    mp = h.GetXaxis().GetBinCenter(h.GetMaximumBin())
    fgaus = ROOT.TF1('fgaus','gaus',mp-5,mp+5)
    h.Fit(fgaus,'QN')
    mp = fgaus.GetParameter(1)
    emp = fgaus.GetParError(1)
    if mp == 0:
        mp = -1
    return [mp,emp]

def divide_histo(histo,raw_rates, n=5):
    rate = raw_rates[-1]
    binsx = histo.GetNbinsX()
    means = []
    mps = []
    rates = []
    min_entries = histo.GetEntries()/n
    # print histo.GetBinContent(0),
    # print histo.GetBinContent(binsx+1)
    bins = binsx/n+1
    # print 'divide histo',n,binsx
    # print '\nmin_entries', min_entries,binsx
    end_bin = 1
    hx = histo.ProjectionX()
    for i in range(n+1):
        entries = 0
        start_bin = end_bin
        k = 0
        while entries < min_entries and start_bin + k <= binsx:
            entries += hx.GetBinContent(start_bin+k)
            k += 1
        end_bin = start_bin + k-1
        h = histo.ProjectionY('',start_bin,end_bin)
        pos = (start_bin-1.)/float(binsx)
        if raw_rates.count(rate) > 1:
            this_rate = get_associated_rate(rate,1.-pos,n)
        else:
            this_rate = get_associated_rate(rate,pos,n)
        # print '%d, %3d, %3d - %3d %4.1f - %4.1f, %4.1e, %6d'%(i,k,start_bin,end_bin,pos,(end_bin)/float(binsx)*100., this_rate,h.GetEntries())
        if h.GetEntries() == 0:
            continue

        means.append(get_mean(h)[0])
        mps.append(get_mp(h)[0])
        rates.append(  this_rate)
        # print means[-1],mps[-1]
        if pos == 100:
            break
    # print rates, means, mps
    # print len(rates),len(means),len(mps)
    return (rates,means,mps)

def get_associated_rate(rate,pos,n=5,rate_scan = True):
    if rate_scan:
        f = math.log10(rate)
        f = int(f)
        f = 10**3
        d = 0.1
        nd = d*n*pos/1.
        r = rate *math.exp(nd)
    else:
        r = rate+ .1*n*pos
    return r

def get_histos(fdir):
    fdir = os.path.abspath(fdir)
    print 'Get histos in Directory: ',fdir

    f = []
    f_landau_gaus = []
    for (dirpath, dirnames, filenames) in walk(fdir):
        f.extend(filenames)
        for fname in filenames:
            if 'time_2d' in fname:
                f_landau_gaus.append(dirpath+'/'+fname)
    histos = {}
    for f in f_landau_gaus:
        print '\t',f
        fname = f.split('/')[-1].split('.')[0]
        fname = fname[fname.find('-run-')+5:]
        fname = fname.split('-')
        f_new = os.path.abspath(f)

        run = int(fname[0])
        print '\t\trun',run
        print '\t\tfname',fname
        statbuf = os.stat(f_new)
        delta_time = time.time()-statbuf.st_mtime
        print "\t\tdelta time:",delta_time
        print "\t\tlast change:",datetime.datetime.fromtimestamp(statbuf.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        if delta_time > (24*3600):
            raw_input('key press')
        root_file  = ROOT.TFile.Open(f_new)

        if not root_file:
            print 'CANNOT FIND ROOT FILE!!!!',f,f_new
            continue
        canvas = root_file.Get('time_canvas')
        for key in canvas.GetListOfPrimitives():
            prim  = canvas.GetPrimitive(key.GetName()).Clone()
            if 'h_time_2d' == key.GetName():
                histos[run] = (copy.deepcopy(prim),copy.deepcopy(copy.deepcopy(prim.ProjectionY())))
        print '\t\tadded %d histos.'%len(histos)
    return histos


def draw_voltage_scan(my_style,raw_bias,last_means,rate):
    print 'draw_voltage_scan'

    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    if parser.has_option('Calibration','ADC'):
        calibration = parser.getfloat('Calibration','ADC')
    else:
        calibration = 1.0
    pos_means = []
    neg_means = []
    pos_bias =  []
    neg_bias =  []
    l = map(lambda x,y: [x,round(y*calibration,1)],raw_bias,last_means)
    for bias,mean in (l):
        if bias < 0:
            neg_bias.append((-1.*bias,mean))
        else:
            pos_bias.append((bias,mean))
    bias = -1e9
    print 'positive check of ', pos_bias
    new_bias = []
    for b in pos_bias:
        if b[0] < bias:
            print 'ignore pos',b
        else:
            bias = b[0]
            new_bias.append(b)
    pos_bias = new_bias

    bias = -1e9
    new_bias = []
    for b in neg_bias:
        if b[0] < bias:
            print 'ignore neg',b
        else:
            bias = b[0]
            new_bias.append(b)
    neg_bias = new_bias
    print 'neg check of',neg_bias
    print sorted(raw_bias)
    print len(pos_bias),len(neg_bias)

    if len(pos_bias) == 0 or len(neg_bias) == 0:
        return

    g_pos = ROOT.TGraph(len(pos_bias))
    g_pos.SetName('g_pos')
    g_pos.SetTitle('positive Bias')
    g_pos.SetMarkerStyle(22)
    g_pos.SetMarkerSize(2)
    g_pos.SetMarkerColor(ROOT.kRed)
    g_pos.SetFillColor(0)
    g_pos.SetFillStyle(0)
    for i in range(len(pos_bias)):
        g_pos.SetPoint(i,pos_bias[i][0],pos_bias[i][1])
    g_neg = ROOT.TGraph(len(neg_bias))
    g_neg.SetName('g_neg')
    g_neg.SetTitle('negative Bias')
    g_neg.SetMarkerStyle(23)
    g_neg.SetMarkerSize(2)
    g_neg.SetMarkerColor(ROOT.kGreen)
    g_neg.SetFillColor(0)
    g_neg.SetFillStyle(0)
    for i in range(len(neg_bias)):
        g_neg.SetPoint(i,neg_bias[i][0],neg_bias[i][1])

    c1 = my_style.get_canvas('rate_scan_development')
    xmin = 0
    xmax = 1000
    delta = xmax-xmin
    xmin = xmin - .1*delta
    xmax = xmax + .1*delta
    ymax = max(last_means)*calibration
    ymin = min(last_means + [0])*calibration
    delta = ymax - ymin
    ymax = ymax + delta*.1
    ymin = ymin - delta*.1
    frame_plot = c1.DrawFrame(xmin,ymin,xmax,ymax)
    mg = ROOT.TMultiGraph('mg',';bias / V; signal / adc')
    mg.Add(g_pos)
    mg.Add(g_neg)
    mg.Draw('PL')
    leg = my_style.make_legend(.5,.5,2)
    leg.AddEntry(g_pos)
    leg.AddEntry(g_neg)
    leg.Draw()
    frame_plot.GetYaxis().SetTitleOffset(frame_plot.GetYaxis().GetTitleOffset()*1.1)
    if parser.has_option('Calibration','ADC'):
        frame_plot.GetYaxis().SetTitle(parser.get('Calibration','Title'))
    else:
        frame_plot.GetYaxis().SetTitle('signal / adc')
    frame_plot.GetXaxis().SetTitle(' #||{bias voltage} / V')
    c1.Update()
    my_style.save_canvas(c1,'bias_scan_means_rate_%1.0E'%(rate))

def create_graph(dia_name,my_style,xx,mmps,mmeans,ppedestals,bias,rate = 0,draw_mp = True):

    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    if parser.has_option('Calibration','ADC'):
        calibration = parser.getfloat('Calibration','ADC')
    else:
        calibration = 1.0

    is_bias_scan = (bias ==0)
    x = xx[0]
    if len(x) == 0:
        return
    e_x = xx[1]

    mps = map(lambda x: calibration*x,mmps[0])
    print mmps[0],mps
    e_mps =  map(lambda x: calibration*x,mmps[1])
    means =  map(lambda x: calibration*x,mmeans[0])
    e_means =  map(lambda x: calibration*x,mmeans[1])
    pedestals =  map(lambda x: calibration*x,ppedestals[0])
    e_pedestals =  map(lambda x: calibration*x,ppedestals[1])
    print 'create graph for bias'
    ratios = []
    for i in range(len(x)):
        ratios.append(means[i]/mps[i])

    c1 = my_style.get_canvas('rate_scan_development')
    if bias == 0:
        option =''
    else:
        option = 'logx'
    if draw_mp:
        pad_plot  = my_style.make_pad('plot',option)
        pad_ratio = my_style.make_pad('ratio',option)
        pad_plot.SetTicks(1,1)
        pad_ratio.SetTicks(1,1)
    else:
        pad_plot = c1
        if option=='logx':
            c1.SetLogx()

    g_mp = ROOT.TGraph(len(x))
    g_mp.SetName('g_mp')
    g_mp.SetTitle('MP')
    g_mp.SetMarkerStyle(20)
    g_mp.SetMarkerColor(ROOT.kBlue)
    g_mp.SetFillColor(0)
    g_mp.SetFillStyle(0)

    g_mean = ROOT.TGraphErrors(len(x))
    g_mean.SetName('g_mean')
    g_mean.SetTitle('mean')
    g_mean.SetMarkerStyle(21)
    g_mean.SetMarkerColor(ROOT.kGreen)
    g_mean.SetFillColor(0)
    g_mean.SetFillStyle(0)

    g_ratio = ROOT.TGraphErrors(len(x))
    g_ratio.SetName('g_ratio')
    g_ratio.SetTitle('mean / mpv')
    g_ratio.SetMarkerStyle(22)
    g_ratio.SetMarkerColor(ROOT.kRed)
    g_ratio.SetFillColor(0)
    g_ratio.SetFillStyle(0)

    g_pedestal = ROOT.TGraphErrors(len(x))
    g_pedestal.SetName('g_pedestals')
    g_pedestal.SetTitle('Pedestal')
    g_pedestal.SetMarkerStyle(20)
    g_pedestal.SetMarkerColor(ROOT.kViolet)
    g_pedestal.SetFillColor(0)
    g_pedestal.SetFillStyle(0)

    for i in range(len(x)):
        r = x[i]
        g_mp.SetPoint(i,x[i],mps[i])
        g_mean.SetPoint(i,x[i],means[i])
        g_ratio.SetPoint(i,x[i],ratios[i])
        g_mean.SetPointError(i,e_x[i],1.)
        g_pedestal.SetPoint(i,x[i],pedestals[i])
        g_pedestal.SetPointError(i,0,e_pedestals[i])
    if draw_mp:
        pad_plot.cd()
    else:
        c1.cd()
    xmin = min(x)
    xmax = max(x)
    if bias != 0:
        xmin = (xmin/10**int(math.log10(xmin))-1)*10**int(math.log10(xmin))
        xmax = (xmax/10**int(math.log10(xmax))+1)*10**int(math.log10(xmax))
    else:
        delta = xmax-xmin
        xmin = xmin - .1*delta
        xmax = xmax + .1*delta
    ymax = max(means+mps+pedestals)
    ymin = min(means+mps+pedestals)

    delta = ymax - ymin
    ymax = ymax + delta*.1
    ymin = ymin - delta*.1
    ymin = min(ymin, min(lambda x,y: x-y, pedestals,e_pedestals))
    frame_plot = pad_plot.DrawFrame(xmin,ymin,xmax,ymax)
    if not is_bias_scan:
        mg = ROOT.TMultiGraph('mg',';rate / #frac{Hz}{cm^{2}}; signal / adc')
    else:
        mg = ROOT.TMultiGraph('mg',';bias / V; signal / adc')
    if draw_mp:
        mg.Add(g_mp)
    mg.Add(g_mean)
    mg.Add(g_pedestal)
    mg.Draw('P')
    frame_plot.GetYaxis().SetTitleOffset(frame_plot.GetYaxis().GetTitleOffset()*1.1)
    if parser.has_option('Calibration','ADC'):
        frame_plot.GetYaxis().SetTitle( parser.get('Calibration','Title'))
    else:
        frame_plot.GetYaxis().SetTitle('signal / adc')
    if bias != 0:
        frame_plot.GetXaxis().SetTitle(' #frac{Hz}{cm^{2}}')
    else:
        frame_plot.GetXaxis().SetTitle('bias voltage / V')
    # mg.GetXaxis().SetRangeUser(1,2.2e6)
    if draw_mp:
        n = 3
    else:
        n = 2
    if not is_bias_scan:
        leg = my_style.make_legend(.4,.55,n)
    else:

        if min(x) < 0:
            if max(x) > 0:
                sign = 'all'
            else:
                sign = 'neg'
        else:
            sign = 'pos'
        if sign == 'neg':
            leg = my_style.make_legend(.2,.65,n)
        else:
            leg = my_style.make_legend(.7,.65,n)
    if draw_mp:
        leg.AddEntry(g_mp)
    leg.AddEntry(g_mean)
    leg.AddEntry(g_pedestal)
    leg.Draw()
    c1.Update()

    if draw_mp:
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
        g_ratio.Draw('LP')

    pad_plot.cd()
    arrow = ROOT.TArrow()
    arrow_means = []
    arrow_mps = []
    arrow_pedestals = []
    for i in range(len(x)-1):
        if math.copysign(1,x[i+1]) != math.copysign(1,x[i]):
            continue
        arrow_means.append(arrow.DrawArrow(x[i],means[i],x[i+1],means[i+1],0.02,'->-'))
        arrow_pedestals.append(arrow.DrawArrow(x[i],pedestals[i],x[i+1],pedestals[i+1],0.02,'--'))
        if draw_mp:
            arrow_mps.append(arrow.DrawArrow(x[i],mps[i],x[i+1],mps[i+1],0.02,'->-'))
    c1.Update()
    if bias != 0:
        pt = ROOT.TPaveText(0.01,0.01,0.3,0.1,'NDC')
        pt.SetTextAlign(12)
        pt.SetTextSize(.03)
        pt.SetTextFont(42)
        pt.AddText('Diamond: %s'%dia_name)
        pt.AddText('Bias: %+5d V'%bias)
        pt.SetFillStyle(0)
        pt.SetFillColor(0)
        pt.SetBorderSize(0)
        pt.SetLineColor(0)
        pt.SetLineWidth(0)
        pt.Draw()
        my_style.save_canvas(c1,'rate_scan_%s_means'%get_voltage_string(bias))
    else:
        if min(x) < 0:
            if max(x) > 0:
                sign = 'all'
            else:
                sign = 'neg'
        else:
            sign = 'pos'
        print 'X:',sorted(x)
        pt = ROOT.TPaveText(0.01,0.01,0.3,0.1,'NDC')
        pt.SetTextAlign(12)
        pt.SetTextSize(.03)
        pt.SetTextFont(42)
        pt.AddText('Diamond: %s'%dia_name)
        pt.AddText('Rate: %1.0E Hz/cm^{2}'%rate)
        pt.SetFillStyle(0)
        pt.SetFillColor(0)
        pt.SetBorderSize(0)
        pt.SetLineColor(0)
        pt.SetLineWidth(0)
        pt.Draw()
        # raw_input(sign)
        my_style.save_canvas(c1,'bias_scan_%s_means_rate_%1.0E'%(sign,rate))

def get_pedestal_histo(directory,this_run):
    print 'get_pedestal_histo',
    print directory,this_run
    input_dir = directory+'/../../pedestal/root/'
    print input_dir
    input_dir = os.path.abspath(input_dir)
    print input_dir
    print this_run.pedestal_run
    if this_run.pedestal_run <0:
        return None
    ped_run = RunInfo.RunInfo.runs[this_run.pedestal_run]
    fname = 'pedestal_{dia}-run-{run:03d}-{volt}-{fs11}_{fsh13}-pedestal.root'.format(
        dia = ped_run.diamond,
        run = ped_run.pedestal_run,
        volt = ped_run.get_voltage_string(False),
        fs11 = ped_run.fs11,
        fsh13= abs(ped_run.fsh13)
        )
    print fname
    f = input_dir + '/' + fname
    print f
    if not os.path.exists(f):
        warnings.warn('cannot find %s'%f)
        return None
    root_file = ROOT.TFile.Open(f)
    print root_file
    histo = None
    canvas = root_file.Get('foo')
    print canvas,list(canvas.GetListOfPrimitives())
    for key in canvas.GetListOfPrimitives():
        prim  = canvas.GetPrimitive(key.GetName())
        if 'h_time_2d_py' == key.GetName() or 'h_raw_factor' == key.GetName():
            print 'added',key, prim.GetName()
            histo  = copy.deepcopy(prim.Clone())
    if not histo:
        print root_file != None, canvas!=None, histo!=None
        if canvas:
            print [key.GetName() for key in canvas.GetListOfPrimitives()]
        warnings.warn('cannot find canvas in %s'%f)
        raw_input('Press key')
    return histo

def create_pedestal_histos(my_style,all_histos,raw_bias,raw_rates,run_infos):
    print len(all_histos),all_histos
    print len(raw_bias), raw_bias
    print len(raw_rates), raw_rates
    c1 = my_style.get_canvas('overview')
    n_histos = len(all_histos)
    if n_histos > 5:
        col = 2
        rows = n_histos / 5 + (n_histos % 5 + 4) / 5
    else:
        col = 1
        rows = n_histos
    while col*rows < n_histos:
        rows += 1
    c1.Divide(col,rows)
    colors = [ROOT.kBlack,ROOT.kBlue]
    pts = []
    for i in range(len(all_histos)):
        c1.cd(i+1)
        c1.cd(i+1).DrawFrame(-100,0,500,1.1)
        for j in range(len(all_histos[i])):
            h = all_histos[i][j]
            if not h:
                continue
            h.SetLineColor(colors[j])
            maximum = h.GetBinContent(h.GetMaximumBin())
            if maximum == 0:
                maximum = 1.
            h.Scale(1./maximum)
            print h.GetBinContent(h.GetMaximumBin())
            all_histos[i][j].Draw('same')
        print i,'add pave text'
        pt = run_infos[i].addDiamondInfo(.65, .3,.80,.75)
        pt.AddText('Pedestal: %+4.1f +/- %3.1f'%(run_infos[i].pedestal,run_infos[i].pedestal_sigma))
        pts.append(pt)
        pt.Draw()
    name = 'pedestal'
    if len(set(raw_bias)) == 1:
        name += '_rate_scan_bias_%s'%get_voltage_string(raw_bias[-1])
    elif len(set(raw_rates)) == 1:
        if len(raw_bias)> 0 and min(raw_bias) < 0:
            if max(raw_bias) > 0:
                sign = 'all'
            else:
                sign = 'neg'
        else:
            sign = 'pos'
        name += '_bias_scan_%s_rate_%1.0EHz'%(sign,raw_rates[-1])
    else:
        if len(raw_bias)==0:
            raw_bias = [9999]
        if len(raw_rates)==0:
            raw_rates = ['UNKNOWN']
        name += '_bias_%s_rate_%1.0E'%(get_voltage_string(raw_bias[i]),raw_rates[i])

    my_style.save_canvas(c1,name)


