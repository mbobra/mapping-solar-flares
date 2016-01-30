"""
Purpose:   To query the from the GOES X-Ray flux database for a list of flaring active regions (along with their various parameters, such as flare class and peak time) and to query the SDO Joint Science Operations Center database for the latitude and longitude of each active region; this then creates a macro-list of flaring active regions with the following parameters: class, level, time, latitude, and longitude. The output .csv files can be used read by the flares.html file in this same directory to create a visualization of solar flares.

Inputs:    -- t_start: start time, e.g.: '2014/10/30 04:25'
           -- t_end: end time, e.g.: '2015/01/06 00:00'
           -- flare_class: minimum goes x-ray flux flare classification, e.g.: 'X1'
           -- ofile: output file to append to, e.g.: 'xflares.csv'

Usage:     This code depends on the numpy, scipy, pandas, urllib, and sunpy libraries.

Examples:  ipython:
           > %run get_the_flare_data.py --t_start='2014/10/01 00:00' --t_end='2015/01/06 00:00' --flare_class='X1' --ofile='xflares.csv'

           command line:
           > python get_the_flare_data.py --help
           > python get_the_flare_data.py --t_start='2014/10/01 00:00' --t_end='2015/01/06 00:00' --flare_class='X1' --ofile='xflares.csv'
           
Written:   Monica Bobra
           04 August 2015
           29 January 2016 -- modified to check for 'MISSING' keyword value
"""

import urllib, json, pandas as pd, numpy as np, argparse
from sunpy.time import TimeRange
import sunpy.instr.goes

t_start    = ''
t_end      = ''
    
parser = argparse.ArgumentParser(description='determine a flare level, classification, associated active region, and peak time from the GOES X-Ray flux database')
parser.add_argument('-a', '--t_start', type=str, help='start time, e.g.: 2014/10/30 04:25', required=True)
parser.add_argument('-b', '--t_end', type=str, help='end time, e.g.: 2015/06/06 00:00', required=True)
parser.add_argument('-c', '--flare_class', type=str, help='minimum goes x-ray flux flare classification, e.g.: X1', required=True)
parser.add_argument('-d', '--ofile', type=str, help='output file to append to, e.g.: xflares.csv [note: the only files that can be appended to are flares.csv or xflares.csv; appending to mflares with a flare_class of M1 or higher will also write X-flares into that file]', required=True)
parser._optionals.title = "flag arguments"
args = parser.parse_args()

t_start     = args.t_start
t_end       = args.t_end
flare_class = args.flare_class
ofile       = args.ofile

# query goes database
# n.b.: use a time range such that you can just append to the previous list
time_range = TimeRange(t_start,t_end)
listofresults = sunpy.instr.goes.get_goes_event_list(time_range, flare_class)
n_elements = len(listofresults)

# level
level = []
for i in range(n_elements):
    level.append(listofresults[i]['goes_class'][1:])

# classification
classification = []
for i in range(n_elements):
    classification.append(listofresults[i]['goes_class'][:1])

# change datetime object into jsoc_info readable:
t_rec = []
nice_time = []   
for i in range(n_elements):
    t_rec.append(listofresults[i]['peak_time'].strftime('%Y.%m.%d_%H:%m_TAI'))
    nice_time.append(listofresults[i]['peak_time'].strftime('%d %B %Y at %H:%M'))

# noaa active region number
ar = []
for i in range(n_elements):
    ar.append(str(listofresults[i]['noaa_active_region']))

# read http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt
# to transform noaa active region number to harpnum:
answer = pd.read_csv('http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt',sep=' ')

# open the output file:
f = open(ofile,"a")

f.write("class,level,time,latitude,longitude\n")

for i in range(len(listofresults)):
	print listofresults[i]['goes_class'],listofresults[i]['peak_time'],listofresults[i]['noaa_active_region']

for i in range(n_elements):
    # if there's no NOAA active region, quit
    if (str(ar[i]) == '0'):
        continue
    
    # match NOAA_ARS to HARPNUM
    idx = answer[answer['NOAA_ARS'].str.contains(str(ar[i]))]
	
    # if there's no HARPNUM, quit
    if (idx.empty == True):
        continue

    #construct jsoc_info queries and query jsoc database
    url = "http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info?ds=hmi.sharp_720s["+str(idx.HARPNUM.values[0])+"]["+str(t_rec[i])+"]&op=rs_list&key=LAT_FWT,LON_FWT,CRLN_OBS"
    response = urllib.urlopen(url)
    data = json.loads(response.read())

    # if there's no data at this time, quit
    if data['count'] == 0:
        continue

    # if there's missing keyword information, quit
    if ('MISSING' in str(data['keywords'])):
        continue

    # transform into carrington coordinates
    # LAT_FWT is keyword 0 and LON_FWT is keyword 1 and CRLN_OBS is keyword 3
    
    lat_fwt = float(data['keywords'][0]['values'][0])
    lon_fwt = float(data['keywords'][1]['values'][0])
    if lat_fwt > 1000:
        continue
    if lon_fwt > 1000:
        continue
    
    latitude = str(lat_fwt)
    longitude = str(np.mod(lon_fwt + float(data['keywords'][2]['values'][0]),360))
    
    print classification[i]+","+level[i]+","+nice_time[i]+","+longitude+","+latitude
    f.write(classification[i]+","+level[i]+","+nice_time[i]+","+longitude+","+latitude+"\n")

f.close()

__author__ = 'Monica Bobra'