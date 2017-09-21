#!/bin/env python

import sys,os,re
import argparse
import cPickle as pickle
import json
from nesteddict import nesteddict as ndict

"""
egrep "(cross\ section|event-level|genfilter|Cut)" -r xsec_CITo2*.log|egrep -v TimeReport|awk -F'[=:]' '{print "key="$1,$2,$3,$4,$5,$6}'

xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log minCut  800
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log maxCut  1300
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log Before Filtrer  total cross section   1.421e-02 +- 3.585e-05 pb
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log Filter efficiency (event-level)  (50000) / (50000)   1.000e+00 +- 0.000e+00
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log After filter  final cross section   1.421e-02 +- 3.585e-05 pb
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log Before Filtrer  total cross section   1.421e-02 +- 3.585e-05 pb
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log Filter efficiency (event-level)  (50000) / (50000)   1.000e+00 +- 0.000e+00
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log After filter  final cross section   1.421e-02 +- 3.585e-05 pb
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log TrigReport     1    0      50000      40094       9906          0 genfilter
xsec_CITo2Mu_M800_CUETP8M1_Lam34TeVConLL_13TeV_Pythia8_Corrected-v4.log TrigReport      50000      50000      40094       9906          0 genfilter
"""

parser = argparse.ArgumentParser()
parser.add_argument("infile",  help="Input filename",type=str)
parser.add_argument("-d", "--debug", help="debugging information",action="store_true")

args = parser.parse_args()

sampleDict = ndict()
keys = ndict()
with open("ci_xsec_data.pkl","wb") as pkl:
    with open("ci_xsec_data.json","w") as js:
        with open(args.infile) as f:
            # data = f.read()
            for line in f:
                if args.debug:
                    print("line:",line)
                    pass
                splitline = filter(None,re.split('.log|:|=|\n|\+\-| ',line))
                if args.debug:
                    print("splitline:",splitline,len(splitline))
                    pass

                sample  = splitline[0].split('_')
                main    = sample[1]
                mass    = sample[2]
                special = sample[4].split("TeV")
                if args.debug:
                    print("sample:", sample)
                    print("main:",   main)
                    print("mass:",   mass)
                    print("special:",special)

                sample = sampleDict[main]
                if "CI" in main:
                    lval   = special[0]
                    inte   = special[1][:-2]
                    heli   = special[1][-2:]
                    sample = sample[lval][inte][heli][mass]
                else:
                    sample = sample[mass]
                if (sample.keys()):
                    if args.debug:
                        print("dict:",sample)
                    if splitline[1] == "maxCut":
                        sample[splitline[1]] = float(splitline[2])
                    else:
                        if splitline[1] == "TrigReport":
                            if (int(splitline[2]) == 1):
                                sample["cutEfficiency"] = (int(splitline[5]),int(splitline[6]))
                                pass
                            pass
                        elif splitline[1] == "Before":
                            sample["xsec"] = (float(splitline[6]),float(splitline[7]),str(splitline[8]))
                            pass
                        pass
                else:
                    if args.debug:
                        print("create dict:",main,mass,lval,inte,heli)
                        print("splitline2:",splitline)
                        print("splitline3:",splitline[1],splitline[2])
                        pass
                    sample[splitline[1]] = float(splitline[2])
                    pass
                pass
            pass
        json.dump(sampleDict,js)
        pass
    pickle.dump(sampleDict,pkl)
    pass

if args.debug:
    with open("ci_xsec_data.pkl","rb") as pkl:
        di = pickle.load(pkl)
        for d in di:
            print(d,di[d])
            pass
        pass

    with open("ci_xsec_data.json","r") as js:
        di = json.load(js)
        for d in di:
            print(d,di[d])
            pass
        pass
    pass
