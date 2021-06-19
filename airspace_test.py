# -*- coding: utf-8 -*-
"""
Created on Sat Jun 19 15:03:36 2021

@author: vostok
"""
import requests
import json
import pandas as pd

# {'C', 'CTR', 'D', 'GP', 'P', 'Q', 'R', 'RMZ', 'W'}

def get_openair_AC(feature):
    
    if 'CTR' in feature['name']:
        return 'CTR'
    
    if feature.airspaceclass == 'C':
        return 'C'
    
    if feature.airspaceclass == 'D':
        return 'D'
    
    if feature['name'] == 'ADIZ':
        return 'GP'
    
    try:
        if 'gliding' in feature.activitytype.lower():
            return 'W'
    except AttributeError:
        pass
    
    if feature.airspaceclass == 'Danger':
        return 'Q'
    
    if feature.airspaceclass == 'Restricted':
        return 'R'
    
    if feature.airspaceclass == 'Prohibited':
        return 'P'
    
    if 'FIZ' in feature['name']:
        return 'RMZ'

def AR_string(freq, callsign):
    if not len(freq):
        return ''

    parts = freq.split(' ')
    
    try: 
        parts.remove('119.700')
    except ValueError:
        pass
    
    try: 
        parts.remove('121.500')
        parts.remove('(EMERG)')
    except ValueError:
        pass
    
    parts.insert(1, callsign)
    
    return f'AR {" ".join(parts)} \n'

def deg_to_dms(deg):
    m, s = divmod(deg*3600, 60)
    d, m = divmod(m, 60)
    
    return f'{d:02.0f}:{m:02.0f}:{s:02.0f}'

def polygon_to_DP(coordinates):
    s = ""
    
    for c in coordinates:
        lon, lat = c
        
        s += f'DP {deg_to_dms(lat)} N {deg_to_dms(lon)} E\n'
    
    return s

def feature_to_openair(f):
    s = ""
    
    try:
        AC = f.openair_AC
    except KeyError:
        AC = get_openair_AC(f)
    
    
    s += f'''AC {AC}
AN {f["name"]}
AL {f.lower}
AH {f.upper}\n'''

    s += AR_string(f.freq, f.callsign)
    
    s += polygon_to_DP(f.coordinates)
    
    return s

def features_properties_coordinates_combine(features):
    feat_props = []
    for feature in features:
        d = feature['properties'].copy()
        d['coordinates'] = feature['geometry']['coordinates'][0]
        
        feat_props.append(d)
        
    # feat_props = [feature['properties'] for feature in features]
    
    df = pd.DataFrame(feat_props)
    
    df['openair_AC'] = df.apply(get_openair_AC, axis=1)
    
    df = df[~df.openair_AC.isnull()]

    return df
def df_to_openair(df):
    s = ""
    
    for ind, row in df.iterrows():
        s += feature_to_openair(row) + '\n'
    
    return s
    

r = requests.get(r'https://aviamaps.com/api/airspaces.geojson')

s = r.text
j = json.loads(s)

df = features_properties_coordinates_combine(j['features'])

s = df_to_openair(df[df.openair_AC.isin(['W'])])

from pathlib import Path
Path(r'C:\Users\vostok\Documents\XCSoarData\openair.txt').write_text(s)

# old_openair = requests.get('http://vostok.kapsi.fi/xcsoar/PIK_ilmatila_2018-05-24.txt').text