import sciris as sc
from datetime import datetime, timedelta
from glob import glob
import numpy as np
import sys
import os

start = datetime.strptime("2020-01-21", "%Y-%m-%d")
august = datetime.strptime("2020-09-01", "%Y-%m-%d")
t = (august - start).days

points = {}
data = sys.argv[1]

for f in glob(os.path.join(data, "*.obj")): 
    o = sc.loadobj(f)
    new_inf = max(o["msim"]["new_infections"][t:])
    cum_inf = o["msim"]["cum_infections"][-1]
    cum_death = o["msim"]["cum_deaths"][-1]
    r_eff   = max(o["msim"]["r_eff"][t:])
    test = 100 * (1.0 - (1.0 - o["args"].test)**10)
    trace = o["args"].trace

    points.setdefault(test, {})[trace] = (new_inf, cum_inf, cum_death, r_eff)

for test in sorted(points.keys()):
    for trace in sorted(points[test].keys()):
        print("%s\t%s\t%s" % (test, trace, "\t".join(map(str, points[test][trace]))))
    print()
