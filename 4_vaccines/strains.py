import covasim as cv
import numpy as np
import covasim.parameters as cvp
pars = {'use_waning': True, 'pop_infected': 100}
sim = cv.Sim(pars=pars)
#custom_strain = cv.strain(label='custom', strain=cvp.get_strain_pars()['b117'],
#                          days=np.arange(20, 21), n_imports=40)
#sim['strains'] += [custom_strain]

b117 = cv.strain('b117', days=np.arange(sim.day('2020-03-01'), sim.day('2020-03-10')), n_imports=100)
#im['strains'] += [b117]
    # Add B.1.1351 strain
b1351 = cv.strain('b1351', days=np.arange(sim.day('2020-04-05'), sim.day('2020-04-20')), n_imports=200)
#sim['strains'] += [b1351]
custom_strain = cv.strain(label='custom', strain = cvp.get_strain_pars()['b1351'],
                              days=np.arange(sim.day('2020-03-15'), sim.day('2020-03-30')), n_imports=40)
sim['strains'] += [b117, b1351, custom_strain]

sim.init_strains()
sim.init_immunity()
sim['immunity']
pre = {'wild': 0.0, 'b117': 0.0, 'b1351': 0.0, 'custom':1.0}
prior = {'wild': 0.0, 'b117': 0.0, 'b1351': 0.0, 'custom': 1.0}
cross_immunities = cvp.get_cross_immunity()
for k, v in sim['strain_map'].items():
    if v == 'custom':
        for j, j_lab in sim['strain_map'].items():
            sim['immunity'][k][j] = prior[j_lab]
            sim['immunity'][j][k] = pre[j_lab]
sim.run()
sim.plot('strains', do_save=True, do_show=False, fig_path=f'uk_strain.png')
#sim.plot('strains')