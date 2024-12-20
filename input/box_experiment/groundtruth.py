import numpy as np
import lib

# CONFIGURATION 01: light flywheel

m_dev = 0.073  # [kg]

grid = np.array([
    [1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1]
], dtype=bool)
m, _, trueInertia = lib.calcGridObject(grid)
m_obj = m

print(m)
print(trueInertia)
