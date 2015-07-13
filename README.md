mapping-solar-flares
====================

Mapping Solar Flares

You can use this code to plot all the solar flares observed by the Solar Dynamics Observatory, which takes more data than any other NASA satellite in history, in a standard stereographic projection using D3.js. The Solar Dynamics Observatory takes about a terabyte and a half of data a day and has been running since April 2010. 

[Check out the visualization.](http://www.scientificamerican.com/article/mapping-solar-flares-interactive/)

To query for the list of flares observed by GOES, you can use the `get_goes_event_list` function in [SunPy](https://github.com/sunpy/sunpy/blob/stable/sunpy/instr/goes.py); to determine the corresponding latitude and Carrington longitude coordinates of the flux-weighted centroid of each NOAA active region, query the SDO database. A good example is in the `plot_swx_d3.ipynb` notebook in the [calculating-spaceweather-keywords repository](https://github.com/mbobra/calculating-spaceweather-keywords).
