import sciris as sc
import covasim as cv
import pylab as pl
import numpy as np
import matplotlib as mplt

########################################################################
# Settings and initialisation
########################################################################
# Check version
cv.check_version('2.0.2')
cv.git_info('covasim_version.json')



# Saving and plotting settings
do_plot = 1
do_save = 1
save_sim = 1
do_show = 0
verbose = 1
seed    = 1
n_runs = 200
to_plot = sc.objdict({
    'Cumulative diagnoses': ['cum_diagnoses'],
    'New infections': ['new_infections'],
    'R': ['r_eff'],
    'Cumulative deaths': ['cum_deaths'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'scens', # Takes the best-fitting runs and projects these forward under different mask and TTI assumptions
              'devel']
whattorun = runoptions[1] #Select which of the above to run

# Filepaths
# Filepaths
data_path = 'UK_Covid_cases_august28.xlsx'
resfolder = 'results'

# Important dates
start_day = '2020-01-21'
end_day = '2020-12-31'
data_end = '2020-08-31' # Final date for calibration


########################################################################
# Create the baseline simulation
########################################################################

def make_sim(seed, beta, calibration=True, scenario=None, future_symp_test=None, future_t_eff=None, end_day=None, verbose=0):

    # Set the parameters
    total_pop    = 67.86e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 1500
    beta         = beta
    asymp_factor = 2
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}
    beta_layer   = {'h':3.0, 's':1.0, 'w':0.6, 'c':0.3}
    if end_day is None: end_day = '2020-12-31'

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
        rand_seed    = seed,
        verbose      = verbose,
        #rel_severe_prob = 0.4,
        #rel_crit_prob = 2.3,
        #rel_death_prob=1.5,
    )

    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 0-10
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 10-20
    
    # ADD BETA INTERVENTIONS
    beta_past  = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90, ],
                           '2020-03-16': [1.00, 0.90, 0.80, 0.80, ],
                           '2020-03-23': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-04-30': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-05-15': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-06-01': [1.00, 0.23, 0.40, 0.40, ],
                           '2020-06-15': [1.00, 0.38, 0.50, 0.50, ],
                           '2020-07-22': [1.29, 0.00, 0.30, 0.50, ],
                           '2020-08-22': [1.29, 0.00, 0.30, 0.50, ]
                           })

    if not calibration:
        if scenario == 'masks15':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.765, 0.90, 0.595, 0.425, 0.765, 0.595
        elif scenario == 'masks30':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.63,  0.90, 0.49,  0.35,  0.63,  0.49
        elif scenario == 'masks15_notschools':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.90,  0.90, 0.595, 0.425, 0.765, 0.595
        elif scenario == 'masks30_notschools':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.90,  0.90, 0.49,  0.35,  0.63,  0.49

        beta_scens = sc.odict({'2020-09-02': [1.25, sbv1, wbv1, cbv1],
                               '2020-10-28': [1.25, 0.00, wbv2, cbv2],
                               '2020-11-01': [1.25, sbv1, wbv1, cbv1],
                               '2020-12-23': [1.25, 0.00, wbv2, cbv2],
                               '2020-12-25': [1.50, 0.00, 0.20, 0.70],
                               '2021-01-03': [1.25, sbv1, wbv1, cbv1],
                               '2021-02-17': [1.25, 0.00, wbv2, cbv2],
                               '2021-02-21': [1.25, sbv1, wbv1, cbv1],
                               '2021-04-06': [1.25, 0.00, wbv2, cbv2],
                               '2021-04-19': [1.25, sbv2, wbv1, cbv1]
                              })

        beta_dict = sc.mergedicts(beta_past, beta_scens)
    else:
        beta_dict = beta_past

    beta_days = list(beta_dict.keys())
    h_beta = cv.change_beta(days=beta_days, changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=[c[3] for c in beta_dict.values()], layers='c')

    # Add a new change in beta to represent the takeover of the novel variant VOC 202012/01
    # Assume that the new variant is 60% more transmisible (https://cmmid.github.io/topics/covid19/uk-novel-variant.html,
    # Assume that between August and Jan 30, the new variant grows from 0-100% of cases
    #voc_days   = np.linspace(sim.day('2020-08-01'), sim.day('2021-01-30'), 31)
    #voc_prop   = 0.6/(1+np.exp(-0.075*(voc_days-sim.day('2020-09-30')))) # Use a logistic growth function to approximate fig 2A of https://cmmid.github.io/topics/covid19/uk-novel-variant.html
    #voc_change = voc_prop*1.63 + (1-voc_prop)*1.
    #voc_beta = cv.change_beta(days=voc_days,
    #                          changes=voc_change)

    #interventions = [h_beta, w_beta, s_beta, c_beta, voc_beta]  
    interventions = [h_beta, w_beta, s_beta, c_beta]  

    
    # ADD TEST AND TRACE INTERVENTIONS
    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sep= sim.day('2020-09-01')
    tti_day_oct= sim.day('2020-10-01')
    tti_day_nov= sim.day('2020-11-01')
    tti_day_dec= sim.day('2020-12-01')
    tti_day_jan= sim.day('2021-01-01')
    tti_day_vac= sim.day('2020-12-20')

    s_prob_april = 0.009
    s_prob_may   = 0.017
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769
    s_prob_sep = 0.02769

    if future_symp_test is None: future_symp_test = s_prob_sep
    t_delay       = 1.0

    #isolation may-july
    iso_vals = [{k:0.7 for k in 'hswc'}]
    #isolation august
    iso_vals1 = [{k:0.7 for k in 'hswc'}]
    #isolation september
    iso_vals2 = [{k:0.7 for k in 'hswc'}]

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.0075, asymp_prob=0.0, symp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay),
        cv.test_prob(symp_prob=future_symp_test, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_sep, test_delay=t_delay),
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.5, 'w': 0.5, 'c': 0.05},
                           trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
                           start_day='2020-06-01',
                           quar_period=10),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}})]
    

# Finally, update the parameters
    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    sim.initialize()

    return sim

########################################################################
# Run calibration and scenarios
########################################################################
if __name__ == '__main__':

    #betas = [i / 10000 for i in range(72, 77, 1)]

    # Quick calibration
    if whattorun=='quickfit':
        s0 = make_sim(seed=1, beta=0.00748, end_day='2020-09-10', verbose=0.1)
        sims = []
        for seed in range(30):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
        #msim.reduce()
        msim.reduce(quantiles = [0.10,0.90]) 
        #sim.to_excel('my-sim.xlsx')
        if do_plot:
            msim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path=f'uk.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)


    # Run scenarios
    elif whattorun=='scens':

        #scenarios = ['masks15', 'masks30', 'masks15_notschools', 'masks30_notschools']
        scenarios = ['masks30', 'masks30_notschools']
        for scenname in scenarios:

            print('---------------\n')
            print(f'Beginning scenario: {scenname}')
            print('---------------\n')
            sc.blank()
            s0 = make_sim(seed=1, beta=0.00748, end_day='2020-12-31', calibration=False, scenario=scenname, verbose=0.1)
            #s0.run(until='2020-08-31')
            sims = []
            

            for seed in range(30):
                sim = s0.copy()
                sim['rand_seed'] = seed
                sim.set_seed()
                sim.label = f"Sim {seed}"
                sims.append(sim)
            msim = cv.MultiSim(sims)
            msim.run(n_cpus=30)
           # msim.run(keep_people=keep_people)
            msim.reduce(quantiles=[0.10, 0.90])

            if save_sim:
                    msim.reduce(quantiles=[0.10, 0.90])
                    msim.save(f'{resfolder}/uk_sim_{scenname}.obj',keep_people=True)
                    #msim.save(f'{resfolder}/uk_sim_{scenname}.obj',keep_people=False)
            if do_plot:
                msim.reduce(quantiles=[0.10, 0.90])
                msim.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk_{scenname}_current.png',
                          legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=60, n_cols=2)

            print(f'... completed scenario: {scenname}')
            #sc.toc(T) 
    # Devel scenario
    elif whattorun == 'devel':
        s0 = make_sim(seed=1, beta=0.00748, end_day=data_end, verbose=0.1)
        s0.run()
        s0.plot(to_plot=to_plot)
        # s0.save('devel.sim', keep_people=True)

