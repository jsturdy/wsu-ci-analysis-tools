#!/bin/env python

import sys,os,re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("sample",        help="Sample to stitch together",type=str)
parser.add_argument("--lamVal",      help="Lambda value to use",      type=int)
parser.add_argument("--infMode",     help="Interference mode to use", type=str)
parser.add_argument("--heliModel",   help="Heliciy model to use",     type=str)
parser.add_argument("-d", "--debug", help="debugging information",action="store_true")

args = parser.parse_args()

import cPickle as pickle
from nesteddict import nesteddict as ndict
import ROOT as r
# from wsuPyROOTUtils import *

if not args.debug:
    r.gROOT.SetBatch(r.kTRUE)

allowedValues = {
    "lamVal":    [16,22,28,34],
    "infMode":   ["Con","Des"],
    "heliModel": ["LL","LR","RR"],
    "mass": [300,800,1300],
}

if "CI" in args.sample:
    if args.lamVal not in allowedValues["lamVal"]:
        print("Invalid lambda value specified, must be in:",allowedValues["lamVal"])
        exit(1)
    elif args.infMode not in allowedValues["infMode"]:
        print("Invalid interference mode specified, must be in:",allowedValues["infMode"])
        exit(1)
    elif args.heliModel not in allowedValues["heliModel"]:
        print("Invalid helicity model specified, must be in:",allowedValues["heliModel"])
        exit(1)
    if args.infMode == "Con" and args.heliModel == "LL":
        allowedValues["mass"].append(2000)
        pass
    pass

samples = None
with open("ci_xsec_data.pkl","rb") as pkl:
    samples = pickle.load(pkl)
    pass

if "2E" in args.sample:
    histname = "diElectronMass"
else:
    histname = "diMuonMass"

# CITo2Mu_M800_CUETP8M1_Lam28TeVConLL_13TeV_Pythia8_Corrected-v4_summary.root
# raw inputs
# scaled by xs
# scaled by xs in specified bin(s)

hout  = []
outcan  = r.TCanvas("outcan","outcan",  800,800)
outcan2 = r.TCanvas("outcan2","outcan2",800,800)
outcan3 = r.TCanvas("outcan3","outcan3",800,800)

hMin = 1e-9
hMax = 1e10

for i,mass in enumerate(allowedValues["mass"]):
    infname = "%s_M%s_CUETP8M1_Lam%dTeV%s%s_13TeV_Pythia8_Corrected-v4_summary.root"%(args.sample,
                                                                                      mass,
                                                                                      args.lamVal,
                                                                                      args.infMode,
                                                                                      args.heliModel)

    sample = samples["Lam%d"%(args.lamVal)]["M%d"%(mass)][args.infMode][args.heliModel][args.sample]
    print(sample)
    lumi  = 1.0 # in /pb
    lfact = 1.0 # to get to human readable, i.e., -> 1/pb, 1/fb etc
    npass  = sample["cutEfficiency"][0]
    nfail  = sample["cutEfficiency"][0]
    ngen  = npass+nfail
    ncut  = sample["cutEfficiency"][0]
    eff   = npass/ngen
    xs    = sample["xsec"][0] ## in pb
    lumif = xs*lumi*lfact/ngen
    sf    = lumif*eff
    print(ngen,npass,nfail,eff,xs,lumif,sf)

    # with r.TFile(infname,"READ") as infile:
    hist = []
    with open("test.txt","w") as f:
        infile = r.TFile(infname,"READ")
        r.SetOwnership(infile,False)
        hist.append(infile.Get("genfilter/%s"%(histname)))
        r.SetOwnership(hist,False)
        hist[0].SetLineWidth(2)
        extra = i if (i%2==0) else -i
        hist[0].SetLineColor(r.kViolet + extra)

        # don't apply the mass cuts
        hist.append(hist[0].Clone("m%d_full"%(mass)))
        hist2.Scale(lumif)
        hist[0].Scale(sf)
        # scaled with no mass cuts
        hist3 = hist[0].Clone("m%d_eff"%(mass))

        if i == 0:
            hMax = 1.25*hist[0].GetMaximum()
        elif i == (len(allowedValues["mass"])-1):
            hMin = 0.8*hist[0].GetMinimum(1e-8)

        minBin = hist[0].FindBin(sample["minCut"])
        maxBin = hist[0].FindBin(sample["maxCut"])
        if args.debug:
            print(minBin,hist[0].GetBinLowEdge(minBin),hist[0].GetBinCenter(minBin),hist[0].GetBinWidth(minBin))
            print(maxBin,hist[0].GetBinLowEdge(maxBin),hist[0].GetBinCenter(maxBin),hist[0].GetBinWidth(maxBin))
        for bi in range(hist[0].GetNbinsX()):
            if bi < minBin or bi > maxBin:
                hist[0].SetBinContent(bi+1,0)
                hist[0].SetBinError(bi+1,0)
            pass

        if hout:
            outcan.cd()
            hout.Add(hist)
            hist[0].SetMinimum(hMin)
            hist[0].SetMaximum(hMax)
            hist[0].Draw("sames")

            outcan2.cd()
            hout2.Add(hist2)
            hist2.SetMinimum(hMin)
            hist2.SetMaximum(hMax)
            hist2.Draw("sames")
        else:
            outcan.cd()
            hout = hist[0].Clone("scaledAndMerged")
            hist[0].SetMinimum(hMin)
            hist[0].SetMaximum(hMax)
            hist[0].Draw("")

            outcan2.cd()
            hout2 = hist2.Clone("scaledAndMerged2")
            r.SetOwnership(hist2,False)
            hist2.SetMinimum(hMin)
            hist2.SetMaximum(hMax)
            hist2.Draw("")
            pass
        # raw_input("Next histogram")
        pass
    pass

print hMin,hMax
outcan.cd()
hist[0].GetXaxis().SetRangeUser(275.,5000.)
hist[0].SetMinimum(hMin)
hist[0].SetMaximum(hMax)
r.gPad.SetLogy(r.kTRUE)
outcan.Update()
outcan.SaveAs("%s_Lambda%dTeV_%s_%s.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
r.gPad.SetLogx(r.kTRUE)
outcan.Update()
outcan.SaveAs("%s_Lambda%dTeV_%s_%s_logx.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
hout.SetLineWidth(2)
hout.SetLineColor(r.kRed)
if args.debug:
    raw_input("draw combined")
hout.Draw("sames")
r.gPad.SetLogx(r.kFALSE)
outcan.Update()
outcan.SaveAs("%s_Lambda%dTeV_%s_%s_combined.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
r.gPad.SetLogx(r.kTRUE)
outcan.Update()
outcan.SaveAs("%s_Lambda%dTeV_%s_%s_combined_logx.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))

outcan2.cd()
hist2.SetMinimum(hMin)
hist2.SetMaximum(hMax)
r.gPad.SetLogy(r.kTRUE)
outcan2.Update()
outcan2.SaveAs("%s_Lambda%dTeV_%s_%s_noCut.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
r.gPad.SetLogx(r.kTRUE)
outcan2.Update()
outcan2.SaveAs("%s_Lambda%dTeV_%s_%s_noCut_logx.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
hout2.SetLineWidth(2)
hout2.SetLineColor(r.kRed)
if args.debug:
    raw_input("draw combined")
hout2.Draw("sames")
r.gPad.SetLogx(r.kFALSE)
outcan2.Update()
outcan2.SaveAs("%s_Lambda%dTeV_%s_%s_combined_noCut.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
r.gPad.SetLogx(r.kTRUE)
outcan2.Update()
outcan2.SaveAs("%s_Lambda%dTeV_%s_%s_combined_noCut_logx.png"%(args.sample,args.lamVal,args.infMode,args.heliModel))
if args.debug:
    raw_input("exit")
