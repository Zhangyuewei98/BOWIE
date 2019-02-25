from builtins import object
import numpy

__all__ = ["PhotometricParameters"]

class LSSTDefaultPhotometricParameters(object):
    """
    This class will just contain a bunch of dict which store
    the default PhotometricParameters for LSST Bandpasses

    Users should not access this class (which is why it is
    not included in the __all__ declaration for this file).

    It is only used to initialize PhotometricParameters off of
    a bandpass name.
    """

    # Obviously, some of these parameters (effarea, gain, platescale,
    # darkcurrent, and readnoise) will not change as a function of bandpass;
    # we are just making them dicts here to be consistent with
    # everything else (and to make it possible for
    # PhotometricParameters to access them using the bandpass name
    # passed to its constructor)
    #
    # Note: all dicts contain an 'any' key which will be the default
    # value if an unknown bandpass is asked for
    #
    # 'any' values should be kept consistent with r band

    bandpassNames = ['u', 'g', 'r', 'i', 'z', 'y', 'any']

    def makeDict(value,
                 bandpassNames = ('u', 'g', 'r', 'i', 'z', 'y', 'any')):
        newdict = {}
        for f in bandpassNames:
            newdict[f] = value
        return newdict

    #Seeing see LSST page (arcseconds) (sigma in gaussian PSF)
    seeingSec = 0.7
    seeing = makeDict(seeingSec)

    # exposure time in seconds
    exptimeSec = 15.0
    exptime = makeDict(exptimeSec)

    # number of exposures
    nexpN = 2
    nexp = makeDict(nexpN)

    # effective area in cm^2
    effareaCm2 = numpy.pi * (6.423/2.*100)**2
    effarea = makeDict(effareaCm2)

    # electrons per ADU
    gainADU = 2.3
    gain = makeDict(gainADU)

    # electrons per pixel per exposure
    readnoiseE = 8.8
    readnoise = makeDict(readnoiseE)

    # electrons per pixel per second
    darkcurrentE = 0.2
    darkcurrent = makeDict(darkcurrentE)

    # electrons per pixel per exposure
    othernoiseE = 0.0
    othernoise = makeDict(othernoiseE)

    # arcseconds per pixel
    platescaleAS = 0.2
    platescale = makeDict(platescaleAS)

    # systematic squared error in magnitudes
    # see Table 14 of the SRD document
    # https://docushare.lsstcorp.org/docushare/dsweb/Get/LPM-17
    sigmaSys = {'u':0.0075, 'g':0.005, 'r':0.005, 'i':0.005, 'z':0.0075, 'y':0.0075,
                'any':0.005}

class SDSSDefaultPhotometricParameters(object):
    """
    https://www.sdss.org/instruments/camera/

    This class will just contain a bunch of dict which store
    the default PhotometricParameters for LSST Bandpasses

    Users should not access this class (which is why it is
    not included in the __all__ declaration for this file).

    It is only used to initialize PhotometricParameters off of
    a bandpass name.
    """

    # Obviously, some of these parameters (effarea, gain, platescale,
    # darkcurrent, and readnoise) will not change as a function of bandpass;
    # we are just making them dicts here to be consistent with
    # everything else (and to make it possible for
    # PhotometricParameters to access them using the bandpass name
    # passed to its constructor)
    #
    # Note: all dicts contain an 'any' key which will be the default
    # value if an unknown bandpass is asked for
    #
    # 'any' values should be kept consistent with r band

    bandpassNames = ['u', 'g', 'r', 'i', 'z', 'any']

    def makeDict(value,
                 bandpassNames = ('u', 'g', 'r', 'i', 'z', 'any')):
        newdict = {}
        for f in bandpassNames:
            newdict[f] = value
        return newdict

    # https://iopscience.iop.org/article/10.1086/300645/pdf
    seeingSec = 0.8
    seeing = makeDict(seeingSec)

    # exposure time in seconds
    exptimeSec = 54.0
    exptime = makeDict(exptimeSec)

    # number of exposures
    nexpN = 1
    nexp = makeDict(nexpN)

    # effective area in cm^2
    effareaCm2 = numpy.pi * (6.423/2.*100)**2
    effarea = makeDict(effareaCm2)

    # electrons per ADU
    # https://iopscience.iop.org/article/10.1086/300645/pdf
    gainADU = 1.0
    gain = makeDict(gainADU)

    # electrons per pixel per exposure
    readnoiseE = 5.0
    readnoise = makeDict(readnoiseE)

    # electrons per pixel per second
    # assume same as LSST ?? TODO: check this
    # https://iopscience.iop.org/article/10.1086/300645/pdf
    darkcurrentE = 0.5
    darkcurrent = makeDict(darkcurrentE)

    # electrons per pixel per exposure
    othernoiseE = 0.0
    othernoise = makeDict(othernoiseE)

    # arcseconds per pixel
    platescaleAS = 0.396
    platescale = makeDict(platescaleAS)

    # systematic squared error in magnitudes
    # see Table 14 of the SRD document
    # https://docushare.lsstcorp.org/docushare/dsweb/Get/LPM-17
    sigmaSys = {'u':0.0075, 'g':0.005, 'r':0.005, 'i':0.005, 'z':0.0075, 'y':0.0075,
                'any':0.005}


class PhotometricParameters(object):

    def __init__(self, telescope_name='LSST',
                 seeing=None,
                 exptime=None,
                 nexp=None,
                 effarea=None,
                 gain=None,
                 readnoise=None,
                 darkcurrent=None,
                 othernoise=None,
                 platescale=None,
                 sigmaSys=None,
                 bandpass=None):

        """
        @param [in] exptime exposure time in seconds (defaults to LSST value)

        @param [in] nexp number of exposures (defaults to LSST value)

        @param [in] effarea effective area in cm^2 (defaults to LSST value)

        @param [in] gain electrons per ADU (defaults to LSST value)

        @param [in] readnoise electrons per pixel per exposure (defaults to LSST value)

        @param [in] darkcurrent electons per pixel per second (defaults to LSST value)

        @param [in] othernoise electrons per pixel per exposure (defaults to LSST value)

        @param [in] platescale arcseconds per pixel (defaults to LSST value)

        @param [in] sigmaSys systematic error in magnitudes
        (defaults to LSST value)

        @param [in] bandpass is the name of the bandpass to which these parameters
        correspond.  If set to an LSST bandpass, the constructor will initialize
        PhotometricParameters to LSST default values for that bandpass, excepting
        any parameters that have been set by hand, i.e

        myPhotParams = PhotometricParameters(nexp=3, bandpass='u')

        will initialize a PhotometricParameters object to u bandpass defaults, except
        with 3 exposures instead of 2.

        If bandpass is left as None, other parameters will default to LSST r band
        values (except for those values set by hand).  The bandpass member variable
        of PhotometricParameters will, however, remain None.
        """

        # readnoise, darkcurrent and othernoise are measured in electrons.
        # This is taken from the specifications document LSE-30 on Docushare
        # Section 3.4.2.3 states that the total noise per pixel shall be 12.7 electrons per visit
        # which the defaults sum to (remember to multply darkcurrent by the number
        # of seconds in an exposure=15). [9 e- per 15 second exposure]

        self._seeing = None
        self._exptime = None
        self._nexp = None
        self._effarea = None
        self._gain = None
        self._platescale = None
        self._sigmaSys = None
        self._readnoise = None
        self._darkcurrent = None
        self._othernoise = None


        self._bandpass = bandpass
        try:
            defaults = globals()[telescope_name.upper() + 'DefaultPhotometricParameters']()
        except KeyError:
            pass

        if bandpass is None:
            bandpassKey = 'any'
            # This is so we do not set the self._bandpass member variable
            # without the user's explicit consent, but we can still access
            # default values from the PhotometricParameterDefaults
        else:
            bandpassKey = bandpass

        if bandpassKey in defaults.bandpassNames:
            self._seeing = defaults.seeing[bandpassKey]
            self._exptime = defaults.exptime[bandpassKey]
            self._nexp = defaults.nexp[bandpassKey]
            self._effarea = defaults.effarea[bandpassKey]
            self._gain = defaults.gain[bandpassKey]
            self._platescale = defaults.platescale[bandpassKey]
            self._sigmaSys = defaults.sigmaSys[bandpassKey]
            self._readnoise = defaults.readnoise[bandpassKey]
            self._darkcurrent = defaults.darkcurrent[bandpassKey]
            self._othernoise = defaults.othernoise[bandpassKey]

        if seeing is not None:
            self._seeing = seeing

        if exptime is not None:
            self._exptime = exptime

        if nexp is not None:
            self._nexp = nexp

        if effarea is not None:
            self._effarea = effarea

        if gain is not None:
            self._gain = gain

        if platescale is not None:
            self._platescale = platescale

        if sigmaSys is not None:
            self._sigmaSys = sigmaSys

        if readnoise is not None:
            self._readnoise = readnoise

        if darkcurrent is not None:
            self._darkcurrent = darkcurrent

        if othernoise is not None:
            self._othernoise = othernoise

        failureMessage = ''
        failureCt = 0

        if self._exptime is None:
            failureMessage += 'did not set exptime\n'
            failureCt += 1

        if self._nexp is None:
            failureMessage += 'did not set nexp\n'
            failureCt += 1

        if self._effarea is None:
            failureMessage += 'did not set effarea\n'
            failureCt += 1

        if self._gain is None:
            failureMessage += 'did not set gain\n'
            failureCt += 1

        if self._platescale is None:
            failureMessage += 'did not set platescale\n'
            failureCt +=1

        if self._sigmaSys is None:
            failureMessage += 'did not set sigmaSys\n'
            failureCt += 1

        if self._readnoise is None:
            failureMessage += 'did not set readnoise\n'
            failureCt += 1

        if self._darkcurrent is None:
            failureMessage += 'did not set darkcurrent\n'
            failureCt +=1

        if self._othernoise is None:
            failureMessage += 'did not set othernoise\n'
            failureCt += 1

        if failureCt>0:
            raise RuntimeError('In PhotometricParameters:\n%s' % failureMessage)



    @property
    def bandpass(self):
        """
        The name of the bandpass associated with these parameters (can be None)
        """
        return self._bandpass

    @bandpass.setter
    def bandpass(self, value):
        raise RuntimeError("You should not be setting bandpass on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")

    @property
    def seeing(self):
        """
        sigma of gaussian PSF
        """
        return self._seeing

    @property
    def exptime(self):
        """
        exposure time in seconds
        """
        return self._exptime

    @exptime.setter
    def exptime(self, value):
        raise RuntimeError("You should not be setting exptime on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def nexp(self):
        """
        number of exposures
        """
        return self._nexp

    @nexp.setter
    def nexp(self, value):
        raise RuntimeError("You should not be setting nexp on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def effarea(self):
        """
        effective area in cm^2
        """
        return self._effarea

    @effarea.setter
    def effarea(self, value):
        raise RuntimeError("You should not be setting effarea on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def gain(self):
        """
        electrons per ADU
        """
        return self._gain

    @gain.setter
    def gain(self, value):
        raise RuntimeError("You should not be setting gain on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def platescale(self):
        """
        arcseconds per pixel
        """
        return self._platescale

    @platescale.setter
    def platescale(self, value):
        raise RuntimeError("You should not be setting platescale on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def readnoise(self):
        """
        electrons per pixel per exposure
        """
        return self._readnoise

    @readnoise.setter
    def readnoise(self, value):
        raise RuntimeError("You should not be setting readnoise on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def darkcurrent(self):
        """
        electrons per pixel per second
        """
        return self._darkcurrent

    @darkcurrent.setter
    def darkcurrent(self, value):
        raise RuntimeError("You should not be setting darkcurrent on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def othernoise(self):
        """
        electrons per pixel per exposure
        """
        return self._othernoise

    @othernoise.setter
    def othernoise(self,value):
        raise RuntimeError("You should not be setting othernoise on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")


    @property
    def sigmaSys(self):
        """
        systematic error in magnitudes
        """
        return self._sigmaSys


    @sigmaSys.setter
    def sigmaSys(self, value):
        raise RuntimeError("You should not be setting sigmaSys on the fly; " +
                           "Just instantiate a new case of PhotometricParameters")
