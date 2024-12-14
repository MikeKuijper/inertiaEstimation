from lib import *
import lib

LOGFILES_ROOT = "input"
LOGFILE_PATH = "cyberzoo_test_the_second"
dirlist = ["device", "test"]

# window_length = 250
throw_offset = 300
default_filter_cutoff = 150

def calibrateFlywheel(LOGFILE_PATH, LOGFILES_ROOT = "input", dirlist = ["device", "test"], GROUNDTRUTH_PATH="", filter_cutoff=default_filter_cutoff, new_motor=False):
    print("==== CALIBRATING FLYWHEEL INERTIA ====")

    # if GROUNDTRUTH_PATH:
    #     sys.path.append(os.path.join(LOGFILES_ROOT, GROUNDTRUTH_PATH))
    # else:
    sys.path.append(os.path.join(LOGFILES_ROOT, LOGFILE_PATH, GROUNDTRUTH_PATH))

    Is = []
    xs = []
    for dir in dirlist:
        l_filtered_omegas = []
        l_omega_dots = []
        l_filtered_flywheel_omegas = []
        l_flywheel_omega_dots = []
        l_filtered_accelerations = []
        print(os.path.join(LOGFILE_PATH, dir))
        for (dirpath, dirnames, files) in os.walk(os.path.join(LOGFILES_ROOT, LOGFILE_PATH, dir)):
            for f in files:
                if ".py" in f:
                    continue
                df, omegas, accelerations, times, flywheel_omegas \
                    = importDatafile(os.path.join(LOGFILES_ROOT, LOGFILE_PATH, dir, f),
                                     new_motor=new_motor)

                # Prepare discrete filter coefficients
                filter_cutoff = 100
                dt = (times[-1] - times[0]) / len(times)
                lib.filter_coefs = recomputeFilterCoefficients(filter_cutoff, dt)

                # Apply filter to data
                # filtered_omegas = omegas
                # filtered_flywheel_omegas = flywheel_omegas
                lib.filter_coefs = recomputeFilterCoefficients(300, dt)
                filtered_omegas = filterVectorSignal(omegas)
                filtered_flywheel_omegas = filterVectorSignal(flywheel_omegas)

                lib.filter_coefs = recomputeFilterCoefficients(50, dt)
                filtered_accelerations = filterVectorSignal(accelerations)

                # Numerically differentiate filtered signals
                jerks = differentiateVectorSignal(filtered_accelerations, dt)
                omega_dots = differentiateVectorSignal(filtered_omegas, dt)
                flywheel_omega_dots = differentiateVectorSignal(filtered_flywheel_omegas, dt)

                lib.filter_coefs = recomputeFilterCoefficients(filter_cutoff, dt)
                omega_dots = filterVectorSignal(omega_dots)
                flywheel_omega_dots = filterVectorSignal(flywheel_omega_dots)

                # filtered_omegas = delaySavGolFilterVectorSignal(filtered_omegas)
                # filtered_flywheel_omegas = delaySavGolFilterVectorSignal(filtered_flywheel_omegas)

                # Find lengths of filtered values
                absolute_accelerations = np.sqrt(accelerations[:, 0] ** 2 +
                                                 accelerations[:, 1] ** 2 +
                                                 accelerations[:, 2] ** 2)
                absolute_omegas = np.sqrt(omegas[:, 0] ** 2 +
                                          omegas[:, 1] ** 2 +
                                          omegas[:, 2] ** 2)
                absolute_jerks = np.sqrt(jerks[:, 0] ** 2 +
                                         jerks[:, 1] ** 2 +
                                         jerks[:, 2] ** 2)

                starts, ends = detectThrow(times, absolute_omegas, absolute_accelerations, absolute_jerks, flywheel_omegas)

                # Set flywheel inertia
                lib.Jflywheel = 1

                if len(starts) == 0:
                    continue

                l_filtered_omegas.extend(filtered_omegas[starts[0] + throw_offset:-lib.WINDOW_LENGTH])
                l_omega_dots.extend(omega_dots[starts[0] + throw_offset:-lib.WINDOW_LENGTH])
                l_filtered_flywheel_omegas.extend(filtered_flywheel_omegas[starts[0] + throw_offset:-lib.WINDOW_LENGTH])
                l_flywheel_omega_dots.extend(flywheel_omega_dots[starts[0] + throw_offset:-lib.WINDOW_LENGTH])
                l_filtered_accelerations.extend(filtered_accelerations[starts[0] + throw_offset:-lib.WINDOW_LENGTH])
            # Compute inertia tensor with filtered data
            I, residuals = computeI(l_filtered_omegas,
                         l_omega_dots,
                         l_filtered_flywheel_omegas,
                         l_flywheel_omega_dots)
            x, resx = computeX(l_filtered_omegas,
                         l_omega_dots,
                         l_filtered_accelerations)
            Is.append(I)
            xs.append(x)
            break

    try:
        import calibration_groundtruth
    except ImportError:
        import groundtruth as calibration_groundtruth

    r = (calibration_groundtruth.m_dev / calibration_groundtruth.m_obj) * (xs[0] - xs[1])
    s = xs[0] - xs[1]

    translated_true_inertia = (calibration_groundtruth.trueInertia +
                               parallelAxisTheorem(calibration_groundtruth.m_obj, r) +
                               parallelAxisTheorem(calibration_groundtruth.m_dev, s))
    right_side_matrix = Is[1] - Is[0]

    left_side_vector = buildVector(translated_true_inertia)
    right_side_vector = buildVector(right_side_matrix)
    j = np.dot(right_side_vector, left_side_vector) / np.linalg.norm(right_side_vector) ** 2
    e = j * right_side_vector - left_side_vector

    # phi = np.linalg.lstsq(right_side_matrix, left_side_vector)

    print(f"\nOrthogonal projection flywheel inertia:  {j:.4e} kgm^2")
    print(f"OPF inertial error:                      {np.linalg.norm(e):.4e} kgm^2")

    print("\n== ERROR MATRIX ==")
    print(buildTensor(e))
    print("\n== GROUND TRUTH MATRIX ==")
    print(calibration_groundtruth.trueInertia)

    print("\n== RELATIVE ERROR PERCENTAGES ==")
    # Calibration error wrt true assumed inertia
    with np.errstate(divide='ignore'):
        print(f"{100 * buildTensor(e / buildVector(calibration_groundtruth.trueInertia))} %")
    print("\n== ESTIMATE INERTIAL AND ALIGNMENT ERROR ==")
    epsilon, psi = computeError(calibration_groundtruth.trueInertia + buildTensor(e), calibration_groundtruth.trueInertia)

    del calibration_groundtruth
    sys.path.remove(os.path.join(LOGFILES_ROOT, LOGFILE_PATH, GROUNDTRUTH_PATH))
    return j, epsilon, psi

if __name__=="__main__":
    calibrateFlywheel("cyberzoo_tests_the_second",
                                dirlist=["device", "calibration"],
                                GROUNDTRUTH_PATH="calibration",
                                new_motor=True)