import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg


class ResponseError(Exception):
    pass


def ComputeQSPResponse(
        adat,
        phiset,
        signal_operator="Wx",
        measurement=None):
    """
    Compute QSP response.

    Args:
        adat: array of inputs to the polynomial
        phiset: array of QSP phases
        signal_operator: QSP signal-dependent operation ['Wx', 'Wz']
        measurement: measurement basis (defaults to signal operator basis)

    Returns:
        Response object.
    """
    pdat = []

    if measurement is None:
        if signal_operator == "Wx":
            measurement = "x"
        elif signal_operator == "Wz":
            measurement = "z"

    # define model parameters
    model = (signal_operator, measurement)
    if signal_operator == "Wx":
        def sig_op(a): return np.array(
            [[a, 1j * np.sqrt(1 - a**2)],
             [1j * np.sqrt(1 - a**2), a]])

        def qsp_op(phi): return np.array(
            [[np.exp(1j*phi), 0.],
             [0., np.exp(-1j*phi)]])
    elif signal_operator == "Wz":
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)

        def sig_op(a): return H @ np.array(
            [[a, 1j * np.sqrt(1 - a**2)],
             [1j * np.sqrt(1 - a**2), a]]) @ H

        def qsp_op(phi): return H @ np.array(
            [[np.exp(1j*phi), 0.],
             [0., np.exp(-1j*phi)]]) @ H
    else:
        raise ResponseError(
            "Invalid signal_operator: {}".format(signal_operator)
        )

    if measurement == "x":
        p_state = np.array([[1.], [1.]]) / np.sqrt(2)
    elif measurement == "z":
        p_state = np.array([[1.], [0.]])
    else:
        raise ResponseError(
            "Invalid measurement: {}".format(measurement)
        )

    # Compute response
    pmats = []
    for phi in phiset:
        pmats.append(qsp_op(phi))

    for a in adat:
        W = sig_op(a)
        U = pmats[0]
        for pm in pmats[1:]:
            U = U @ W @ pm
        pdat.append((p_state.T @ U @ p_state)[0, 0])

    pdat = np.array(pdat, dtype=np.complex128)

    ret = {'adat': adat,
           'pdat': pdat,
           'model': model,
           'phiset': phiset,
           }
    return ret


def PlotQSPResponse(
        phiset,
        signal_operator="Wx",
        measurement=None,
        npts=100,
        pcoefs=None,
        target=None,
        show=True,
        title=None,
        plot_magnitude=False,
        plot_positive_only=False,
        plot_real_only=False,
        plot_tight_y=False):
    """
    Plot QSP response.

    Args:
        phiset: array of QSP phases
        signal_operator: QSP signal-dependent operation ['Wx', 'Wz']
        measurement: measurement basis (defaults to signal operator basis)
        npts: number of points to plot
        pcoefs: coefficients for expected polynomial response; will be plotted,
        if provided
        target: reference function, if provided
        show: call show function
        title: plot title, if provided
        plot_magnitude: if True, show magnitude instead of real and imaginary
            parts
        plot_positive_only: if True, then only show positive ordinate values
        plot_real_only: if Truw, show only real part
        plot_tight_y: if True, set y-axis scale to be from min to max of real
            part; else go from +1.5 max to -1.5 max

    Returns:
        Response object.
    """
    if plot_positive_only:
        adat = np.linspace(0., 1., npts)
    else:
        adat = np.linspace(-1., 1., npts)

    qspr = ComputeQSPResponse(adat,
                              phiset,
                              signal_operator=signal_operator,
                              measurement=measurement)
    pdat = qspr['pdat']

    plt.figure(figsize=[8, 5])

    if pcoefs is not None:
        poly = np.polynomial.Polynomial(pcoefs)
        expected = poly(adat)
        plt.plot(adat, expected, 'k-', label="target polynomial",
                 linewidth=3, alpha=0.5)

    if target is not None:
        L = np.max(np.abs(adat))
        xref = np.linspace(-L, L, 101)
        plt.plot(xref, target(xref), 'k--', label="target function",
                 linewidth=3, alpha=0.5)

    if plot_magnitude:
        plt.plot(adat, abs(pdat), 'r', label="abs[F(a)]")
    else:
        plt.plot(adat, np.real(pdat), 'k', label="Re[F(a)]")
        if not plot_real_only:
            plt.plot(adat, np.imag(pdat), 'b', label="Im[F(a)]")
    # plt.plot(adat, abs(pdat), 'k')

    # format plot
    plt.ylabel("response")
    plt.xlabel("a")
    plt.legend(loc="upper right")

    if title is not None:
        plt.title(title)

    ymax = np.max(np.abs(np.real(pdat)))
    ymin = np.min(np.abs(np.real(pdat)))
    plt.xlim([np.min(adat), np.max(adat)])
    if plot_tight_y:
        plt.ylim([1.05 * ymin, 1.05 * ymax])
    else:
        plt.ylim([-1.5 * ymax, 1.5 * ymax])

    if show:
        plt.show()


def PlotQSPPhases(phiset, show=True):
    """
    Generate plot of QSP response function polynomial, i.e. Re( <0| U |0> )
    For values of model, see ComputeQSPResponse.

    pcoefs - coefficients for expected polynomial response; will be plotted,
        if provided
    target - reference function, if provided
    """
    plt.figure(figsize=[8, 5])

    plt.stem(phiset, markerfmt='bo', basefmt='k-')
    plt.xlabel("k")
    plt.ylabel("phi_k")
    plt.ylim([-np.pi, np.pi])

    if show:
        plt.show()
