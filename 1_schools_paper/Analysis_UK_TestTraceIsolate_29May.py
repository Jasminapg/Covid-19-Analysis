'''
UK scenarios
'''
import matplotlib
matplotlib.use('Agg')
import sciris as sc
import covasim as cv
import pylab as pl

# Check version
cv.check_version('1.3.3')
cv.git_info('covasim_version.json')

# Plotting and output controls
do_plot = 1
do_save = 1
do_show = 0
verbose = 1
seed    = 1
do_parallel = 0

# Analysis steps
rerun = False # If false, loads saved runs

# Paths for saving and loading
version   = 'v1'
date      = '2020may26'
folder    = f'results_FINAL_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = 'UK_Covid_cases_may21.xlsx'


def create_base_sim():
    # Create a sim calibrated to the UK epidemic to date, including interventions in effect until May 31

    start_day = '2020-01-21'
    end_day  = '2021-07-31' # We're running the analysis steps, which means running til July 2021

    # Set the parameters
    total_pop    = 67.86e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 4000
    beta         = 0.0060
    asymp_factor = 1.9
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}

    pars = sc.objdict(
        pop_size     = pop_size,
        pop_infected = pop_infected,
        pop_scale    = pop_scale,
        pop_type     = pop_type,
        start_day    = start_day,
        end_day      = end_day,
        beta         = beta,
        asymp_factor = asymp_factor,
        contacts     = contacts,
        rescale      = True,
    )

    # Create the baseline simulation
    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')

    # Create the distancing interventions that were in effect from the beginning of the epidemic until May 31
    beta_days       = ['2020-02-14',    '2020-03-16',   '2020-03-23',   '2020-04-30',   '2020-05-15']
    h_beta_changes  = [1.00,            1.00,           1.29,           1.29,           1.29        ] # Assume increase household transmission after schools closed
    s_beta_changes  = [1.00,            0.90,           0.02,           0.02,           0.02,       ] # Schools closed March 23
    w_beta_changes  = [0.90,            0.80,           0.20,           0.20,           0.20,       ] # Workplace closures
    c_beta_changes  = [0.90,            0.80,           0.20,           0.20,           0.20        ] # Reduce effective community contacts

    h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c')
    interventions = [h_beta, w_beta, s_beta, c_beta]

    # Create the testing interventions that were in place from the beginning of the epidemic until May 31
    tc_day = sim.day('2020-03-16')  # intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01')  # intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01')  # intervention of increased testing (tt) starts on 1st May
    tti_day = sim.day('2020-06-01')  # intervention of tracing and enhanced testing (tti) starts on 1st June

    s_prob_march = 0.009
    s_prob_april = 0.012
    s_prob_may   = 0.0139
    t_delay = 1.0
    iso_vals = [{k:0.1 for k in 'hswc'}]

    interventions += [
        cv.test_prob(symp_prob=s_prob_march, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
      ]

    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']: intervention.do_plot = False
    return sim


def create_scenario(sim, schoolscen, ttiscen):
    # Create and run the scenarios

    # The beta interventions differ over the first 3 dates: June 8, July 1, and July 22
    initial_bd  =           ['2020-06-08',  '2020-07-01',   '2020-07-22']
    hb = {'jun-opening':    [1.00,          1.00,           1.29        ],
          'sep-opening':    [1.29,          1.29,           1.29        ],
          'phased':         [1.00,          1.00,           1.29,       ],
          'phased-delayed': [1.29,          1.00,           1.29,       ]}
    sb = {'jun-opening':    [0.80,          0.80,           0.00        ],
          'sep-opening':    [0.02,          0.02,           0.00        ],
          'phased':         [0.25,          0.70,           0.00        ],
          'phased-delayed': [0.02,          0.70,           0.00        ]}
    wb = {'jun-opening':    [0.70,          0.70,           0.50        ],
          'sep-opening':    [0.20,          0.40,           0.40        ],
          'phased':         [0.40,          0.70,           0.50        ],
          'phased-delayed': [0.20,          0.70,           0.50        ]}
    cb = {'jun-opening':    [0.80,          0.80,           0.70        ],
          'sep-opening':    [0.20,          0.40,           0.40        ],
          'phased':         [0.40,          0.70,           0.70        ],
          'phased-delayed': [0.20,          0.70,           0.70        ]}

    initial_h = cv.change_beta(days=initial_bd, changes=hb[schoolscen], layers='h')
    initial_s = cv.change_beta(days=initial_bd, changes=sb[schoolscen], layers='s')
    initial_w = cv.change_beta(days=initial_bd, changes=wb[schoolscen], layers='w')
    initial_c = cv.change_beta(days=initial_bd, changes=cb[schoolscen], layers='c')
    interventions = [initial_h, initial_s, initial_w, initial_c]

    # Thereafter, the beta interventions all take the same values across each scenario, but the values change depending on whether it's term time or holidays
    common_bd   = ['2020-09-02', '2020-10-28', '2020-11-01', '2020-12-23', '2021-01-03', '2021-02-17', '2021-02-21', '2021-04-06', '2021-04-17']
    common_hb   = [1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
    common_sb   = [0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
    common_wb   = [0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
    common_cb   = [0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90]
    common_h    = cv.change_beta(days=common_bd, changes=common_hb, layers='h')
    common_s    = cv.change_beta(days=common_bd, changes=common_sb, layers='s')
    common_w    = cv.change_beta(days=common_bd, changes=common_wb, layers='w')
    common_c    = cv.change_beta(days=common_bd, changes=common_cb, layers='c')
    interventions += [common_h, common_s, common_w, common_c]

    # Define the test/trace interventions
    tti_day = sim.day('2020-06-01')  # intervention of tracing and enhanced testing (tti) starts on 1st June

    s_prob_june = {'none': 0.0139,
                   '40%':  0.0429,
                   '80%':  0.06}[ttiscen]

    t_eff_june = {'none': 0.0,
                  '40%':  0.4,
                  '80%':  0.8}[ttiscen]

    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}
    t_probs_june = {k: t_eff_june for k in 'hwsc'}
    t_delay = 1

    interventions += [
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, test_delay=t_delay),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day),
      ]

    sim['interventions'] += interventions
    for intervention in sim['interventions']:
        intervention.do_plot = False

    sim.label = f'{schoolscen}_{ttiscen}'

    return sim


if __name__ == '__main__':

    # Details of scenarios
    school_scens = ['jun-opening', 'sep-opening', 'phased', 'phased-delayed']
    tti_scens    = ['none', '40%', '80%']

    if rerun:
        # Create the scenarios
        msims = []
        for ss in school_scens:
            for ttis in tti_scens:
                sim = create_base_sim()
                this_sim = create_scenario(sim, ss, ttis)
                this_msim = cv.MultiSim(base_sim=this_sim)  # Create using your existing sim as the base
                this_msim.init_sims(n_runs=6, verbose=True, reseed=True, noise=0)
                msims.append(this_msim)

        # Run the scenarios in parallel
        big_msim = cv.MultiSim.merge(*msims)
        big_msim.run()  # Run with uncertainty

        # Separate the scenarios out and save them
        final_msims = sc.objdict()
        final_sims = sc.objdict()
        keys = set([sim.label for sim in big_msim.sims])
        for key in keys:
            final_sims[key] = []
            for sim in big_msim.sims:
                if sim.label == key:
                    final_sims[key].append(sim)
        for key in keys:
            final_msims[key] = cv.MultiSim(sims=final_sims[key])
            final_msims[key].reduce()
        sc.saveobj(filename='uk_scens.obj', obj=final_msims)
    else:
        final_msims = sc.loadobj(filename='uk_scens.obj')

    # Save the key figures
    if do_plot:

        # Make individual plots
        plot_customizations = dict(
            interval   = 90, # Number of days between tick marks
            dateformat = '%m/%Y', # Date format for ticks
            fig_args   = {'figsize':(14,8)}, # Size of the figure (x and y)
            axis_args  = {'left':0.15}, # Space on left side of plot
            )

        for mkey, msim in final_msims.items():

            msim.plot_result('r_eff', do_show=do_show, **plot_customizations)
            pl.axhline(1.0, linestyle='--', c=[0.8,0.4,0.4], alpha=0.8, lw=4) # Add a line for the R_eff = 1 cutoff
            pl.title('')
            if do_save: cv.savefig(f'R_eff_{mkey}.png')

            msim.plot_result('cum_deaths', do_show=do_show, **plot_customizations)
            pl.title('')
            if do_save: cv.savefig(f'Deaths_{mkey}.png')

            msim.plot_result('new_infections', do_show=do_show, **plot_customizations)
            pl.title('')
            if do_save: cv.savefig(f'Infections_{mkey}.png')

            msim.plot_result('cum_diagnoses', do_show=do_show, **plot_customizations)
            pl.title('')
            if do_save: cv.savefig(f'Diagnoses_{mkey}.png')



##for calibration figures
   # msim.plot_result('cum_deaths', interval=20, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
   # pl.title('')
   # cv.savefig('Deaths.png')

   # msim.plot_result('cum_diagnoses', interval=20, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
   # pl.title('')
   # cv.savefig('Diagnoses.png')



#    # Recalculate R_eff with a larger window
#    for sim in msim.sims:
#        sim.compute_r_eff(smoothing=20)


    #to produce mean cumulative infections and deaths for barchart figure
#    print('Mean cumulative values:')
#    print('Deaths: ',     msim.results['cum_deaths'][-1])
#    print('Infections: ', msim.results['cum_infectious'][-1])

