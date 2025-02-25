.. _jointfitter:

JointFitter
===========

There are cases where one may wish to fit multiple datasets with models that
share parameters.  This is possible with the
`astropy.modeling.fitting.JointFitter`.  Basically, this fitter is
setup with a list of defined models, the parameters in common between the
different models, and the initial values for those parameters. Then the fitter
is called supplying as many x and y arrays, one for each model to be fit.  The
fit parameters are the result of the jointly fitting the models to the
combined datasets.

.. note::
   The JointFitter uses the scipy.optimize.leastsq.  In addition, it
   does not support fixed, bounded, or tied parameters at this time.

Example: Spectral Line
======================

This example is for two spectral segments with different spectral resolutions
that have the same spectral line in the wavelength region that is overlapping
between both segments.

We will need to define a Gaussian function that has mean wavelength, area, and
width parameters.  This is needed as the `astropy.modeling.functional_models.Gaussian1D`
function has mean wavelength, central intensity, and width parameters, but the
central intensity of a line will be different at different spectral resolutions,
but the area will be the same.

First, imports needed for this example

.. code-block:: python

   # imports
   import numpy as np
   import math
   import matplotlib.pyplot as plt
   from astropy.modeling import fitting, Fittable1DModel
   from astropy.modeling.parameters import Parameter
   from astropy.modeling.functional_models import FLOAT_EPSILON, GAUSSIAN_SIGMA_TO_FWHM

Now define AreaGaussian1D with area instead of intensity as a parameter.
This new is modified and trimmed version of the standard Gaussian1D model.

.. code-block:: python

   class AreaGaussian1D(Fittable1DModel):
       """
       One dimensional Gaussian model with area as a parameter.

       Parameters
       ----------
       area : float or `~astropy.units.Quantity`.
           Integrated area
           Note: amplitude = area / (stddev * np.sqrt(2 * np.pi))
       mean : float or `~astropy.units.Quantity`.
           Mean of the Gaussian.
       stddev : float or `~astropy.units.Quantity`.
           Standard deviation of the Gaussian with FWHM = 2 * stddev * np.sqrt(2 * np.log(2)).
       """

       area = Parameter(default=1)
       mean = Parameter(default=0)

       # Ensure stddev makes sense if its bounds are not explicitly set.
       # stddev must be non-zero and positive.
       stddev = Parameter(default=1, bounds=(FLOAT_EPSILON, None))

       def bounding_box(self, factor=5.5):
           """
           Tuple defining the default ``bounding_box`` limits,
           ``(x_low, x_high)``

           Parameters
           ----------
           factor : float
               The multiple of `stddev` used to define the limits.
               The default is 5.5, corresponding to a relative error < 1e-7.
           """

           x0 = self.mean
           dx = factor * self.stddev

           return (x0 - dx, x0 + dx)

       @staticmethod
       def evaluate(x, area, mean, stddev):
           """
           Gaussian1D model function.
           """
           return (area / (stddev * np.sqrt(2 * np.pi))) * np.exp(
               -0.5 * (x - mean) ** 2 / stddev ** 2
           )

       @property
       def input_units(self):
           if self.mean.unit is None:
               return None
           return {self.inputs[0]: self.mean.unit}

Data to be fit is simulated.  The 1st spectral segment will have a spectral
resolution that is a factor of 2 higher than the second segment.  The first
segment will have wavelengths from 1 to 6 and the second from 4 to 10 giving
an overlapping wavelength region from 4 to 6.

.. code-block:: python

   # Generate fake data
   mean = 5.1
   sigma1 = 0.2
   sigma2 = 0.4
   noise = 0.10

   # compute the central amplitudes so the lines in each segement have the
   # same area
   area = 1.5
   amp1 = area / np.sqrt(2.0 * math.pi * sigma1 ** 2)
   amp2 = area / np.sqrt(2.0 * math.pi * sigma2 ** 2)

   # segment 1
   np.random.seed(0)
   x1 = np.linspace(1.0, 6.0, 200)
   y1 = amp1 * np.exp(-0.5 * (x1 - mean) ** 2 / sigma1 ** 2)
   y1 += np.random.normal(0.0, noise, x1.shape)

   # segment 2
   np.random.seed(0)
   x2 = np.linspace(4.0, 10.0, 200)
   y2 = amp2 * np.exp(-0.5 * (x2 - mean) ** 2 / sigma2 ** 2)
   y2 += np.random.normal(0.0, noise, x2.shape)

Now define the models to be fit and fitter to use.  Then fit the two simulated
datasets.

.. code-block:: python

   # define the two models to be fit
   gjf1 = AreaGaussian1D(area=1.0, mean=5.0, stddev=1.0)
   gjf2 = AreaGaussian1D(area=1.0, mean=5.0, stddev=1.0)

   # define the jointfitter specifying the parameters in common and their initial values
   fit_joint = fitting.JointFitter(
       [gjf1, gjf2], {gjf1: ["area", "mean"], gjf2: ["area", "mean"]}, [1.0, 5.0]
   )

   # perform the fit
   g12 = fit_joint(x1, y1, x2, y2)


The resulting fit parameters show that the area and mean wavelength of the
two AreaGaussian1D models are exactly the same while the width (stddev) is
different reflecting the different spectral resolutions of the two segments.

.. code-block:: python

   print("AreaGaussian1 parameters")
   print(gjf1.param_names)
   print(gjf1.parameters)
   print("AreaGaussian2 parameters")
   print(gjf1.param_names)
   print(gjf2.parameters)

::

   AreaGaussian1 parameters
   ('area', 'mean', 'stddev')
   [1.48697226 5.09826068 0.19761087]
   AreaGaussian2 parameters
   ('area', 'mean', 'stddev')
   [1.48697226 5.09826068 0.4015368 ]


The simulated data and best fit models can be plotted showing good agreement
between the two AreaGaussian1D models and the two spectral segments.

.. code-block:: python

   # Plot the data with the best-fit models
   plt.figure(figsize=(8,5))
   plt.plot(x1, y1, 'bo', alpha=0.25)
   plt.plot(x2, y2, 'go', alpha=0.25)
   plt.plot(x1, gjf1(x1), 'b--', label='AreaGaussian1')
   plt.plot(x2, gjf2(x2), 'g--', label='AreaGaussian2')
   plt.xlabel('Wavelength')
   plt.ylabel('Flux')
   plt.legend(loc=2)

.. image:: example_spectal_segments_jointfitter.png
