#!/usr/bin/env python

"""
Analysis of the Runs and plot production
"""

# ##############################
# Imports
###############################

import pickle
import ROOT, copy, sys, math, os
from RunInfo import RunInfo
import AnalyzeHelpers as ah
import warnings
import root_style
import ConfigParser

try:
    import progressbar

    progressbar_loaded = True
except ImportError, e:
    print 'Module "progressbar" is installed, fall back to no progressbar'
    progressbar_loaded = False
    pass
###############################
# Usage
###############################
def usage():
    print 'use this thusly:'
    print '    ./Analyze.py <runnumber>'
    return

ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.Eval)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.Minimization)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.Plotting)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.Fitting)
ROOT.RooMsgService.instance().setSilentMode(True)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.FATAL)
###############################
# set the palette to 53
###############################
this_style = root_style.root_style()
width = 1000

ROOT.gStyle.SetPalette(53)
ROOT.gStyle.SetNumberContours(999)

ROOT.gROOT.SetBatch()
this_style.set_style(width, width, 1)

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def saveCanvas(c1, name,save_to_rootfile = True):
    #print 'Save Canvas:',name
    name = name.split('/')
    fdir = '/'.join(name[:-1])
    this_style.main_dir = fdir
    this_style.save_canvas(c1, name[-1])
    if save_to_rootfile:
        c1.Write('', ROOT.TObject.kWriteDelete)

def getPedestalValue(hist):
    # tmp_hist = copy.deepcopy(hist.ProjectionY())
    tmp_hist = copy.deepcopy(hist)
    tmp_hist.SetBinContent(0, 0)
    tmp_hist.SetBinContent(1, 0)
    tmp_hist.SetBinContent(tmp_hist.GetNbinsX(), 0)
    tmp_hist.SetBinContent(tmp_hist.GetNbinsX() + 1, 0)
    rms = tmp_hist.GetRMS()
    maximum_bin = tmp_hist.GetMaximumBin()
    maximum = tmp_hist.GetBinContent(maximum_bin)
    mp = tmp_hist.GetBinCenter(maximum_bin)
    x_low = maximum_bin
    x_high = maximum_bin
    while tmp_hist.GetBinContent(x_low) > maximum / 2 and x_low > 0:
        x_low -= 1
    x_low = tmp_hist.GetBinCenter(x_low)
    while tmp_hist.GetBinContent(x_high) > maximum / 2 and x_high < tmp_hist.GetNbinsX():
        x_high += 1
    x_high = tmp_hist.GetBinCenter(x_high)
    fwhm = x_high - x_low
    fit_range = min(rms, fwhm)
    # print 'mp',mp,'rms',rms,'fwhm',fwhm, 'range',fit_range
    func = ROOT.TF1('gaus_fit', 'gaus', mp - fit_range / 2, mp + fit_range / 2)
    tmp_hist.Fit(func, 'Q', '', mp - rms / 2, mp + rms / 2)
    central = func.GetParameter(1)
    sigma = func.GetParameter(2)
    c0 = ROOT.TCanvas('foo', 'bar', 600, 600)
    tmp_hist.Draw('')
    tmp_hist.GetXaxis().SetTitle('signal in adc')
    lat = ROOT.TLatex()
    lat.SetNDC()
    lat.DrawLatex(0.5, 0.03, 'pedestal')
    func.Draw('same')
    pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
    pave.Draw()
    saveCanvas(c0, targetdir + '/' + 'pedestal_' + prefix)
    return central, sigma

def get_single_projections(prof,initial_scaling = False):
    histos = []
    for ybin in range(1,prof.GetNbinsY()+1):
        histo = prof.ProjectionX(prof.GetName()+'_%d'%ybin,ybin,ybin)
        if initial_scaling:
            histo.Scale(1./histo.GetBinContent(1))
        else:
            print histo.GetName(),[histo.GetBinContent(bin) for bin in range(1,histo.GetNbinsX()+1)]

        histo.SetTitle(prof.GetYaxis().GetBinLabel(ybin))
        histos.append(histo)
    return histos

def get_projection_plot(h_signal_cp,h_entries_cp,ybin,zmin,zmax,maximum):
    ymin = h_signal_cp.GetYaxis().GetBinLowEdge(ybin)
    ymax = h_signal_cp.GetYaxis().GetBinUpEdge(ybin)
    h_signal_cp.GetYaxis().SetRange(ybin, ybin)
    h_entries_cp.GetYaxis().SetRange(ybin, ybin)
    proj_signal = copy.deepcopy(h_signal_cp.Project3D('xz'))
    proj_entries = copy.deepcopy(h_entries_cp.Project3D('xz'))
    print ybin, proj_signal.GetEntries(), proj_entries.GetEntries()
    prof = copy.deepcopy(proj_signal)
    prof.SetName('h_avrgsignal_ybin%d' % ybin)
    prof.SetTitle('Profile y pos %4.1f - %4.1f cm' % (ymin, ymax))
    prof.Divide(proj_entries)
    for j in range(1,prof.GetNbinsY()+1):
        prof.GetYaxis().SetBinLabel(j,'Pos %d %d'%(j,ybin))
    prof.GetYaxis().SetLabelSize(prof.GetYaxis().GetLabelSize()*2)
    prof.GetYaxis().SetLabelOffset(prof.GetYaxis().GetLabelOffset()/2)
    prof.GetYaxis().SetNdivisions(prof.GetNbinsY()*100)
    prof.Draw('colz')
    prof.GetYaxis().SetTitle('x pos / cm')
    prof.GetXaxis().SetTitle('minutes')
    prof.GetZaxis().SetRangeUser(zmin, zmax)
    if my_run.data_type == 3:
        prof.GetXaxis().SetTitle('n*10 minutes')
    prof.Draw('colz')
    proj_entries.Draw('sameTEXT')
    prof_rel = copy.deepcopy(prof)
    prof_rel.Scale(1. / maximum)
    prof_rel.GetZaxis().SetRangeUser(0, 1.05)
    return prof,prof_rel,proj_entries

def create_stacks(name,projections,ybin=-1,entries=4):
    c0 = this_style.get_canvas(name)
    c0.cd()
    stack = ROOT.THStack('stack_'+name,':Time:Signal/adc')
    i=0
    mins = []
    maxs = []
    g_range = ROOT.TGraphErrors(len(projections))
    g_range.SetName('g_range_'+name)
    g_range.SetTitle('h_range_'+name)
    for p in projections:
        signals = [p.GetBinContent(bin) for bin in range(1,p.GetNbinsX())]
        print projections.index(p), min(signals),max(signals)
    for histo in projections:
        histo.GetXaxis().SetRange(1,histo.GetXaxis().GetNbins()-1)
        ymin = min(filter(lambda x: x>0, [histo.GetBinContent(bin) for bin in range(1,histo.GetNbinsX())]))
        ymax = max(filter(lambda x: x>0, [histo.GetBinContent(bin) for bin in range(1,histo.GetNbinsX())]))
        mins.append(ymin)
        maxs.append(ymax)
        g_range.SetPoint(projections.index(histo),projections.index(histo),(ymax+ymin)/2)
        g_range.SetPointError(projections.index(histo),0,ymax-(ymax+ymin)/2)
        i+=1
        histo.SetLineColor(i)
        stack.Add(copy.deepcopy(histo))
    stack.Draw('nostack')
    factor = .1

    y_min = min(mins)
    y_max = max(maxs)
    print y_min,y_max
    delta = y_max - y_min
    y_min = y_min - factor * delta
    y_max = y_max + factor * delta
    stack.GetYaxis().SetRangeUser(y_min,y_max)
    stack.SetMaximum(y_max)
    stack.SetMinimum(y_min)
    leg = this_style.make_legend(.20,.45,len(projections))
    for histo in projections:
        j = projections.index(histo)
        if ybin == -1:
            y = j/entries
        else:
            y = ybin
        title = 'Pos %d %d'%(j%entries+1,y)
        leg.AddEntry(histo, title,'l')
    stack.Draw('nostack')
    stack.GetXaxis().SetTitle('Time')
    stack.GetYaxis().SetTitle('signal adc')
    leg.Draw()
    pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
    pave.Draw()
    saveCanvas(c0, targetdir + '/' + name+ '_'+prefix)
    c1 = this_style.get_canvas('g_range_'+name)
    g_range.Draw('AP0')
    y_min = g_range.GetYaxis().GetXmin()
    y_max = g_range.GetYaxis().GetXmax()
    print y_min,y_max

    g_range.GetXaxis().SetRangeUser(-5,i)
    g_range.GetXaxis().SetTitle('')
    g_range.GetYaxis().SetTitle('Range')
    frame = c1.DrawFrame(-.5,y_min,i,y_max)
    for j in range(0,i):
        if ybin == -1:
            y = j/entries
        else:
            y = ybin
        bin= g_range.GetXaxis().FindBin(j)
        g_range.GetXaxis().SetBinLabel(bin, 'Pos %d %d'%(j%entries+1,y+1))
        bin= frame.GetXaxis().FindBin(j)
        frame.GetXaxis().SetBinLabel(bin, 'Pos %d %d'%(j%entries+1,y+1))
    c1.Update()
    g_range.Draw('0P')
    saveCanvas(c1, targetdir + '/g_range_' + name+ '_'+prefix)
    print 'done'

def make_circled_time_plots(hSignal, hEntries,):
    circles = my_run.get_mask().areas
    h_entries = copy.deepcopy(hEntries)
    h_signal2 = copy.deepcopy(hSignal)
    h_entries2 = copy.deepcopy(hEntries)

    this_style.set_style(width,width,1)
    c1 = this_style.get_canvas('time_plots_circled')
    if len(circles) > 0:
        h_signal = copy.deepcopy(hSignal)
        h_signal.GetXaxis().SetRange()
        h_signal.GetYaxis().SetRange()
        h_signal.GetZaxis().SetRange()
        h_entries.GetXaxis().SetRange()
        h_entries.GetYaxis().SetRange()
        h_entries.GetZaxis().SetRange()
        signal_histos = []
        highs = [ROOT.kRed,ROOT.kMagenta,ROOT.kOrange,ROOT.kRed +2,ROOT.kPink]
        lows = [ROOT.kBlue,ROOT.kCyan,ROOT.kBlue+3,ROOT.kBlue-7]
        n_low = 0
        n_high = 0
        for circle in circles:
            if 'low' in circle[3]:
                color = lows[n_low]
                n_low += 1
            else:
                color = highs[n_high]
                n_high+=1
            index = circles.index(circle)
            descr = '%s_'%index + circle[3]
            signal, entries, rel = ah.make_area_time_plot(h_signal, h_entries, circle[0],circle[1],circle[2],descr)
            signal.SetTitle(descr)
            signal.SetLineColor(color)
            signal.SetMarkerColor(color)
            signal.SetMarkerSize(2)
            signal.SetMarkerStyle(20+index)
            signal.GetYaxis().SetRangeUser(50., 320.)
            c1.cd()
            signal_histos.append(copy.deepcopy(signal))
            signal.Draw('E1')
            fit = ROOT.TF1('fit_%s'%descr,'pol0')
            minx = signal.GetXaxis().GetBinCenter(2)
            maxx = signal.GetXaxis().GetBinCenter(signal.GetNbinsX()-1)
            signal.Fit(fit,'Wq','',minx,maxx)
            # entries.Draw('TEXTsame')
            pave = ah.addDiamondInfo(0.01, 0.01, 0.15, 0.09, my_run)
            pave.Draw()
            n_entries = [entries.GetBinContent(b) for b in range(1,entries.GetNbinsX()+1)]
            n_entries = filter(lambda x:x>0,n_entries)
            mean_events,sigma = ah.get_mean_and_sigma(n_entries)
            text = 'avrg. entries: %4d +/- %2d'%(mean_events,sigma)
            y_pos = .2
            pt = ROOT.TPaveText(.5,y_pos,.5,y_pos,'NDC NB')
            values = [signal_histos[-1].GetBinContent(b) for b in range(1,entries.GetNbinsX()+1)]
            print values
            values = values[1:-1]
            mean = reduce(lambda x, y: x+y,values)/len(values)
            values2=map(lambda x: x**2, values)
            mean2 = reduce(lambda x, y: x+y,values2)/len(values)
            sigma = math.sqrt(mean2-mean**2)
            pt.AddText(text)
            text = 'mean: %.2f +/- %.3f'%(mean,sigma)#(fit.GetParameter(0),fit.GetParError(0))
            print text
            print 'calc. mean: %.2f +/- %.3f'%(mean,sigma)
            signal_histos[-1].SetTitle('%s: %.2f +/- %.3f'%(descr,mean,sigma))#fit.GetParameter(0),fit.GetParError(0)))
            pt.AddText(text)
            pt.SetTextSize(0.03)
            pt.Draw()
            #hSignalTime_%s
            saveCanvas(c1,targetdir + '/hSignalTime_circle_%d_%s'%(index,circle[3])+ '_'+prefix)

        stack = ROOT.THStack('hstack','all plots:minutes:avrg. Signal')
        for histo in signal_histos:
            stack.Add(histo,"P hist")
        stack.Draw('nostack')
        pave = ah.addDiamondInfo(0.01, 0.01, 0.15, 0.09, my_run)
        pave.Draw()
        leg = this_style.make_legend(.3,.45,len(signal_histos))
        for histo in signal_histos:
            leg.AddEntry(histo)

        leg.Draw()
        saveCanvas(c1,targetdir + '/hSignalTime_circle_all_'+prefix)
    this_style.set_style(width+200,width,1)
    c1 = this_style.get_canvas('time_plots_circled')
    signal = copy.deepcopy(h_signal2.Project3D('yx'))
    entries = copy.deepcopy(h_entries2.Project3D('yx'))
    signal.Divide(entries)
    signal.Draw('colz')
    signal.GetXaxis().SetRangeUser(my_run.get_mask().min_x,my_run.get_mask().max_x)
    signal.GetYaxis().SetRangeUser(my_run.get_mask().min_y,my_run.get_mask().max_y)
    fname = 'xy_plots_range.pl'
    try:
        ranges = pickle.load(open(fname, "rb"))
    except IOError:
        ranges = {}
    key = my_run.diamond+'_3D'
    zmin,zmax = ah.find_range_3d(signal)
    if key in ranges:
        zmin = min(ranges[key][0],zmin)
        zmax = max(ranges[key][1],zmax)
        print "Found Range: ",ranges[key]
    if zmin < zmax:
        ##signal.GetZaxis().SetRangeUser(zmin,zmax)
        signal.GetZaxis().SetRangeUser(110,305)
    ranges[key] = [zmin,zmax]
    pickle.dump(ranges, open(fname, "wb"))

    signal.Draw('colz')
    c1.Update()
    drawn_circles = []
    for circle in circles:
        index = circles.index(circle)
        x = circle[0]
        y = circle[1]
        r = circle[2]
        if 'low' in circle[3]:
            color = ROOT.kBlue
        else:
            color = ROOT.kPink
        if 'square' in circle[3]:
            circ = ROOT.TBox(x-r/2,y-r/2,x+r/2,y+r/2)
        else:
            circ = ROOT.TEllipse(x,y,r,r)
        drawn_circles.append(copy.deepcopy(circ))
        drawn_circles[-1].SetLineColor(color)
        drawn_circles[-1].SetLineWidth(2)
        drawn_circles[-1].SetFillStyle(0)
        drawn_circles[-1].Draw('same')
        pt = ROOT.TPaveText(x,y,x,y,'nb')
        descr = '%s_'%index + circle[3]
        pt.AddText(descr)
        pt.SetTextSize(0.02)
        pt.SetTextColor(color)
        drawn_circles.append(pt)
        drawn_circles[-1].Draw('same')

    c1.Update()
    pave = (ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run))
    pave.Draw()
    saveCanvas(c1,targetdir + '/'+'time_plots_circle_positions_'+prefix,False)
    this_style.set_style(width,width,1)

def makeTimePlots(h_time_2d, name='time_2d'):
    if name == 'time_2d':
        profileY = h_time_2d.ProfileY()
        neg_landau = False
        if profileY.GetMean() < 0.:
            neg_landau = True

        if neg_landau:
            func = ROOT.TF1('my_landau', '[0] * TMath::Landau(-x,[1],[2])', h_time_2d.GetYaxis().GetXmin(),
                            h_time_2d.GetYaxis().GetXmax())
        else:
            func = ROOT.TF1('my_landau', '[0] * TMath::Landau(x,[1],[2])', h_time_2d.GetYaxis().GetXmin(),
                            h_time_2d.GetYaxis().GetXmax())
        func.SetParameters(1, h_time_2d.GetMean(), h_time_2d.GetRMS())

        land = copy.deepcopy(h_time_2d.ProjectionY())
        fit_res = ah.fitLandauGaus(land, True)
        this_style.set_style(1200, 600, 1 / 2.)
        c0 = this_style.get_canvas('time_canvas')
        c0.cd()
        this_style.print_margins()
        fit_res[2].Draw()
        pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
        pave.Draw()
        saveCanvas(c0, targetdir + '/' + 'landauGaus_' + prefix)
        fit_res[-1].Draw()
        pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
        pave.Draw()
        saveCanvas(c0, targetdir + '/' + 'histo_' + prefix)
        # return

    arr = ROOT.TObjArray()
    h_time_2d.FitSlicesY(func, 0, -1, 0, 'QNR', arr)

    mpvs = arr[1]  ## MPVs are fit parameter 1
    if neg_landau:
        mpvs.Scale(-1.)

    mpvs.SetMarkerStyle(24)
    mpvs.SetMarkerColor(ROOT.kBlack)
    mpvs.SetMarkerSize(0.8)
    mpvs.SetLineColor(ROOT.kBlack)

    errs = arr[2]
    for ibin in range(1, mpvs.GetNbinsX() + 1):
        mpvs.SetBinError(ibin, errs.GetBinContent(ibin))

    h_time_2d.SetTitle('Time evolution of the signal pulse')
    # x-axis
    h_time_2d.GetXaxis().SetTitle('minutes')
    if my_run.data_type == 3: h_time_2d.GetXaxis().SetTitle('n*10 minutes')
    h_time_2d.GetXaxis().SetTitleSize(0.05)
    h_time_2d.GetXaxis().SetLabelSize(0.05)

    # y-axis
    h_time_2d.GetYaxis().SetTitle('pulse height')
    h_time_2d.GetYaxis().SetLabelSize(0.05)
    h_time_2d.GetYaxis().SetTitleSize(0.05)
    h_time_2d.GetYaxis().SetRangeUser(-100, 500)
    h_time_2d.Draw('colz')

    pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
    mpvs.Draw('same pe')
    pave.Draw()
    saveCanvas(c0, targetdir + '/' + name + prefix)
    return arr

def makeXYPlots(h_3d):
    if my_run.calibration_event_fraction < 0.5:
        return
    cp2d = copy.deepcopy(h_3d.Project3D('yx'))

    tmp_size = ROOT.gStyle.GetTitleSize()
    tmp_marg_right = ROOT.gStyle.GetPadRightMargin()
    tmp_marg_left = ROOT.gStyle.GetPadLeftMargin()
    tmp_marg_top = ROOT.gStyle.GetPadTopMargin()
    tmp_marg_Bottom = ROOT.gStyle.GetPadBottomMargin()

    # set some style parameters
    ROOT.gStyle.SetTitleSize(0.07, 't')
    ROOT.gStyle.SetPadRightMargin(0.12)
    ROOT.gStyle.SetPadLeftMargin(0.12)
    ROOT.gStyle.SetPadBottomMargin(0.12)
    ROOT.gStyle.SetPadTopMargin(0.12)
    # y axis
    cp2d.GetXaxis().SetTitle('cm')
    cp2d.GetXaxis().SetTitleSize(0.06)
    cp2d.GetXaxis().SetLabelSize(0.06)
    cp2d.GetXaxis().SetTitleOffset(0.8)
    cp2d.GetXaxis().SetNdivisions(505)
    # y axis
    cp2d.GetYaxis().SetTitle('cm')
    cp2d.GetYaxis().SetTitleSize(0.06)
    cp2d.GetYaxis().SetLabelSize(0.06)
    cp2d.GetYaxis().SetTitleOffset(1.0)
    cp2d.GetYaxis().SetNdivisions(505)

    h_2d_mpv = copy.deepcopy(cp2d)
    h_2d_sigma = copy.deepcopy(cp2d)
    h_2d_mean = copy.deepcopy(cp2d)
    h_2d_nfill = copy.deepcopy(cp2d)

    mpvs = []
    means = []
    sigmas = []

    counter = 0
    for xbin in range(1, h_3d.GetNbinsX() + 1):
        for ybin in range(1, h_3d.GetNbinsY() + 1):
            z_histo = h_3d.ProjectionZ(h_3d.GetName() + '_pz_' + str(xbin) + '_' + str(ybin), xbin, xbin, ybin, ybin)
            if z_histo.Integral() < 100.:
                continue
            counter += 1
            fit_res = ah.fitLandauGaus(z_histo)

            mean = z_histo.GetMean()
            mpv = z_histo.GetXaxis().GetBinCenter(z_histo.GetMaximumBin())
            sig = z_histo.GetRMS()

            mpvs.append(mpv)
            sigmas.append(sig)
            means.append(mean)

            h_2d_mpv.SetBinContent(xbin, ybin, mpv)
            h_2d_sigma.SetBinContent(xbin, ybin, sig)
            h_2d_mean.SetBinContent(xbin, ybin, mean)
            h_2d_nfill.SetBinContent(xbin, ybin, z_histo.Integral())

    #get ranges
    fname = 'xy_plots_range.pl'
    try:
        ranges = pickle.load(open(fname, "rb"))
    except IOError:
        ranges = {}
    dia = my_run.diamond
    central = ah.mean(means)
    old_range = ranges.get(dia, [1e9, -1e9])
    print dia
    print 'old range', old_range
    this_range = [central - 50, central + 50]
    print 'this range', this_range
    new_range = [min(old_range[0], this_range[0]), max(old_range[1], this_range[1])]
    print new_range
    ranges[dia] = new_range
    pickle.dump(ranges, open(fname, "wb"))

    #save canvases
    ROOT.gStyle.SetOptStat(0)
    c1 = this_style.get_canvas('space_resloved_means')
    ROOT.gPad.SetTicks(1, 1)
    h_2d_mean.SetTitle('XY distribution of mean PH')
    h_2d_mean.UseCurrentStyle()

    #only mean distribution
    h_2d_mean.Draw('colz')
    h_2d_mean.GetZaxis().SetRangeUser(new_range[0], new_range[1])
    pave = my_run.addDiamondInfo(0.6, 0.9, 0.9, 0.99)
    pave.Draw('same')
    c1.Update()
    saveCanvas(c1, targetdir + '/' + prefix + '_xyMeans')

    #mean and no of tracks
    c1 = this_style.get_canvas('space_resloved_signals')
    c1.Divide(1, 2)

    c1.cd(1)
    ROOT.gPad.SetTicks(1, 1)
    h_2d_nfill.SetTitle('number of tracks in XY')
    h_2d_nfill.Draw('colz')

    c1.cd(2)
    h_2d_mean.Draw('colz')
    h_2d_mean.GetZaxis().SetRangeUser(new_range[0], new_range[1])

    c1.cd(0)
    pave = my_run.addDiamondInfo(0.4, 0.45, 0.6, 0.55)
    pave.Draw('same')

    saveCanvas(c1, targetdir + '/' + prefix + '_xyPlots')
    # ROOT.gStyle.Reset()
    # reset the style
    ROOT.gStyle.SetTitleSize(tmp_size, 't')
    ROOT.gStyle.SetPadRightMargin(tmp_marg_right)
    ROOT.gStyle.SetPadLeftMargin(tmp_marg_left)
    ROOT.gStyle.SetPadBottomMargin(tmp_marg_Bottom)
    ROOT.gStyle.SetPadTopMargin(tmp_marg_top)

    del h_2d_mpv, h_2d_mean, h_2d_nfill, h_3d

## reorganize later
if __name__ == "__main__":

    ###############################
    # Get all the runs from the json
    ###############################

    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    RunInfo.load(parser.get('JSON', 'runs'))

    global my_rn
    ## my_rn  = int(sys.argv[-1])
    print 'argv:', sys.argv
    my_rn = int(
        [i for i in sys.argv if i.isdigit() == True][0])  ## search for the first number in the list of arguments
    my_run = RunInfo.runs[my_rn]
    # print my_run.__dict__

    ###############################
    # check if timing went alright
    ###############################
    ignore_timing = True
    if not ignore_timing:
        if my_run.calibration_event_fraction < 0.7:
            print 'timing didn\'t work. fraction below 70 %. redo the timing.'
            print 'exiting...'
            sys.exit(-1)

    reloadAnyway = False
    if 'reload' in sys.argv:
        reloadAnyway = True

    ###############################
    # get the correct file for the selected run
    ###############################

    # adapt these lines to find the right file eventually
    fname = 'results/runs/run_' + str(my_rn) + '/track_info.root'
    print fname
    if not os.path.isfile(fname):
        raise Exception('Cannot find File %s' % fname)
    infile = ROOT.TFile(fname, 'READ')
    my_tree = infile.Get('track_info')
    print my_tree

    n_ev = my_tree.GetEntries()

    print 'there\'s a total of %.0f events in the tree' % (n_ev)

    global loaded, targetdir, prefix
    loaded = False

    ###############################
    # get a bit of information for the correct folder and prefix for the plots
    ###############################

    voltage = my_run.bias_voltage
    if voltage > 0:
        volt_str = 'pos' + str(voltage)
    else:
        volt_str = 'neg' + str(-1 * voltage)

    # check run type
    rate = str(my_run.fs11) + '_' + str(abs(my_run.fsh13))
    if my_run.data_type == 0:
        runtype = 'rate-scan'
        #prefix = '{diamond}-run-{run:03d}-{volt_str}-{rate}-rate'
        prefix = my_run.diamond + '-run-' + '%03d' % (my_rn) + '-' + volt_str + '-' + rate + '-rate'
    elif my_run.data_type == 1:
        runtype = 'pedestal'
        prefix = my_run.diamond + '-run-' + '%03d' % (my_rn) + '-' + volt_str + '-' + rate + '-pedestal'
    elif my_run.data_type == 2:
        runtype = 'voltage-scan'
        prefix = my_run.diamond + '-run-' + '%03d' % (my_rn) + '-' + volt_str + '-' + rate + '-voltage'
    elif my_run.data_type == 3:
        runtype = 'rate-scan'
        prefix = my_run.diamond + '-run-' + '%03d' % (my_rn) + '-' + volt_str + '-' + rate + '-data-long'
    else:
        runtype = 'other'
        prefix = my_run.diamond + '-run-' + '%03d' % (my_rn) + '-' + volt_str + '-' + rate + '-other'

    targetdir = 'results/' + my_run.diamond + '/' + runtype + '/'
    if runtype == 'rate-scan':
        targetdir += volt_str+'/'

    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)


    ###############################
    # check if the histograms are already in the file. load them if they're there
    ###############################
    h_3d = None
    h_time_2d = None
    h_time_3d_signal = None
    h_time_3d_entries = None
    h_raw = None
    h_raw_factor = None
    h_pedestal = None
    h_signal = None
    print '%20s' % 'h_3dfull', infile.Get('h_3dfull') != None
    print '%20s' % 'h_time_2d', infile.Get('h_time_2d') != None
    print '%20s' % 'h_time_3d_signal', infile.Get('h_time_3d_signal') != None
    print '%20s' % 'h_time_3d_entries', infile.Get('h_time_3d_entries') != None
    print '%20s' % 'h_signal', infile.Get('h_signal') != None
    loaded  = True

    runPedestal = (my_run.data_type == 1)
    if runPedestal:
        if infile.Get('h_pedestal')!= None:
            h_pedestal = infile.Get('h_pedestal')
        else:
            loaded = False
    if loaded and infile.Get('h_3dfull') != None and \
                    infile.Get('h_time_2d') != None and \
                    infile.Get('h_time_3d_signal') != None and \
                    infile.Get('h_time_3d_entries') != None and \
                    infile.Get('h_raw') != None and \
                    infile.Get('h_raw_factor') != None and \
                    infile.Get('h_signal') != None:
        h_3d = copy.deepcopy(infile.Get('h_3dfull'))
        h_time_2d = copy.deepcopy(infile.Get('h_time_2d'))
        h_time_3d_signal = copy.deepcopy(infile.Get('h_time_3d_signal'))
        h_time_3d_entries = copy.deepcopy(infile.Get('h_time_3d_entries'))
        h_raw = copy.deepcopy(infile.Get('h_raw'))
        h_raw_factor = copy.deepcopy(infile.Get('h_raw_factor'))
        h_signal = copy.deepcopy(infile.Get('h_signal'))
        loaded = True
        print 'file already loaded'
    else:
        loaded = False


    # if the histograms aren't yet there, fill them. or do it if the user chooses to do so
    ###############################
    if reloadAnyway:
        loaded = False
    print 'loaded: ', loaded
    if not loaded:
        xmin = my_run.get_mask().min_x
        xmax = my_run.get_mask().max_x
        ymin = my_run.get_mask().min_y
        ymax = my_run.get_mask().max_y

        print 'loading the histograms into the root file'
        if h_3d:
            h_3d.Delete()
        h_3d = ROOT.TH3F('h_3dfull', '3D histogram',
                         25, xmin, xmax,
                         25, ymin, ymax,
                         250, -500.00, 500.00)
        h_3d_chn2offest = ROOT.TH3F('h_3dfull_chn2offest', '3D histogram with chn2 offset',
                                    25, xmin, xmax,
                                    25, ymin, ymax,
                                    250, -500.00, 500.00)

        ## runPedestal = math.isnan(my_run.pedestal) and (my_run.pedestal_run == -1 or my_run.number == my_run.pedestal_run)

        print 'is nan?', math.isnan(my_run.pedestal)
        if math.isnan(my_run.pedestal) and (my_run.pedestal_run != -1 and my_run.number != my_run.pedestal_run):
            print 'analyze the pedestal run first!! it\'s run', my_run.pedestal_run
            sys.exit()
        # if runPedestal:
        #     pedestal = 0.
        # else:
        pedestal = my_run.pedestal

        ########################################
        # get the times of first and last events
        ########################################

        # make the time binning 10 minutes for < 100 Hz and one minute above
        time_binning = 60.
        if my_run.rate_trigger < 100:
            time_binning = 600.

        my_tree.GetEntry(0)
        try:
            time_first = my_tree.timestamp
        except:
            time_first = my_tree.t_pad
        my_tree.GetEntry(n_ev - 1)

        try:
            time_last = my_tree.timestamp
        except:
            time_first = my_tree.t_pad
        length = time_last - time_first
        mins = length / 60.
        print mins
        if mins > 60:
            hours = int(mins / 60.)
            real_mins = mins % 60
            print 'Run of %d h and %f min length' % (int(hours), real_mins)
        else:
            print 'run of %.2f minutes length' % (mins)
        mins = length / time_binning


        if my_run.bias_voltage >= 0:
            factor = -1.0
        else:
            factor = 1.0

        if h_raw:
            h_raw.Delete()
        h_raw = ROOT.TH1F('h_raw','h_raw',1000, -500, 500.)
        h_raw.GetXaxis().SetTitle('Signal_{raw} / ADC')
        h_raw.GetYaxis().SetTitle('number of entries')
        if h_raw_factor:
            h_raw_factor.Delete()
        h_raw_factor = ROOT.TH1F('h_raw_factor','h_raw_factor: {0:+3.1f}'.format(factor),1000, -500, 500.)
        h_raw_factor.GetXaxis().SetTitle('Signal_{raw,factored} / ADC')
        h_raw_factor.GetYaxis().SetTitle('number of entries')

        if runPedestal:
            h_pedestal = ROOT.TH1F('h_pedestal','h_Pedestal',1000, -500, 500.)
            h_pedestal.GetXaxis().SetTitle('Pedestal / ADC')
            h_pedestal.GetYaxis().SetTitle('number of entries')

        if h_signal:
            h_signal.Delete()
        h_signal = ROOT.TH1F('h_signal','h_signal: {0:+6.1f}'.format(pedestal),1000, -500, 500.)
        h_signal.GetXaxis().SetTitle('signal / ADC')
        h_signal.GetYaxis().SetTitle('number of entries')

        if h_time_2d:
            h_time_2d.Delete()
        h_time_2d = ROOT.TH2F('h_time_2d', 'h_time_2d: {0:+6.1f}'.format(pedestal), int(mins + 1), 0., int(mins + 1), 1000, -500, 500.)
        h_time_2d.GetYaxis().SetTitle('Signal / adc')
        h_time_2d.GetXaxis().SetTitle('Time')
        h_time_2d_chn2offset = ROOT.TH2F('h_time_2d_chn2offset', 'h_time_2d_chn2offset', int(mins + 1), 0.,
                                         int(mins + 1), 1000, -500, 500.)
        if h_time_3d_signal:
            h_time_3d_signal.Delete()
        nbins = 48
        h_time_3d_signal = ROOT.TH3D('h_time_3d_signal', 'time evaluated 2d distribution:{0:+6.1f}'.format(pedestal),
                                     nbins, xmin, xmax,
                                     nbins, ymin, ymax,
                                     int(mins + 1), 0., int(mins + 1))
        h_time_3d_signal.GetXaxis().SetTitle('xpos / cm')
        h_time_3d_signal.GetYaxis().SetTitle('ypos /cm')
        h_time_3d_signal.GetZaxis().SetTitle('time / minutes')
        if h_time_3d_entries:
            h_time_3d_entries.Delete()
        h_time_3d_entries = ROOT.TH3D('h_time_3d_entries', 'time evaluated 2d distribution: {0:+6.1f}'.format(pedestal),
                                      nbins, xmin, xmax,
                                      nbins, ymin, ymax,
                                      int(mins + 1), 0., int(mins + 1))
        h_time_3d_entries.GetXaxis().SetTitle('xpos / cm')
        h_time_3d_entries.GetYaxis().SetTitle('ypos /cm')
        h_time_3d_entries.GetZaxis().SetTitle('time / minutes')

        ###############################
        n_wrong_delay = 0
        ## fill the tree data in the histograms
        if progressbar_loaded:
            widgets = [progressbar.Bar('=', ' [', ']'), ' ', progressbar.Percentage()]
            # bar = progressbar.ProgressBar("Analyzed Events:",maxval=max_events, widgets=widgets).start()
            bar = progressbar.ProgressBar(maxval=my_tree.GetEntries(), widgets=widgets, term_width=50).start()
        i = 0
        for ev in my_tree:
            i += 1
            if bar:
                try:
                    bar.update(i)
                except ValueError:
                    pass
            if ev.track_x < -99. and ev.track_y < -99.:  ## ommit empty events
                continue
            if ev.calib_flag:  # these are calibration events
                continue
            if ev.saturated:
                continue
            if abs(ev.integral50) > 499.:
                continue


            ########################################
            # check if the delay is correct, if not exit after 10 wrong events
            try:
                if abs(ev.delay_cali - ev.fixed_delay_cali) > 5 or abs(ev.delay_data - ev.fixed_delay_data) > 5:
                    n_wrong_delay += 1
                    if n_wrong_delay > 10:
                        print 'the delay is screwed up. difference between fixed and event by event is off by 5 in more than 10 events'
                        print 'exiting...'
                        sys.exit(-1)
            except AttributeError as e:
                if n_wrong_delay == 0:
                    warnings.warn('cannot find delays for this run')
                n_wrong_delay += 1
            ########################################
            try:
                now = ev.timestamp
            except:
                now = ev.t_pad
            rel_time = int((now - time_first) / time_binning)  ## change to t_pad
            try:
                avrg_chn2 = ev.avrg_first_chn2
            except:
                avrg_chn2 = 0
            signal = factor * (ev.integral50) - pedestal
            signal_chn2 = factor * (ev.integral50  - avrg_chn2) - pedestal
            # print rel_time,signal
            # fill the 3D histogram
            if ev.accepted:
                h_3d.Fill(ev.track_x, ev.track_y, signal)

                h_3d_chn2offest.Fill(ev.track_x, ev.track_y, signal_chn2)

                h_time_3d_signal.Fill(ev.track_x, ev.track_y, rel_time, signal)
                h_time_3d_entries.Fill(ev.track_x, ev.track_y, rel_time, 1)

            # fill all the time histograms with the integral
            h_raw.Fill(ev.integral50)
            h_raw_factor.Fill(factor*ev.integral50)
            h_signal.Fill(signal)
            h_time_2d.Fill(rel_time, signal)
            h_time_2d_chn2offset.Fill(rel_time, signal_chn2)
            if runPedestal:
                h_pedestal.Fill(factor * (ev.integral50))
        print
        # re-open file for writing
        infile.ReOpen('UPDATE')
        infile.cd()
        # print 'h_time_2d',h_time_2d.GetEntries(),
        # raw_input()
        h_raw.Write('', ROOT.TObject.kWriteDelete)
        h_raw_factor.Write('', ROOT.TObject.kWriteDelete)
        h_3d.Write('', ROOT.TObject.kWriteDelete)
        h_signal.Write('', ROOT.TObject.kWriteDelete)
        h_time_2d.Write('', ROOT.TObject.kWriteDelete)
        h_time_3d_signal.Write('', ROOT.TObject.kWriteDelete)
        h_time_3d_entries.Write('', ROOT.TObject.kWriteDelete)
        if runPedestal:
            h_pedestal.Write('', ROOT.TObject.kWriteDelete)
        loaded = True

    ROOT.gStyle.SetOptStat(11)
    if my_run.data_type == 1:
        print '------------------------------------'
        print '--- this is a pedestal run ---------'
        print '------------------------------------'
        pedestal = getPedestalValue(h_raw_factor)[0]
        pedestal_sig = getPedestalValue(h_raw_factor)[1]

        RunInfo.load(parser.get('JSON', 'runs'))
        my_run = RunInfo.runs[my_rn]
        my_run.pedestal = pedestal
        my_run.pedestal_sigma = pedestal_sig
        print 'PEDESTAL: ', pedestal, pedestal_sig
        RunInfo.update_run_info(my_run)
        for rn, r in RunInfo.runs.items():
            if r == my_run: continue
            if r.pedestal_run == my_run.number:
                r.pedestal = pedestal
                r.pedestal_sigma = pedestal_sig
                RunInfo.update_run_info(r)
    else:
        print '------------------------------------'
        print '--- this is a data run -------------'
        print '------------------------------------'
        if math.isnan(my_run.pedestal):
            print 'this run still needs a pedestal!'
            ped_run = my_run.pedestal_run
        ROOT.gROOT.SetBatch()
        # makeXYPlots(h_3d)
        # b = makeTimePlots(h_time_2d)
        # make3D_time_plot(h_time_3d_signal, h_time_3d_entries, 4,4)
        make_circled_time_plots(h_time_3d_signal, h_time_3d_entries)
        print 'done'
    print 'done2'
    infile.Close()
    print 'done3'
