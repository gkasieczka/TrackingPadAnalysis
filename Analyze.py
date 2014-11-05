#!/usr/bin/env python

"""
Analysis of the Runs and plot production
"""

###############################
# Imports
###############################

import ROOT, copy, sys, math
from RunInfo import RunInfo
import AnalyzeHelpers as ah

###############################
# Usage
###############################
def usage():
    print 'use this thusly:'
    print '    ./Analyze.py <runnumber>'
    return


###############################
# set the palette to 53
###############################

ROOT.gStyle.SetPalette(53)
ROOT.gStyle.SetNumberContours( 999 )

def getPedestalValue(hist):
    tmp_hist = copy.deepcopy(hist.ProjectionY())
    rms = tmp_hist.GetRMS()
    mp = tmp_hist.GetBinCenter(tmp_hist.GetMaximumBin())
    func = ROOT.TF1('gaus_fit','gaus',mp-rms/2,mp+rms/2)
    tmp_hist.Fit(func,'','',mp-rms/2,mp+rms/2)
    central = func.GetParameter(1)
    c0 = ROOT.TCanvas('foo', 'bar', 600, 600)
    tmp_hist.Draw('')
    func.Draw('same')
    c0.SaveAs('results/run_'+str(my_rn)+'/pedestal.pdf')
    return central
    

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


    land = h_time_2d.ProjectionY()
    land.Fit(func)
    c0 = ROOT.TCanvas('time_canvas', 'Canvas of the time evolution', 600, 300)
    if neg_landau:
        land.GetXaxis().SetRangeUser(-250,0)
    else:
        land.GetXaxis().SetRangeUser(0,250)
    land.Draw()
    c0.SaveAs('results/run_'+str(my_rn)+'/landau.pdf')


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
    h_time_2d.GetXaxis().SetTitleSize(0.05)
    h_time_2d.GetXaxis().SetLabelSize(0.05)

    # y-axis
    h_time_2d.GetYaxis().SetTitle('pulse height')
    h_time_2d.GetYaxis().SetLabelSize(0.05)
    h_time_2d.GetYaxis().SetTitleSize(0.05)
    h_time_2d.Draw('colz')
    mpvs.Draw('same pe')

    c0.SaveAs('results/run_'+str(my_rn)+'/time_2d.pdf')
    return arr


def makeXYPlots(h_3d):

    cp2d = copy.deepcopy(h_3d.Project3D('yx'))

    tmp_size = ROOT.gStyle.GetTitleSize()
    tmp_marg = ROOT.gStyle.GetPadRightMargin()

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
            print 'counter:', counter
            #print 'at xbin %d and ybin %d' %(xbin, ybin)
            #z_histo.Fit('landau','q')
            fit_res = ah.fitLandauGaus(z_histo)
            ##### print 'this is the fit result from the ROOFIT fit:', fit_res[1]
            ##### print ' printValue of the parameter list:', fit_res[1].find('ml')
            ##### print ' mean  landau', fit_res[1].getRealValue('ml')
            ##### print ' sigma landau', fit_res[1].getRealValue('sl')
    
            ## get the mean and MPV of the landau for all the bins with non-zero integral
            # mpv = z_histo.GetFunction('landau').GetParameter(1) #fit_res[1].GetParameter(1)
    
            mpv = fit_res[1].getRealValue('ml')
            sig = fit_res[1].getRealValue('sl')
            #mpv = fit_res[1][1]
            #sig = fit_res[1][2]
            mean = z_histo.GetMean()

            mpvs.append(mpv)
            sigmas.append(sig)
            means.append(mean)
    
            h_2d_mpv  .SetBinContent(xbin, ybin, mpv )
            h_2d_sigma.SetBinContent(xbin, ybin, sig )
            h_2d_mean .SetBinContent(xbin, ybin, mean)
            h_2d_nfill.SetBinContent(xbin, ybin, z_histo.Integral())
    
    ROOT.gStyle.SetOptStat(0)
    
    c1 = ROOT.TCanvas('foo', 'bar', 600, 600)
    c1.Divide(2,2)
    
    c1.cd(1)
    ROOT.gPad.SetTicks(1,1)
    h_2d_nfill.SetTitle('number of hits in XY')
    h_2d_nfill.Draw('colz')
    
    c1.cd(2)
    ROOT.gPad.SetTicks(1,1)
    central = ah.mean(means)
    h_2d_mean.SetTitle('XY distribution of mean PH')
    h_2d_mean.Draw('colz')
    h_2d_mean.GetZaxis().SetRangeUser(central-50., central+50.)
    
    c1.cd(3)
    ROOT.gPad.SetTicks(1,1)
    #central = ah.mean(means)
    central = abs(mean)
    h_2d_mpv.SetTitle('XY distribution of MPV of PH')
    h_2d_mpv.Draw('colz')
    h_2d_mpv.GetZaxis().SetRangeUser(central-40., central+40.)
    
    c1.cd(4)
    ROOT.gPad.SetTicks(1,1)
    central = ah.mean(sigmas)
    h_2d_sigma.SetTitle('width of PH')
    h_2d_sigma.Draw('colz')
    h_2d_sigma.GetZaxis().SetRangeUser(0., central+10.)
    
    c1.SaveAs('results/run_'+str(my_rn)+'/plots.pdf')
    # ROOT.gStyle.Reset()
    # reset the style
    ROOT.gStyle.SetTitleSize(tmp_size,'t')
    ROOT.gStyle.SetPadRightMargin (tmp_marg)
    ROOT.gStyle.SetPadLeftMargin  (tmp_marg)
    ROOT.gStyle.SetPadBottomMargin(tmp_marg)
    ROOT.gStyle.SetPadTopMargin   (tmp_marg)

    del h_2d_mpv, h_2d_mean, h_2d_nfill, h_3d

## reorganize later
if __name__ == "__main__":

    ##  if len(sys.argv) != 2:
    ##      usage()
    ##      sys.exit(-1)

    ###############################
    # Get all the runs from the json
    ###############################
    
    RunInfo.load('runs.json')

    
    global my_rn
    ## my_rn  = int(sys.argv[-1])
    my_rn  = int([i for i in sys.argv if i.isdigit() == True][0]) ## search for the first number in the list of arguments
    my_run = RunInfo.runs[my_rn]
    print my_run.__dict__

    reloadAnyway = False
    if 'reload' in sys.argv:
        reloadAnyway = True

    ###############################
    # get the correct file for the selected run
    ###############################
    
    # adapt these lines to find the right file eventually
    infile = ROOT.TFile('results/run_'+str(my_rn)+'/track_info.root','READ')
    my_tree = infile.Get('track_info')

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
    if   my_run.data_type == 0:
        runtype = 'pedestal'
        prefix  = my_run.diamond+'-run-'str(my_rn)+'-'+volt_str+'pedestal'
    elif my_run.data_type == 1:
        runtype = 'rate-scan'
        prefix  = my_run.diamond+'-run-'str(my_rn)+'-'+volt_str+'data'
    elif my_run.data_type == 2: 
        runtype = 'voltage-scan'
        prefix  = my_run.diamond+'-run-'str(my_rn)+'-'+volt_str+'data'
    elif my_run.data_type == 3:
        runtype = 'long-run'
        prefix  = my_run.diamond+'-run-'str(my_rn)+'-'+volt_str+'data-long'
    else
        runtype = 'other'
        prefix  = my_run.diamond+'-run-'str(my_rn)+'-'+volt_str+'other'

    targetdir = 'results/'+my_run.diamond+'/'+runtype+'/'
    if not os.path.isdir(targetdir):
        os.mkdir(targetdir)


    ###############################
    # check if the histograms are already in the file. load them if they're there
    ###############################

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
        h_3d = ROOT.TH3F('h_3dfull','3D histogram', 
             25,   -0.30,   0.20, 
             25,   -0.10,   0.40, 
            200, -400.00, 400.00)

        runPedestal = math.isnan(my_run.pedestal) and (my_run.pedestal_run == -1 or my_run.number == my_run.pedestal_run)

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
        time_first = my_tree.t_pad
        my_tree.GetEntry(n_ev-1)
        time_last  = my_tree.t_pad
        length = time_last - time_first
        mins = length/time_binning

        h_time_2d = ROOT.TH2F('h_time_2d', 'h_time_2d', int(mins+1), 0., int(mins+1), 500, -250., 250.)
    
        print 'run of %.2f minutes length' %(mins)
        
        ## fill the tree data in the histograms
        for ev in my_tree:
            if ev.track_x < -99. and ev.track_y < -99.: ## ommit empty events
                continue
            if ev.calib_flag: # these are calibration events
                continue
            rel_time = int( (ev.t_pad - time_first) / time_binning) ## change to t_pad 
        
            # fill the 3D histogram
            h_3d.Fill(ev.track_x, ev.track_y, ev.integral50 - pedestal)
        
            # fill all the time histograms with the integral
            h_time_2d.Fill(rel_time, ev.integral50 - pedestal)
        
        # re-open file for writing
        infile.ReOpen('UPDATE')
        infile.cd()

        h_3d.Write()
        h_time_2d.Write()
        loaded = True
    
    if my_run.data_type == 1:
        print '------------------------------------'
        print '--- this is a pedestal run ---------'
        print '------------------------------------'
        pedestal = getPedestalValue(h_time_2d)
        my_run.pedestal = pedestal
        for rn, r in RunInfo.runs.items():
            if r == my_run: continue
            if r.pedestal_run == my_run.number:
                r.pedestal = pedestal
        RunInfo.dump('runs.json')
        
        
    else:
        print '------------------------------------'
        print '--- this is a data run -------------'
        print '------------------------------------'
        if math.isnan(my_run.pedestal):
            print 'this run still needs a pedestal!'
            ped_run = my_run.pedestal_run

        ROOT.gROOT.SetBatch()
        # makeXYPlots(h_3d)
        b = makeTimePlots(h_time_2d)

    infile.Close()


