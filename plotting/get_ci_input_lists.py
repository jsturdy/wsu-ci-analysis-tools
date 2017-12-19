#!/bin/env python

import sys,os

# pickle dict is:
#  DY samples:
#     d[sample]["M%d"%(mass)]
#  CI samples:
#     d[sample]["Lam%s"%(lval)][infm][heli]["M%s"%(mass)]
# Data is structured as:
# {
#  'minCut': minCut,
#  'xsec': [xs_val, xs_err, xs_unit],
#  'maxCut': maxCut,
#  'cutEfficiency': [n_pass, n_fail]
# }

## for using the pickled sample information
# import cPickle as pickle
# with open("ci_xsec_data.pkl","rb") as pkl:
#     sdict = pickle.load(pkl)
## for using the json formatted sample information
samples = {"2mu":["DYTo2Mu","CITo2Mu"],"2e":["DYTo2E","CITo2E"]}
import json
with open("ci_xsec_data.json","rb") as jsn:
    with open("ci_input_counts_test.json","rb") as cnt:
        sdict = json.load(jsn)
        cdict = json.load(cnt)
        print(cdict)
        for lf in samples:
            with open("bkg_input_dy%s_AN.txt"%(lf),"w") as ofi:
                mdict = sdict[samples[lf][0]]
                print(samples[lf][0],mdict)
                for m in mdict:
                    xsdict = mdict[m]
                    xsec = xsdict["xsec"][0]
                    sname = "%s_%s_CUETP8M1_13TeV_Pythia8_Corrected-v3_ntuple"%(samples[lf][0],m)
                    count = cdict[samples[lf][0]][m]
                    ofi.write("%s %d %d %d %f\n"%(sname,count,1,count,xsec))
                    pass
                pass
            with open("sig_input_%s_AN_short.txt"%(lf),"w") as ofi:
                #     d[sample]["Lam%s"%(lval)][infm][heli]["M%s"%(mass)]
                lvdict = sdict[samples[lf][1]]
                for lv in lvdict:
                    if lv in ["Lam1","Lam10","Lam22","Lam28"]:
                        continue
                    infdict = lvdict[lv]
                    for inf in infdict:
                        if lv in ["Lam16","Lam34"] and inf in ["Des"]:
                            continue
                        heldict = infdict[inf]
                        for hel in heldict:
                            if lv in ["Lam16","Lam34"] and hel in ["LR","RR"]:
                                continue
                            mdict = heldict[hel]
                            print(lv,samples[lf][1],mdict)
                            for m in mdict:
                                xsdict = mdict[m]
                                xsec = xsdict["xsec"][0]
                                sname = "%s_%s_CUETP8M1_%sTeV%s%s_13TeV_Pythia8_Corrected-v4_ntuple"%(samples[lf][1],m,lv,inf,hel)
                                count = cdict[samples[lf][1]][lv][inf][hel][m]
                                ofi.write("%s %d %d %d %f\n"%(sname,count,1,count,xsec))
                                pass
                            pass
                        pass
                    pass
                pass
            pass
        pass
    pass
