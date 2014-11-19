#!/usr/bin/env python

"""
Analysis of the Runs and plot production
"""

###############################
# Imports
###############################

import pickle
import ROOT, copy, sys, math, os
from RunInfo import RunInfo
import AnalyzeHelpers as ah
import warnings
import root_style
import ConfigParser

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
ROOT.gStyle.SetNumberContours( 999 )

ROOT.gROOT.SetBatch()
this_style.set_style(width,width,1)

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def saveCanvas(c1,name):
    #print 'Save Canvas:',name
    name = name.split('/')
    fdir = '/'.join(name[:-1])
    this_style.main_dir = fdir
    this_style.save_canvas(c1,name[-1])


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def saveCanvas(c1,name):
    #print 'Save Canvas:',name
    name = name.split('/')
    fdir = '/'.join(name[:-1])
    exts = ['pdf','eps','tex','root','png']
    #print '\t',name
    for ext in exts:
        fname= fdir+'/{ext}/{name}.{ext}'.format(ext=ext,name=name[-1])
        #print '\t',fname
        ensure_dir(fname)
        c1.SaveAs(fname)

def getPedestalValue(hist):
    tmp_hist = copy.deepcopy(hist.ProjectionY())
    tmp_hist.SetBinContent(0,0)
    tmp_hist.SetBinContent(1,0)
    tmp_hist.SetBinContent(tmp_hist.GetNbinsX(),0)
    tmp_hist.SetBinContent(tmp_hist.GetNbinsX()+1,0)
    rms = tmp_hist.GetRMS()
    maximum_bin = tmp_hist.GetMaximumBin()
    maximum = tmp_hist.GetBinContent(maximum_bin)
    mp = tmp_hist.GetBinCenter(maximum_bin)
    x_low = maximum_bin
    x_high = maximum_bin
    while tmp_hist.GetBinContent(x_low) > maximum/2 and x_low > 0:
        x_low -= 1
    x_low = tmp_hist.GetBinCenter(x_low)
    while tmp_hist.GetBinContent(x_high) > maximum/2 and x_high < tmp_hist.GetNbinsX():
        x_high += 1
    x_high = tmp_hist.GetBinCenter(x_high)
    fwhm = x_high - x_low
    fit_range = min(rms,fwhm)
    # print 'mp',mp,'rms',rms,'fwhm',fwhm, 'range',fit_range
    func = ROOT.TF1('gaus_fit','gaus',mp-fit_range/2,mp+fit_range/2)
    tmp_hist.Fit(func,'Q','',mp-rms/2,mp+rms/2)
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
    saveCanvas(c0,targetdir+'/'+'pedestal_'+prefix)
    return central, sigma

def makeTimePlots(h_time_2d):
    profileY = h_time_2d.ProfileY()
    neg_landau = False
    if profileY.GetMean() < 0.:
        neg_landau = True

    if neg_landau:
        func = ROOT.TF1('my_landau','[0] * TMath::Landau(-x,[1],[2])', h_time_2d.GetYaxis().GetXmin(), h_time_2d.GetYaxis().GetXmax())
    else:
        func = ROOT.TF1('my_landau','[0] * TMath::Landau(x,[1],[2])' , h_time_2d.GetYaxis().GetXmin(), h_time_2d.GetYaxis().GetXmax())
    func.SetParameters(1, h_time_2d.GetMean(), h_time_2d.GetRMS() )


    land = copy.deepcopy(h_time_2d.ProjectionY())
    # land.Fit(func)
    fit_res = ah.fitLandauGaus(land, True)
    this_style.set_style(1200,600,1/2.)
    c0 = this_style.get_canvas('time_canvas')
    # c0 = ROOT.TCanvas('time_canvas', 'Canvas of the time evolution', 1200, 600)
    c0.cd()
    ### if neg_landau:
    ###     land.GetXaxis().SetRangeUser(-250,0)
    ### else:
    ###     land.GetXaxis().SetRangeUser(0,250)
    ### land.Draw()
    ### c0.SaveAs(targetdir+'/'+prefix+'_landau.pdf')
    #land.Draw()
    this_style.print_margins()
    fit_res[2].Draw()
    pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
    pave.Draw()
    saveCanvas(c0,targetdir+'/'+'landauGaus_'+prefix)
    fit_res[-1].Draw()
    pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
    pave.Draw()
    saveCanvas(c0,targetdir+'/'+'histo_'+prefix)
    # return

    arr = ROOT.TObjArray()
    h_time_2d.FitSlicesY(func, 0, -1, 0, 'QNR', arr)

    mpvs = arr[1] ## MPVs are fit parameter 1
    if neg_landau:
        mpvs.Scale(-1.)

    mpvs.SetMarkerStyle(24)
    mpvs.SetMarkerColor(ROOT.kBlack)
    mpvs.SetMarkerSize(0.8)
    mpvs.SetLineColor(ROOT.kBlack)

    errs = arr[2]
    for ibin in range(1,mpvs.GetNbinsX()+1):
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
    h_time_2d.GetYaxis().SetRangeUser(-100,500)
    h_time_2d.Draw('colz')

    pave = ah.addDiamondInfo(0.02, 0.02, 0.15, 0.11, my_run)
    mpvs.Draw('same pe')
    pave.Draw()
    saveCanvas(c0,targetdir+'/'+'time_2d'+prefix)
    return arr


def makeXYPlots(h_3d):
    if my_run.calibration_event_fraction < 0.5:
        return
    cp2d = copy.deepcopy(h_3d.Project3D('yx'))

    tmp_size = ROOT.gStyle.GetTitleSize()
    tmp_marg_right = ROOT.gStyle.GetPadRightMargin()
    tmp_marg_left  = ROOT.gStyle.GetPadLeftMargin()
    tmp_marg_top = ROOT.gStyle.GetPadTopMargin()
    tmp_marg_Bottom= ROOT.gStyle.GetPadBottomMargin()

    # set some style parameters
    ROOT.gStyle.SetTitleSize(0.07,'t')
    ROOT.gStyle.SetPadRightMargin (0.12)
    ROOT.gStyle.SetPadLeftMargin  (0.12)
    ROOT.gStyle.SetPadBottomMargin(0.12)
    ROOT.gStyle.SetPadTopMargin   (0.12)
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

    h_2d_mpv   = copy.deepcopy(cp2d)
    h_2d_sigma = copy.deepcopy(cp2d)
    h_2d_mean  = copy.deepcopy(cp2d)
    h_2d_nfill = copy.deepcopy(cp2d)

    mpvs   = []
    means  = []
    sigmas = []
    
    counter = 0
    for xbin in range(1,h_3d.GetNbinsX()+1):
        for ybin in range(1,h_3d.GetNbinsY()+1):
            z_histo = h_3d.ProjectionZ(h_3d.GetName()+'_pz_'+str(xbin)+'_'+str(ybin), xbin, xbin, ybin, ybin)
            if z_histo.Integral() < 100.: 
                continue
            counter += 1
            # if counter > 3: continue
            # print 'counter:', counter
            #print 'at xbin %d and ybin %d' %(xbin, ybin)
            #z_histo.Fit('landau','q')
            fit_res = ah.fitLandauGaus(z_histo)
            ##### print 'this is the fit result from the ROOFIT fit:', fit_res[1]
            ##### print ' printValue of the parameter list:', fit_res[1].find('ml')
            ##### print ' mean  landau', fit_res[1].getRealValue('ml')
            ##### print ' sigma landau', fit_res[1].getRealValue('sl')
    
            ## get the mean and MPV of the landau for all the bins with non-zero integral
            # mpv = z_histo.GetFunction('landau').GetParameter(1) #fit_res[1].GetParameter(1)
    
            #mpv = fit_res[1].getRealValue('ml')
            #sig = fit_res[1].getRealValue('sl')

            #mpv = fit_res[1][1]
            #sig = fit_res[1][2]
            mean = z_histo.GetMean()
            mpv = z_histo.GetXaxis().GetBinCenter( z_histo.GetMaximumBin()  )
            sig = z_histo.GetRMS()

            mpvs.append(mpv)
            sigmas.append(sig)
            means.append(mean)
    
            h_2d_mpv  .SetBinContent(xbin, ybin, mpv )
            h_2d_sigma.SetBinContent(xbin, ybin, sig )
            h_2d_mean .SetBinContent(xbin, ybin, mean)
            h_2d_nfill.SetBinContent(xbin, ybin, z_histo.Integral())

    #get ranges
    fname = 'xy_plots_range.pl'
    try:
        ranges = pickle.load( open( fname, "rb" ) )
    except IOError:
        ranges = {}
    dia = my_run.diamond
    central = ah.mean(means)
    old_range = ranges.get(dia,[1e9,-1e9])
    print dia
    print 'old range', old_range
    this_range = [central-50,central+50]
    print 'this range',this_range
    new_range = [min(old_range[0],this_range[0]),max(old_range[1],this_range[1])]
    print new_range
    ranges[dia] = new_range
    pickle.dump( ranges, open( fname, "wb" ) )

    #save canvases
    ROOT.gStyle.SetOptStat(0)
    c1 = this_style.get_canvas('space_resloved_means')
    ROOT.gPad.SetTicks(1,1)
    h_2d_mean.SetTitle('XY distribution of mean PH')
    h_2d_mean.UseCurrentStyle()

    #only mean distribution
    h_2d_mean.Draw('colz')
    h_2d_mean.GetZaxis().SetRangeUser(new_range[0],new_range[1])
    pave = my_run.addDiamondInfo(0.6, 0.9, 0.9, 0.99)
    pave.Draw('same')
    c1.Update()
    saveCanvas(c1,targetdir+'/'+prefix+'_xyMeans')

    #mean and no of tracks
    c1 = this_style.get_canvas('space_resloved_signals')
    c1.Divide(1,2)

    c1.cd(1)
    ROOT.gPad.SetTicks(1,1)
    h_2d_nfill.SetTitle('number of tracks in XY')
    h_2d_nfill.Draw('colz')
    
    c1.cd(2)
    h_2d_mean.Draw('colz')
    h_2d_mean.GetZaxis().SetRangeUser(new_range[0],new_range[1])



    # h_2d_mean.GetZaxis().SetRangeUser(central-50., central+50.)
    # c1.cd(3)
    # ROOT.gPad.SetTicks(1,1)
    # central = ah.mean(mpvs)
    # #central = abs(mean)
    # h_2d_mpv.SetTitle('XY distribution of MPV of PH')
    # h_2d_mpv.Draw('colz')
    # h_2d_mpv.GetZaxis().SetRangeUser(central-40., central+40.)
    #
    # c1.cd(4)
    # ROOT.gPad.SetTicks(1,1)
    # central = ah.mean(sigmas)
    # h_2d_sigma.SetTitle('width of PH')
    # h_2d_sigma.Draw('colz')
    # h_2d_sigma.GetZaxis().SetRangeUser(0., central+10.)

    c1.cd(0)
    pave = my_run.addDiamondInfo(0.4, 0.45, 0.6, 0.55)
    pave.Draw('same')
    
    saveCanvas(c1,targetdir+'/'+prefix+'_xyPlots')
    # ROOT.gStyle.Reset()
    # reset the style
    ROOT.gStyle.SetTitleSize(tmp_size,'t')
    ROOT.gStyle.SetPadRightMargin (tmp_marg_right)
    ROOT.gStyle.SetPadLeftMargin  (tmp_marg_left)
    ROOT.gStyle.SetPadBottomMargin(tmp_marg_Bottom)
    ROOT.gStyle.SetPadTopMargin   (tmp_marg_top)

    del h_2d_mpv, h_2d_mean, h_2d_nfill, h_3d

## reorganize later
if __name__ == "__main__":

    ###############################
    # Get all the runs from the json
    ###############################

    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    RunInfo.load(parser.get('JSON','runs'))

    global my_rn
    ## my_rn  = int(sys.argv[-1])
    print 'argv:',sys.argv
    my_rn  = int([i for i in sys.argv if i.isdigit() == True][0]) ## search for the first number in the list of arguments
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
    fname = 'results/run_'+str(my_rn)+'/track_info.root'
    print fname
    if not os.path.isfile(fname):
        raise Exception('Cannot find File %s'%fname)
    infile = ROOT.TFile(fname,'READ')
    my_tree = infile.Get('track_info')
    print my_tree

    n_ev = my_tree.GetEntries()
    
    print 'there\'s a total of %.0f events in the tree' %(n_ev)
    
    global loaded, targetdir, prefix
    loaded = False
    
    ###############################
    # get a bit of information for the correct folder and prefix for the plots
    ###############################
    
    voltage = my_run.bias_voltage
    if voltage > 0:
        volt_str = 'pos'+str(voltage)
    else:  
        volt_str = 'neg'+str(-1*voltage)

    # check run type
    rate    = str(my_run.fs11)+'_'+str(abs(my_run.fsh13))
    if   my_run.data_type == 0:
        runtype = 'rate-scan'
        #prefix = '{diamond}-run-{run:03d}-{volt_str}-{rate}-rate'
        prefix  = my_run.diamond+'-run-'+'%03d'%(my_rn)+'-'+volt_str+'-'+rate+'-rate'
    elif my_run.data_type == 1:
        runtype = 'pedestal'
        prefix  = my_run.diamond+'-run-'+'%03d'%(my_rn)+'-'+volt_str+'-'+rate+'-pedestal'
    elif my_run.data_type == 2: 
        runtype = 'voltage-scan'
        prefix  = my_run.diamond+'-run-'+'%03d'%(my_rn)+'-'+volt_str+'-'+rate+'-voltage'
    elif my_run.data_type == 3:
        runtype = 'rate-scan'
        prefix  = my_run.diamond+'-run-'+'%03d'%(my_rn)+'-'+volt_str+'-'+rate+'-data-long'
    else:
        runtype = 'other'
        prefix  = my_run.diamond+'-run-'+'%03d'%(my_rn)+'-'+volt_str+'-'+rate+'-other'

    targetdir = 'results/'+my_run.diamond+'/'+runtype+'/'
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)


    ###############################
    # check if the histograms are already in the file. load them if they're there
    ###############################
    h_3d = None
    h_time_2d = None

    if infile.Get('h_3dfull') != None and infile.Get('h_time_2d') != None:
        h_3d      = copy.deepcopy(infile.Get('h_3dfull') )
        h_time_2d = copy.deepcopy(infile.Get('h_time_2d'))

        loaded = True
        print 'file already loaded'
    
    ###############################
    # if the histograms aren't yet there, fill them. or do it if the user chooses to do so
    ###############################
    if reloadAnyway:
        loaded = False
    if not loaded:

        print 'loading the histograms into the root file'
        if h_3d:
            h_3d.Delete()
        h_3d = ROOT.TH3F('h_3dfull','3D histogram', 
             25,   -0.30,   0.20, 
             25,   -0.10,   0.40, 
            250, -500.00, 500.00)
        h_3d_chn2offest = ROOT.TH3F('h_3dfull_chn2offest','3D histogram with chn2 offset', 
             25,   -0.30,   0.20, 
             25,   -0.10,   0.40, 
            250, -500.00, 500.00)

        ## runPedestal = math.isnan(my_run.pedestal) and (my_run.pedestal_run == -1 or my_run.number == my_run.pedestal_run)
        runPedestal = (my_run.data_type == 1)

        print 'is nan?', math.isnan(my_run.pedestal)
        if math.isnan(my_run.pedestal) and (my_run.pedestal_run != -1 and my_run.number != my_run.pedestal_run):
            print 'analyze the pedestal run first!! it\'s run', my_run.pedestal_run
            sys.exit()
        if runPedestal:
            pedestal = 0.
        else:
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
        my_tree.GetEntry(n_ev-1)

        try:
            time_last = my_tree.timestamp
        except:
            time_first = my_tree.t_pad
        length = time_last - time_first
        mins = length/time_binning

        if h_time_2d:
            h_time_2d.Delete()
        h_time_2d            = ROOT.TH2F('h_time_2d'           , 'h_time_2d'           , int(mins+1), 0., int(mins+1), 1000, -500, 500.)
        h_time_2d_chn2offset = ROOT.TH2F('h_time_2d_chn2offset', 'h_time_2d_chn2offset', int(mins+1), 0., int(mins+1), 1000, -500, 500.)
    
        print 'run of %.2f minutes length' %(mins)
        
        n_wrong_delay = 0
        if my_run.bias_voltage >= 0:
            factor = -1.0
        else:
            factor = 1.0
        ## fill the tree data in the histograms
        for ev in my_tree:
            
            if ev.track_x < -99. and ev.track_y < -99.: ## ommit empty events
                continue
            if ev.calib_flag: # these are calibration events
                continue
            if ev.saturated:
                continue
            if abs(ev.integral50) > 499.:
                continue
               
            ########################################
            # check if the delay is correct, if not exit after 10 wrong events
            try:
                if abs(ev.delay_cali-ev.fixed_delay_cali) > 5 or abs(ev.delay_data-ev.fixed_delay_data) > 5:
                    n_wrong_delay += 1
                    if n_wrong_delay > 10:
                        print 'the delay is screwed up. difference between fixed and event by event is off by 5 in more than 10 events'
                        print 'exiting...'
                        sys.exit(-1)
            except AttributeError as e:
                if n_wrong_delay ==0:
                    warnings.warn('cannot find delays for this run')
                n_wrong_delay+=1
            ########################################
            try:
                now = ev.timestamp
            except:
                now = ev.t_pad
            rel_time = int( (now - time_first) / time_binning) ## change to t_pad
            try:
                avrg_chn2 = ev.avrg_first_chn2
            except:
                avrg_chn2 = 0
            signal = factor*(ev.integral50 - pedestal)
            signal_chn2 = factor*(ev.integral50 - pedestal - avrg_chn2)
            # print rel_time,signal
            # fill the 3D histogram
            h_3d           .Fill(ev.track_x, ev.track_y, signal)

            h_3d_chn2offest.Fill(ev.track_x, ev.track_y, signal_chn2)
        
            # fill all the time histograms with the integral
            h_time_2d           .Fill(rel_time, signal)
            h_time_2d_chn2offset.Fill(rel_time, signal_chn2)
        # re-open file for writing
        infile.ReOpen('UPDATE')
        infile.cd()
        # print 'h_time_2d',h_time_2d.GetEntries(),
        # raw_input()

        h_3d.Write()
        h_time_2d.Write()
        loaded = True
    
    ROOT.gStyle.SetOptStat(11)
    if my_run.data_type == 1:
        print '------------------------------------'
        print '--- this is a pedestal run ---------'
        print '------------------------------------'
        pedestal = getPedestalValue(h_time_2d)[0]
        pedestal_sig = getPedestalValue(h_time_2d)[1]

        RunInfo.load(parser.get('JSON','runs'))
        my_run = RunInfo.runs[my_rn]
        my_run.pedestal = pedestal
        my_run.pedestal_sigma = pedestal_sig
        print 'PEDESTAL: ',pedestal,pedestal_sig
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
        makeXYPlots(h_3d)
        b = makeTimePlots(h_time_2d)
    infile.Close()