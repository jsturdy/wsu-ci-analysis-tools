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
    r.gStyle.SetOptStat(11111111)

allowedValues = {
    "lamVal":    [16,22,28,34],
    "infMode":   ["Con","Des"],
    "heliModel": ["LL","LR","RR"],
    "mass": [300,800,1300],
}

ciextra = None
ciname  = None

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
    ciextra = "_Lam%dTeV%s%s"%(args.lamVal,
                               args.infMode,
                               args.heliModel)
    ciname  = "_Lambda%dTeV_%s_%s"%(args.lamVal,
                                    args.infMode,
                                    args.heliModel)

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
plotTypes = [
    "raw",                     # 0
    "xs_scaled",               # 1
    "xs_by_eff_scaled",        # 2
    "raw_binned",              # 3
    "xs_scaled_binned",        # 4
    "xs_by_eff_scaled_binned", # 5
    # new binning+eff?
]

plotLabels = [
    "Generated events",                       # 0
    "Gen events scaled by xs",                # 1
    "Gen events scaled by xs*eff",            # 2
    "Generated events, in selected mass bin", # 3
    "Gen events scaled by xs, in selected mass bin",     # 4
    "Gen events scaled by xs*eff, in selected mass bin", # 5
    # new binning+eff?
]

hout   = []
stack  = []
outcan = []
legends = []
for i,plt in enumerate(plotTypes):
    outcan.append(r.TCanvas("outcan_%s"%(plt), "outcan_%s"%(plt), 800, 800))
    if (i < 3):
        legends.append(r.TLegend(0.15,0.75,0.45,0.9))
    else:
        legends.append(r.TLegend(0.75,0.75,0.9,0.9))
    legends[i].SetBorderSize(0)
    legends[i].SetLineWidth(0)
    legends[i].SetFillColor(0)
    legends[i].SetFillStyle(3000)
    pass

summary = r.TCanvas("summary", "summary", 1440,900)
summary.Divide(3,2)

gScaleHist = [] # for proper scaling because... ROOT

hMin = [1e-9 for x in range(len(plotTypes))]
hMax = [1e10 for x in range(len(plotTypes))]

# for i,mass in enumerate(allowedValues["mass"][::-1]):
for i,mass in enumerate(allowedValues["mass"]):
    sample = samples[args.sample]
    if "CI" in args.sample:
        sample = sample["M%d"%(mass)]["Lam%d"%(args.lamVal)][args.infMode][args.heliModel]
        fver   = "Corrected-v4"
        title  = "#Lambda == %d TeV, %s interference, #eta=%s"%(args.lamVal,args.infMode,args.heliModel)
    else:
        fver   = "Corrected-v3"
        sample = sample["M%d"%(mass)]
        title  = "DrellYan"
        pass

    infname = "%s_M%s_CUETP8M1%s_13TeV_Pythia8_%s_summary.root"%(args.sample, mass, ciextra if ciextra else "", fver)
    print(sample)
    lumi  = 1.0 # in /pb
    lfact = 1.0 # to get to human readable, i.e., -> 1/pb, 1/fb etc
    npass = sample["cutEfficiency"][0]
    nfail = sample["cutEfficiency"][1]
    ngen  = npass+nfail
    eff   = float(npass)/float(ngen)
    xs    = sample["xsec"][0] ## in pb
    lumif = xs*lumi*lfact/ngen
    sf    = lumif*eff
    print(ngen,npass,nfail,eff,xs,lumif,sf)

    hist = [] # stores the various histograms

    ## for adding to the TColor
    extra = i if (i%2==0) else -i

    scaleF = [1, lumif, sf, 1, lumif, sf]
    # with r.TFile(infname,"READ") as infile:
    with open("test.txt","w") as f:
        infile = r.TFile(infname,"READ")
        r.SetOwnership(infile,False)
        basehist = infile.Get("genfilter/%s"%(histname))
        r.SetOwnership(basehist,False)

        for plt in range(len(plotTypes)):
            hist.append(basehist.Clone("m%d_%s"%(mass,plotTypes[plt])))
            r.SetOwnership(hist[plt],False)
            hist[plt].SetLineWidth(2)
            hist[plt].SetLineColor(r.kOrange + extra)
            hist[plt].Scale(scaleF[plt])
            hist[plt].SetStats(0)
            origTitle = hist[plt].GetTitle()
            hist[plt].SetTitle(title)
            hist[plt].GetYaxis().SetTitle("%s / 5 GeV"%(plotLabels[plt]))
            hist[plt].GetYaxis().SetTitleOffset(1.5)
            hist[plt].GetYaxis().SetNdivisions(510);
            hist[plt].GetXaxis().SetTitle("%s [GeV]"%(origTitle))
            hist[plt].GetXaxis().SetTitleOffset(1.25)
            hist[plt].GetXaxis().SetNdivisions(410);

            if i == 0:
                gScaleHist.append(hist[plt])
                hMax[plt] = 1.25*hist[plt].GetMaximum()
                hMin[plt] = 0.8*hist[plt].GetMinimum(1e-8)
                gScaleHist[plt].SetMinimum(hMin[plt])
                gScaleHist[plt].SetMaximum(hMax[plt])
            elif i == (len(allowedValues["mass"])-1):
                hMin[plt] = 0.8*hist[plt].GetMinimum(1e-8)
                gScaleHist[plt].SetMinimum(hMin[plt])
                pass
            pass
        print(mass,hMin,hMax)
        minBin = basehist.FindBin(sample["minCut"])
        maxBin = basehist.FindBin(sample["maxCut"])
        if args.debug:
            print(minBin,basehist.GetBinLowEdge(minBin),basehist.GetBinCenter(minBin),basehist.GetBinWidth(minBin))
            print(maxBin,basehist.GetBinLowEdge(maxBin),basehist.GetBinCenter(maxBin),basehist.GetBinWidth(maxBin))
        for bi in range(basehist.GetNbinsX()):
            if bi < minBin or bi >= maxBin:
                for plt in [3,4,5]:
                    hist[plt].SetBinContent(bi+1,0)
                    hist[plt].SetBinError(bi+1,0)
                    pass
                pass
            pass

        if len(hout):
            for plt in range(len(plotTypes)):
                # outcan[plt].cd()
                summary.cd(plt+1)
                hout[plt].Add(hist[plt])
                stack[plt].Add(hist[plt])
                if args.debug:
                    print("drawing sames",hist[plt])
                hist[plt].Draw("sames")
                legends[plt].AddEntry(hist[plt],"M%d"%(mass),"lpef")
                r.gPad.Update()
                # outcan[plt].Update()
                summary.Update()
                pass
        else:
            for plt in range(len(plotTypes)):
                # outcan[plt].cd()
                summary.cd(plt+1)
                hout.append(hist[plt].Clone("%s"%(plotTypes[plt])))
                r.gStyle.SetPalette(r.kOcean)
                stack.append(r.THStack("%s_stack"%(plotTypes[plt]),"%s"%(hist[plt].GetTitle())))
                stack[plt].Add(hist[plt])
                r.SetOwnership(hist[plt],False)
                if args.debug:
                    print("drawing first",hist[plt])
                # hist[plt].Draw("")
                gScaleHist[plt].Draw("")
                # legends[plt].SetHeader(title)
                # legends[plt].AddTitle(title)
                legends[plt].AddEntry(gScaleHist[plt],"M%d"%(mass),"lpef")
                legends[plt].Draw("nb")
                r.gPad.SetLogy(r.kTRUE)
                r.gPad.Update()
                # outcan[plt].Update()
                summary.Update()
                pass
            # if args.debug:
            #     raw_input("Next histogram")
            pass
        # if args.debug:
        #     raw_input("Next histogram")
        pass
    pass

print(hMin)
print(hMax)
for plt in range(len(plotTypes)):
    # outcan[plt].cd()
    summary.cd(plt+1)
    hist[plt].GetYaxis().SetRangeUser(hMin[plt],hMax[plt])
    hist[plt].GetXaxis().SetRangeUser(275.,5000.)
    # hist[plt].SetMinimum(hMin[plt])
    # hist[plt].SetMaximum(hMax[plt])
    r.gPad.SetLogy(r.kTRUE)
    r.gPad.Update()
    # outcan[plt].Update()
    # outcan[plt].SaveAs("%s%s_%s.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
summary.Update()
summary.SaveAs("%s%s_summary.png"%(args.sample,ciname if ciname else ""))

for plt in range(len(plotTypes)):
    # outcan[plt].cd()
    summary.cd(plt+1)
    if (plt > 2):
        gScaleHist[plt].GetXaxis().SetRangeUser(275.,5000.)
        gScaleHist[plt].Draw("sames")
    r.gPad.SetLogx(r.kTRUE)
    r.gPad.Update()
    # outcan[plt].Update()
    # outcan[plt].SaveAs("%s%s_%s_logx.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
summary.Update()
summary.SaveAs("%s%s_summary_logx.png"%(args.sample,ciname if ciname else ""))

if args.debug:
    print(stack)
    raw_input("draw stack")

for plt in range(len(plotTypes)):
    # outcan[plt].cd()
    summary.cd(plt+1)
    stack[plt].Draw("pfc hist")
    legends[plt].Draw("nb")
    stack[plt].Draw("pfc hist")
    r.gPad.SetLogx(r.kFALSE)
    r.gPad.Update()
    # outcan[plt].Update()
    # outcan[plt].SaveAs("%s%s_%s_stack.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
summary.Update()
summary.SaveAs("%s%s_stack.png"%(args.sample,ciname if ciname else ""))

for plt in range(len(plotTypes)):
    # outcan[plt].cd()
    summary.cd(plt+1)
    if (plt > 2):
        stack[plt].GetXaxis().SetRangeUser(275.,5000.)
    stack[plt].Draw("pfc hist")
    r.gPad.SetLogx(r.kTRUE)
    r.gPad.Update()
    # outcan[plt].Update()
    # outcan[plt].SaveAs("%s%s_%s_stack_logx.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
summary.Update()
summary.SaveAs("%s%s_stack_logx.png"%(args.sample,ciname if ciname else ""))

if args.debug:
    print(hout)
    raw_input("draw stack")

for plt in range(len(plotTypes)):
    # outcan[plt].cd()
    summary.cd(plt+1)
    hout[plt].GetYaxis().SetRangeUser(hMin[plt],hMax[plt])
    hout[plt].GetXaxis().SetRangeUser(275.,5000.)
    hout[plt].SetMinimum(hMin[plt])
    hout[plt].SetMaximum(hMax[plt])
    hout[plt].SetLineWidth(2)
    hout[plt].SetLineColor(r.kRed)
    hout[plt].Draw("")
    r.gPad.SetLogx(r.kFALSE)
    r.gPad.Update()
    # outcan[plt].Update()
    # outcan[plt].SaveAs("%s%s_%s_combined.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
summary.Update()
summary.SaveAs("%s%s_combined.png"%(args.sample,ciname if ciname else ""))

for plt in range(len(plotTypes)):
    # outcan[plt].cd()
    summary.cd(plt+1)
    r.gPad.SetLogx(r.kTRUE)
    r.gPad.Update()
    # outcan[plt].Update()
    # outcan[plt].SaveAs("%s%s_%s_combined_logx.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
summary.Update()
summary.SaveAs("%s%s_combined_logx.png"%(args.sample,ciname if ciname else ""))

if args.debug:
    raw_input("exit")
