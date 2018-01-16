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

args = parser.parse_args()
constraints = args.constraint

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

r.gROOT.SetBatch(True)

#lvals=["1", "10", "16", "22", "28", "34", "100k"]
lvals=[1, 10, 16, 22, 28, 34, 100000]
bvals=[i for i in range(len(lvals))]
helis=["LL","LR","RR"]
intfs=["Con","Des"]
supers = [400,500,700,1100,1900,3500,5000]

uncertainties = {
    "nominal":   "CSMassBinned",
    "scaleup":   "CSMassUpBinned",
    "scaledown": "CSMassDownBinned",
    "smeared":   "CSSmearedMassBinned"
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

# if __name__ == "__main__":
for emutype in ["e","mu"]:
    # xvals=np.zeros(len(lvals),'float64')
    xvals=np.array(lvals,dtype='float64')
    # emutype = "mu"
    with open("ciparametrization_2{0:s}_{1:s}_{2:s}_{3:s}.json".format(emutype,unc,etabin,csbin),"r") as js:
        params = json.load(js)
        outf = r.TFile("cito2{0:s}_{1:s}_{2:s}_{3:s}_parametrization.root".format(emutype,unc,etabin,csbin),"recreate")
        for heli in helis:
            conFitPar = []
            for intf in intfs:
                # print("{0:s}{1:s}".format(intf,heli))
                for i,point in enumerate(supers[:-1]):
                    print("{0:s}{1:s} {2:d}".format(intf,heli,point))
                    fn = r.TF1("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"[0]+[1]/(x**2)+[2]/(x**4)",0.1,10000000)
                    yvals = np.array(params["{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)],dtype='float64')
                    if intf == "Con":
                        conFitPar.append(0)
                    print(xvals,yvals)
                    gr = r.TGraph(len(lvals),xvals,yvals)
                    gr.SetName("gr_{0:s}{1:s}_m{2:d}".format(intf,heli,point))
                    if i == 0:
                        gr.Draw("ap")
                    else:
                        gr.Draw("psame")
                    fitChi2 = 0
                    MinChi2Temp = 99999999
                    stepN = 0
    
                    random = r.TRandom3()
                    random.SetSeed(123456)
                    ## want to constrain the fit parameters between constructive and destructive functions
                    # fn.FixParameter(0,gr.Eval(100000))
    
                    while (stepN < 100):
                        randu = random.Uniform(0, 1)
                        randg = random.Gaus(10, 5)
    
                        if (randg < 0.0 or randg > 100):
                            continue
    
                        # set constant term to the value of the 100kTeV point?
                        # fn.SetParameter(0,8+stepN*8)
                        if args.fixinf:
                            fn.SetParameter(0,gr.Eval(100000))
                            fn.SetParLimits(0,0.975*gr.Eval(100000+randu),1.025*gr.Eval(100000+randu))
                            pass

                        if intf == "Con" or not args.fixdes:
                            fn.SetParameter(1,randg)
                        else:
                            conval = -conFitPar[i]
                            fn.SetParameter(1,conval)
                            # fn.FixParameter(1,-conFitPar[i])
                            fn.SetParameter(1,conval)
                            uplim = conval + ((randu/10.)*abs(conval))
                            lolim = conval - ((randu/10.)*abs(conval))
                            print(lolim,conval,uplim)
                            fn.SetParLimits(1,lolim,uplim)
                            pass
    
                        fn.SetParameter(2,8+stepN*8)
                        fn.SetParLimits(2,1e-5,1e10)
                        
                        fitR = gr.Fit("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"REMSQ","",0.5+randu,110000)
                        fitEmpty = fitR.IsEmpty()
                        if fitEmpty:
                            # Don't try to fit empty data again
                            break
                        fitValid = fitR.IsValid()
                        if not fitValid:
                            continue
                        fitChi2 = fn.GetChisquare()
                        fitNDF  = fn.GetNDF()
                        stepN += 1
                        if (fitChi2 < MinChi2Temp and fitChi2 > 0.0):
                            MinChi2Temp = fitChi2
                            pass
                        if (MinChi2Temp < 50):
                            break
                        pass
                    print(stepN)
                    if intf == "Con":
                        conFitPar[i] = fn.GetParameter(1)
                    print(fitR.Print())
                    r.gPad.SetLogy(True)
                    r.gPad.SetLogx(True)
                    fn.Draw("same")
                    fitR.SetName("fitR_m400_{0:s}{1:s}".format(intf,heli))
                    fitR.Write()
                    fn.Write()
                    gr.Write()
                    outf.Write()
                    # raw_input("continue")
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
    
                gr400  = outf.Get("gr_{0:s}{1:s}_m400".format(intf,heli))
                f400   = outf.Get("fn_m400_{0:s}{1:s}".format(intf,heli)).GetChisquare()
                gr500  = outf.Get("gr_{0:s}{1:s}_m500".format(intf,heli))
                f500   = outf.Get("fn_m500_{0:s}{1:s}".format(intf,heli)).GetChisquare()
                gr700  = outf.Get("gr_{0:s}{1:s}_m700".format(intf,heli))
                f700   = outf.Get("fn_m700_{0:s}{1:s}".format(intf,heli)).GetChisquare()
                gr1100 = outf.Get("gr_{0:s}{1:s}_m1100".format(intf,heli))
                f1100  = outf.Get("fn_m1100_{0:s}{1:s}".format(intf,heli)).GetChisquare()
                gr1900 = outf.Get("gr_{0:s}{1:s}_m1900".format(intf,heli))
                f1900  = outf.Get("fn_m1900_{0:s}{1:s}".format(intf,heli)).GetChisquare()
                gr3500 = outf.Get("gr_{0:s}{1:s}_m3500".format(intf,heli))
                f3500  = outf.Get("fn_m3500_{0:s}{1:s}".format(intf,heli)).GetChisquare()
    
                gr400.Draw("ap")
                r.gStyle.SetOptStat(0)
                r.gStyle.SetOptFit(0)
                gr400.GetYaxis().SetRangeUser(1,1e7)
                gr400.SetMinimum(0.01)
                gr400.SetMaximum(1e7)
                r.gPad.SetLogy(r.kTRUE)
                r.gPad.SetLogx(r.kTRUE)
                r.gPad.Update()
    
                gr500.SetMarkerColor(r.kRed)
                gr500.GetYaxis().SetRangeUser(1,1e7)
                gr500.SetMinimum(0.01)
                gr500.SetMaximum(1e7)
                
                gr700.SetMarkerColor(r.kBlue)
                gr700.GetYaxis().SetRangeUser(1,1e7)
                gr700.SetMinimum(0.01)
                gr700.SetMaximum(1e7)
                
                gr1100.SetMarkerColor(r.kYellow)
                gr1100.GetYaxis().SetRangeUser(1,1e7)
                gr1100.SetMinimum(0.01)
                gr1100.SetMaximum(1e7)
                
                gr1900.SetMarkerColor(r.kViolet)
                gr1900.GetYaxis().SetRangeUser(1,1e7)
                gr1900.SetMinimum(0.01)
                gr1900.SetMaximum(1e7)
                
                gr3500.SetMarkerColor(r.kGreen)
                gr3500.GetYaxis().SetRangeUser(1,1e7)
                gr3500.SetMinimum(0.01)
                gr3500.SetMaximum(1e7)
                
                gr500.Draw("psame")
                gr700.Draw("psame")
                gr1100.Draw("psame")
                gr1900.Draw("psame")
                gr3500.Draw("psame")
                r.gPad.Update()
                
                leg = r.TLegend(0.5,0.7,0.9,0.9)
                leg.AddEntry(gr400, "400 < M [GeV] < 500, #chi^{2} = %2.2f"%(f400),    "p")
                leg.AddEntry(gr500, "500 < M [GeV] < 700, #chi^{2} = %2.2f"%(f500),    "p")
                leg.AddEntry(gr700, "700 < M [GeV] < 1100, #chi^{2} = %2.2f"%(f700),   "p")
                leg.AddEntry(gr1100,"1100 < M [GeV] < 1900, #chi^{2} = %2.2f"%(f1100), "p")
                leg.AddEntry(gr1900,"1900 < M [GeV] < 3500, #chi^{2} = %2.2f"%(f1900), "p")
                leg.AddEntry(gr3500,"3500 < M [GeV] < 5000, #chi^{2} = %2.2f"%(f3500), "p")
                leg.Draw("")
                can.Modified()
                can.Update()
                r.gPad.Update()
    
                # raw_input("continue")
                for ftype in ["png","C","pdf","eps"]:
                    can.SaveAs("~/public/forCIAnalysis/params_2{3:s}_{1:s}_{2:s}_{4:s}_{5:s}_{6:s}.{0:s}".format(ftype,
                                                                                                                 intf,heli,emutype,
                                                                                                                 unc,etabin,csbin))
                    pass
                pass
            pass
        outf.Close()
        pass
