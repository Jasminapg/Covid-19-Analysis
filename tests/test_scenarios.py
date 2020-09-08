import UK_tradeoffs as ukto
import sys
import os
import covasim as cv
import numpy as np

def compare(u, v, threshold=0.01):
    assert np.all(np.abs(np.array(u)-np.array(v)) < threshold), (u,v)

# Create the baseline simulation
sim = cv.Sim(pars=ukto.pars, datafile=ukto.data_path, location='uk')

args = ukto.parser.parse_args()

args.scenario = "no_masks"
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.70, 0.60, 0.70, 0.60, 0.70, 0.60, 0.70, 0.60, 0.70, 0.60, 0.70, 0.60, 0.70, 0.60, 0.70, 0.60])

args.scenario = 'low_comp'
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51])

args.scenario = 'med_comp'
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42])

args.scenario = 'high_comp'
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30])

args.scenario = 'low_comp_notschools'
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51, 0.60, 0.51])

args.scenario = 'med_comp_notschools'
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42, 0.49, 0.42])

args.scenario = 'high_comp_notschools'
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30, 0.35, 0.30])

## test new machinery for overriding effective coverage, a, and b
args.ec = 0.7
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40, 0.50, 0.40])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.21, 0.18, 0.21, 0.18, 0.21, 0.18, 0.21, 0.18, 0.21, 0.18, 0.21, 0.18, 0.21, 0.18, 0.21, 0.18])

args.ec = None
args.a = 0.8
args.b = 0.5
_, _, _, w_beta_changes, c_beta_changes, interventions = ukto.scenario_beta_changes(sim, args)
compare(w_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.80, 0.70, 0.80, 0.70, 0.80, 0.70, 0.80, 0.70, 0.80, 0.70, 0.80, 0.70, 0.80, 0.70, 0.80, 0.70])
compare(c_beta_changes, [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, 0.25, 0.20, 0.25, 0.20, 0.25, 0.20, 0.25, 0.20, 0.25, 0.20, 0.25, 0.20, 0.25, 0.20, 0.25, 0.20])
