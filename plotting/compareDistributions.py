#!/bin/env python

import sys, os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-num",  help="Numerator sample encoding",      type=str)
parser.add_argument("-den",  help="Denominator sample encoding",    type=str)
parser.add_argument("-d", "--debug", help="Debug on, pop plots to window",
                    action="store_true")
parser.add_argument("-v", "--verbose", help="Increase output verbosity",
                    action="store_true")
#CI,2Mu,New,100k,Con,LL
#DY,2E,Testing,None,None,None

args = parser.parse_args()

numlist = args.num.split(',')
denlist = args.den.split(',')

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

antypes={
    "E":["e","Ele"],
    "Mu":["mu","Mu"]
    }
print(numlist)
print(denlist)

baseform="root://cmseos.fnal.gov///store/user/sturdy/ZprimeAnalysis/histos{0:s}/histosZprime{1:s}{1:s}/"
ciform="output_CITo2%s_M%d_CUETP8M1_Lam%sTeV%s%s_13TeV_Pythia8_Corrected-v4_ntuple.root"
dyform="output_DYTo2%s_M%d_CUETP8M1_13TeV_Pythia8_Corrected-v3_ntuple.root"

r.gROOT.SetBatch(True)
if args.debug:
    r.gROOT.SetBatch(False)
    pass

mvals=[300,800,1300]

supers = [400,500,700,1100,1900,3500]
bins = [0,50,100,150,200,250,300,350,400,450,500,550,600,700,800,900,1000,1250,1500,2000,2500,3000,5000]
rbins = np.array(bins, np.dtype('float64'))

files=[]
hist = ndict()
pnames = ndict()

samples = {
    "{0:s}To2{1:s}".format(numlist[0],numlist[1][1:]):numlist,
    "{0:s}To2{1:s}".format(denlist[0],denlist[1][1:]):denlist
    }

numspecial = ""
if numlist[0] == "CI":
    numspecial = "{0:s}TeV{1:s}{2:s}".format(numlist[3],numlist[4],numlist[5])
    pass
denspecial = ""
if denlist[0] == "CI":
    denspecial = "{0:s}TeV{1:s}{2:s}".format(denlist[3],denlist[4],denlist[5])
    pass

for sample in samples:
    numsample = samples[sample]
    antype = antypes[numsample[1][1:]]
    flav   = numsample[1]
    src    = numsample[2]
    if numsample[0] == "CI":
        lval = numsample[3]
        intf = numsample[4]
        heli = numsample[5]
        pname = "ci2"+antype[0]+"lam"+lval+intf+heli+src
    else:
        pname  = "dy2"+antype[0]+src
        pass
    pnames[sample] = pname
    base   = baseform.format(src,antype[1])
    hist[sample] = None
    print(flav,src,base)

    can   = r.TCanvas("can","",800,800)
    stack = r.THStack("stack","")
    leg = r.TLegend(0.5,0.7,0.9,0.9)

    for mval in mvals:
        if numsample[0] == "CI":
            lf = r.TFile.Open("%s%s"%(base,ciform%(numsample[1][1:],mval,lval,intf,heli)))
        else:
            lf = r.TFile.Open("%s%s"%(base,dyform%(numsample[1][1:],mval)))
            pass

        if not lf or lf == None:
            print(lf,hist[sample])
            continue
        elif not lf.IsOpen() or lf.IsZombie():
            print(lf,hist[sample])
            continue
        pass

        files.append(lf)
        htmp = lf.Get("ZprimeRecomass")
        htmp.Scale(1.3)
        # htmp = htmp.Rebin(100,"%s_%d_rebinned"%(htmp.GetName(),mval))
        htmp = htmp.Rebin(len(rbins)-1,"%s_%d_rebinned"%(htmp.GetName(),mval),rbins)
        if mval == 300:
            hist[sample] = htmp.Clone("htmp_%s%d"%(sample,mval))
            htmp.SetLineColor(r.kOrange)
            htmp.SetFillColor(r.kOrange)
            htmp.SetFillStyle(3001)
            stack.Add(htmp)
            leg.AddEntry(hist[sample],"{0:s} {1:d} GeV".format(sample,mval),"f")
        else:
            if hist[sample]:
                hist[sample].Add(htmp.Clone("htmp_%s%d"%(sample,mval)))
            else:
                hist[sample] = htmp.Clone("htmp_%s%d"%(sample,mval))
                pass

            if mval == 1300:
                htmp.SetLineColor(r.kGreen)
                htmp.SetFillColor(r.kGreen)
                htmp.SetFillStyle(3001)
                stack.Add(htmp)
                leg.AddEntry(hist[sample],"{0:s} {1:d} GeV".format(sample,mval),"f")
            else:
                htmp.SetLineColor(r.kBlue)
                htmp.SetFillColor(r.kBlue)
                htmp.SetFillStyle(3001)
                stack.Add(htmp)
                leg.AddEntry(hist[sample],"{0:s} {1:d} GeV".format(sample,mval),"f")
                pass

            if numsample[0] == "CI":
                if mval == 1300 and "%s%s"%(intf,heli) == "ConLL":
                    lf = r.TFile.Open("%s%s"%(base,ciform%(numsample[1][1:],2000,lval,intf,heli)))
                    print("M2000 sample",lf)
                    if not lf or lf == None:
                        print(lf,hist[sample])
                        continue
                    elif not lf.IsOpen() or lf.IsZombie():
                        print(lf,hist[sample])
                        continue

                    htmp = lf.Get("ZprimeRecomass")
                    htmp.Scale(1.3)
                # htmp = htmp.Rebin(100,"%s_%d_rebinned"%(htmp.GetName(),2000))
                    htmp = htmp.Rebin(len(rbins)-1,"%s_%d_rebinned"%(htmp.GetName(),2000),rbins)
                    hist[sample].Add(htmp.Clone("htmp_%s%d"%(numsample[0],2000)))
                    htmp.SetLineColor(r.kRed)
                    htmp.SetFillColor(r.kRed)
                    htmp.SetFillStyle(3001)
                    stack.Add(htmp)
                    leg.AddEntry(hist[sample],"{0:s} {1:d} GeV".format(sample,2000),"f")
                    pass
                pass
            pass
        pass
    # stack.Rebin(10)
    # hist[sample].Rebin(10)
    stack.SetMinimum(0.8*hist[sample].GetMinimum(0.001))
    stack.SetMaximum(1.25*hist[sample].GetMaximum())
    stack.Draw("hist")
    stack.GetXaxis().SetRangeUser(0,5000)
    stack.GetXaxis().SetNdivisions(505)
    r.gPad.SetLogy(True)
    hist[sample].Draw("same")
    leg.Draw("")
    can.Modified()
    can.Update()
    # raw_input()
    for ftype in ["png","C","pdf","eps","png"]:
        # can.SaveAs("~/public/forCIAnalysis/cilam{3:s}vsdyto2{1:s}_{2:s}.{0:s}".format(ftype,antype[0],numsample[0],lval))
        can.SaveAs("~/public/forCIAnalysis/{0:s}_{1:s}.{2:s}".format(pname,src,ftype))
        # raw_input("enter to continue")
        pass
    for p,point in enumerate(supers[:-1]):
        bval  = hist[sample].FindBin(point)
        upval = hist[sample].FindBin(supers[p+1]-0.05)
        val  = hist[sample].Integral(bval,upval)
        print("{0:s} {1:d} {2:d} {3:d} {4:2.4f}".format(numsample[0],point,bval,upval,val))
        pass
    pass

can   = r.TCanvas("can","",800,800)
plot  = r.TPad("plotpad","",0,0.15,1,1)
rplot = r.TPad("ratiopad","",0,0,1,0.15)
hist["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])].SetLineColor(r.kRed)
hist["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])].SetLineWidth(2)
hist["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])].SetLineColor(r.kBlue)
hist["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])].SetLineWidth(2)
# rhist = hist["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])].Clone("lam{0:s}dyratio".format(lval))
rhist = hist["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])].Clone("{0:s}vs{1:s}ratio".format(pnames["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])],pnames["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])]))
rhist.Divide(hist["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])])
plot.cd()
leg = r.TLegend(0.5,0.7,0.9,0.9)
leg.AddEntry(hist["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])],"numerator:   {0:s}To2{1:s} {2:s}".format(numlist[0],numlist[1][1:],numspecial),"lep")
leg.AddEntry(hist["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])],"denominator: {0:s}To2{1:s} {2:s}".format(denlist[0],denlist[1][1:],denspecial),"lep")
hist["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])].Draw()
hist["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])].Draw("same")
leg.Draw("")
can.Modified()
r.gPad.SetLogy(True)
r.gPad.SetGridy(True)
r.gPad.SetGridx(True)

rplot.cd()
rhist.SetLineColor(r.kBlack)
rhist.GetYaxis().SetLabelSize(0.15)
rhist.GetYaxis().SetRangeUser(0,2)
rhist.GetYaxis().SetNdivisions(505)
rhist.GetXaxis().SetLabelSize(0.)
rhist.GetXaxis().SetTickLength(0.1)
rhist.Draw()
r.gPad.SetGridy(True)
r.gPad.SetGridx(True)

can.cd()
plot.Draw()
rplot.Draw("same")
if args.debug:
    raw_input("enter")
    pass
for ftype in ["png","C","pdf","eps","png"]:
    # can.SaveAs("~/public/forCIAnalysis/ratio_cilam{2:s}vsdyto2{1:s}.{0:s}".format(ftype,antype[0],lval))
    can.SaveAs("~/public/forCIAnalysis/ratio_{0:s}vs{1:s}.{2:s}".format(pnames["{0:s}To2{1:s}".format(numlist[0],numlist[1][1:])],pnames["{0:s}To2{1:s}".format(denlist[0],denlist[1][1:])],ftype))
    # raw_input("enter to continue")
    pass
