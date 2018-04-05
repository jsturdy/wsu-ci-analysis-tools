def doFitOnGraph(params, lvals, xvals, xerrs,
                 intf, heli, i, point, outf, conFitPar,
                 fixinf=False, fixdes=False):
    import ROOT as r
    import numpy as np
    r.gErrorIgnoreLevel = r.kWarning
    keyname = "{0:s}{1:s} {2:d}".format(intf,heli,point)
    print("Keyname:",keyname)
    fn = r.TF1("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"[0]+[1]/(x**2)+[2]/(x**4)",5,100000)
    # fn = r.TF1("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"[0]+[1]/(x**2)+[2]/(x**4)",10,100)
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
    # gr = r.TGraph(len(lvals),xvals,yvals)
    gr = r.TGraphErrors(len(lvals),xvals,yvals,xerrs,yerrs)
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
    # fn   = None
    fitR    = None
    bestFit = None
    while (stepN < 100):
        randu1  = random.Uniform(0, 1)
        randu5  = random.Uniform(-2., 2.5)
        randu10 = random.Uniform(-5, 5)
        randg   = random.Gaus(10., 5.)
    
        if (randg < 0.0 or randg > 100):
            continue
    
        # fn = r.TF1("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"[0]+[1]/(x**2)+[2]/(x**4)",5.0+randu5,100000+(10*randu10))
        fn.SetRange(0.5,100000+(10*randu10))
        # set constant term to the value of the 100kTeV point?
        # fn.SetParameter(0,8+stepN*8)
        if fixinf:
            fn.SetParameter(0,gr.Eval(100000))
            fn.SetParLimits(0,0.9*gr.Eval(100000+10*randu10),1.1*gr.Eval(100000-10*randu10))
        else:
            fn.SetParLimits(0,0.,1e5)
            pass
    
        if intf == "Con":
            # fn.SetParameter(1,randg)
            fn.SetParLimits(1,0.,1e10)
            fn.SetParLimits(2,0.,1e10)
            pass
        elif not fixdes:
            fn.SetParLimits(1,-1e10,0.)
            fn.SetParLimits(2,0.,1e10)
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
    
        # fn.SetParameter(2,12345*randg+stepN*randu10*randg)
        # fn.SetParLimits(2,1e-5,1e10)
        # this should change the function range for fitting
        # fn.SetRange(5.0+randu5,100000-5+randu10)
        # this is just the fit itself, the range here is only for drawing
        fitR = gr.Fit("fn_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"REMS","",5,10000)
        fitEmpty = fitR.IsEmpty()
        if fitEmpty:
            # Don't try to fit empty data again
            print("WARNING: Fit data is empty")
            break
        fitValid = fitR.IsValid()
        if not fitValid:
            print("INFO: Fit not valid, continuing")
            # Need to retry the fit with drastically different initial settings?
            stepN += 1
            continue
        fitChi2 = fn.GetChisquare()
        fitNDF  = fn.GetNDF()
        if (fitChi2 < MinChi2Temp and fitChi2 > 0.0):
            MinChi2Temp = fitChi2
            bestFit     = fitR.Clone("bestFit_{0:s}".format(fitR.GetName()))
            print("Fit iteration",stepN)
            fitR.Print("V")
            # if ((MinChi2Temp < 25 or fitChi2/(1.0*fitNDF) < 5.)):
            if ((MinChi2Temp < 25 or fitChi2/(1.0*fitNDF) < 5.) and stepN > 0):
                print("Step {0:0} Good fit result".format(stepN),fitR.Print("V"))
                break
            pass
        pass
        stepN += 1

    print("Executed steps:",stepN)
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
    
    # Functional form for the uncertainty on the fit, taking only minimization uncertainties
    uncfn = r.TF1("fn_unc_m{0:d}_{1:s}{2:s}".format(point,intf,heli),"sqrt(([0])^2+([1]/(x**2))^2+([2]/(x**4))^2)",0.1,10000000)
    uncfn.SetParameter(0,fn.GetParError(0))
    uncfn.SetParameter(1,fn.GetParError(1))
    uncfn.SetParameter(2,fn.GetParError(2))
    
    r.gPad.SetLogy(True)
    r.gPad.SetLogx(True)
    fn.Draw("same")
    fitR.SetName("fitR_m{0:d}_{1:s}{2:s}".format(point,intf,heli))
    fitR.Write()
    fn.Write()
    uncfn.Write()
    gr.Write()
    outf.Write()
    # raw_input("continue")
    pass
