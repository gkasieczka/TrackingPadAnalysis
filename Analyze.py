#!/usr/bin/env python

"""
Analysis of the Runs and plot production
"""

###############################
# Imports
###############################

import ROOT, copy, sys
from RunInfo import RunInfo
import AnalyzeHelpers as ah
# from ROOT import RooFit, RooRealVar, RooGaussian, RooLandau, RooDataSet, RooArgList, RooTreeData, RooFFTConvPdf, RooDataHist

###############################
# Usage
###############################
def usage():
    print 'use this thusly:'
    print '    ./Analyze.py <runnumber>'
    return



## ## reorganize later
## if __name__ == '__main__':
## 
##     if len(sys.argv) != 2:
##         usage()
##         sys.exit(-1)
## 
##     ###############################
##     # Get all the runs from the json
##     ###############################
##     
##     RunInfo.load('runs.json')
##     
##     my_run = RunInfo.runs[63]
##     print my_run.__dict__




###############################
# get the correct file for the selected run
###############################

# adapt those lines to find the right file eventually
infile = ROOT.TFile('../track_info.root','READ')
my_tree = infile.Get('track_info')

###############################
# fill a 3D histogram with all the data
###############################

h_3d = ROOT.TH3F('h_3dfull','3D histogram', 
	 25,   -0.30,   0.20, 
	 25,   -0.10,   0.40, 
	200, -400.00, 400.00)

cp2d = copy.deepcopy(h_3d.Project3D('yx'))
h_2d_mpv  = copy.deepcopy(cp2d)
h_2d_mean = copy.deepcopy(cp2d)

h_1dtest = ROOT.TH1F('h_1dtest', 'h_1dtest', 500, -250.00, 250.00)

n_ev = my_tree.GetEntries()

print 'there\'s a total of %.0f events in the tree' %(n_ev)

n_10k = int(n_ev/10000.)+1
print 'producing %d histograms for the time evolution with 10K events in each' %(n_10k)
time_hists = []
for i in range(n_10k):
    hist = ROOT.TH1F('h_time'+str(i), 'h_time'+str(i), 500, -250., 250.)
    time_hists.append(hist)

n = 0
time_ind = 0
for ev in my_tree:
    if not n%10000:
        time_ind += 1
    n += 1
    if ev.track_x < -99. and ev.track_y < -99.: ## ommit empty events
        continue

    # fill the 3D histogram
    h_3d.Fill(ev.track_x, ev.track_y, ev.integral50)

    # fill all the time histograms with the integral
    time_hists[time_ind-1].Fill(ev.integral50)


# time evolution first
h_time_evo = ROOT.TH1F('h_time_evo','Time evolution of signal height', n_10k, 0, n_10k)
for i in range(n_10k):
    if time_hists[i].Integral() == 0.:
        continue
    tmp_hist = copy.deepcopy(time_hists[i])
    ##tmp_hist.Fit('landau','q')
    res = ah.fitLandauGaus(tmp_hist)
    tmp_mpv = res[1].GetParameter(1) # get the mpv
    tmp_err = res[1].GetParameter(2) # get the mpv
    h_time_evo.SetBinContent(i+1, tmp_mpv)
    h_time_evo.SetBinError  (i+1, tmp_err)
    
ah.drawHisto(h_time_evo)


# 2d behavior next
mpvs  = []
means = []

for xbin in range(1,h_3d.GetNbinsX()+1):
  for ybin in range(1,h_3d.GetNbinsY()+1):
    z_histo = h_3d.ProjectionZ(h_3d.GetName()+'_pz_'+str(xbin)+'_'+str(ybin), xbin, xbin, ybin, ybin)
    if z_histo.Integral() == 0.: 
        continue
    z_histo.Fit('landau','q')
    ## get the mean and MPV of the landau for all the bins with non-zero integral
    mpv = z_histo.GetFunction('landau').GetParameter(1)
    mpvs.append(mpv)
    mean = z_histo.GetMean()
    means.append(mean)
    h_2d_mpv .SetBinContent(xbin, ybin, mpv )
    h_2d_mean.SetBinContent(xbin, ybin, mean)

central = ah.mean(mpvs)
ah.useNiceColorPalette()
h_2d_mpv.Draw('colz')
h_2d_mpv.GetZaxis().SetRangeUser(central-50., central+50.)



