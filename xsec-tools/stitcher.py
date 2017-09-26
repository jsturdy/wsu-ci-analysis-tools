#!/bin/env python

import sys,os,re
import argparse
import math

parser = argparse.ArgumentParser()
parser.add_argument("sample",        help="Sample to stitch together",type=str)
parser.add_argument("--lumi",        help="Luminosity value to scael to",type=float,default=1.0)
parser.add_argument("--lamVal",      help="Lambda value to use",      type=str)
parser.add_argument("--infMode",     help="Interference mode to use", type=str)
parser.add_argument("--heliModel",   help="Heliciy model to use",     type=str)
parser.add_argument("--rebin",       help="Rebin input histograms",   type=int)
parser.add_argument("--tails",       help="Show tails in last bin",    action="store_true")
parser.add_argument("--preFSR",      help="Use pre-FSR gen particles", action="store_true")
parser.add_argument("-d", "--debug", help="debugging information",     action="store_true")

args = parser.parse_args()

import cPickle as pickle
from nesteddict import nesteddict as ndict
import ROOT as r
# from wsuPyROOTUtils import *

if not args.debug:
    r.gROOT.SetBatch(r.kTRUE)
    r.gStyle.SetOptStat(11111111)
    r.gErrorIgnoreLevel = r.kError

allowedValues = {
    "lamVal":    ["1", "10", "16", "22", "28", "34", "100k"],
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
    ciextra = "_Lam%sTeV%s%s"%(args.lamVal,
                               args.infMode,
                               args.heliModel)
    ciname  = "_Lambda%sTeV_%s_%s"%(args.lamVal,
                                    args.infMode,
                                    args.heliModel)

    pass

samples = None
with open("ci_xsec_data.pkl","rb") as pkl:
    samples = pickle.load(pkl)
    pass

prefsrExtra = "Pre" if args.preFSR else ""
if "2E" in args.sample:
    histname = "diElectronMass%s"%(prefsrExtra)
else:
    histname = "diMuonMass%s"%(prefsrExtra)
prefsrExtra = "_preFSR" if args.preFSR else ""

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
    if args.debug:
        print("sample",sample["M%d"%(mass)])
    if "CI" in args.sample:
        if args.debug:
            print("M%d"%(mass),"Lam%s"%(args.lamVal),args.infMode,args.heliModel)
            print("lambda:key",sample["Lam%s"%(args.lamVal)])
            print("interference:key",sample["Lam%s"%(args.lamVal)][args.infMode])
            print("helicity:key",sample["Lam%s"%(args.lamVal)][args.infMode][args.heliModel])
            print("mass:key",sample["Lam%s"%(args.lamVal)][args.infMode][args.heliModel]["M%d"%(mass)])
        sample = sample["Lam%s"%(args.lamVal)][args.infMode][args.heliModel]["M%d"%(mass)]
        fver   = "Corrected-v4"
        title  = "#Lambda == %s TeV, %s interference, #eta=%s"%(args.lamVal,args.infMode,args.heliModel)
    else:
        fver   = "Corrected-v3"
        sample = sample["M%d"%(mass)]
        title  = "DrellYan"
        pass

    if not sample:
        print("Sample %s%s%s has no keys in mapping"%(args.sample, mass, ciextra if ciextra else ""))
        continue
    infname = "%s_M%s_CUETP8M1%s_13TeV_Pythia8_%s_summary.root"%(args.sample, mass, ciextra if ciextra else "", fver)
    if args.debug:
        print(sample)
    lumi  = args.lumi # in /fb
    lfact = 1000. # to get to human readable, i.e., -> 1/pb, 1/fb etc
    npass = sample["cutEfficiency"][0]
    nfail = sample["cutEfficiency"][1]
    ngen  = npass+nfail
    eff   = float(npass)/float(ngen)
    xs    = sample["xsec"][0] ## in pb
    lumif = xs*lumi*lfact/float(ngen)
    sf    = lumif*eff
    print(ngen,npass,nfail,eff,xs,lumif,sf)

    hist = [] # stores the various histograms

    ## for adding to the TColor
    extra = i if (i%2==0) else -i

    scaleF = [1, lumif, sf, 1, lumif, sf]
    # with r.TFile(infname,"READ") as infile:
    with open("test.txt","w") as f:
        infile = r.TFile(infname,"READ")
        if not infile or infile.IsZombie() or not infile.IsOpen():
            print("Error opening file: %s"%(infname))
            continue

        r.SetOwnership(infile,False)
        basehist = infile.Get("genfilter/%s"%(histname))
        if args.rebin:
            basehist = basehist.Rebin(args.rebin)
        r.SetOwnership(basehist,False)

        for plt in range(len(plotTypes)):
            hist.append(basehist.Clone("m%d_%s"%(mass,plotTypes[plt])))
            r.SetOwnership(hist[plt],False)

            ## Get the tail right
            if args.tails:
                lastBin     = hist[plt].GetNbinsX()
                lastBinVal  = hist[plt].GetBinContent(lastBin)
                lastBinVal  = lastBin + hist[plt].GetBinContent(lastBin+1)
                lastBinErr2 = hist[plt].GetBinError(lastBin)**2
                lastBinErr2 = lastBinErr2 + hist[plt].GetBinError(lastBin)**2
                hist[plt].SetBinContent(lastBin,lastBinVal)
                hist[plt].SetBinError(  lastBin,math.sqrt(lastBinErr2))

            ## Set up the display
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

            # not robust against missing the first sample
            if i == 0:
                gScaleHist.append(hist[plt])
                hMax[plt] = 1.25*hist[plt].GetMaximum()
                hMin[plt] = 0.8*hist[plt].GetMinimum(1e-8)
            elif i == (len(allowedValues["mass"])-1):
                hMin[plt] = 0.8*hist[plt].GetMinimum(1e-8)
                pass
            pass

        ## Ensure no double counting in inclusive mass-binned samples
        print(mass,hMin,hMax)
        minBin = basehist.FindBin(sample["minCut"])
        maxBin = basehist.FindBin(sample["maxCut"])
        if args.debug:
            print(minBin,basehist.GetBinLowEdge(minBin),basehist.GetBinCenter(minBin),basehist.GetBinWidth(minBin))
            print(maxBin,basehist.GetBinLowEdge(maxBin),basehist.GetBinCenter(maxBin),basehist.GetBinWidth(maxBin))
        for bi in range(basehist.GetNbinsX()+1):
            if bi < minBin or bi >= maxBin:
                for plt in [3,4,5]:
                    # print("Zeroing bin %d"%(bi))
                    hist[plt].SetBinContent(bi,0)
                    hist[plt].SetBinError(bi,0)
                    pass
                pass
            pass
        # Zero out the over/underflow bins for certain samples
        for plt in [3,4,5]:
            if mass in [800,1300,2000]:
                hist[plt].SetBinContent(0,0)
                hist[plt].SetBinError(  0,0)
            if mass in [300,800,1300]:
                hist[plt].SetBinContent(hist[plt].GetNbinsX()+1,0)
                hist[plt].SetBinError(  hist[plt].GetNbinsX()+1,0)
            pass
        # Verification
        if args.debug:
            bi = 0
            print("%s: Bin[%d](%d,%.1f,%.1f) content %d"%(hist[3].GetName(),bi,
                                                          hist[3].GetBinLowEdge(bi),
                                                          hist[3].GetBinCenter(bi),
                                                          hist[3].GetBinWidth(bi),
                                                          hist[3].GetBinContent(bi)))
            for bi in range(basehist.GetNbinsX()):
                if (hist[3].GetBinContent(bi) > 0):
                    print("%s: Bin[%d](%d,%.1f,%.1f) content %d"%(hist[3].GetName(),bi,
                                                                  hist[3].GetBinLowEdge(bi),
                                                                  hist[3].GetBinCenter(bi),
                                                                  hist[3].GetBinWidth(bi),
                                                                  hist[3].GetBinContent(bi)))
                    pass
                pass
            for up in range(10):
                bi = hist[3].GetNbinsX()+up
                print("%s: Bin[%d](%d,%.1f,%.1f) content %d"%(hist[3].GetName(),bi,
                                                              hist[3].GetBinLowEdge(bi),
                                                              hist[3].GetBinCenter(bi),
                                                              hist[3].GetBinWidth(bi),
                                                              hist[3].GetBinContent(bi)))
                pass
            pass

        ## Make the plots
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

if gScaleHist:
    print(hMin)
    print(hMax)
    for plt in range(len(plotTypes)):
        # outcan[plt].cd()
        summary.cd(plt+1)
        gScaleHist[plt].GetYaxis().SetRangeUser(hMin[plt],hMax[plt])
        gScaleHist[plt].GetXaxis().SetRangeUser(275.,5000.)
        gScaleHist[plt].SetMinimum(hMin[plt])
        gScaleHist[plt].SetMaximum(hMax[plt])
        gScaleHist[plt].Draw("sames")
        r.gPad.SetLogy(r.kTRUE)
        r.gPad.Update()
        # outcan[plt].Update()
        # outcan[plt].SaveAs("%s%s_%s.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
    summary.Update()
    summary.SaveAs("%s%s%s%s_summary.png"%(args.sample,ciname if ciname else "", prefsrExtra, "_rebin%d"%(args.rebin) if args.rebin else ""))

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
    summary.SaveAs("%s%s%s%s_summary_logx.png"%(args.sample,ciname if ciname else "", prefsrExtra, "_rebin%d"%(args.rebin) if args.rebin else ""))

    if args.debug:
        print(stack)
        raw_input("draw stack")

    for plt in range(len(plotTypes)):
        # outcan[plt].cd()
        summary.cd(plt+1)
        r.gPad.SetLogx(r.kFALSE)
        stack[plt].Draw("pfc hist")
        r.gPad.Update()
        title = hist[plt].GetTitle()
        print(stack[plt],stack[plt].GetXaxis(),stack[plt].GetYaxis())
        stack[plt].SetTitle(title)
        stack[plt].GetYaxis().SetTitle("%s / 5 GeV"%(plotLabels[plt]))
        stack[plt].GetYaxis().SetTitleOffset(1.5)
        stack[plt].GetYaxis().SetNdivisions(510);
        stack[plt].GetXaxis().SetTitle("%s [GeV]"%(origTitle))
        stack[plt].GetXaxis().SetTitleOffset(1.25)
        stack[plt].GetXaxis().SetNdivisions(410);
        if args.debug:
            print(stack[plt],stack[plt].GetMinimum(),stack[plt].GetMaximum())
        stack[plt].SetMinimum(hMin[plt])
        # stack[plt].SetMinimum(0.8*stack[plt].GetMinimum(1e-7))
        stack[plt].SetMaximum(1.2*stack[plt].GetMaximum())
        stack[plt].Draw("pfc hist")
        r.gPad.Update()
        legends[plt].Draw("nb")
        r.gPad.Update()
        # outcan[plt].Update()
        # outcan[plt].SaveAs("%s%s_%s_stack.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
    summary.Update()
    summary.SaveAs("%s%s%s%s_stack.png"%(args.sample,ciname if ciname else "", prefsrExtra, "_rebin%d"%(args.rebin) if args.rebin else ""))

    for plt in range(len(plotTypes)):
        # outcan[plt].cd()
        summary.cd(plt+1)
        stack[plt].Draw("pfc hist")
        if (plt > 2):
            stack[plt].GetXaxis().SetRangeUser(275.,5000.)
        stack[plt].Draw("pfc hist")
        r.gPad.SetLogx(r.kTRUE)
        r.gPad.Update()
        legends[plt].Draw("nb")
        r.gPad.Update()
        # outcan[plt].Update()
        # outcan[plt].SaveAs("%s%s_%s_stack_logx.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
    summary.Update()
    summary.SaveAs("%s%s%s%s_stack_logx.png"%(args.sample,ciname if ciname else "", prefsrExtra, "_rebin%d"%(args.rebin) if args.rebin else ""))

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
    summary.SaveAs("%s%s%s%s_combined.png"%(args.sample,ciname if ciname else "", prefsrExtra, "_rebin%d"%(args.rebin) if args.rebin else ""))

    for plt in range(len(plotTypes)):
        # outcan[plt].cd()
        summary.cd(plt+1)
        r.gPad.SetLogx(r.kTRUE)
        r.gPad.Update()
        # outcan[plt].Update()
        # outcan[plt].SaveAs("%s%s_%s_combined_logx.png"%(args.sample,ciname if ciname else "",plotTypes[plt]))
    summary.Update()
    summary.SaveAs("%s%s%s%s_combined_logx.png"%(args.sample,ciname if ciname else "", prefsrExtra, "_rebin%d"%(args.rebin) if args.rebin else ""))

if args.debug:
    raw_input("finish")
