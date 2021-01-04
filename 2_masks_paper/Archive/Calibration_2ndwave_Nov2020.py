import pandas as pd
import numpy as np
import pylab as pl
import sciris as sc
import covasim as cv
import optuna as op
#pl.switch_backend('agg')

def create_sim(x):

    beta = x[0]
    pop_infected = x[1]
    s_prob_sep = x[2]
    s_prob_oct = x[3]
    s_prob_nov = x[4]
    iso_vals1 = x[5]
    iso_vals2 = x[6]
    iso_vals3 = x[7]
    iso_vals4 = x[8]

    start_day = '2020-01-21'
    end_day   = '2020-12-07'
    data_path = 'UK_Covid_cases_december6.xlsx'

    # Set the parameters
    total_pop    = 67.86e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    asymp_factor = 2
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
        verbose      = 0.1,
    )

    # Create the baseline simulation
    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1 # ages 0-10
    sim['prognoses']['sus_ORs'][1] = 1 # ages 10-20
    sim['rel_severe_prob'] = 1.0
    sim['rel_crit_prob']  = 1.0 # Scale factor for proportion of severe cases that become critical
    sim['rel_death_prob']  = 1.0 # Scale factor for proportion of critical cases that result in death


    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day = sim.day('2020-06-01') #some schools reopen 1st June and start of enhanced TTI
    tti_day_july = sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sep = sim.day('2020-09-01')
    tti_day_oct = sim.day('2020-10-01')
    tti_day_nov = sim.day('2020-11-01')
    tti_day_dec = sim.day('2020-12-01')
    ti_day = sim.day('2020-12-07')


    beta_days = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-01', '2020-06-15', '2020-07-22', '2020-08-01', '2020-09-02', '2020-10-01', '2020-10-16', '2020-10-26', '2020-11-01', '2020-11-05', '2020-11-14', '2020-11-21', '2020-11-30', '2020-12-03']

    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.50, 1.50, 1.50, 1.29, 1.29]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.63, 0.63, 0.63, 0.63]
    #w_beta_changes =[14feb16march23marh30apr 5may  1june15june22july 1aug  2sep 1octoct16oct 26oct 1nov  5nov 14nov 21nov 30nov  dec03 
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40, 0.50, 0.50, 0.50, 0.50, 0.50, 0.40, 0.40, 0.40, 0.40, 0.60]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40, 0.60, 0.60, 0.60, 0.60, 0.60, 0.40, 0.40, 0.40, 0.40, 0.70]

    # Define the beta changes
    h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c')

    #next line to save the intervention
    interventions = [h_beta, w_beta, s_beta, c_beta]
    
    s_prob_march = 0.012
    s_prob_april = 0.017
    s_prob_may   = 0.02769
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769
    s_prob_sept = 0.05769
    s_prob_oct = 0.05769
    s_prob_nov = 0.05769
    t_delay       = 1.0

    #isolation until august
    iso_vals = [{k:0.1 for k in 'hswc'}]
    #isolation in august
    iso_vals1 = [{k:0.3 for k in 'hswc'}]
    #isolation in september
    iso_vals2 = [{k:0.4 for k in 'hswc'}]
    #isolation in october
    iso_vals3 = [{k:0.7 for k in 'hswc'}]
    #isolation in november
    iso_vals4 = [{k:0.7 for k in 'hswc'}]

    #tracing level at 42.35% in June; 47.22% in July, 44.4% in August and 49.6% in Septembre (until 16th Sep)
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_eff_august = 0.44
    t_eff_sep    = 0.50
    t_eff_oct    = 0.50
    t_eff_nov    = 0.60
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    t_probs_august = {k:t_eff_august for k in 'hwsc'}
    t_probs_sep = {k:t_eff_sep for k in 'hwsc'}
    t_probs_oct = {k:t_eff_oct for k in 'hwsc'}
    t_probs_nov = {k:t_eff_nov for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay,test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.0175, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.0175, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.0275, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_nov, test_delay=t_delay, test_sensitivity=0.97),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
        cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july, end_day=tti_day_august-1),
        cv.contact_tracing(trace_probs=t_probs_august, trace_time=trace_d_1, start_day=tti_day_august, end_day=tti_day_sep-1),
        cv.contact_tracing(trace_probs=t_probs_sep, trace_time=trace_d_1, start_day=tti_day_sep, end_day=tti_day_oct-1),
        cv.contact_tracing(trace_probs=t_probs_oct, trace_time=trace_d_1, start_day=tti_day_oct, end_day=tti_day_nov-1),
        cv.contact_tracing(trace_probs=t_probs_nov, trace_time=trace_d_1, start_day=tti_day_nov),
        cv.dynamic_pars({'iso_factor': {'days': tti_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_oct, 'vals': iso_vals3}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_nov, 'vals': iso_vals4}}),
        #cv.dynamic_pars({'rel_death_prob': {'days': tti_day_august, 'vals': 2.0}}),
        #cv.dynamic_pars({'rel_death_prob': {'days': [tti_day_july, tti_day_sep], 'vals': [0.5, 0.5]}}),
      ]

    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    return sim



def objective(x):
    ''' Define the objective function we are trying to minimize '''

    # Create and run the sim
    sim = create_sim(x)
    sim.run()
    fit = sim.compute_fit()

    return fit.mismatch


def get_bounds():
    ''' Set parameter starting points and bounds '''
    pdict = sc.objdict(
        beta              = dict(best=0.0071, lb=0.0067, ub=0.0073),
        pop_infected      = dict(best=1500,  lb=1400,   ub=1600),
        s_prob_sep        = dict(best=0.058,  lb=0.05,   ub=0.08),
        s_prob_oct        = dict(best=0.058,  lb=0.05,   ub=0.08),
        s_prob_nov        = dict(best=0.058,  lb=0.05,   ub=0.08),
        iso_vals1         = dict(best=0.2,  lb=0.01,   ub=0.03),
        iso_vals2         = dict(best=0.3,  lb=0.2,   ub=0.5),
        iso_vals3         = dict(best=0.4,  lb=0.3,   ub=0.7),
        iso_vals4         = dict(best=0.4,  lb=0.3,   ub=0.7),
        #rel_severe_prob   = dict(best=1.0,  lb=1.0,   ub=1.5),
        #rel_crit_prob     = dict(best=1.0,  lb=1.0,   ub=1.5),
        #rel_death_prob    = dict(best=1.0,  lb=0.5,   ub=1.0),
        
    )

    # Convert from dicts to arrays
    pars = sc.objdict()
    for key in ['best', 'lb', 'ub']:
        pars[key] = np.array([v[key] for v in pdict.values()])

    return pars, pdict.keys()


#%% Calibration

name      = 'covasim_uk_calibration'
storage   = f'sqlite:///{name}.db'
n_trials  = 50
n_workers = 4

pars, pkeys = get_bounds() # Get parameter guesses


def op_objective(trial):

    pars, pkeys = get_bounds() # Get parameter guesses
    x = np.zeros(len(pkeys))
    for k,key in enumerate(pkeys):
        x[k] = trial.suggest_uniform(key, pars.lb[k], pars.ub[k])

    return objective(x)


def worker():
    study = op.load_study(storage=storage, study_name=name)
    return study.optimize(op_objective, n_trials=n_trials)


def run_workers():
    return sc.parallelize(worker, n_workers)


def make_study():
    try: op.delete_study(storage=storage, study_name=name)
    except: pass
    return op.create_study(storage=storage, study_name=name)


def calibrate():
    ''' Perform the calibration '''
    make_study()
    run_workers()
    study = op.load_study(storage=storage, study_name=name)
    output = study.best_params
    return output, study


def savejson(study):
    dbname = 'calibrated_parameters_UK'

    sc.heading('Making results structure...')
    results = []
    failed_trials = []
    for trial in study.trials:
        data = {'index':trial.number, 'mismatch': trial.value}
        for key,val in trial.params.items():
            data[key] = val
        if data['mismatch'] is None:
            failed_trials.append(data['index'])
        else:
            results.append(data)
    print(f'Processed {len(study.trials)} trials; {len(failed_trials)} failed')

    sc.heading('Making data structure...')
    keys = ['index', 'mismatch'] + pkeys
    data = sc.objdict().make(keys=keys, vals=[])
    for i,r in enumerate(results):
        for key in keys:
            data[key].append(r[key])
    df = pd.DataFrame.from_dict(data)

    order = np.argsort(df['mismatch'])
    json = []
    for o in order:
        row = df.iloc[o,:].to_dict()
        rowdict = dict(index=row.pop('index'), mismatch=row.pop('mismatch'), pars={})
        for key,val in row.items():
            rowdict['pars'][key] = val
        json.append(rowdict)
    sc.savejson(f'{dbname}.json', json, indent=2)

    return


if __name__ == '__main__':

    do_save = True

    to_plot = ['cum_infections', 'new_infections', 'cum_tests', 'new_tests', 'cum_diagnoses', 'new_diagnoses', 'cum_deaths', 'new_deaths']

    # # Plot initial
    print('Running initial...')
    pars, pkeys = get_bounds() # Get parameter guesses
    sim = create_sim(pars.best)
    sim.run()
    sim.plot(to_plot=to_plot)
    #pl.gcf().axes[0].set_title('Initial parameter values')
    objective(pars.best)
    pl.pause(1.0) # Ensure it has time to render

    # Calibrate
    print('Starting calibration for {state}...')
    T = sc.tic()
    pars_calib, study = calibrate()
    sc.toc(T)

    # Plot result
    print('Plotting result...')
    sim = create_sim([pars_calib['beta'], pars_calib['pop_infected'], pars_calib['s_prob_sep'], pars_calib['s_prob_oct'], pars_calib['s_prob_nov'], pars_calib['iso_vals1'], pars_calib['iso_vals2'], pars_calib['iso_vals3'], pars_calib['iso_vals4']])
    sim.run()
    sim.plot(to_plot=to_plot)
    pl.gcf().axes[0].set_title('Calibrated parameter values')

    if do_save:
        savejson(study)


print('Done.')