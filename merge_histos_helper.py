import ROOT
import math
from os import walk
import copy

def get_mean(h):
    return [h.GetMean(),h.GetRMS()]

def get_mp(h):
    mp = h.GetXaxis().GetBinCenter(h.GetMaximumBin())
    if mp == 0:
        mp = -1
    return [mp,0]

def divide_histo(histo,rate, n=5):
    binsx = histo.GetNbinsX()
    means = []
    mps = []
    rates = []
    min_entries = histo.GetEntries()/n
    # print histo.GetBinContent(0),
    # print histo.GetBinContent(binsx+1)
    bins = binsx/n+1
    # print 'divide histo',n,binsx
    # print '\nmin_entries', min_entries,binsx
    end_bin = 1
    hx = histo.ProjectionX()
    for i in range(n+1):
        entries = 0
        start_bin = end_bin
        k = 0
        while entries < min_entries and start_bin + k <= binsx:
            entries += hx.GetBinContent(start_bin+k)
            k += 1
        end_bin = start_bin + k-1
        h = histo.ProjectionY('',start_bin,end_bin)
        pos = (start_bin-1)/float(binsx)*100.
        this_rate = get_associated_rate(rate,pos,n)
        # print '%d, %3d, %3d - %3d %4.1f - %4.1f, %4.1e, %6d'%(i,k,start_bin,end_bin,pos,(end_bin)/float(binsx)*100., this_rate,h.GetEntries())
        if h.GetEntries() == 0:
            continue

        means.append(get_mean(h)[0])
        mps.append(get_mp(h)[0])
        rates.append(  this_rate)
        # print means[-1],mps[-1]
        if pos == 100:
            break
    # print rates, means, mps
    # print len(rates),len(means),len(mps)
    return (rates,means,mps)

def get_associated_rate(rate,pos,n=5):
    # print rate,type(rate)
    f = math.log10(rate)
    f = int(f)
    # print rate, f
    f = 10**3
    d = 0.1
    nd = d*n*pos/100.
    # print nd
    r = rate *math.exp(nd)
    return r

def get_histos(dir):
    print 'Get histos in Directory: ',dir
    f = []
    f_landau_gaus = []
    for (dirpath, dirnames, filenames) in walk(dir):
        f.extend(filenames)
        for fname in filenames:
            if 'time_2d' in fname:
                f_landau_gaus.append(dirpath+fname)
    histos = {}
    for f in f_landau_gaus:
        print '\t',f
        fname = f.split('/')[-1].split('.')[0]
        fname = fname[fname.find('-run-')+5:]
        fname = fname.split('-')

        run = int(fname[0])
        print '\t\trun',run
        root_file  = ROOT.TFile.Open(f)
        canvas = root_file.Get('time_canvas')
        for key in canvas.GetListOfPrimitives():
            prim  = canvas.GetPrimitive(key.GetName()).Clone()
            if 'h_time_2d' == key.GetName():
                histos[run] = (copy.deepcopy(prim),copy.deepcopy(copy.deepcopy(prim.ProjectionY())))
        print '\t\tadded %d histos.'%len(histos)
    return histos