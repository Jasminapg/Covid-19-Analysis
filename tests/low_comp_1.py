import os
import sciris as sc
import numpy as np
import covasim as cv

t = cv.daydiff('2020-01-21', '2020-09-01')

scenarios = ['low_comp', 'high_comp', 'low_comp_notschools', 'high_comp_notschools']

scenario = 0
trace = 0.47
for test, expected in [(0.0171, 110000), (0.12, 4000)]:
    ## run the simulation
    cmd = "python UK_Test-Trace_phaseplots_26August.py --samples 12 --scenario %s --test %.02f --trace %.02f" % (scenario, test, trace)
    os.system(cmd)

    ## load the results
    outfile = "%s/test%.02f-trace%.02f.obj" % (scenarios[scenario], test, trace)
    results = sc.loadobj(outfile)

    ## ensure that we get at least some infections
    if not np.any(results["msim"]["new_infections"]):
        raise ValueError("%s got no infections at all, how strange\ncommand: %s" % (scenarios[scenario], cmd))

    ## ensure that the expected value of infections after september is within 10% of expected
    infections = max(results["msim"]["new_infections"][t:])
    if infections < 0.9*expected or infections > 1.1*expected:
        raise ValueError("%s: with test=%s and trace=%s expected %s peak infections after %s and got %s\ncommand: %s" % (scenarios[scenario], test, trace, expected, september, infections, cmd))
