#!/bin/env python

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

antypes=[["E","e","Ele"],["Mu","mu","Mu"]]
form="output_CITo2%s_M%d_CUETP8M1_Lam%sTeV%s%s_13TeV_Pythia8_Corrected-v4_ntuple.root"
dyform="output_DYTo2%s_M%d_CUETP8M1_13TeV_Pythia8_Corrected-v3_ntuple.root"

r.gROOT.SetBatch(True)

mvals=[300,800,1300]
lvals=["1", "10", "16", "22", "28", "34", "100k"]
helis=["LL","LR","RR"]
intfs=["Con","Des"]

supers = [400,500,700,1100,1900,3500]

for antype in antypes:
    base="root://cmseos.fnal.gov///store/user/sturdy/ZprimeAnalysis/histosDec15/histosZprime{0:s}{0:s}/".format(antype[2])
    params = ndict()

    with open("ciparametrization_2%s.json"%(antype[1]),"w") as js:
        with open("cicounts_2%s.txt"%(antype[1]),"w") as out:
            for intf in intfs:
                for heli in helis:
                    files=[]
                    for point in supers[:-1]:
                        # params["%s%s_%dGeV"%(intf,heli,point)] = np.zeros(len(lvals),'float64')
                        params["%s%s_%dGeV"%(intf,heli,point)] = [0 for j in range(len(lvals))]
                    print("{0:s}{1:s}".format(intf,heli))
                    for i,lval in enumerate(lvals):
                        hist = None
                        can   = r.TCanvas("can","",800,800)
                        stack = r.THStack("stack","")
                        for mval in mvals:
                            lf = r.TFile.Open("%s%s"%(base,form%(antype[0],mval,lval,intf,heli)))
                            files.append(lf)  ## ROOT why are you so awful!!!!???
                            if not lf:
                                print(lf,hist)
                                continue
                            htmp = lf.Get("ZprimeRecomass")
                            htmp.Scale(1.3) # apply k-factor on signal samples
                            htmp = htmp.Rebin(100,"%s_%d_rebinned"%(htmp.GetName(),mval))
                            if mval == 300:
                                hist = htmp.Clone("htmp_%s%s%s%d"%(lval,intf,heli,mval))
                                htmp.SetLineColor(r.kOrange)
                                htmp.SetFillColor(r.kOrange)
                                htmp.SetFillStyle(3001)
                                stack.Add(htmp)
                            else:
                                hist.Add(htmp.Clone("htmp_%s%s%s%d"%(lval,intf,heli,mval)))
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
                                if mval == 1300 and "%s%s"%(intf,heli) == "ConLL":
                                    lf = r.TFile.Open("%s%s"%(base,form%(antype[0],2000,lval,intf,heli)))
                                    if not lf:
                                        print(lf,htmp,hist)
                                        continue
                                    htmp = lf.Get("ZprimeRecomass")
                                    htmp.Scale(1.3) # apply k-factor on signal samples
                                    htmp = htmp.Rebin(100,"%s_%d_rebinned"%(htmp.GetName(),2000))
                                    hist.Add(htmp.Clone("htmp_%s%s%s%d"%(lval,intf,heli,2000)))
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
                            can.SaveAs("~/public/forCIAnalysis/cito2{1:s}_{2:s}{3:s}{4:s}.{0:s}".format(ftype,antype[1],lval,intf,heli))
                        # raw_input("enter to continue")
                        for p,point in enumerate(supers[:-1]):
                            bval  = hist.FindBin(point)
                            upval = hist.FindBin(supers[p+1]-0.05)
                            val  = hist.Integral(bval,upval)
                            print("{0:s} {1:d} {2:d} {3:d} {4:2.4f}".format(lval,point,bval,upval,val))
                            out.write("{0:s} {1:d} {2:d} {3:d} {4:2.4f}\n".format(lval,point,bval,upval,val))
                            params["%s%s_%dGeV"%(intf,heli,point)][i] = val
                            pass
                        pass
                    pass
                pass
            print(params)
            pass
        json.dump(params,js)
        pass
    pass
