import sciris as sc
import covasim as cv
import covasim.parameters as cvpar
import pylab as pl
import numpy as np
import calibrate_uk as ca


# Settings
date_before_scens = ca.data_end
day_before_scens  = cv.day(date_before_scens, start_date=ca.start_day)
scen_end_date     = '2022-03-01'
debug = 0
heatmap_file = 'heatmap_data.obj'
verbose = -1
seed = 1

# Define sweep parameters
def sweep_params():
    p = sc.objdict()
    p['rel_sev'] = np.random.choice([1, 2, 3])
    p['rel_beta'] = np.random.uniform(1, 6) # changes the relative transmissibility of omicron
    p['rel_imm'] = np.random.uniform(0.1, 0.4) # changes the relative immunity of omicron (using beta cross-immunity)
    return p

# Scenarios
def add_scens(seed=None, rel_beta=None, rel_imm=None, rel_sev=None, meta=None):
    ''' Add future scenarios to the sim '''

    # Get the historical calibrated sim
    sim = ca.make_sim(seed=seed, beta=ca.beta, verbose=verbose)
    sim['end_day'] = scen_end_date

    interventions   = sc.dcp(sim['interventions'])
    variants        = sc.dcp(sim['variants'])

    # Future lockdowns/NPIs
    beta_dict  = sc.odict({
        '2021-12-15': [1., 1., 1., 1.]
    })
    beta_days = beta_dict.keys()
    h_beta = cv.change_beta(days=beta_days, changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=[c[3] for c in beta_dict.values()], layers='c')
    interventions += [h_beta, w_beta, s_beta, c_beta]

    # Define booster as a custom vaccination
    booster = dict(
        nab_eff=sc.dcp(sim['nab_eff']),
        nab_init=None,
        nab_boost=3,
        doses=1,
        interval=None,
        wild=1.0,
        alpha=1 / 2.3,
        beta=1 / 9,
        gamma=1 / 2.9,
        delta=1 / 6.2,
        omicron=1 / 7  # PLACEHOLDER
    )

    booster_target = {'inds': lambda sim: cv.true(sim.people.doses != 2),
                      'vals': 0}  # Only give boosters to people who have had 2 doses

    def num_boosters(sim):
        if sim.t < sim.day(day_before_scens):   return 0
        else:                                   return 250_000  # Just use a placeholder value

    booster = cv.vaccinate_num(vaccine=booster, label='booster', sequence='age', subtarget=booster_target, num_doses=num_boosters, booster=True)
    interventions += [booster]

    # Omicron variant definition
    var_pars = sc.mergedicts(cvpar.get_variant_pars(default=True), {'rel_beta': rel_beta,
                                                                    'rel_severe_prob': rel_sev})
    omicron = cv.variant(var_pars, label='omicron', days=np.arange(sim.day('2021-11-15'), sim.day('2021-11-30')), n_imports=4000)
    variants += [omicron]

    sim.update_pars(variants=variants, interventions=interventions)

    # Initialize then add immunity escape parameters
    sim.initialize()

    immunity = sim['immunity']
    beta_imm = cvpar.get_cross_immunity()['beta'] # Assume that omicron is like beta
    variant_mapping = sim['variant_map']

    # Now vary omicron's immunity
    for i in range(len(immunity)):
        if i != len(immunity) - 1:
            immunity[len(immunity) - 1, i] = beta_imm[variant_mapping[i]] * rel_imm
            immunity[i, len(immunity) - 1] = beta_imm[variant_mapping[i]] * rel_imm

    # immunity matrix
    sim['immunity'] = immunity

    sim.meta = meta

    return sim


def run_sim(sim, do_shrink=True):
    ''' Run a simulation '''

    print(f'Running sim {sim.meta.count:5g} of {sim.meta.n_sims:5g} {str(sim.meta.vals.values()):40s}')
    sim.run(until=day_before_scens) # Run the partial sim
    sim.run() # Run the rest of the sim
    if do_shrink: sim.shrink()

    return sim


def make_msims(sims):
    ''' Take a slice of sims and turn it into a multisim '''
    msim = cv.MultiSim(sims)
    msim.reduce(use_mean=True)
    draw, seed = sims[0].meta.inds
    for s,sim in enumerate(sims): # Check that everything except seed matches
        assert draw == sim.meta.inds[0]
        assert (s==0) or seed != sim.meta.inds[1]
    msim.meta = sc.objdict()
    msim.meta.inds = [draw]
    msim.meta.vals = sc.dcp(sims[0].meta.vals)
    msim.meta.vals.pop('seed')
    print(f'Processing multisim {msim.meta.vals.values()}...')

    return msim


########################################################################
# Run calibration and scenarios
########################################################################
if __name__ == '__main__':

    # p = sweep_params()
    # sim = add_scens(seed=0, **p)
    # sim.run()

    n_seeds = [5, 1][debug]
    n_draws = [2000, 4][debug]
    n_sims = n_seeds * n_draws
    count = 0
    ikw = []
    T = sc.tic()

    # Make sims
    sc.heading('Making sims...')
    for draw in range(n_draws):
        p = sweep_params()
        for seed in range(n_seeds):
            print(f'Creating arguments for sim {count} of {n_sims}...')
            count += 1
            meta = sc.objdict()
            meta.count = count
            meta.n_sims = n_sims
            meta.inds = [draw, seed]
            meta.vals = sc.objdict(sc.mergedicts(p, dict(seed=seed)))
            ikw.append(sc.dcp(meta.vals))
            ikw[-1].meta = meta

    sim_configs = sc.parallelize(add_scens, iterkwargs=ikw)

    # Run sims
    all_sims = sc.parallelize(run_sim, iterarg=sim_configs)
    sims = np.empty((n_draws, n_seeds), dtype=object)
    for sim in all_sims:  # Unflatten array
        draw, seed = sim.meta.inds
        sims[draw, seed] = sim

    # Convert to msims
    all_sims_semi_flat = []
    for draw in range(n_draws):
        sim_seeds = sims[draw, :].tolist()
        all_sims_semi_flat.append(sim_seeds)
    msims = np.empty(n_draws, dtype=object)
    all_msims = sc.parallelize(make_msims, iterarg=all_sims_semi_flat)
    for msim in all_msims:  # Unflatten array
        draw = msim.meta.inds
        msims[draw] = msim

    # Do processing and store results
    variables = ['cum_infections', 'cum_severe', 'cum_deaths']
    d = sc.objdict()
    d.rel_beta = []
    d.rel_imm = []
    d.rel_sev = []
    for v in variables: d[v] = []
    for msim in all_msims:
        d.rel_beta.append(msim.meta.vals['rel_beta'])
        d.rel_imm.append(msim.meta.vals['rel_imm'])
        d.rel_sev.append(msim.meta.vals['rel_sev'])
        for v in variables:
            d[v].append(msim.results[v].values[-1]-msim.results[v].values[day_before_scens])
        sc.saveobj(heatmap_file, d)
    sc.toc(T)



