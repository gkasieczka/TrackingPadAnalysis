import os
import ROOT
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

class root_style(object) :
    def __init__(self) :
        # ROOT.gROOT.SetBatch(1)
        self.marg_top = 50.
        self.marg_bot = 130.
        self.marg_left = 150.
        self.marg_right = 0
        self.histo_height = 0
        self.histo_width = 0
        self.width = 0
        self.height = 0
        self.main_dir = '.'


    def make_legend(self,X1,Y2, nentries):
        width = 0.3
        X2 = X1 + width
        Y1 = Y2 - nentries *.25 * width
        # raw_input('nentries: %s'%nentries)
        l = ROOT.TLegend(X1,Y1,X2,Y2)
        l.SetLineWidth(2)
        l.SetBorderSize(0)
        l.SetFillColor(0)
        l.SetFillStyle(0)
        l.SetTextFont(42)
        l.SetTextSize(0.04)
        # l.SetBorderSize(1)
        l.SetTextAlign(12)
        return l


    def set_style(self,width,height,ratio):
        self.width = width
        self.height = height
        ROOT.gStyle.SetPalette(53)
        ROOT.gStyle.SetCanvasBorderMode(0);
        ROOT.gStyle.SetCanvasColor(ROOT.kWhite)
        ROOT.gStyle.SetCanvasDefH(height); ##gHeight of canvas
        ROOT.gStyle.SetCanvasDefW(width); ##gWidth of canvas
        ROOT.gStyle.SetCanvasDefX(0);   ##gPOsition on screen
        ROOT.gStyle.SetCanvasDefY(0);

        ##g For the Pad:
        ROOT.gStyle.SetPadBorderMode(0);
        ##g ROOT.gStyle.SetPadBorderSize(Width_t size = 1);
        ROOT.gStyle.SetPadColor(ROOT.kWhite);
        ROOT.gStyle.SetPadGridX(False);
        ROOT.gStyle.SetPadGridY(False);
        ROOT.gStyle.SetGridColor(0);
        ROOT.gStyle.SetGridStyle(3);
        ROOT.gStyle.SetGridWidth(1);

        ##g For the frame:
        ROOT.gStyle.SetFrameBorderMode(0);
        ROOT.gStyle.SetFrameBorderSize(1);
        ROOT.gStyle.SetFrameFillColor(0);
        ROOT.gStyle.SetFrameFillStyle(0);
        ROOT.gStyle.SetFrameLineColor(1);
        ROOT.gStyle.SetFrameLineStyle(1);
        ROOT.gStyle.SetFrameLineWidth(1);

        ##g For the histo:
        ##g      ROOT.gStyle.SetHistFillColor(63);
        ROOT.gStyle.SetHistFillStyle(0);
        ROOT.gStyle.SetHistLineColor(1);
        ROOT.gStyle.SetHistLineStyle(0);
        ROOT.gStyle.SetHistLineWidth(2);
        ##g ROOT.gStyle.SetLegoInnerR(Float_t rad = 0.5);
        ##g ROOT.gStyle.SetNumberContours(Int_t number = 20);

        ##g  ROOT.gStyle.SetEndErrorSize(0);
        ROOT.gStyle.SetErrorX(0.);
        ##g  ROOT.gStyle.SetErrorMarker(20);

        ROOT.gStyle.SetMarkerStyle(20);

        ##gFor the fit/function:
        ROOT.gStyle.SetOptFit(1);
        ROOT.gStyle.SetFitFormat("5.4g");
        ROOT.gStyle.SetFuncColor(2);
        ROOT.gStyle.SetFuncStyle(1);
        ROOT.gStyle.SetFuncWidth(1);

        ##gFor the date:
        ROOT.gStyle.SetOptDate(0);
        ##g ROOT.gStyle.SetDateX(Float_t x = 0.01);
        ##g ROOT.gStyle.SetDateY(Float_t y = 0.01);

        ##g For the statistics box:
        ROOT.gStyle.SetOptFile(0);
        ROOT.gStyle.SetOptStat(0); ##g To display the mean and RMS:   SetOptStat("mr");
        ROOT.gStyle.SetStatColor(ROOT.kWhite);
        ROOT.gStyle.SetStatFont(42);
        ROOT.gStyle.SetStatFontSize(0.025);
        ROOT.gStyle.SetStatTextColor(1);
        ROOT.gStyle.SetStatFormat("6.4g");
        ROOT.gStyle.SetStatBorderSize(1);
        ROOT.gStyle.SetStatH(0.1);
        ROOT.gStyle.SetStatW(0.15);
        ##g ROOT.gStyle.SetStatStyle(Style_t style = 1001);
        ##g ROOT.gStyle.SetStatX(Float_t x = 0);
        ##g ROOT.gStyle.SetStatY(Float_t y = 0);

        ##g Margins:
        self.histo_height = height - self.marg_bot - self.marg_top
        self.histo_width = self.histo_height/ratio
        self.marg_right = width-self.marg_left - self.histo_width
        # print self.histo_width,self.histo_height
        # raw_input ('%s = %s + %s + %s'%(width, self.marg_left, self.histo_width, self.marg_right))
        ROOT.gStyle.SetPadTopMargin(self.marg_top/height);
        ROOT.gStyle.SetPadBottomMargin(self.marg_bot/height);
        ROOT.gStyle.SetPadLeftMargin(self.marg_left/width);
        ROOT.gStyle.SetPadRightMargin(self.marg_right/width);

        ##g For the Global title:

        ##g  ROOT.gStyle.SetOptTitle(0);
        ROOT.gStyle.SetTitleFont(42);
        ROOT.gStyle.SetTitleColor(ROOT.kBlack);
        ROOT.gStyle.SetTitleTextColor(1);
        ROOT.gStyle.SetTitleFillColor(10);
        ROOT.gStyle.SetTitleFontSize(0.05);
        ROOT.gStyle.SetOptTitle(0);
        ##g ROOT.gStyle.SetTitleH(0); // Set the height of the title box
        ##g ROOT.gStyle.SetTitleW(0); // Set the width of the title box
        ##g ROOT.gStyle.SetTitleX(0); // Set the position of the title box
        ##g ROOT.gStyle.SetTitleY(0.985); // Set the position of the title box
        ##g ROOT.gStyle.SetTitleStyle(Style_t style = 1001);
        ##g ROOT.gStyle.SetTitleBorderSize(2);

        ##g For the axis titles:

        ROOT.gStyle.SetTitleColor(ROOT.kBlack, "XYZ");
        ROOT.gStyle.SetTitleFont(42, "XYZ");
        ROOT.gStyle.SetTitleSize(0.04, "XYZ");
        ##g ROOT.gStyle.SetTitleXSize(Float_t size = 0.02); // Another way to set the size?
        ##g ROOT.gStyle.SetTitleYSize(Float_t size = 0.02);
        ROOT.gStyle.SetTitleXOffset(1.33);
        ROOT.gStyle.SetTitleYOffset(1+.27*ratio);
        ROOT.gStyle.SetTitleOffset(1.4, "Z"); ##g Another way to set the Offset

        ##g For the axis labels:

        ROOT.gStyle.SetLabelColor(ROOT.kBlack, "XYZ");
        ROOT.gStyle.SetLabelFont(42, "XYZ");
        ROOT.gStyle.SetLabelOffset(0.010, "XYZ");
        ROOT.gStyle.SetLabelOffset(0.1, "Z");
        ROOT.gStyle.SetLabelSize(0.04, "XYZ");

        ##g For the axis:

        ROOT.gStyle.SetAxisColor(1, "XYZ");
        ROOT.gStyle.SetStripDecimals(True);
        ROOT.gStyle.SetTickLength(0.03, "XYZ");
        ROOT.gStyle.SetTickLength(0.03*ratio, "Y");
        ROOT.gStyle.SetTickLength(0.02, "Z");
        ROOT.gStyle.SetNdivisions(510, "XYZ");
        ROOT.gStyle.SetPadTickX(1);  ##g To get tick marks on the opposite side of the frame
        ROOT.gStyle.SetPadTickY(1);

        ##g Change for log plots:
        ROOT.gStyle.SetOptLogx(0);
        ROOT.gStyle.SetOptLogy(0);
        ROOT.gStyle.SetOptLogz(0);

        ##gLegend
        ROOT.gStyle.SetLegendFont(42);


        ROOT.gStyle.cd();

    def get_canvas(self,name):
        canvas = ROOT.TCanvas(name,'',self.width,self.height)
        canvas.UseCurrentStyle()
        return canvas

    def save_canvas(self,canvas,name):
        canvas.Update()
        fname = self.main_dir
        if not fname.endswith('/'):
            fname+='/'
        fname += 'output/%s/'+name+'.%s'
        ftypes = ['png','pdf','eps','root','tex']
        for f in ftypes:
            ensure_dir(fname%(f,f))
            canvas.SaveAs(fname%(f,f))

