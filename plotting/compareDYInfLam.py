#!/bin/env python

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

antypes=[["E","e","Ele"],
         ["Mu","mu","Mu"]]
form="output_CITo2%s_M%d_CUETP8M1_Lam%sTeV%s%s_13TeV_Pythia8_Corrected-v4_ntuple.root"
dyform="output_DYTo2%s_M%d_CUETP8M1_13TeV_Pythia8_Corrected-v3_ntuple.root"
samples=["DY","CI"]

r.gROOT.SetBatch(True)

lvals = ["16","34"]
params = ndict()

mvals=[300,800,1300]
helis=["LL","LR","RR"]
intfs=["Con","Des"]
intf = "Con"
heli = "LL"

supers = [400,500,700,1100,1900,3500]
bins = [0,100,200,300,400,500,700,900,1100,1500,2000,2500,3000,5000]
rbins = np.array(bins, np.dtype('float64'))
srcs = ["Jan17"]
for src in srcs:
    for antype in antypes:
        base="root://cmseos.fnal.gov///store/user/sturdy/ZprimeAnalysis/histos{0:s}/histosZprime{1:s}{1:s}/".format(src,antype[2])
        for lval in lvals:
            files=[]
            hist = ndict()
            
            for sample in samples:
                hist[sample] = None
                can   = r.TCanvas("can","",800,800)
                stack = r.THStack("stack","")
                for mval in mvals:
                    if sample == "CI":
                        lf = r.TFile.Open("%s%s"%(base,form%(antype[0],mval,"100k",intf,heli)))
                    else:
                        # lf = r.TFile.Open("%s%s"%(base,dyform%(antype[0],mval)))
                        lf = r.TFile.Open("%s%s"%(base,form%(antype[0],mval,lval,intf,heli)))
                        pass
                    files.append(lf)  ## ROOT why are you so awful!!!!???
                    if not lf or lf == None:
                        print(lf,hist[sample])
                        continue
                    htmp = lf.Get("ZprimeRecomass")
                    htmp.Scale(1.3) # apply k-factor on signal samples
                    # htmp = htmp.Rebin(100,"%s_%d_rebinned"%(htmp.GetName(),mval))
                    htmp = htmp.Rebin(len(rbins)-1,"%s_%d_rebinned"%(htmp.GetName(),mval),rbins)
                    if mval == 300:
                        # if sample in samples:
                        #     continue
                        hist[sample] = htmp.Clone("htmp_%s%d"%(sample,mval))
                        htmp.SetLineColor(r.kOrange)
                        htmp.SetFillColor(r.kOrange)
                        htmp.SetFillStyle(3001)
                        stack.Add(htmp)
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
                        else:
                            htmp.SetLineColor(r.kBlue)
                            htmp.SetFillColor(r.kBlue)
                            htmp.SetFillStyle(3001)
                            stack.Add(htmp)
                            pass
                        if mval == 1300 and "%s%s"%(intf,heli) == "ConLL": # and sample == "CI":
                            if sample == "CI":
                                lf = r.TFile.Open("%s%s"%(base,form%(antype[0],2000,"100k",intf,heli)))
                            else:
                                lf = r.TFile.Open("%s%s"%(base,form%(antype[0],2000,lval,intf,heli)))
                                pass
                            if not lf:
                                print(lf,htmp,hist[sample])
                                continue
                            htmp = lf.Get("ZprimeRecomass")
                            htmp.Scale(1.3) # apply k-factor on signal samples
                            # htmp = htmp.Rebin(100,"%s_%d_rebinned"%(htmp.GetName(),2000))
                            htmp = htmp.Rebin(len(rbins)-1,"%s_%d_rebinned"%(htmp.GetName(),2000),rbins)
                            hist[sample].Add(htmp.Clone("htmp_%s%d"%(sample,2000)))
                            htmp.SetLineColor(r.kRed)
                            htmp.SetFillColor(r.kRed)
                            htmp.SetFillStyle(3001)
                            stack.Add(htmp)
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
                can.Update()
                # raw_input()
                for ftype in ["png","C","pdf","eps","png"]:
                    # can.SaveAs("~/public/forCIAnalysis/cilam{3:s}vsdyto2{1:s}_{2:s}.{0:s}".format(ftype,antype[1],sample,lval))
                    can.SaveAs("~/public/forCIAnalysis/cilam{3:s}vsto2{1:s}_{2:s}_{4:s}.{0:s}".format(ftype,antype[1],sample,lval,src))
                    # raw_input("enter to continue")
                    pass
                for p,point in enumerate(supers[:-1]):
                    bval  = hist[sample].FindBin(point)
                    upval = hist[sample].FindBin(supers[p+1]-0.05)
                    val  = hist[sample].Integral(bval,upval)
                    print("{0:s} {1:d} {2:d} {3:d} {4:2.4f}".format(sample,point,bval,upval,val))
                    pass
                pass
            can = r.TCanvas("can","",800,800)
            plot  = r.TPad("plotpad","",0,0.15,1,1)
            rplot = r.TPad("ratiopad","",0,0,1,0.15)
            hist["CI"].SetLineColor(r.kRed)
            hist["CI"].SetLineWidth(2)
            hist["DY"].SetLineColor(r.kBlue)
            hist["DY"].SetLineWidth(2)
            # rhist = hist["CI"].Clone("lam{0:s}dyratio".format(lval))
            rhist = hist["CI"].Clone("lam{0:s}lam100kratio".format(lval))
            rhist.Divide(hist["DY"])
            plot.cd()
            hist["CI"].Draw()
            hist["DY"].Draw("same")
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
            # raw_input("enter")
            for ftype in ["png","C","pdf","eps","png"]:
                # can.SaveAs("~/public/forCIAnalysis/ratio_cilam{2:s}vsdyto2{1:s}.{0:s}".format(ftype,antype[1],lval))
                can.SaveAs("~/public/forCIAnalysis/ratio_cilam{2:s}vslam100kto2{1:s}_{3:s}.{0:s}".format(ftype,antype[1],lval,src))
                # raw_input("enter to continue")
                pass
            pass
        pass
    pass
