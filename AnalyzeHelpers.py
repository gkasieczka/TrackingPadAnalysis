###############################
# Imports
###############################

import ROOT, copy
from array import array
import math
from ROOT import RooFit, RooRealVar, RooGaussian, RooLandau, RooDataSet, RooArgList, RooTreeData, RooFFTConvPdf, RooDataHist


def irr(diamond):
    if diamond in ['IIa-2', 'IIa-3', 'S30','2A87-E']:
        return 'n-irr.'
    if diamond in ['S129', 'IIa-1', 'IIa-5']:
        return 'non-irr.'
    if diamond in ['S125', 'S66']:
        return 'p-irr.'
    else:
        return 'unknown'


def addDiamondInfo(x1, y1, x2, y2, my_run):
    pave = ROOT.TPaveText(x1, y1, x2, y2, 'NDC NB')
    pave.SetTextAlign(12)
    pave.SetTextFont(82)
    pave.SetFillColor(0)
    pave.SetFillStyle(0)
    pave.AddText(my_run.diamond+',\t'+irr(my_run.diamond)+', run %s'%my_run.number)
    pave.AddText('bias: '+str(my_run.bias_voltage)+' V')
    pave.AddText('rate: %s' %(my_run.get_rate_string()))
    pave.SetShadowColor(0)
    pave.SetBorderSize(0)
    pave.SetTextFont(42)
    pave.SetTextSize(0.025)
    return pave

def median(ls):
    sls = sorted(ls)
    length = len(ls)
    return sls[length/2]

def mean(ls):
    if len(ls) == 0: 
        print 'trying to calculate the mean of an empty list'
        return 0.
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

def fitLandauGaus(hist, full = False):

    ## c1 = ROOT.TCanvas()
    ## c1.Divide(2)
    ## c1.cd(1)
    ## hist.Draw()
    neg_landau = False
    if hist.GetMean() < 0.:
        neg_landau = True
    if neg_landau:
        hist = turnHisto(hist)

    hist.Rebin(2)
    hist.SetTitle('')
    hist.SetName('hSignal')
    ## c1.cd(2)
    ## hist.Draw('hist')
    ## c1.SaveAs('foobar.pdf')

    ### #if neg_landau:
    ### #    func = ROOT.TF1('my_landau','[0] * TMath::Landau(-x,[1],[2])', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    ### #    func.SetParameters(1, hist.GetMean(), hist.GetRMS() )
    ### #else:
    ### func = ROOT.TF1('my_landau','[0] * TMath::Landau(x,[1],[2])', hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
    ### func.SetParameters(1, hist.GetMean(), hist.GetRMS() )

    ### hist.Fit('my_landau','q')
    ### fit_res = []
    ### fit_res.append(func.GetParameter(0) if not neg_landau else     func.GetParameter(0))
    ### fit_res.append(func.GetParameter(1) if not neg_landau else -1.*func.GetParameter(1))
    ### fit_res.append(func.GetParameter(2) if not neg_landau else     func.GetParameter(2))
    ### return hist, fit_res

## ROOFIT VERSION

    xmin = hist.GetXaxis().GetXmin()
    xmax = hist.GetXaxis().GetXmax()
    mean = hist.GetMean()
    mp = hist.GetXaxis().GetBinCenter(hist.GetMaximumBin())
    rms = hist.GetRMS()
    flandau = ROOT.TF1('flandau','landau',mp-20,mp+40)
    flandau.SetLineWidth(1)
    flandau.SetLineColor(ROOT.kBlue)
    hist2 = hist.Clone(hist.GetName()+'_2')
    if hist2.GetBinContent(hist2.GetMaximumBin()):
        hist2.Scale(1./hist2.GetBinContent(hist2.GetMaximumBin()))
    hist2.Fit(flandau,'Q','',mp-20,mp+40)

    flandau2 = flandau.Clone('flandau2')
    flandau2.SetRange(0,500)
    flandau2.SetLineStyle(2)

    for i in range(flandau.GetNpar()):
        flandau2.SetParLimits(i,flandau.GetParameter(i),flandau.GetParameter(i))
    hist2.Fit(flandau2,'Q+')#,'same',mp-20,mp+40)
    for i in range(flandau.GetNpar()):
        par_i = flandau.GetParameter(i)
        # print i, par_i
        if i == 0 and par_i == 0:
            par_i = 1.0
        if i == 2 and par_i == 0:
            par_i == 1.0
        # print i,par_i,type(i),type(par_i)
        flandau3 = hist2.GetFunction('flandau2')
        if flandau3:
            # print flandau3,flandau3.GetNpar()
            flandau3.SetParameter(i,par_i)
    if False:
        for i in range(flandau.GetNpar()):
            print flandau.GetParameter(i),flandau2.GetParameter(i)

    x   = RooRealVar('x', 'signal / adc', 0,500)
    x.setRange("signal",mp - 40, mp+90)
    x.setRange("draw",0,500)
    ral = RooArgList(x)
    dh  = RooDataHist('dh', 'dh', ral, RooFit.Import(hist))
    
    
    if full: 
        ml     = RooRealVar('ml', 'mean landau' , mp, mp-20., mp+30)
        sl     = RooRealVar('sl', 'sigma landau', 10, 1., 25.)
    else:
        ml     = RooRealVar('ml', 'mean landau' , mean, mean-40., mean)
        sl     = RooRealVar('sl', 'sigma landau', 10., 6., 14.)
    landau = RooLandau ('lx', 'lx', x, ml, sl)
    
    mean = 0
    if full: 
        mg     = RooRealVar ('mg', 'mean gaus' , 0,0,0)
        sg     = RooRealVar ('sg', 'sigma gaus', flandau.GetParameter(2), 0.1, 30.)
    else:
        mg     = RooRealVar ('mg', 'mean gaus' , 0,0,0) #mean, mean-30.,  mean+30.)
        sg     = RooRealVar ('sg', 'sigma gaus', 2., 0.1, 20.)
    gaus   = RooGaussian('gx', 'gx', x, mg, sg)
    
    x.setBins(1000,'cache')
    
    ## Construct landau (x) gauss
    lxg = RooFFTConvPdf('lxg','landau (x) gaus', x, landau, gaus)
    lxg.fitTo(dh,RooFit.Range("signal"), RooFit.PrintEvalErrors(-1))
    #,RooFit.Normalization(ROOT.RooAbsReal.NumEvent,1))
    a = lxg.getParameters(dh)
    if False:
        print 'fit par0                                     %+6.1f'%flandau.GetParameter(0)
        print 'fit par1                                     %+6.1f'%flandau.GetParameter(1)
        print 'fit par2                                     %+6.1f'%flandau.GetParameter(2)
        print 'mp                                           %+6.1f'%mp
        print 'rms                                          %+6.1f'%rms
        print 'lxg.getParameters(dh).getRealValue(\'ml\'):  %+6.1f'% a.getRealValue('ml')
        print 'lxg.getParameters(dh).getRealValue(\'sl\'):  %+6.1f'% a.getRealValue('sl')
        print 'lxg.getParameters(dh).getRealValue(\'sg\'):  %+6.1f'% a.getRealValue('sg')

    frame = x.frame(RooFit.Title('landau (x) gauss convolution'),RooFit.Range("draw"))
    #,RooFit.Normalization(ROOT.RooAbsReal.NumEvent,1))
    dh.plotOn(frame,RooFit.Range("draw"))
    #,RooFit.Normalization(1./dh.numEntries(),ROOT.RooAbsReal.Raw))
    lxg.plotOn(frame,RooFit.LineColor(ROOT.kRed),RooFit.Range("draw"))
    #,RooFit.Normalization(1,ROOT.RooAbsReal.Raw))
    #lxg.plotOn(frame,RooFit.LineColor(ROOT.kBlue),RooFit.Range("signal"),RooFit.Components('lx,gx'))
    
    # c = ROOT.TCanvas('lg_convolution','landau (x) gaus', 600, 600)
    # c.Divide(2)
    # c.cd(1)
    # hist.Draw()
    # c.cd(2)
    # ROOT.gPad.SetLeftMargin(0.15)
    # frame.GetYaxis().SetTitleOffset(1.4)
    # frame.Draw()
    # c.SaveAs('histograms/outputhisto'+hist.GetName().split('pz')[1]+'.pdf')
    return dh, copy.deepcopy(a), copy.deepcopy(frame),copy.deepcopy(hist2)


def make_area_time_plot(h_signal, h_entries, xpos,ypos,radius,descr=''):
    if descr != '':
        name = 'hSignalTime_%s_x%03d_y%03d_r%03d'%(descr,xpos*100,ypos*100,radius*100)
    else:
        name = 'hSignalTime_x%03d_y%03d_r%03d'%(xpos*100,ypos*100,radius*100)
    title = 'Signal vs. Time: %4.1d/%4.1f, r = %2.1f'%(xpos,ypos,radius)
    bins = h_signal.GetNbinsZ()
    zmin = h_signal.GetZaxis().GetXmin()
    zmax = h_signal.GetZaxis().GetXmax()
    signal = ROOT.TH1F(name,title,bins,zmin,zmax)
    name = 'hSignalEntriesTime_x%03d_y%03d_r%03d'%(xpos*100,ypos*100,radius*100)
    entries = ROOT.TH1F(name,title,bins,zmin,zmax)
    for xbin in range(1,h_signal.GetNbinsX()+1):
        for ybin in range(1,h_signal.GetNbinsY()+1):
            x = h_signal.GetXaxis().GetBinCenter(xbin)
            y = h_signal.GetYaxis().GetBinCenter(ybin)
            #check if bin within the radius
            xx = x - xpos
            yy = y - ypos
            # print '%2.4f/%2.4f %2.4f/%2.4f %2.4f/%2.4f %2.4f %2.4f => %d'%(x,y,xpos,ypos,xx,yy,(xx)**2+(yy)**2,radius**2,(xx)**2+(yy)**2 > radius**2)
            if (xx)**2+(yy)**2 > radius**2:
                continue
            h_signal.GetXaxis().SetRange(xbin, xbin)
            h_signal.GetYaxis().SetRange(ybin, ybin)
            h_entries.GetXaxis().SetRange(xbin, xbin)
            h_entries.GetYaxis().SetRange(ybin, ybin)
            proj_signal = h_signal.Project3D('z')
            proj_entries = h_entries.Project3D('z')
            signal.Add(proj_signal,1)
            entries.Add(proj_entries,1)

    signal.GetXaxis().SetTitle('minutes')
    signal.Divide(entries)
    for bin in range(1,signal.GetNbinsX()+1):
        nentries = entries.GetBinContent(bin)
        if nentries == 0: nentries = 1
        signal.SetBinError(bin,signal.GetBinContent(bin)/math.sqrt(nentries))

    signal_rel = copy.deepcopy(signal)
    if signal[1] !=0:
        signal_rel.Scale(1. / signal[1])
    signal_rel.GetZaxis().SetRangeUser(0, 1.05)
    return signal,entries,signal_rel

def get_mean_and_sigma(sample):
    if len(sample) == 0:
        mean = 0
        variance = 0
    else:
        mean = float(reduce(lambda x,y : x+y, sample)) / len(sample)
        variance = reduce(lambda x,y: x+y, map(lambda xi: (xi-mean)**2, sample))/ len(sample)
    return mean, math.sqrt(variance)

def find_range_3d(signal):
    signals = []
    print signal.GetXaxis().GetFirst(),signal.GetXaxis().GetLast()
    print signal.GetYaxis().GetFirst(),signal.GetYaxis().GetLast()
    for xbin in range(signal.GetXaxis().GetFirst(),signal.GetXaxis().GetLast()):
        for ybin in range(signal.GetYaxis().GetFirst(),signal.GetYaxis().GetLast()):
            signals.append(signal.GetBinContent(xbin,ybin))
    l = len(signals)
    signals = sorted(s for s in signals if s > 5)
    signals = signals[int(l*.05):int(l*.95)]

    xlow,xup =  signals[int(l*.05)],signals[-2]
    mean,sigma = get_mean_and_sigma(signals)
    if xup>mean + 4 *sigma:
        xup = mean + 4 *sigma
    if xlow<mean - 4 *sigma:
        xlow = mean - 4 *sigma
    print xlow,xup
    return xlow,xup
