#!/bin/env python

import sys,os,re
import argparse
import cPickle as pickle
import json
from nesteddict import nesteddict as ndict

"""
CITo2E_Lambda_1TeV_Des_LL
M300
Cross section	369.568
Cross section error	12.0772
Number of events	48196
M800
Cross section	204.339
Cross section error	2.93421
Number of events	44360
M1300
Cross section	113.608
Cross section error	2.90056
Number of events	49322
M2000
"""

parser = argparse.ArgumentParser()
parser.add_argument("infile",  help="Input filename",type=str)
parser.add_argument("-d", "--debug", help="debugging information",action="store_true")

args = parser.parse_args()

sampleDict = ndict()
keys       = ndict()
cuts = {
    "M300": [300., 800. ],
    "M800": [800., 1300.],
    "M1300":[1300.,2000.],
    "M2000":[2000.,1e8  ] # only for ConLL samples? or some?
    }

with open("ci_private_xsec_data.pkl","wb") as pkl:
    with open("ci_private_xsec_data.json","w") as js:
        with open(args.infile) as f:
            # data = f.read()
            main  = None
            lval  = None
            inte  = None
            heli  = None
            mass  = None
            xsec  = None
            xserr = None
            npass = None
            nfail = 0
            ngen  = None

            foundHeader  = False
            printTheInfo = False
            sample       = None

            for line in f:
                if args.debug:
                    print("line:",line)
                    pass

                splitline = filter(None,re.split('_|\n| ',line))

                if args.debug:
                    print("splitline:",splitline,len(splitline))
                    pass

                xsinfoline = splitline
                if len(xsinfoline) == 5:
                    foundHeader  = True
                    printTheInfo = False

                    main = xsinfoline[0]
                    if "CI" in main:
                        lval    = xsinfoline[2].split("TeV")[0]
                        inte    = xsinfoline[3]
                        heli    = xsinfoline[4]
                        pass
                elif len(xsinfoline) == 12:
                    if foundHeader:
                        printTheInfo = True
                        foundHeader  = False
                    mass  = xsinfoline[0][1:]
                    xsec  = xsinfoline[3]
                    xserr = xsinfoline[7] 
                    npass = xsinfoline[11]
                    nfail = 0

                    if printTheInfo:
                        if args.debug:
                            print("Populating the dictionary entry")
                            print(main,lval,heli,inte,mass,xsec,xserr,npass,nfail)
                            print(float(mass), int(mass))
                            print(float(npass),int(npass))
                            print(float(nfail),int(nfail))
                            print(float(xsec))
                            print(float(xserr))
                        ## fill the dict object
                        sample = sampleDict[main]
                        if "CI" in main:
                            sample = sample["Lam%s"%(lval)][inte][heli]["M%s"%(mass)]
                        else:
                            sample = sample[mass]
                            pass
                        # "maxCut":
                        if inte == "Con" and heli == "LL":
                            cuts["M1300"][1] = 1e8
                        else:
                            cuts["M1300"][1] = 2000.
                        sample["minCut"]        = cuts["M%s"%(mass)][0]
                        sample["maxCut"]        = cuts["M%s"%(mass)][1]
                        sample["cutEfficiency"] = (int(npass), int(nfail))
                        sample["xsec"]          = (float(xsec),float(xserr),"pb")
                        pass

                    pass
                pass
            pass
        json.dump(sampleDict,js)
        pass
    pickle.dump(sampleDict,pkl)
    pass

if args.debug:
    with open("ci_private_xsec_data.pkl","rb") as pkl:
        di = pickle.load(pkl)
        for d in di:
            print(d,di[d])
            pass
        pass

    with open("ci_private_xsec_data.json","r") as js:
        di = json.load(js)
        for d in di:
            print(d,di[d])
            pass
        pass
    pass
