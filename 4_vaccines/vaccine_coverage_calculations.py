import numpy as np
import covasim as cv

pop_size = 100e3
sim = cv.Sim(location='uk', pop_type='hybrid', pop_size=pop_size)
sim.initialize()

data = [
    [ 0, 12,  0,  0,  0],
    [12, 17, 10, 60, 90],
    [18, 40, 90, 70, 90],
    [40, 60, 90, 90, 90],
    [60, 99, 95, 95, 95],
]

data = np.array(data)

n_scens = data.shape[1]-2
results = np.zeros(n_scens)

for row in data:
    matches = (sim.people.age >= row[0]) * (sim.people.age < row[1])
    for i in range(n_scens):
        results[i] += sum(matches)*row[i+2]/100

print('Counts:')
for i in range(n_scens):
    print(f'Coverage for scenario {i+1}: {results[i]/pop_size*100:0.1f}%')
