import covasim as cv
import numpy as np
import covasim.parameters as cvp
pars = {'use_waning': True, 'pop_infected': 40}
sim = cv.Sim(pars=pars)
custom_strain = cv.strain(label='custom', strain=cvp.get_strain_pars()['b117'],
                          days=np.arange(20, 21), n_imports=40)
sim['strains'] += [custom_strain]
sim.init_strains()
sim.init_immunity()
sim['immunity']
pre = {'wild': 0.5, 'b117': 0.8, 'b1351': 0.8, 'custom':1.0}
prior = {'wild': 0.0, 'b117': 0.0, 'b1351': 0.0, 'custom': 1.0}
cross_immunities = cvp.get_cross_immunity()
for k, v in sim['strain_map'].items():
    if v == 'custom':
        for j, j_lab in sim['strain_map'].items():
            sim['immunity'][k][j] = prior[j_lab]
            sim['immunity'][j][k] = pre[j_lab]
sim.run()
sim.plot('strains')