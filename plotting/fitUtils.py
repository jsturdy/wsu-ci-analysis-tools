def doFitOnGraph(params, lvals, xvals, xerrs,
                 intf, heli, i, point, outf, conFitPar,
                 fixinf=False, fixdes=False,
                 limitPars=None, fitRange=(0.5,125000.)):
    import ROOT as r
    import numpy as np
    import math

    r.gErrorIgnoreLevel = r.kWarning
    keyname = "{0:s}{1:s} {2:d}".format(intf,heli,point)
    print("Keyname:",keyname)
    fn = r.TF1("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),
               "[0]+[1]/(x**2)+[2]/(x**4)",fitRange[0],fitRange[1])
    keyname = "{0:s}{1:s}_{2:d}GeV".format(intf,heli,point)
    pvals = params["{0:s}".format(keyname)]
    perrs = params["{0:s}_err".format(keyname)]
    print("Values:",pvals)
    print("Errors:",perrs)
    yvals = np.array(pvals,dtype='float64')
    yerrs = np.array(perrs,dtype='float64')
    if intf == "Con":
        conFitPar.append(0)
    print("Values (numpy):",xvals,yvals)
    print("Errors (numpy):",xerrs,yerrs)
    print("Fit range:",fitRange)
    print("Constraints:",limitPars)
    gr = r.TGraphErrors(len(lvals),xvals,yvals,xerrs,yerrs)
    gr.SetName("gr_{0:s}{1:s}_m{2:d}".format(intf,heli,point))
    if i == 0:
        gr.Draw("ap")
        gr.GetYaxis().SetTitle("Yield")
        gr.GetYaxis().SetRangeUser(1e-3,1e7)
        gr.GetXaxis().SetTitle("#Lambda [TeV]")
    else:
        gr.Draw("psame")

    fitChi2     = 0
    MinChi2Temp = 99999999
    stepN       = 0
    nGoodFits   = 0

    random = r.TRandom3()
    random.SetSeed(95369)

    r.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2","MINIMIZE")
    r.Math.MinimizerOptions.SetDefaultStrategy(1)
    r.Math.MinimizerOptions.SetDefaultTolerance(0.000001)
    # r.Math.MinimizerOptions.SetDefaultPrecision(0.000001)
    # r.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(5000)
    # r.Math.MinimizerOptions.SetDefaultMaxIterations(1000)

    ## want to constrain the fit parameters between constructive and destructive functions
    # fn.FixParameter(0,gr.Eval(100000))
    # fn   = None
    fitR    = None
    bestFit = None

    #### Set up the fitting guess######################
    randu1  = random.Uniform(0, 1)
    randu5  = random.Uniform(-2.5, 2.5)
    randu10 = random.Uniform(0., 10)
    randg   = random.Gaus(10., 5.)
    
    while (randg < 0.0 or randg > 100):
        randg = random.Gaus(10., 5.)
        continue
    
    # fn = r.TF1("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"[0]+[1]/(x**2)+[2]/(x**4)",5.0+randu5,100000+(10*randu10))
    # fn.SetRange(0.5,100000+(10*randu10))
    # set constant term to the value of the 100kTeV point?
    # fn.SetParameter(0,8+stepN*8)
    fn.SetParameter(0,gr.Eval(100000))
    
    fn.SetParameter(2,1e4*randg)
    if intf == "Con":
        fn.SetParameter(1,randu1*1e4*math.fabs(randg))
    elif not fixdes:
        fn.SetParameter(1,-(randu1)*1e4*math.fabs(randg))
        pass
    else:
        conval = -conFitPar[i]
        fn.SetParameter(1,conval)
        # fn.FixParameter(1,-conFitPar[i])
        fn.SetParameter(1,conval)
        uplim = conval + ((randu1/10.)*abs(conval))
        lolim = conval - ((randu1/10.)*abs(conval))
        print("Limits:",lolim,conval,uplim)
        fn.SetParLimits(1,lolim,uplim)
        pass
    
    fn.SetParameter(2,12345*randg+stepN*randu10*randg)

    #### Set up the fitting parameter limits###########
    if fixinf:
        fn.SetParLimits(0,0.9*gr.Eval(100000+10*randu10),1.1*gr.Eval(100000-10*randu10))
        pass
    elif (limitPars['p0']):
        print("Setting p0 limits to:",limitPars['p0'][0],limitPars['p0'][1])
        fn.SetParLimits(0,limitPars['p0'][0],limitPars['p0'][1])
    else:
        pass

    if (limitPars['p1']):
        if intf == "Con":
            print("Setting p1 limits to:",limitPars['p1'][0],limitPars['p1'][1])
            fn.SetParLimits(1,limitPars['p1'][0],limitPars['p1'][1])
        elif not fixdes:
            print("Setting p1 limits to:",-limitPars['p1'][1],limitPars['p1'][0])
            fn.SetParLimits(1,-limitPars['p1'][1],limitPars['p1'][0])
            pass
        pass

    if (limitPars['p2']):
        print("Setting p2 limits to:",limitPars['p2'][0],limitPars['p2'][1])
        fn.SetParLimits(2,limitPars['p2'][0],limitPars['p2'][1])
        # fn.SetParLimits(2,0.,1e10)
        # fn.SetParLimits(2,1e-5,1e10)
        pass

    #### Run the fitting###############################
    while stepN < 500:
        stepN += 1
        fitR = gr.Fit("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),
                      "REMS Q MULTITHREAD","",fitRange[0],fitRange[1])
        fitEmpty = fitR.IsEmpty()
        fitValid = fitR.IsValid()
        if fitEmpty:
            # Don't try to fit empty data again
            print("WARNING: Fit data is empty")
            r.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2","MINIMIZE")
        elif not fitValid:
            print("WARNING: Fit not valid, continuing")
            # Need to retry the fit with drastically different initial settings?
            r.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2","MINIMIZE")
            continue
        else:
            # fitChi2 = fn.GetChisquare()
            # fitNDF  = fn.GetNDF()
            fitChi2 = fitR.Chi2()
            fitNDF  = fitR.Ndf()
            nGoodFits += 1

            if (fitChi2 < MinChi2Temp and fitChi2 > 0.0):
                print("INFO: Step {0:d} has a better fit result".format(stepN))
                MinChi2Temp = fitChi2
                bestFit     = fitR.Clone("bestFit_{0:s}".format(fitR.GetName()))
                pass
            else:
                print("INFO: Step {0:d} has a good fit result, minChi2 is {1:2.2f}".format(stepN,MinChi2Temp))
                pass
            fitR.Print("V")
            r.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2","MIGRAD")
            pass

        if (((MinChi2Temp < 25) or (fitR.Status() != 4)) and nGoodFits > 0):
            print("INFO: Found best fit result")
            break
        pass

    print("Executed {0:d} steps with {1:d} good fits".format(stepN,nGoodFits))

    if intf == "Con":
        conFitPar[i] = fn.GetParameter(1)

    print("Fit result")
    fitR.Print("V")

    if bestFit:
        print("Best fit result")
        bestFit.Print("V")
        bestFit.SetName("bestFit_m{0:d}_{1:s}{2:s}".format(point,intf,heli))
        bestFit.Write()
        pass

    fitRes     = fitR.FittedFunction()
    fitPars    = fitR.GetParams()
    fitParErrs = fitR.Errors()

    # Function to manually grab the fit result parameters
    resfn = r.TF1("fnFitted_m{0:d}_{1:s}{2:s}".format(point,intf,heli),
                  "[0]+[1]/(x**2)+[2]/(x**4)",0.1,1e8)
    # Functional form for the uncertainty on the fit, taking only minimization uncertainties
    uncfn = r.TF1("fn_unc_m{0:d}_{1:s}{2:s}".format(point,intf,heli),
                  "sqrt(([0])^2+([1]/(x**2))^2+([2]/(x**4))^2)",0.1,1e8)
    for par in range(3):
        # sometimes the fn doesn't have good values?
        print("Setting function p{:d} to {:2.4f} {:2.4f}".format(par,fitPars[par],fitParErrs[par]))
        resfn.SetParameter(par,fitPars[par])
        resfn.SetParError(par,fitParErrs[par])

        uncfn.SetParameter(par,fn.GetParError(par))
        # sometimes the fn doesn't have good values?
        # uncfn.SetParameter(par,fitParErrs[par])
        pass

    print("Pre parameter scan")
    print("fn\np0: {:2.4f}  {:2.4f}\np1: {:2.4f}  {:2.4f}\np2: {:2.4f}  {:2.4f}".format(fn.GetParameter(0),
                                                                                        fn.GetParError(0),
                                                                                        fn.GetParameter(1),
                                                                                        fn.GetParError(1),
                                                                                        fn.GetParameter(2),
                                                                                        fn.GetParError(2)))
    
    print("fit\np0: {:2.4f}  {:2.4f}\np1: {:2.4f}  {:2.4f}\np2: {:2.4f}  {:2.4f}".format(fitPars[0],
                                                                                         fitParErrs[0],
                                                                                         fitPars[1],
                                                                                         fitParErrs[1],
                                                                                         fitPars[2],
                                                                                         fitParErrs[2]))
    
    print("resfn\np0: {:2.4f}  {:2.4f}\np1: {:2.4f}  {:2.4f}\np2: {:2.4f}  {:2.4f}".format(resfn.GetParameter(0),
                                                                                           resfn.GetParError(0),
                                                                                           resfn.GetParameter(1),
                                                                                           resfn.GetParError(1),
                                                                                           resfn.GetParameter(2),
                                                                                           resfn.GetParError(2)))

    grs = [None,None,None]
    parmap = {0:2,1:0,2:1}
    for par in range(3):
        # suspect for broken fits
        print("Scanning parameter scan {0:d} 500 {1:2.4f} {2:2.4f}".format(par,
                                                                           fn.GetParameter(parmap[par])-fn.GetParError(parmap[par]),
                                                                           fn.GetParameter(parmap[par])+fn.GetParError(parmap[par])))
        r.gMinuit.Command("scan {0:d} 100".format(par))
        grs[par] = r.TGraph(r.gMinuit.GetPlot())
        grs[par].SetName("par_scan_m{0:d}_{1:s}{2:s}_p{3:d}".format(point,intf,heli,parmap[par]))
        grs[par].SetMarkerStyle(21)
        grs[par].Write()
        # grs[par].GetYaxis().SetTitle("FCN #chi^{2}")
        # grs[par].GetXaxis().SetTitle("Fit parameter {0:d}".format(parmap[par]))
        pass

    print("Post parameter scan")
    fitRes     = fitR.FittedFunction()
    fitPars    = fitR.GetParams()
    fitParErrs = fitR.Errors()
    print("fn\np0: {:2.4f}  {:2.4f}\np1: {:2.4f}  {:2.4f}\np2: {:2.4f}  {:2.4f}".format(fn.GetParameter(0),
                                                                                        fn.GetParError(0),
                                                                                        fn.GetParameter(1),
                                                                                        fn.GetParError(1),
                                                                                        fn.GetParameter(2),
                                                                                        fn.GetParError(2)))
    
    print("fit\np0: {:2.4f}  {:2.4f}\np1: {:2.4f}  {:2.4f}\np2: {:2.4f}  {:2.4f}".format(fitPars[0],
                                                                                         fitParErrs[0],
                                                                                         fitPars[1],
                                                                                         fitParErrs[1],
                                                                                         fitPars[2],
                                                                                         fitParErrs[2]))
    
    print("resfn\np0: {:2.4f}  {:2.4f}\np1: {:2.4f}  {:2.4f}\np2: {:2.4f}  {:2.4f}".format(resfn.GetParameter(0),
                                                                                           resfn.GetParError(0),
                                                                                           resfn.GetParameter(1),
                                                                                           resfn.GetParError(1),
                                                                                           resfn.GetParameter(2),
                                                                                           resfn.GetParError(2)))
    r.gPad.SetLogy(True)
    r.gPad.SetLogx(True)
    r.gPad.SetGridy(True)
    r.gPad.SetGridx(True)
    resfn.SetLineWidth(2)
    resfn.SetLineStyle(2)
    fn.SetLineWidth(2)
    fn.SetLineStyle(1)
    fn.Draw("same")
    fitR.SetName("fitR_m{0:d}_{1:s}{2:s}".format(point,intf,heli))
    fitR.Write()
    fn.Write()
    resfn.Write()
    uncfn.Write()
    gr.Write()
    outf.Write()
    pass
