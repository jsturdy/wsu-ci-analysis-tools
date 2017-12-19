#!/bin/env python

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

# import argparse
## need options and flags here :)

r.gROOT.SetBatch(True)

#lvals=["1", "10", "16", "22", "28", "34", "100k"]
lvals=[1, 10, 16, 22, 28, 34, 100000]
bvals=[i for i in range(len(lvals))]
helis=["LL","LR","RR"]
intfs=["Con","Des"]
supers = [400,500,700,1100,1900,3500]

# xvals=np.zeros(len(lvals),'float64')
xvals=np.array(lvals,dtype='float64')
emutype = "mu"
with open("ciparametrization_2{0:s}.json".format(emutype),"r") as js:
    params = json.load(js)
    outf = r.TFile("cito2{0:s}_parametrization.root".format(emutype),"recreate")
    for heli in helis:
        conFitPar = []
        for intf in intfs:
            # print("%s%s"%(intf,heli))
            for i,point in enumerate(supers[:-1]):
                print("%s%s %d"%(intf,heli,point))
                fn = r.TF1("fn_m%d_%s%s"%(point,intf,heli),"[0]+[1]/(x**2)+[2]/(x**4)",0.1,10000000)
                yvals = np.array(params["%s%s_%dGeV"%(intf,heli,point)],dtype='float64')
                if intf == "Con":
                    conFitPar.append(0)
                print(xvals,yvals)
                gr = r.TGraph(len(lvals),xvals,yvals)
                gr.SetName("gr_%s%s_m%d"%(intf,heli,point))
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
                    fn.SetParameter(0,gr.Eval(100000))
                    fn.SetParLimits(0,0.975*gr.Eval(100000+randu),1.025*gr.Eval(100000+randu))
                    if intf == "Con":
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
                    
                    fitR = gr.Fit("fn_m%d_%s%s"%(point,intf,heli),"REMSQ","",0.5,110000)
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
            gr1100 = outf.Get("gr_{0:s}{1:s}_m1900".format(intf,heli))
            f1100  = outf.Get("fn_m1100_{0:s}{1:s}".format(intf,heli)).GetChisquare()
            gr1900 = outf.Get("gr_{0:s}{1:s}_m1100".format(intf,heli))
            f1900  = outf.Get("fn_m1900_{0:s}{1:s}".format(intf,heli)).GetChisquare()

            gr400.Draw("ap")
            r.gStyle.SetOptStat(0)
            r.gStyle.SetOptFit(0)
            gr400.GetYaxis().SetRangeUser(1,1e7)
            gr400.SetMinimum(1)
            gr400.SetMaximum(1e7)
            r.gPad.SetLogy(r.kTRUE)
            r.gPad.SetLogx(r.kTRUE)
            r.gPad.Update()

            gr500.SetMarkerColor(r.kRed)
            gr500.GetYaxis().SetRangeUser(1,1e7)
            gr500.SetMinimum(1)
            gr500.SetMaximum(1e7)
            
            gr700.SetMarkerColor(r.kBlue)
            gr700.GetYaxis().SetRangeUser(1,1e7)
            gr700.SetMinimum(1)
            gr700.SetMaximum(1e7)
            
            gr1100.SetMarkerColor(r.kYellow)
            gr1100.GetYaxis().SetRangeUser(1,1e7)
            gr1100.SetMinimum(1)
            gr1100.SetMaximum(1e7)
            
            gr1900.SetMarkerColor(r.kViolet)
            gr1900.GetYaxis().SetRangeUser(1,1e7)
            gr1900.SetMinimum(1)
            gr1900.SetMaximum(1e7)
            
            gr500.Draw("psame")
            gr700.Draw("psame")
            gr1100.Draw("psame")
            gr1900.Draw("psame")
            r.gPad.Update()
            
            leg = r.TLegend(0.5,0.7,0.9,0.9)
            leg.AddEntry(gr400, "400 < M [GeV] < 500, #chi^{2} = %2.2f"%f400,   "p")
            leg.AddEntry(gr500, "500 < M [GeV] < 700, #chi^{2} = %2.2f"%f500,   "p")
            leg.AddEntry(gr700, "700 < M [GeV] < 1100, #chi^{2} = %2.2f"%f700,  "p")
            leg.AddEntry(gr1100,"1100 < M [GeV] < 1900, #chi^{2} = %2.2f"%f1100, "p")
            leg.AddEntry(gr1900,"1900 < M [GeV] < 3500, #chi^{2} = %2.2f"%f1900, "p")
            leg.Draw("")
            can.Modified()
            can.Update()
            r.gPad.Update()

            # raw_input("continue")
            for ftype in ["png","C","pdf","eps"]:
                can.SaveAs("~/public/forCIAnalysis/params_2{3:s}_{0:s}_{1:s}.{2:s}".format(intf,heli,ftype,emutype))
                pass
            pass
        pass
    outf.Close()
    pass
