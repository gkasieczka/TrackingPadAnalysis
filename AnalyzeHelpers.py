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
        

def turnHisto(hist):
    tmp_hist = copy.deepcopy(hist)
    nbins = hist.GetNbinsX()
    for bin in range(0,nbins):
        tmp_hist.SetBinContent(nbins-bin, hist.GetBinContent(bin+1))
        tmp_hist.SetBinError  (nbins-bin, hist.GetBinError  (bin+1))
    return tmp_hist

def fitLandauGaus(hist):

    neg_landau = False
    if hist.GetMean() < 0.:
        neg_landau = True
    if neg_landau:
        hist = turnHisto(hist)

    #if neg_landau:
    #    func = ROOT.TF1('my_landau','[0] * TMath::Landau(-x,[1],[2])', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    #    func.SetParameters(1, hist.GetMean(), hist.GetRMS() )
    #else:
    func = ROOT.TF1('my_landau','[0] * TMath::Landau(x,[1],[2])', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    func.SetParameters(1, hist.GetMean(), hist.GetRMS() )

    hist.Fit('my_landau','q')
    fit_res = []
    fit_res.append(func.GetParameter(0) if not neg_landau else     func.GetParameter(0))
    fit_res.append(func.GetParameter(1) if not neg_landau else -1.*func.GetParameter(1))
    fit_res.append(func.GetParameter(2) if not neg_landau else     func.GetParameter(2))
    return hist, fit_res

## ROOFIT VERSION

    ### x   = RooRealVar('x', 'x', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    ### ral = RooArgList(x)
    ### dh  = RooDataHist('dh', 'dh', ral, RooFit.Import(hist))
    ### 
    ### 
    ### ml     = RooRealVar('ml', 'mean landau' , hist.GetMean(), hist.GetXaxis().GetXmin(),  hist.GetXaxis().GetXmax())
    ### sl     = RooRealVar('sl', 'sigma landau', 10., -30., 30.)
    ### landau = RooLandau ('lx', 'lx', x, ml, sl)
    ### 
    ### mg     = RooRealVar ('mg', 'mean gaus' , hist.GetMean(), hist.GetXaxis().GetXmin(),  hist.GetXaxis().GetXmax())
    ### sg     = RooRealVar ('sg', 'sigma gaus', 10., -30., 30.)
    ### gaus   = RooGaussian('gx', 'gx', x, mg, sg)
    ### 
    ### x.setBins(1000,'cache')
    ### 
    ### ## Construct landau (x) gauss
    ### lxg = RooFFTConvPdf('lxg','landau (x) gaus', x, landau, gaus)
    ### lxg.fitTo(dh)

    ### a = lxg.getParameters(dh)
    ### return a

    ### # frame = x.frame(RooFit.Title('landau (x) gauss convolution'))
    ### # dh.plotOn(frame)
    ### # lxg.plotOn(frame)
    ### # landau.plotOn(frame,RooFit.LineStyle(ROOT.kDashed))
    ### 
    ### # c = ROOT.TCanvas('lg_convolution','landau (x) gaus', 600, 600)
    ### # ROOT.gPad.SetLeftMargin(0.15)
    ### # frame.GetYaxis().SetTitleOffset(1.4)
    ### # frame.Draw()
