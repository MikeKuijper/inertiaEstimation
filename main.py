import sys

from lib import *
import lib
import os

for (dirpath, dirnames, filenames) in os.walk("input"):
    for f in filenames:
        print(f)
        df, omegas, accelerations, times, flywheel_omegas = importDatafile(f)

        # Prepare discrete filter coefficients
        filter_cutoff = 50
        dt = (times[-1] - times[0])/len(times)
        lib.filter_coefs = recomputeFilterCoefficients(filter_cutoff, dt)

        # Apply filter to data
        filtered_omegas = filterVectorSignal(omegas)
        filtered_flywheel_omegas = filterVectorSignal(flywheel_omegas)
        filtered_accelerations = filterVectorSignal(accelerations)

        # Numerically differentiate filtered signals
        jerks = differentiateVectorSignal(filtered_accelerations, dt)
        omega_dots = differentiateVectorSignal(filtered_omegas, dt)
        # omega_dots = filterVectorSignal(omega_dots)
        flywheel_omega_dots = differentiateVectorSignal(filtered_flywheel_omegas, dt)

        # Find lengths of filtered values
        absolute_accelerations = np.sqrt(accelerations[:,0] ** 2 +
                                         accelerations[:,1] ** 2 +
                                         accelerations[:,2] ** 2)
        absolute_omegas = np.sqrt(omegas[:,0] ** 2 +
                                  omegas[:,1] ** 2 +
                                  omegas[:,2] ** 2)
        absolute_jerks = np.sqrt(jerks[:,0] ** 2 +
                                 jerks[:,1] ** 2 +
                                 jerks[:,2] ** 2)

        # Initialise plot
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex="col", gridspec_kw={'height_ratios': [3, 1]})
        timePlotVector(times, omegas, ax=ax1, label="Angular velocity", ylabel="Angular velocity (rad/s)")
        timePlotVector(times, filtered_omegas, ax=ax1, label="Filtered angular velocity", alpha=0.5)
        # timePlotVector(times, omega_dots, ax=ax1, label="Angular acceleration", linestyle="dashed", alpha=0.7)
        # timePlotVector(times, flywheel_omega_dots, ax=ax2, label="Flywheel angular acceleration", linestyle="dashed", alpha=0.7)
        timePlotVector(times, -filtered_flywheel_omegas, ax=ax2, label="Filtered flywheel angular velocity", ylabel="Flywheel angular velocity (rad/s)")

        starts, ends = detectThrow(times, absolute_omegas, absolute_accelerations, absolute_jerks)
        ax1.axvline([times[starts[0]] * 1e3], linestyle="dashed", color="gray")

        if len(starts) == 0:
            plt.show()
            sys.exit()

        # Set flywheel inertia
        # lib.Jflywheel = 9.42e-8 # kg*m^2
        # lib.Jflywheel = 9.415e-08 # kg*m^2
        # lib.Jflywheel = 8.430e-08
        # lib.Jflywheel = 1.32905077e-07
        lib.Jflywheel = 9.909e-08 # kg*m^2

        # Compute inertia tensor with filtered data
        I = computeI(filtered_omegas[starts[0]:],
                     omega_dots[starts[0]:],
                     filtered_flywheel_omegas[starts[0]:],
                     flywheel_omega_dots[starts[0]:])
        print(I)

        simulation_omegas = simulateThrow(I,
                                          times[starts[0]:],
                                          filtered_omegas[starts[0]],
                                          filtered_flywheel_omegas[starts[0]:],
                                          flywheel_omega_dots[starts[0]:])
        timePlotVector(times[starts[0]+1:], simulation_omegas, label="Simulation fit", ax=ax1, linestyle="dashed", alpha=0.8)

        # formatTicks(100, 20)
        plt.tight_layout()
        plt.show()
    break