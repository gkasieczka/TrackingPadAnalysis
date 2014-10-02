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


###############################
# set the palette to 53
###############################
ROOT.gStyle.SetPalette(53)
ROOT.gStyle.SetNumberContours( 999 )

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
h_2d_mpv   = copy.deepcopy(cp2d)
h_2d_mean  = copy.deepcopy(cp2d)
h_2d_nfill = copy.deepcopy(cp2d)


n_ev = my_tree.GetEntries()

print 'there\'s a total of %.0f events in the tree' %(n_ev)

# get the times of first and last events
my_tree.GetEntry(0)
## CHANGE THIS TO T_PAD EVENTUALLY!!!
time_first = my_tree.n_pad
my_tree.GetEntry(n_ev-1)
time_last  = my_tree.n_pad
length = time_last - time_first
mins = length/10000. ## should be 60 for time in seconds

print 'run of %.2f minutes length' %(mins)

h_time_2d = ROOT.TH2F('h_time_2d', 'h_time_2d', int(mins+2), 0., int(mins+2), 500, -250., 250.)

for ev in my_tree:
    if ev.track_x < -99. and ev.track_y < -99.: ## ommit empty events
        continue
    if ev.integral50 == -1.:
        continue
    rel_time = int( (ev.n_pad - time_first) / 10000.) ## change to t_pad 

    # fill the 3D histogram
    h_3d.Fill(ev.track_x, ev.track_y, ev.integral50)

    # fill all the time histograms with the integral
    h_time_2d.Fill(rel_time, ev.integral50)

c0 = ROOT.TCanvas('foo', 'bar', 600, 400)
h_time_2d.Draw('colz')
c0.SaveAs('time_2d.pdf')



# 2d behavior next
mpvs  = []
means = []

for xbin in range(1,h_3d.GetNbinsX()+1):
  for ybin in range(1,h_3d.GetNbinsY()+1):
    z_histo = h_3d.ProjectionZ(h_3d.GetName()+'_pz_'+str(xbin)+'_'+str(ybin), xbin, xbin, ybin, ybin)
    if z_histo.Integral() < 100.: 
        continue
    print 'at xbin %d and ybin %d' %(xbin, ybin)
    #z_histo.Fit('landau','q')
    fit_res = ah.fitLandauGaus(z_histo)

    # if xbin == 12 and ybin == 12:
    #     fuck = copy.deepcopy(z_histo)
    ## get the mean and MPV of the landau for all the bins with non-zero integral
    # mpv = z_histo.GetFunction('landau').GetParameter(1) #fit_res[1].GetParameter(1)

    mpv = fit_res.getRealValue('ml')
    mpvs.append(mpv)

    mean = z_histo.GetMean()
    means.append(mean)
    h_2d_mpv  .SetBinContent(xbin, ybin, mpv )
    h_2d_mean .SetBinContent(xbin, ybin, mean)
    h_2d_nfill.SetBinContent(xbin, ybin, z_histo.Integral())


c1 = ROOT.TCanvas('foo', 'bar', 600, 400)
c1.Divide(2,2)

c1.cd(1)
central = ah.mean(mpvs)
h_2d_mpv.Draw('colz')
h_2d_mpv.GetZaxis().SetRangeUser(central-40., central+40.)

c1.cd(2)
central = ah.mean(means)
h_2d_mean.Draw('colz')
h_2d_mean.GetZaxis().SetRangeUser(central-50., central+50.)

c1.cd(3)
h_2d_nfill.Draw('colz')

c1.cd(4)
h_2d_nfill.Draw('colz')

c1.SaveAs('plots.pdf')


