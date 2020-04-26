'''
Adapted frrom how_many_tests/sim_apr23.py
'''
​
import sciris as sc
import covasim as cv
​
cv.check_version('0.28.6')
​
do_save   = 1
version   = 'v1'
date      = '2020apr24'
folder    = f'.'
file_path = f'{folder}/perfect_{version}' # Completed below
​
​
# Set the parameters
​
quar_eff = 0.0
quar_effs = {k:quar_eff for k in 'hwsc'}
​
pars = dict(
    pop_size = 20e3,
    n_days = 600,
    pop_infected = 10,
    pop_type = 'synthpops',
    beta = 0.015,
    rel_symp_prob = 0.5,
    quar_eff=quar_effs,
    )
​
​
ttq_day = 20
​
# testing to drive suppression
s_prob = 1.0
a_prob = 0.0
q_prob = 1.0
t_delay = 0
extra_tests = cv.test_prob(symp_prob=s_prob,
                            asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                            start_day=ttq_day, test_delay=t_delay)
​
# immediate isolation
d_eff = 0.0
isolation = cv.dynamic_pars({'diag_factor': {'days': ttq_day, 'vals': d_eff}})
​
# immediate home quarantine
t_eff = 1.0
t_time = 0
t_probs = {k:t_eff for k in 'hwsc'}
t_times = {k:t_time for k in 'hwsc'}
ttq = cv.contact_tracing(trace_probs=t_probs, trace_time=t_times, start_day=ttq_day)
​
pars['interventions'] = [extra_tests, isolation, ttq]
​
​
sim = cv.Sim(pars)
​
to_plot = sc.dcp(cv.default_sim_plots)
to_plot['Total counts'] += ['n_quarantined']
to_plot['Daily counts'] += ['new_tests']
to_plot['Daily counts'] += ['new_quarantined']
sim.update_pars(pars)
sim.run()
fig = sim.plot(to_plot=to_plot)
​
if do_save:
    fig.savefig(f'{file_path}.png')