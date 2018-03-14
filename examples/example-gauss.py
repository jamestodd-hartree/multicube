"""
A working example script:
* generates a spectral FITS cube
* makes a guess grid based on given parameter ranges
* makes best guess calculatons and goodness-of-fit estimates
"""
import numpy as np
import matplotlib.pylab as plt
import pyspeckit
from multicube.subcube import SubCube
from multicube.astro_toolbox import make_test_cube
from multicube.astro_toolbox import get_ncores

# TODO: rewrite into a jupyter notebook example!

# generating a dummy FITS file
make_test_cube((300, 10, 10), outfile='foo.fits', sigma=(10, 5))
sc = SubCube('foo.fits')

# TODO: move this to astro_toolbox.py
#       as a general synthetic cube generator routine
# let's tinker with the cube a bit!
# this will introduce a radial velocity gradient:
def tinker_ppv(arr):
    scale_roll = 15
    rel_shift = 30
    rel_str = 5
    shifted_component = np.roll(arr, rel_shift) / rel_str
    for y, x in np.ndindex(arr.shape[1:]):
        roll = np.sqrt((x - 5)**2 + (y - 5)**2) * scale_roll
        arr[:, y, x] = np.roll(arr[:, y, x], int(roll))
    return arr + shifted_component
sc.cube = tinker_ppv(sc.cube)

sc.update_model('gaussian')

minpars = [0.1, sc.xarr.min().value, 0.1]
maxpars = [2.0, sc.xarr.max().value, 2.0]
finesse = 10

#print "Estimating SNR . . ."
sc.get_snr_map()

print("Making a guess grid based on parameter permutations . . .")
sc.make_guess_grid(minpars, maxpars, finesse)
print("Generating spectral models for all {}"
      " guesses . . .".format(sc.guess_grid.shape[0]))
sc.generate_model()
print("Calculating the best guess on the grid . . .")
sc.best_guess()

sc1, sc2 = sc, sc.copy()

# fitting the whole cube with a single guess, selected
# to be the best among all the pixels
sc1.fiteach(fittype = sc1.fittype,
            guesses = sc1.best_overall,
            multicore = get_ncores(),
            errmap = sc1._rms_map,
            **sc1.fiteach_args)

# computing chi^2 statistics to judge the goodness of fit:
sc1.get_chi_squared(sigma=sc1.header['RMSLVL'])
sc1.chi_squared_stats(plot_chisq=True)

# let's plot the velocity field:
sc1.show_fit_param(1, cmap='coolwarm')
clb = sc1.mapplot.FITSFigure.colorbar
clb.set_axis_label_text(sc1.xarr.unit.to_string('latex_inline'))

# and overlay the pixels that didn't converge properly:
sc1.mark_bad_fits(cut = 1e-40) # not so good at the edges, right?
# (the velocity centroid varies too much across the map)

# now let's pass fiteach the best guesses for every x,y pixel!
sc2.fiteach(fittype = sc2.fittype,
            guesses = sc2.best_guesses,
            multicore = get_ncores(),
            errmap = sc2._rms_map,
            **sc2.fiteach_args)

# computing chi^2 statistics to judge the goodness of fit:
sc2.get_chi_squared(sigma=sc2.header['RMSLVL'], refresh=True)
sc2.chi_squared_stats()

sc2.show_fit_param(1, cmap='coolwarm')
clb = sc2.mapplot.FITSFigure.colorbar
clb.set_axis_label_text(sc2.xarr.unit.to_string('latex_inline'))

# and overlay the pixels that didn't converge properly:
sc2.mark_bad_fits(cut = 1e-40) # voila! all the pixels are fit!
plt.show()
