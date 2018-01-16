#!/bin/env python

import sys, os
import argparse
parser = argparse.ArgumentParser()
#parser.add_argument("-inFile", help="Input file", type=str)
parser.add_argument("-flav", help="Lepton flavor", type=str)
parser.add_argument("-d",    help="debug", action='store_true')

args = parser.parse_args()

import ROOT as r
import numpy as np
from nesteddict import nesteddict as ndict
import json

antypes=[["E","e","Ele"],
         ["Mu","mu","Mu"]]
base="root://cmseos.fnal.gov///store/group/lpcci2dileptons/ZprimeDiLeptonsAnalysis2017/CINtuples_Dec15/"
# base="root://cmseos.fnal.gov///store/user/sturdy/CINtuples_Dec15/"
ciform="CITo2{0:s}_M{1:d}_CUETP8M1_Lam{2:s}TeV{3:s}{4:s}_13TeV_Pythia8_Corrected-v4_ntuple.root"
dyform="DYTo2{0:s}_M{1:d}_CUETP8M1_13TeV_Pythia8_Corrected-v3_ntuple.root"
samples=["DY","CI"]

r.gROOT.SetBatch(True)

mvals=[300,800,1300]
lvals=["1", "10", "16", "22", "28", "34", "100k"]
# lvals=["16", "34", "100k"]
helis=["LL","LR","RR"]
intfs=["Con","Des"]
# helis=["LL"]
# intfs=["Con"]


debug = args.d


for antype in antypes:
    params = ndict()
    with open("ci_input_counts_2{0:s}.json".format(antype[1]),"w") as js:
        main = "{0:s}To2{1:s}".format(samples[0],antype[0])
        sample = params[main]
        for mval in mvals:
            lf = r.TFile.Open("{0:s}{1:s}".format(base,dyform.format(antype[0],mval)))
            if lf == None:
                continue
            if not lf.IsOpen() or lf.IsZombie():
                continue
            tree = lf.Get("tree")
            hist = r.TH1D("hist","",10,-0.5,9.5)
            lf.Get("tree").Draw("event_runNo>>hist")
            print(lf,lf.IsOpen(),lf.IsZombie(),hist.GetEntries())
            sample["M{0:d}".format(mval)] = hist.GetEntries()
            pass
        main = "{0:s}To2{1:s}".format(samples[1],antype[0])
        sample = params[main]
        for i,lval in enumerate(lvals):
            for intf in intfs:
                if intf == "Des" and lval in lvals[:2]:
                    pass # continue
                for heli in helis:
                    if heli in helis[1:] and lval in lvals[:2]:
                        pass # continue
                    for mval in mvals:
                        lf = r.TFile.Open("{0:s}{1:s}".format(base,ciform.format(antype[0],mval,lval,intf,heli)))
                        if lf == None:
                            continue
                        if not lf.IsOpen() or lf.IsZombie():
                            continue
                        tree = lf.Get("tree")
                        hist = r.TH1D("hist","",10,-0.5,9.5)
                        lf.Get("tree").Draw("event_runNo>>hist")
                        print(lf,lf.IsOpen(),lf.IsZombie(),hist.GetEntries())
                        sample["Lam{0:s}".format(lval)][intf][heli]["M{0:d}".format(mval)] = hist.GetEntries()
                        if mval == 1300 and intf+heli == "ConLL":
                            lf = r.TFile.Open("{0:s}{a:s}".format(base,ciform.format(antype[0],2000,lval,intf,heli)))
                            tree = lf.Get("tree")
                            hist = r.TH1D("hist","",10,-0.5,9.5)
                            lf.Get("tree").Draw("event_runNo>>hist")
                            print(lf,lf.IsOpen(),lf.IsZombie(),hist.GetEntries())
                            sample["Lam{0:s}".format(lval)][intf][heli]["M{0:d}".format(2000)] = hist.GetEntries()
                            pass
                        pass
                    pass
                pass
            pass
        json.dump(params,js)
    pass
