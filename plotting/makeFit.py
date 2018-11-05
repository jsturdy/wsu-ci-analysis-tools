#!/bin/env python

import sys, os
import argparse
parser = argparse.ArgumentParser()
#parser.add_argument("-inFile", help="Input file", type=str)
parser.add_argument("-flav", help="Lepton flavor", type=str)
parser.add_argument("-unc",  help="Uncertainty: 'nominal'*, 'scaleup', 'scaledown', 'muonid', 'smeared'", type=str, default="nominal")
parser.add_argument("-eta",  help="Eta bin: 'inc'*, 'bb', 'be', 'ee', 'be+', 'be-', 'e+e-', 'e-e-', 'e+e+'", type=str, default="inc")
parser.add_argument("-cs",   help="CS bin: 'inc'*, 'cs+', 'cs-'", type=str, default="inc")
parser.add_argument("-d",    help="debug", action='store_true')

args = parser.parse_args()

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

"/store/user/jschulte/ZprimeAnalysis/histos/histosZprimeEleEle"
"/store/user/jschulte/ZprimeAnalysis/histos/histosZprimeMuMu"
antypes=[
    # ["E","e","Ele","/store/user/sturdy/ZprimeAnalysis/histosHLTWeighted"],
    # ["Mu","mu","Mu","/store/user/sturdy/ZprimeAnalysis/histosCutHLT"]
    ["E","e","Ele", "/store/user/jschulte/ZprimeAnalysis/histos"],
    ["Mu","mu","Mu","/store/user/jschulte/ZprimeAnalysis/histos"]
    ]
form="output_CITo2{0:s}_M{1:d}_CUETP8M1_Lam{2:s}TeV{3:s}{4:s}_13TeV_Pythia8_Corrected-v4_ntuple.root"
dyform="output_DYTo2{0:s}_M{1:d}_CUETP8M1_13TeV_Pythia8_Corrected-v3_ntuple.root"

r.gROOT.SetBatch(True)

mvals=[300,800,1300]
lvals=["1", "10", "16", "22", "28", "34", "100k"]
helis=["LL","LR","RR"]
intfs=["Con","Des"]

supers = [400,500,700,1100,1900,3500,5000]

uncertainties = {
    "nominal":   "CSMassBinned",
    "scaleup":   "CSMassUpBinned",
    "scaledown": "CSMassDownBinned",
    "pileup":    "CSMassPUUpBinned",
    "piledown":  "CSMassPUDownBinned",
    ## muon only
    "smeared":   "CSSmearedMassBinned",
    "muonid":    "CSMassMuIDBinned",
    }
etabins = ["inc","bb","be","ee","be+","be-","e+e-","e-e-","e+e+"]
#             0    1    2    3
csbins = ["inc","cs+","cs-"]
#            0     1     2

etabin = args.eta
csbin  = args.cs
unc    = args.unc
histbin = (etabins.index(etabin)*3)+csbins.index(csbin)+1
debug = args.d

if csbin not in csbins:
    print("CS bin '{0}' not in:".format(csbin),csbins)
    exit(1)
if etabin not in etabins:
    print("Eta bin '{0}' not in:".format(etabin),etabins)
    exit(1)
if unc not in uncertainties:
    print("Plot type '{0}' not in:".format(unc),uncertainties)
    exit(1)

for antype in antypes:
    muonlyuncs = ["muonid", "smeared"]
    if unc in muonlyuncs and antype[2] == "Ele":
        print("Not processing uncertainty '{0:s}' for lepton flavour '{1:s}'".format(unc,antype[2]))
        continue
    base="root://cmseos.fnal.gov//{1:s}/histosZprime{0:s}{0:s}/".format(antype[2],antype[3])
    params = ndict()

    with open("ciparametrization_2{0:s}_{1:s}_{2:s}_{3:s}.json".format(antype[1],unc,etabin,csbin),"w") as js:
        with open("cicounts_2{0:s}_{1:s}_{2:s}_{3:s}.txt".format(antype[1],unc,etabin,csbin),"w") as out:
            for intf in intfs:
                for heli in helis:
                    files=[]
                    for point in supers[:-1]:
                        # params["{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)] = np.zeros(len(lvals),'float64')
                        params["{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)]     = [0. for j in range(len(lvals))]
                        params["{0:s}{1:s}_{2:d}GeV_err".format(intf,heli,point)] = [0. for j in range(len(lvals))]
                        pass
                    for point in [1000+x for x in range(0,1500,200)]:
                        params["{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)]     = [0. for j in range(len(lvals))]
                        params["{0:s}{1:s}_{2:d}GeV_err".format(intf,heli,point)] = [0. for j in range(len(lvals))]
                        pass
                    print("{0:s}{1:s}".format(intf,heli))
                    for i,lval in enumerate(lvals):
                        hist = None
                        can   = r.TCanvas("can","",800,800)
                        stack = r.THStack("stack","")
                        for mval in mvals:
                            if debug:
                                print("opening {1:s}{0:s}".format(base,form.format(antype[0],mval,lval,intf,heli)))
                                exit(1)
                            lf = r.TFile.Open("{0:s}{1:s}".format(base,form.format(antype[0],mval,lval,intf,heli)))
                            files.append(lf)  ## ROOT why are you so awful!!!!???
                            if not lf:
                                print(lf,hist)
                                continue
                            # htmp = lf.Get("ZprimeRecomass")
                            histname = "cito2{0:s}_m{1}_Lam{2}{3}{4}_{5:s}{6:s}{7:s}".format(antype,mval,lval,intf,heli,
                                                                                             csbin,unc,etabin)
                            print(lf)
                            htmp = lf.Get("{0:s}".format(uncertainties[unc])).ProjectionX(histname,histbin,histbin)
                            htmp.Scale(1.3) # apply k-factor on signal samples
                            htmp = htmp.Rebin(100,"{0:s}_{1:d}_rebinned".format(htmp.GetName(),mval))
                            if mval == 300:
                                hist = htmp.Clone("htmp_{0:s}{1:s}{2:s}{3:d}".format(lval,intf,heli,mval))
                                htmp.SetLineColor(r.kOrange)
                                htmp.SetFillColor(r.kOrange)
                                htmp.SetFillStyle(3001)
                                stack.Add(htmp)
                            else:
                                hist.Add(htmp.Clone("htmp_{0:s}{1:s}{2:s}{3:d}".format(lval,intf,heli,mval)))
                                if mval == 1300:
                                    htmp.SetLineColor(r.kGreen)
                                    htmp.SetFillColor(r.kGreen)
                                    htmp.SetFillStyle(3001)
                                    stack.Add(htmp)
                                else:
                                    htmp.SetLineColor(r.kBlue)
                                    htmp.SetFillColor(r.kBlue)
                                    htmp.SetFillStyle(3001)
                                    stack.Add(htmp)
                                    pass
                                if mval == 1300 and "{0:s}{1:s}".format(intf,heli) == "ConLL":
                                    lf = r.TFile.Open("{0:s}{1:s}".format(base,form.format(antype[0],2000,lval,intf,heli)))
                                    if not lf:
                                        print(lf,htmp,hist)
                                        continue
                                    # htmp = lf.Get("ZprimeRecomass")
                                    histname = "cito2{0:s}_m{1}_Lam{2}{3}{4}_{5:s}{6:s}{7:s}".format(antype,2000,lval,intf,heli,
                                                                                                     csbin,unc,etabin)
                                    print(lf)
                                    htmp = lf.Get("{0:s}".format(uncertainties[unc])).ProjectionX(histname,histbin,histbin)
                                    htmp.Scale(1.3) # apply k-factor on signal samples
                                    htmp = htmp.Rebin(100,"{0:s}_{1:d}_rebinned".format(htmp.GetName(),2000))
                                    hist.Add(htmp.Clone("htmp_{0:s}{1:s}{2:s}{3:d}".format(lval,intf,heli,2000)))
                                    htmp.SetLineColor(r.kRed)
                                    htmp.SetFillColor(r.kRed)
                                    htmp.SetFillStyle(3001)
                                    stack.Add(htmp)
                                    pass
                                pass
                            pass
                        # stack.Rebin(10)
                        # hist.Rebin(10)
                        stack.SetMinimum(0.8*hist.GetMinimum(0.001))
                        stack.SetMaximum(1.25*hist.GetMaximum())
                        stack.Draw("hist")
                        stack.GetXaxis().SetRangeUser(0,5000)
                        stack.GetXaxis().SetNdivisions(505)
                        r.gPad.SetLogy(True)
                        hist.Draw("same")
                        can.Update()
                        # raw_input()
                        for ftype in ["png","C","pdf","eps"]:
                            can.SaveAs("~/public/forCIAnalysis/cito2{1:s}_{2:s}{3:s}{4:s}_{5:s}_{6:s}_{7:s}.{0:s}".format(ftype,antype[1],
                                                                                                                          lval,intf,heli,
                                                                                                                          unc,etabin,csbin))
                        # raw_input("enter to continue")
                        for p,point in enumerate(supers[:-1]):
                            bval  = hist.FindBin(point)
                            upval = hist.FindBin(supers[p+1]-0.05)
                            val   = hist.Integral(bval,upval)
                            err   = r.Double(0)
                            val   = hist.Integral(bval,upval)
                            val2  = hist.IntegralAndError(bval,upval,err)
                            print("{0:s} {1:d} {2:d} {3:d} {4:2.4f} {5:2.4f}".format(lval,point,bval,upval,val,err))
                            out.write("{0:s} {1:d} {2:d} {3:d} {4:2.4f} {5:2.4f}\n".format(lval,point,bval,upval,val,err))
                            params["{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)][i] = val
                            params["{0:s}{1:s}_{2:d}GeV_err".format(intf,heli,point)][i] = err
                            pass

                        # Mass bin scan above 1 TeV
                        for point in [1000+x for x in range(0,1500,200)]:
                            bval  = hist.FindBin(point)
                            upval = hist.FindBin(100000000)
                            val   = hist.Integral(bval,upval)
                            err   = r.Double(0)
                            val   = hist.Integral(bval,upval)
                            val2  = hist.IntegralAndError(bval,upval,err)
                            print("{0:s} {1:d} {2:d} {3:d} {4:2.4f} {5:2.4f}".format(lval,point,bval,upval,val,err))
                            out.write("{0:s} {1:d} {2:d} {3:d} {4:2.4f} {5:2.4f}\n".format(lval,point,bval,upval,val,err))
                            params["{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)][i]     = val
                            params["{0:s}{1:s}_{2:d}GeV_err".format(intf,heli,point)][i] = err
                            pass
                        pass
                    pass
                pass
            print(params)
            pass
        json.dump(params,js)
        pass
    pass
