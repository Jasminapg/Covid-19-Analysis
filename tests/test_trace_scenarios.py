import os
import sciris as sc
import numpy as np
import covasim as cv

t = cv.daydiff('2020-01-21', '2020-09-01')

scenarios = ['no_masks', 'low_comp', 'med_comp', 'low_comp_notschools', 'med_comp_notschools']

testcases = [
## (scenario, trace, test, infections)
    (0, 0.47, 0.03, 110000),
    (0, 0.47, 0.12, 17000),
    (1, 0.47, 0.03, 70000),
    (1, 0.47, 0.12, 5800),
]

for scenario, trace, test, expected in testcases:
    ## run the simulation
    cmd = "python UK_tradeoffs.py --samples 12 --scenario %s --test %.02f --trace %.02f" % (scenario, test, trace)
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
        raise ValueError("%s: with test=%s and trace=%s expected %s peak infections and got %s\ncommand: %s" % (scenarios[scenario], test, trace, expected, infections, cmd))
