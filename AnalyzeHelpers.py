###############################
# Imports
###############################

import ROOT, copy
from array import array
from ROOT import RooFit, RooRealVar, RooGaussian, RooLandau, RooDataSet, RooArgList, RooTreeData, RooFFTConvPdf, RooDataHist

def median(ls):
    sls = sorted(ls)
    length = len(ls)
    return sls[length/2]

def mean(ls):
    tot = 0.
    for i in ls:
        tot = tot + i
    return tot/len(ls)


def useNiceColorPalette( NCont = 999):
    stops = [0.00, 0.34, 0.61, 0.84, 1.00]
    red   = [0.00, 0.00, 0.87, 1.00, 0.51]
    green = [0.00, 0.81, 1.00, 0.20, 0.00]
    blue  = [0.51, 1.00, 0.12, 0.00, 0.00]
    
    s = array('d', stops)
    r = array('d', red)
    g = array('d', green)
    b = array('d', blue)
    
    nstops = len(s)
    ROOT.TColor.CreateGradientColorTable(nstops, s, r, g, b, NCont)
    ROOT.gStyle.SetNumberContours( NCont )


def drawHisto(hist):
    if hist.GetName() == 'h_time_evo':
        hist.GetXaxis().SetTitle('n * 10k events')
        hist.GetYaxis().SetTitle('MPV of pulse height')
        hist.SetMarkerStyle(20)
        hist.SetMarkerColor(ROOT.kBlack)
        hist.SetMarkerSize(0.8)
        c = ROOT.TCanvas('canvas', 'canvas',  600, 450)
        hist.Draw('pe')
        c.SaveAs('time_evolution.pdf')
        

def fitLandauGaus(hist):

    neg_landau = False
    if hist.GetMean() < 0.:
        neg_landau = True

    if neg_landau:
        func = ROOT.TF1('my_landau','[0] * TMath::Landau(-x,[1],[2])', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
        func.SetParameters(1, hist.GetMean(), hist.GetRMS() )
    else:
        func = ROOT.TF1('my_landau','[0] * TMath::Landau(x,[1],[2])', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
        func.SetParameters(1, hist.GetMean(), hist.GetRMS() )

    hist.Fit('my_landau')
    #hist.GetFunction('my_landau').Draw('same')
    return hist, hist.GetFunction('my_landau')

## ROOFIT SCHAS
    ## roofit schas x = RooRealVar('x', 'x', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    ## roofit schas ral = RooArgList(x)
    ## roofit schas dh = RooDataHist('dh', 'dh', ral, RooFit.Import(hist))
    ## roofit schas 
    ## roofit schas 
    ## roofit schas t = RooRealVar('t', 't', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    ## roofit schas 
    ## roofit schas ml     = RooRealVar('ml', 'mean landau' , hist.GetMean(), hist.GetXaxis().GetXmin(),  hist.GetXaxis().GetXmax())
    ## roofit schas sl     = RooRealVar('sl', 'sigma landau', 10., 0.1, 30)
    ## roofit schas landau = RooLandau('lx', 'lx', t, ml, sl)
    ## roofit schas 
    ## roofit schas mg     = RooRealVar('mg', 'mean gaus' , hist.GetMean(), hist.GetXaxis().GetXmin(),  hist.GetXaxis().GetXmax())
    ## roofit schas sg     = RooRealVar('sg', 'sigma gaus', 10., 0.1, 30)
    ## roofit schas gaus   = RooGaussian('lx', 'lx', t, ml, sl)
    ## roofit schas 
    ## roofit schas t.setBins(hist.GetNbinsX(),'cache')
    ## roofit schas 
    ## roofit schas ## Construct landau (x) gauss
    ## roofit schas lxg = RooFFTConvPdf("lxg","landau (X) gaus", t, landau, gaus)
    ## roofit schas lxg.fitTo(dh)

    ## roofit schas frame = t.frame(Title('landau (x) gauss convolution'))
    ## roofit schas hist.plotOn(frame)
    ## roofit schas lxg.plotOn(frame)
    ## roofit schas landau.plotOn(frame,LineStyle(ROOT.kDashed))

    ## roofit schas c = ROOT.TCanvas('lg_convolution','landau (x) gaus', 600, 600)
    ## roofit schas ROOT.gPad.SetLeftMargin(0.15)
    ## roofit schas frame.GetYaxis().SetTitleOffset(1.4)
    ## roofit schas frame.Draw()
