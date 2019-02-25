"""
Author: Michael Katz guided by lal implimentation of PhenomD.
This was used in "Evaluating Black Hole Detectability with LISA" (arXiv:1508.07253),
as a part of the BOWIE package (https://github.com/mikekatz04/BOWIE). Please cite this paper
when using this code.

This code is licensed with the GNU public license.

This python code impliments circular PhenomD waveforms from Husa et al 2016 (arXiv:1508.07250)
and Khan et al 2016 (arXiv:1508.07253). It wraps the accompanying c code, `phenomd/phenomd.c`,
with ``ctypes``. `phenomd/phenomd.c` is mostly from LALsuite. See `phenomd/phenomd.c` for specifics.
Please cite these papers if circular waveforms are generated.

It also implements eccentric inpspiral waveforms according to Peters (1964).

"""

import ctypes
from astropy.cosmology import Planck15 as cosmo
import numpy as np
import os
import scipy.constants as ct
from scipy.special import jv  # bessel function of the first kind

from .csnr import csnr
from ..utils.sourcebase import SourceBase

M_sun = 1.989e30  # kg

class WaveformBase(SourceBase):

    def __init__(self, **kwargs):
        self.set_num_waveform_points()
        self.set_dist_type()
        self.not_broadcasted = True

        for key, item in kwargs.items():
            setattr(self, key, item)

    def set_num_waveform_points(self, num_wave_points=4096):
        """Number of log-spaced points for waveforms.

        The number of points of the waveforms with asymptotically increase
        the accuracy, but will lower the speed of generation.

        Args:
            num_wave_points (int): Number of log-spaced points for the waveforms.

        """
        self.num_points = num_wave_points
        return


class PhenomDWaveforms(WaveformBase):
    """Generate phenomd waveforms

    PhenomDWaveforms is a class that takes binary parameters as inputs, and adds
    characteristic strain waveforms as attributes to self.

    Keyword Arguments:
        dist_type (str, optional): Which type of distance is used. Default is 'redshift'.
            This is stored as an attributed.
        num_points (int, optional): Number of points to use in the waveform.
            The frequency points are log-spaced. Default is 8192. This is stored as an attributed.

    Attributes:
        freqs (1D or 2D array of floats): Frequencies corresponding to the waveforms.
            Shape is (num binaries, num_points) if 2D.
            Shape is (num_points,) if 1D for one binary.
        hc (1D or 2D array of floats): Characteristic strain of the waveforms.
            Shape is (num binaries, num_points) if 2D.
            Shape is (num_points,) if 1D for one binary.
        fmrg: (scalar float or 1D array of floats): Merger frequency of each binary separating
            inspiral from merger phase. (0.014/M) Shape is (num binaries,) if more than one binary.
        fpeak: (scalar float or 1D array of floats): Peak frequency of each binary separating
            merger from ringdown phase. (0.014/M) Shape is (num binaries,) if more than one binary.
        z (float or 1D array of floats): Redshift equivalent of the z_or_dist given.
        dist (float or 1D array of floats): Luminosity distance equivalent of the z_or_dist given.
        remove_axis (bool): Remove axis based on if it is one or more than one binary.
        length (int): Number of binaries.
        Note: All args from :meth:`gwsnrcalc.utils.pyphenomd.PhenomDWaveforms.__call__`
                are stored as attributes.
        Note: All kwargs from above are stored as attributes.

    Raises:
        ValueError: dist_type is not one of the three options.

    """

    def __init__(self, **kwargs):

        WaveformBase.__init__(self, **kwargs)
        self.set_distance_unit(dist_unit='Mpc')
        self.unit_out = 'Mpc'
        # get path to c code
        cfd = os.path.dirname(os.path.abspath(__file__))
        if 'phenomd.cpython-35m-darwin.so' in os.listdir(cfd):
            self.exec_call = cfd + '/phenomd.cpython-35m-darwin.so'

        else:
            self.exec_call = cfd + '/phenomd/phenomd.so'

        if self.dist_type not in ['redshift', 'luminosity_distance', 'comoving_distance']:
            raise ValueError("dist_type needs to be redshift, comoving_distance,"
                             + "or luminosity_distance")

    def _sanity_check(self):
        """Check if parameters are okay.

        Sanity check makes sure each parameter is within an allowable range.

        Raises:
            ValueError: Problem with a specific parameter.

        """
        if any(self.m1 < 0.0):
            raise ValueError("Mass 1 is negative.")
        if any(self.m2 < 0.0):
            raise ValueError("Mass 2 is negative.")

        if any(self.chi_1 < -1.0) or any(self.chi_1 > 1.0):
            raise ValueError("Chi 1 is outside [-1.0, 1.0].")

        if any(self.chi_2 < -1.0) or any(self.chi_2 > 1.0):
            raise ValueError("Chi 2 is outside [-1.0, 1.0].")

        if any(self.z <= 0.0):
            raise ValueError("Redshift is zero or negative.")

        if any(self.dist <= 0.0):
            raise ValueError("Distance is zero or negative.")

        if any(self.st < 0.0):
            raise ValueError("Start Time is negative.")

        if any(self.et < 0.0):
            raise ValueError("End Time is negative.")

        if len(np.where(self.st < self.et)[0]) != 0:
            raise ValueError("Start Time is less than End time.")

        if any(self.m1/self.m2 > 1.0000001e4) or any(self.m1/self.m2 < 9.999999e-5):
            raise ValueError("Mass Ratio too far from unity.")

        return

    def _create_waveforms(self):
        """Create frequency domain waveforms.

        Method to create waveforms for PhenomDWaveforms class.
        It adds waveform information in the form of attributes.

        """

        c_obj = ctypes.CDLL(self.exec_call)

        # prepare ctypes arrays
        freq_amp_cast = ctypes.c_double*self.num_points*self.length
        freqs = freq_amp_cast()
        hc = freq_amp_cast()

        fmrg_fpeak_cast = ctypes.c_double*self.length
        fmrg = fmrg_fpeak_cast()
        fpeak = fmrg_fpeak_cast()

        #import pdb; pdb.set_trace()

        # Find hc
        c_obj.Amplitude(ctypes.byref(freqs), ctypes.byref(hc), ctypes.byref(fmrg),
                        ctypes.byref(fpeak),
                        self.m1.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.m2.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.chi_1.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.chi_2.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.dist.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.z.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.st.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        self.et.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        ctypes.c_int(self.length), ctypes.c_int(self.num_points))

        # turn output into numpy arrays
        self.freqs, self.hc = np.squeeze(np.ctypeslib.as_array(freqs)), np.squeeze(np.ctypeslib.as_array(hc))
        self.fmrg, self.fpeak = np.squeeze(np.ctypeslib.as_array(fmrg)), np.squeeze(np.ctypeslib.as_array(fpeak))
        return

    def instantiate_parallel_func(self):
        return 'parallel_phenomd'

    def __call__(self, m1, m2, chi_1, chi_2, z_or_dist, st, et):
        """Run the waveform creator.

        Create phenomd waveforms in the amplitude frequency domain.

        **Warning**: Binary parameters have to one of three shapes: scalar, len-1 array,
        or array of len MAX. All scalar quantities or len-1 arrays are cast to len-MAX arrays.
        If arrays of different lengths (len>1) are given, a ValueError will be raised.

        Arguments:
            m1 (float or 1D array of floats): Mass 1 in Solar Masses. (>0.0)
            m2 (float or 1D array of floats): Mass 2 in Solar Masses. (>0.0)
            chi_1 (float or 1D array of floats): dimensionless spin of mass 1
                aligned to orbital angular momentum. Default is None (not 0.0). [-1.0, 1.0]
            chi_2 (float or 1D array of floats): dimensionless spin of mass 2
                aligned to orbital angular momentum. Default is None (not 0.0). [-1.0, 1.0]
            z_or_dist (float or 1D array of floats): Distance measure to the binary.
                This can take three forms: redshift (dimensionless, *default*),
                luminosity distance (Mpc), comoving_distance (Mpc).
                The type used must be specified in 'dist_type' parameter. (>0.0)
            st (float or 1D array of floats): Start time of waveform in years before
                end of the merger phase. This is determined using 1 PN order. (>0.0)
            et (float or 1D array of floats): End time of waveform in years before
                end of the merger phase. This is determined using 1 PN order. (>0.0)

        """
        self._check_if_broadcasted(locals())
        self._adjust_distances()
        self.length = len(self.m1)
        self._sanity_check()
        self._create_waveforms()
        return self


def parallel_phenomd(num, params, sources, signal_type,
                     noise_interpolants, prefactor, verbose):
    """SNR calulation with PhenomDWaveforms

    Generate PhenomDWaveforms and calculate their SNR against sensitivity curves.

    Args:
        num (int): Process number. If only a single process, num=0.
        binary_args (tuple): Binary arguments for
            :meth:`gwsnrcalc.utils.waveforms.EccentricBinaries.__call__`.
        phenomdwave (obj): Initialized class of
            :class:`gwsnrcalc.utils.waveforms.PhenomDWaveforms`.
        signal_type (list of str): List with types of SNR to calculate.
            Options are `all` for full wavefrom,
            `ins` for inspiral, `mrg` for merger, and/or `rd` for ringdown.
        noise_interpolants (dict): All the noise noise interpolants generated by
            :mod:`gwsnrcalc.utils.sensitivity`.
        prefactor (float): Prefactor to multiply SNR by (not SNR^2).
        verbose (int): Notify each time ``verbose`` processes finish. If -1, then no notification.

    Returns:
        (dict): Dictionary with the SNR output from the calculation.

    """

    wave = sources(*params)

    out_vals = {}

    for key in noise_interpolants:
        hn_vals = noise_interpolants[key](wave.freqs)
        snr_out = csnr(wave.freqs, wave.hc, hn_vals,
                       wave.fmrg, wave.fpeak, prefactor=prefactor)

        if len(signal_type) == 1:
            out_vals[key + '_' + signal_type[0]] = snr_out[signal_type[0]]
        else:
            for phase in signal_type:
                out_vals[key + '_' + phase] = snr_out[phase]
    if verbose > 0 and (num+1) % verbose == 0:
        print('Process ', (num+1), 'is finished.')

    return out_vals


class EccentricBinaries(WaveformBase):
    """Generate eccentric inspiral waveforms

    EccentricBinaries is a class that takes binary parameters as inputs, and adds
    characteristic strain waveforms as attributes to self.

    Keyword Arguments:
        dist_type (str, optional): Which type of distance is used. Default is 'redshift'.
            This is stored as an attributed.
        num_points (int, optional): Number of points to use in the waveform.
            The frequency points are log-spaced. Default is 8192. This is stored as an attributed.
        initial_cond_type (str, optional): Initial value representing the start of evolution.
            Options are `time`, `frequency`, or `separation`. Default is time.
        n_max (int, optional): Maximum number of higher order harmonics to analyze in the SNR.
            Default is 100.

    Attributes:
        freqs (1D or 2D array of floats): Frequencies corresponding to the waveforms.
            Shape is (num binaries, num_points) if 2D.
            Shape is (num_points,) if 1D for one binary.
        hc (1D or 2D array of floats): Characteristic strain of the waveforms.
            Shape is (num binaries, num_points) if 2D.
            Shape is (num_points,) if 1D for one binary.
        z (float or 1D array of floats): Redshift equivalent of the z_or_dist given.
        dist (float or 1D array of floats): Luminosity distance equivalent of the z_or_dist given.
        f0 (float, 1D array of floats, or None): Initial orbital frequencies.
            If ``initial_cond_type == 'frequency'``, initial values are stored here. Optional.
            Default is None.
        a0 (float, 1D array of floats, or None): Initial orbital semi-major axes.
            If ``initial_cond_type == 'separation'``, initial values are stored here. Optional.
            Default is None.
        t_start (float, 1D array of floats, or None): Initial times before merger.
            If ``initial_cond_type == 'time'``, initial values are stored here. Optional.
            Default is None.
        e_vals (2D array of floats): Eccentricity values over time.
        a_vals (2D array of floats): Semi-major axis values over time.
        t_vals (2D array of floats): Time values corresponding to e_vals and a_vals.
        freqs_orb (2D array of floats): Orbital frequencies over time.
        n (2D array of ints): Radiation mode values.
        ef (1D array of floats): Final eccentricity for each binary.
        remove_axis (bool): Remove axis based on if it is one or more than one binary.
        length (int): Number of binaries.
        Note: All args from :meth:`gwsnrcalc.utils.pyphenomd.PhenomDWaveforms.__call__`
                are stored as attributes.
        Note: All kwargs from above are stored as attributes.

    Raises:
        ValueError: dist_type is not one of the three options.
        ValueError: initial_cond_type is not one of the three options.

    """
    def __init__(self, **kwargs):
        WaveformBase.__init__(self, **kwargs)
        self.set_distance_unit(dist_unit='Mpc')
        self.unit_out = 'm'
        self.set_initial_cond_type()
        self.set_n_max()

    def set_initial_cond_type(self, initial_cond_type='time'):
        self.initial_cond_type = initial_cond_type
        if self.initial_cond_type not in ['frequency', 'time', 'separation']:
            raise ValueError("initial_cond_type must be either frequency, time, or separation.")
        return

    def set_n_max(self, n_max=20):
        """Maximium modes for eccentric signal.

        The number of modes to be considered when calculating the SNR for an
        eccentric signal. This will only matter when calculating eccentric signals.

        Args:
            n_max (int): Maximium modes for eccentric signal.

        """
        self.n_max = n_max
        return

    def _sanity_check(self):
        """Check if parameters are okay.

        Sanity check makes sure each parameter is within an allowable range.

        Raises:
            ValueError: Problem with a specific parameter.

        """
        if any(self.m1 < 0.0):
            raise ValueError("Mass 1 is negative.")
        if any(self.m2 < 0.0):
            raise ValueError("Mass 2 is negative.")

        if any(self.z <= 0.0):
            raise ValueError("Redshift is zero or negative.")

        if any(self.dist <= 0.0):
            raise ValueError("Distance is zero or negative.")

        if any(self.initial_point < 0.0):
            raise ValueError("initial_point is negative.")

        if any(self.t_obs < 0.0):
            raise ValueError("t_obs is negative.")

        if any(self.e0 <= 0.0):
            raise ValueError("e0 must be greater than zero when using EccentricBinaries class.")

        if any(self.e0 > 1.0):
            raise ValueError("e0 greater than 1.")

        return

    def instantiate_parallel_func(self):
        return 'parallel_ecc_snr_func'

    def _convert_units(self):
        """Convert units to geometrized units.

        Change to G=c=1 (geometrized) units for ease in calculations.

        """
        self.m1 = self.m1*M_sun*ct.G/ct.c**2
        self.m2 = self.m2*M_sun*ct.G/ct.c**2
        initial_cond_type_conversion = {
            'time': ct.c*ct.Julian_year,
            'frequency': 1./ct.c,
            'separation': ct.parsec,
        }

        self.initial_point = self.initial_point*initial_cond_type_conversion[self.initial_cond_type]

        self.t_obs = self.t_obs*ct.c*ct.Julian_year
        return

    def _find_integrand(self, e):
        """Integrand in Peters eq. 5.4

        """
        return e**(29./19.)*(1.+(121./304.)*e**2.)**(1181./2299.)/(1.-e**2)**(3./2.)

    def _f_e(self, e):
        """Integrand in Peters eq. 5.4

        """
        return e**(12./19.)*(1.+(121./304.)*e**2.)**(870./2299.)/(1.-e**2)

    def _c0_func(self, a0, e0):
        """Constant of integration from Peters 1964 equation 5.11.

        """
        return a0*(1.-e0**2)/e0**(12./19.) * (1.+(121./304.)*e0**2)**(-870./2299.)

    def _t_of_e(self, a0=None, t_start=None, f0=None, ef=None, t_obs=5.0):
        """Rearranged versions of Peters equations

        This function calculates the semi-major axis and eccentricity over time.

        """
        if ef is None:
            ef = np.ones_like(self.e0)*0.0000001

        beta = 64.0/5.0*self.m1*self.m2*(self.m1+self.m2)

        e_vals = np.asarray([np.linspace(ef[i], self.e0[i], self.num_points)
                            for i in range(len(self.e0))])
        integrand = self._find_integrand(e_vals)
        integral = np.asarray([np.trapz(integrand[:, i:], x=e_vals[:, i:])
                              for i in range(e_vals.shape[1])]).T

        if a0 is None and f0 is None:

            a0 = (19./12.*t_start*beta*1/integral[:, 0])**(1./4.) * self._f_e(e_vals[:, -1])

        elif a0 is None:
            a0 = ((self.m1 + self.m2)/self.f0**2)**(1./3.)

        c0 = self._c0_func(a0, self.e0)

        a_vals = c0[:, np.newaxis]*self._f_e(e_vals)

        delta_t = 12./19*c0[:, np.newaxis]**4/beta[:, np.newaxis]*integral

        return e_vals, a_vals, delta_t

    def _chirp_mass(self):
        """Chirp mass calculation

        """
        return (self.m1*self.m2)**(3./5.)/(self.m1+self.m2)**(1./5.)

    def _f_func(self):
        """Eq. 17 from Peters and Mathews 1963.

        """
        return ((1.+(73./24.)*self.e_vals**2.+(37./96.)
                * self.e_vals**4.)/(1.-self.e_vals**2.)**(7./2.))

    def _g_func(self):
        """Eq. 20 in Peters and Mathews 1963.

        """
        return (self.n**4./32.
                * ((jv(self.n-2., self.n*self.e_vals)
                   - 2. * self.e_vals*jv(self.n-1., self.n*self.e_vals)
                   + 2./self.n * jv(self.n, self.n*self.e_vals)
                   + 2.*self.e_vals*jv(self.n+1., self.n*self.e_vals)
                   - jv(self.n+2., self.n*self.e_vals))**2.
                   + (1.-self.e_vals**2.) * (jv(self.n-2., self.n*self.e_vals)
                   - 2.*jv(self.n, self.n*self.e_vals)
                   + jv(self.n+2., self.n*self.e_vals))**2.
                   + 4./(3.*self.n**2.)*(jv(self.n, self.n*self.e_vals))**2.))

    def _dEndfr(self):
        """Eq. 4 from Orazio and Samsing (2018)

        Takes f in rest frame.

        """
        Mc = self._chirp_mass()
        return (np.pi**(2./3.)*Mc**(5./3.)/(3.*(1.+self.z)**(1./3.)
                * (self.freqs_orb/(1.+self.z))**(1./3.))*(2./self.n)**(2./3.)
                * self._g_func()/self._f_func())

    def _hcn_func(self):
        """Eq. 56 from Barack and Cutler 2004

        """
        self.hc = 1./(np.pi*self.dist)*np.sqrt(2.*self._dEndfr())
        return

    def _create_waveforms(self):
        """Create the eccentric waveforms

        """

        # find eccentricity and semi major axis over time until e=0.
        e_vals, a_vals, t_vals = self._t_of_e(a0=self.a0, f0=self.f0,
                                              t_start=self.t_start, ef=None,
                                              t_obs=self.t_obs)

        f_mrg = 0.02/(self.m1 + self.m2)
        a_mrg = ((self.m1+self.m2)/f_mrg**2)**(1/3)

        # limit highest frequency to ISCO even though this is not innermost orbit for eccentric
        # binaries
        # find where binary goes farther than observation time or merger frequency limit.
        a_ind_start = np.asarray([np.where(a_vals[i] > a_mrg[i])[0][0] for i in range(len(a_vals))])
        t_ind_start = np.asarray([np.where(t_vals[i] < self.t_obs[i])[0][0]
                                 for i in range(len(t_vals))])

        ind_start = (a_ind_start*(a_ind_start >= t_ind_start)
                     + t_ind_start*(a_ind_start < t_ind_start))

        self.ef = np.asarray([e_vals[i][ind] for i, ind in enumerate(ind_start)])

        # higher resolution over the eccentricities seen during observation
        self.e_vals, self.a_vals, self.t_vals = self._t_of_e(a0=a_vals[:, -1],
                                                             ef=self.ef,
                                                             t_obs=self.t_obs)

        self.freqs_orb = np.sqrt((self.m1[:, np.newaxis]+self.m2[:, np.newaxis])/self.a_vals**3)

        # tile for efficient calculation across modes.
        for attr in ['e_vals', 'a_vals', 't_vals', 'freqs_orb']:
            arr = getattr(self, attr)
            new_arr = (np.flip(
                       np.tile(arr, self.n_max).reshape(len(arr)*self.n_max, len(arr[0])), -1))
            setattr(self, attr, new_arr)

        for attr in ['m1', 'm2', 'z', 'dist']:
            arr = getattr(self, attr)
            new_arr = np.repeat(arr, self.n_max)[:, np.newaxis]
            setattr(self, attr, new_arr)

        # setup modes
        self.n = np.tile(np.arange(1, self.n_max + 1), self.length)[:, np.newaxis]

        self._hcn_func()

        # reshape hc
        self.hc = self.hc.reshape(self.length, self.n_max, self.hc.shape[-1])
        self.freqs = np.reshape(self.n*self.freqs_orb/(1+self.z)
                                * ct.c,
                                (self.length, self.n_max, self.freqs_orb.shape[-1]))

        self.hc, self.freqs = np.squeeze(self.hc), np.squeeze(self.freqs)
        return

    def __call__(self, m1, m2, z_or_dist, initial_point, e0, t_obs):
        """Run the waveform creator.

        Create eccentric inspiral waveforms in the amplitude frequency domain.

        **Warning**: Binary parameters have to one of three shapes: scalar, len-1 array,
        or array of len MAX. All scalar quantities or len-1 arrays are cast to len-MAX arrays.
        If arrays of different lengths (len>1) are given, a ValueError will be raised.

        Arguments:
            m1 (float or 1D array of floats): Mass 1 in Solar Masses. (>0.0)
            m2 (float or 1D array of floats): Mass 2 in Solar Masses. (>0.0)
            z_or_dist (float or 1D array of floats): Distance measure to the binary.
                This can take three forms: redshift (dimensionless, *default*),
                luminosity distance (Mpc), comoving_distance (Mpc).
                The type used must be specified in 'dist_type' parameter. (>0.0)
            initial_point (float or 1D array of floats): Initial description point of binary.
                This can either be the start time, frequency, separation. This must be the same
                quantity as ``initial_cond_type``. (>0.0)
            e0 (float or 1D array of floats): Inital eccentricity of binary. (0<e<1)
            t_obs (float or 1D array of floats): Observation time of binary. (>0.0)

        """
        self._check_if_broadcasted(locals())

        self.f0 = None
        self.t_start = None
        self.a0 = None

        self._convert_units()

        initial_cond_set_attr = {
            'time': 't_start',
            'frequency': 'f0',
            'separation': 'a0'
        }

        setattr(self, initial_cond_set_attr[self.initial_cond_type], self.initial_point)

        self._adjust_distances()

        self.length = len(self.m1)
        self._sanity_check()
        self._create_waveforms()
        return self


def parallel_ecc_snr_func(num, params, sources, signal_type,
                          noise_interpolants, prefactor, verbose):
    """SNR calulation with eccentric waveforms

    Generate eccentric waveforms and calculate their SNR against sensitivity curves.

    Args:
        num (int): Process number. If only a single process, num=0.
        binary_args (tuple): Binary arguments for
            :meth:`gwsnrcalc.utils.waveforms.EccentricBinaries.__call__`.
        eccwave (obj): Initialized class of
            :class:`gwsnrcalc.utils.waveforms.EccentricBinaries`.
        signal_type (list of str): List with types of SNR to calculate.
            `all` for quadrature sum of modes or `modes` for SNR from each mode.
            This must be `all` if generating contour data with
            :mod:`gwsnrcalc.generate_contour_data`.
        noise_interpolants (dict): All the noise noise interpolants generated by
            :mod:`gwsnrcalc.utils.sensitivity`.
        prefactor (float): Prefactor to multiply SNR by (not SNR^2).
        verbose (int): Notify each time ``verbose`` processes finish. If -1, then no notification.

    Returns:
        (dict): Dictionary with the SNR output from the calculation.

    """
    wave = sources(*params)

    out_vals = {}

    for key in noise_interpolants:
        hn_vals = noise_interpolants[key](wave.freqs)
        integrand = 1./wave.freqs * (wave.hc**2/hn_vals**2)
        snr_squared_out = np.trapz(integrand, x=wave.freqs)

        if 'modes' in signal_type:
            out_vals[key + '_' + 'modes'] = prefactor*np.sqrt(snr_squared_out)

        if 'all' in signal_type:
            out_vals[key + '_' + 'all'] = prefactor*np.sqrt(np.sum(snr_squared_out, axis=-1))

    if verbose > 0 and (num+1) % verbose == 0:
        print('Process ', (num+1), 'is finished.')

    return out_vals
