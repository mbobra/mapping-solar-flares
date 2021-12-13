"""
Purpose:   To query the from the GOES X-Ray flux database for a list of flaring active regions (along with their various parameters, such as flare class and peak time) and to query the SDO Joint Science Operations Center database for the latitude and longitude of each active region; this then creates a macro-list of flaring active regions with the following parameters: class, level, time, latitude, and longitude. The output .csv files can be used read by the flares.html file in this same directory to create a visualization of solar flares.

Inputs:    -- t_start: start time, e.g.: '2014/10/30 04:25'
           -- t_end: end time, e.g.: '2015/01/06 00:00'
           -- flare_class: minimum goes x-ray flux flare classification, e.g.: 'X1'
           -- ofile: output file to append to, e.g.: 'xflares.csv'

Usage:     This code depends on the numpy, scipy, pandas, urllib, and sunpy (including sunkit-instruments) libraries.

Examples:  command line:
           > python get_the_flare_data.py --help
           > python get_the_flare_data.py --t_start='2014/05/01 00:00' --t_end='2019/06/01 00:00' --min_flare_class='X2.7' --max_flare_class='X9.1' --ofile='xflares.csv'
           
Author:   Monica Bobra

"""

import urllib, json, pandas as pd, numpy as np, argparse, requests
from sunpy.time import TimeRange
from sunkit_instruments.goes_xrs import get_goes_event_list

t_start    = ''
t_end      = ''
    
parser = argparse.ArgumentParser(description='determine a flare level, classification, associated active region, and peak time from the GOES X-Ray flux database')
parser.add_argument('-a', '--t_start', type=str, help='start time, e.g.: 2014/10/30 04:25', required=True)
parser.add_argument('-b', '--t_end', type=str, help='end time, e.g.: 2015/06/06 00:00', required=True)
parser.add_argument('-c', '--min_flare_class', type=str, help='minimum GOES X-Ray flux flare classification, e.g.: X2', required=True)
parser.add_argument('-d', '--max_flare_class', type=str, help='maximum GOES X-Ray flux flare classification, e.g.: X9', required=True)
parser.add_argument('-e', '--ofile', type=str, help='output file to append to', required=True)
parser._optionals.title = "flag arguments"
args = parser.parse_args()

t_start         = args.t_start
t_end           = args.t_end
min_flare_class = args.min_flare_class
max_flare_class = args.max_flare_class
ofile           = args.ofile

# query goes database
# n.b.: use a time range such that you can just append to the previous list
time_range = TimeRange(t_start,t_end)
listofresults = get_goes_event_list(time_range, min_flare_class)
n_elements = len(listofresults)

# recast and parse flare class and level input parameters
min_class_number = float(min_flare_class[1:])
max_class_number = float(max_flare_class[1:])
min_class_letter = min_flare_class[:1]
max_class_letter = max_flare_class[:1]

# create a scheme to quantitatively distinguish letter levels (C, M, X) 
if max_class_letter == 'X': max_class_power = 100
if max_class_letter == 'M': max_class_power = 10
if max_class_letter == 'C': max_class_power = 1
if min_class_letter == 'X': min_class_power = 100
if min_class_letter == 'M': min_class_power = 10
if min_class_letter == 'C': min_class_power = 1

# flare level
listofclasses_number = [float(item["goes_class"][1:]) for item in listofresults]
classes_number = np.array(listofclasses_number)

# flare class
listofclasses_letter = [item["goes_class"][:1] for item in listofresults]
listofclasses_letter_strings = listofclasses_letter.copy()

for i in range(len(listofclasses_letter)):
    if listofclasses_letter[i] == 'X': listofclasses_letter[i] = 100. 
    if listofclasses_letter[i] == 'M': listofclasses_letter[i] = 10.
    if listofclasses_letter[i] == 'C': listofclasses_letter[i] = 1.

classes_letter = np.array(listofclasses_letter)

# now mutiply classes_letter and classes_number to come up with a log scale
flare_classes = classes_number*classes_letter

# select the index of the values for flares in the range specified
ans = [i for i in range(len(flare_classes)) if flare_classes[i] >= min_class_number*min_class_power and flare_classes[i] <= max_class_number*max_class_power]
listofselections = [listofresults[i] for i in ans]

# level
level = [listofclasses_letter_strings[i] for i in ans]

# classification
classification = [listofclasses_number[i] for i in ans]

# times and noaa active region number
t_rec = []
nice_time = []
ar = []
for i in range(len(listofselections)):
    t_rec.append(listofselections[i]['peak_time'].strftime('%Y.%m.%d_%H:%M_TAI'))
    nice_time.append(listofselections[i]['peak_time'].strftime('%d %B %Y at %H:%M'))
    ar.append(str(listofselections[i]['noaa_active_region']))

# read http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt
# to transform noaa active region number to harpnum:
answer = pd.read_csv('http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt',sep=' ')

# open the output file:
f = open(ofile,"a")

f.write("class,level,time,latitude,longitude\n")

for i in range(len(listofselections)):
    print(listofselections[i]['goes_class'],listofselections[i]['peak_time'],listofselections[i]['noaa_active_region'])

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
    response = requests.get(url)
    data = response.json()

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
    
    # I am aware that round has funny properties but it is fine for the purposes of putting a large dot on a webpage
    latitude = str(round(lat_fwt,3))
    longitude = str(round((np.mod(lon_fwt + float(data['keywords'][2]['values'][0]),360)),3))
    
    print(level[i]+","+str(classification[i])+","+nice_time[i]+","+longitude+","+latitude)
    f.write(level[i]+","+str(classification[i])+","+nice_time[i]+","+longitude+","+latitude+"\n")

f.close()

__author__ = 'Monica Bobra'
