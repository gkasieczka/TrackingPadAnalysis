import ROOT, copy
from ROOT import RooFit, RooRealVar, RooGaussian, RooLandau, RooDataSet, RooArgList, RooTreeData, RooFFTConvPdf, RooDataHist


infile = ROOT.TFile('track_info.root','READ')
tree = infile.Get('track_info')

# fill histo with the tracks and integral50

h_3d = ROOT.TH3F('h_3dfull','3D histogram', 
	 25,   -0.30,   0.20, 
	 25,   -0.10,   0.40, 
	200, -400.00, 400.00)

foo = copy.deepcopy(h_3d.Project3D('yx'))
h_2d_mpv  = copy.deepcopy(foo)

h_1dtest = ROOT.TH1F('h_1dtest', 'h_1dtest', 500, -250.00, 250.00)

for ev in tree:
  h_3d.Fill(ev.track_x, ev.track_y, ev.integral50)
##  if(0.05 > ev.track_x > 0. and 0.05 > ev.track_y > 0.):
##  h_1dtest.Fill(ev.integral50)



## h_1dtest.Fit('landau')
## mpv = h_1dtest.GetFunction('landau').GetParameter(1)
## sig = h_1dtest.GetFunction('landau').GetParameter(2)
## h_1dtest.Draw()

for xbin in range(1,h_3d.GetNbinsX()+1):
  for ybin in range(1,h_3d.GetNbinsY()+1):
    #if not xbin == 25: continue
    #if not ybin == 25: continue
    print 'at bins %d %d' %(xbin, ybin)
    z_histo = h_3d.ProjectionZ(h_3d.GetName()+'_pz_'+str(xbin)+'_'+str(ybin), xbin, xbin, ybin, ybin)
    if z_histo.Integral() == 0.: 
      continue
    z_histo.Fit('landau')
    mpv = z_histo.GetFunction('landau').GetParameter(1)
    if mpv < 0: continue
    print 'THIS IS THE MPV: ', mpv
    h_2d_mpv.SetBinContent(xbin, ybin, mpv)

h_2d_mpv.Draw('colz')



## ROOFIT SCHAS

#h_3d.Draw('box')
#test = h_3d.Project3D('yx')
## #test.Draw('colz')
## h_1dtest.Draw()
## x = RooRealVar('x', 'x', -250., 250.)
## ral = RooArgList(x)
## dh = RooDataHist('dh', 'dh', ral, RooFit.Import(h_1dtest))
## 
## 
## t = RooRealVar('t', 't', -10, 30)
## 
## ml     = RooRealVar('ml', 'mean landau' , 100., 0., 300)
## sl     = RooRealVar('sl', 'sigma landau', 1., 0.1, 30)
## landau = RooLandau('lx', 'lx', t, ml, sl)
## 
## mg     = RooRealVar('mg', 'mean gaus' , 100., 0., 300)
## sg     = RooRealVar('sg', 'sigma gaus', 1., 0.1, 30)
## gaus   = RooGaussian('lx', 'lx', t, ml, sl)
## 
## t.setBins(10000,'cache')
## 
## ## Construct landau (x) gauss
## lxg = RooFFTConvPdf("lxg","landau (X) gaus", t, landau, gaus)
## lxg.fitTo(dh)

'''
  // S a m p l e ,   f i t   a n d   p l o t   c o n v o l u t e d   p d f 
  // ----------------------------------------------------------------------

  // Sample 1000 events in x from gxlx
  RooDataSet* data = lxg.generate(t,10000) ;

  // Fit gxlx to data
  lxg.fitTo(*data) ;

  // Plot data, landau pdf, landau (X) gauss pdf
  RooPlot* frame = t.frame(Title("landau (x) gauss convolution")) ;
  data->plotOn(frame) ;
  lxg.plotOn(frame) ;
  landau.plotOn(frame,LineStyle(kDashed)) ;


  // Draw frame on canvas
  new TCanvas("rf208_convolution","rf208_convolution",600,600) ;
  gPad->SetLeftMargin(0.15) ; frame->GetYaxis()->SetTitleOffset(1.4) ; frame->Draw() ;

}
'''
