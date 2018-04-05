#!/bin/env python

import sys, os
import argparse
parser = argparse.ArgumentParser()
#parser.add_argument("-inFile", help="Input file", type=str)
parser.add_argument("-flav", help="Lepton flavor", type=str)
parser.add_argument("-unc",  help="Uncertainty", type=str, default="nominal")
parser.add_argument("-eta",  help="Eta bin", type=str, default="inc")
parser.add_argument("-cs",   help="CS bin", type=str, default="inc")
parser.add_argument("-d",    help="debug", action='store_true')
## need options and flags here :)
parser.add_argument('--constraint', help="constraint for paramter (par up down)", nargs=3, action='append')
parser.add_argument("--fixdes",     help="fix destructive fit parameters based on constructive", action='store_true')
parser.add_argument("--fixinf",     help="fix infinity fit parameter", action='store_true')
# fix 2nd parameter for destructive fits
#   with and without constraint
# fix constant term parameter with constraint
# emutype

args        = parser.parse_args()
debug       = args.d
constraints = args.constraint
from fitUtils import doFitOnGraph

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

r.gROOT.SetBatch(True)
r.gErrorIgnoreLevel = r.kWarning

#lvals = ["1", "10", "16", "22", "28", "34", "100k"]
lvals = [1, 10, 16, 22, 28, 34, 100000]
lerrs = [1., 1., 1., 1., 1., 1., 1.]
bvals = [i for i in range(len(lvals))]
helis = ["LL","LR","RR"]
intfs = ["Con","Des"]
supers      = [400,500,700,1100,1900,3500,5000]
grbins      = [400,500,700,1100,1900,3500]
grcols      = [r.kBlack,r.kRed,r.kBlue,r.kYellow,r.kViolet,r.kGreen]
extragrbins = [1000+x for x in range(0,1500,200)]

uncertainties = {
    "nominal":   "CSMassBinned",
    "scaleup":   "CSMassUpBinned",
    "scaledown": "CSMassDownBinned",
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

desp1type = "float"
if args.fixdes or args.fixinf:
    desp1type = "fixed"
    pass    

if csbin not in csbins:
    print("CS bin '{0}' not in:".format(csbin),csbins)
    exit(1)
if etabin not in etabins:
    print("Eta bin '{0}' not in:".format(etabin),etabins)
    exit(1)
if unc not in uncertainties:
    print("Plot type '{0}' not in:".format(unc),uncertainties)
    exit(1)

# if __name__ == "__main__":
for emutype in ["e","mu"]:
    muonlyuncs = ["muonid", "smeared"]
    if unc in muonlyuncs and emutype == "e":
        print("Not processing uncertainty '{0:s}' for leptonn flavour '{1:s}'".format(unc,emutype))
        continue
    # xvals=np.zeros(len(lvals),'float64')
    xvals=np.array(lvals,dtype='float64')
    xerrs=np.array(lerrs,dtype='float64')
    # emutype = "mu"
    with open("ciparametrization_2{0:s}_{1:s}_{2:s}_{3:s}.json".format(emutype,unc,etabin,csbin),"r") as js:
        print("cito2{0:s}_{1:s}_{2:s}_{3:s}_parametrization_des_{4:s}.root".format(emutype,unc,etabin,csbin,desp1type))
        params = json.load(js)
        outf = r.TFile("cito2{0:s}_{1:s}_{2:s}_{3:s}_parametrization_des_{4:s}.root".format(emutype,unc,etabin,csbin,desp1type),
                       "recreate")
        for heli in helis:
            conFitPar = []
            for intf in intfs:
                # print("{0:s}{1:s}".format(intf,heli))
                print("Fitting primary bins for the limits")
                for i,point in enumerate(supers[:-1]):
                    doFitOnGraph(params, lvals, xvals, xerrs,
                                 intf, heli, i, point, outf, conFitPar,
                                 args.fixinf, args.fixdes)
                    pass
                print("Fitting extra bins for the mass scan")
                for i,point in enumerate(extragrbins):
                    doFitOnGraph(params, lvals, xvals, xerrs,
                                 intf, heli, 1, point, outf, conFitPar,
                                 args.fixinf, args.fixdes)
                    pass
                # raw_input("continue")
                pass
            pass
        outf.Write()
    
        for heli in helis:
            conFitPar = []
            for intf in intfs:
                can = r.TCanvas("can","",800,800)
                r.gStyle.SetOptStat(0)
                r.gStyle.SetOptFit(0)
                grMass = ndict()
                fMass  = ndict()
                leg = r.TLegend(0.5,0.7,0.95,0.9)
                for grbin in grbins:
                    grMass[grbin] = outf.Get("gr_{0:s}{1:s}_m{2:d}".format(intf,heli,grbin))
                    fMass[grbin]  = outf.Get("fn_m{2:d}_{0:s}{1:s}".format(intf,heli,grbin)).GetChisquare()
    
                    if grbin == 400:
                        grMass[grbin].Draw("ap")
                        r.gStyle.SetOptStat(0)
                        r.gStyle.SetOptFit(0)
                        r.gPad.SetLogy(r.kTRUE)
                        r.gPad.SetLogx(r.kTRUE)
                    else:
                        grMass[grbin].Draw("psame")
                        pass
                    grMass[grbin].GetYaxis().SetRangeUser(1,1e7)
                    grMass[grbin].SetMinimum(0.001)
                    grMass[grbin].SetMaximum(1e7)
                    grMass[grbin].SetMarkerColor(grcols[grbins.index(grbin)])
                    if debug:
                        print("Finding {0:d} in supers".format(grbin),supers)
                        pass
                    suIdx = supers.index(grbin)
                    leg.AddEntry(grMass[grbin], "{0:d} < M_{{ll}} [GeV] < {1:d}, #chi^{{2}} = {2:2.2f}".format(supers[suIdx],
                                                                                                               supers[suIdx+1],
                                                                                                               fMass[grbin]), "p")
                    r.gPad.Update()
                    pass
                leg.Draw("")
                can.Modified()
                can.Update()
                r.gPad.Update()

                for ftype in ["png","C","pdf","eps"]:
                    can.SaveAs("~/public/forCIAnalysis/params_2{3:s}_{1:s}_{2:s}_{4:s}_{5:s}_{6:s}_des_{7:s}.{0:s}".format(ftype,
                                                                                                                           intf,heli,emutype,
                                                                                                                           unc,etabin,csbin,
                                                                                                                           desp1type))
                    pass
                can.Clear()
                can.Update()

                leg = r.TLegend(0.5,0.7,0.95,0.9)
                for extrabin in extragrbins:
                    grMass[extrabin] = outf.Get("gr_{0:s}{1:s}_m{2:d}".format(intf,heli,extrabin))
                    fMass[extrabin]  = outf.Get("fn_m{2:d}_{0:s}{1:s}".format(intf,heli,extrabin)).GetChisquare()
    
                    if extragrbins.index(extrabin) == 0:
                        grMass[extrabin].Draw("ap")
                        r.gStyle.SetOptStat(0)
                        r.gStyle.SetOptFit(0)
                        r.gPad.SetLogy(r.kTRUE)
                        r.gPad.SetLogx(r.kTRUE)
                    else:
                        grMass[extrabin].Draw("psame")
                        pass
                    grMass[extrabin].GetYaxis().SetRangeUser(1,1e7)
                    grMass[extrabin].SetMinimum(0.001)
                    grMass[extrabin].SetMaximum(1e7)
                    grMass[extrabin].SetMarkerColor(r.kOrange+extragrbins.index(extrabin))
                    leg.AddEntry(grMass[extrabin], "{0:d} < M_{{ll}} [GeV], #chi^{{2}} = {1:2.2f}".format(extrabin,
                                                                                                          fMass[extrabin]), "p")
                    r.gPad.Update()
                    pass
                leg.Draw("")
                can.Modified()
                can.Update()
                r.gPad.Update()
    
                # raw_input("continue")
                for ftype in ["png","C","pdf","eps"]:
                    can.SaveAs("~/public/forCIAnalysis/scanmass_2{3:s}_{1:s}_{2:s}_{4:s}_{5:s}_{6:s}_des_{7:s}.{0:s}".format(ftype,
                                                                                                                             intf,heli,emutype,
                                                                                                                             unc,etabin,csbin,
                                                                                                                             desp1type))
                    pass
                pass
            pass
        outf.Close()
        pass
