# -*- coding: utf-8 -*-
"""
Created on Sat Jun 19 15:03:36 2021

@author: vostok
"""
import requests
import json
import pandas as pd

# {'C', 'CTR', 'D', 'GP', 'P', 'Q', 'R', 'RMZ', 'W'}

def get_geojson(url):
    r = requests.get(url)
    return json.loads(r.text)

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

def fir_to_series(fir_json):
    coordinates = fir_json['features'][0]['geometry']['coordinates'][0][0]
    
    row = pd.Series({'name': 'FIR',
                     'openair_AC': 'C',
                     'freq': '',
                     'upper': 'FL 660',
                     'lower': 'FL 95', 
                     'callsign': '',
                     'airspaceclass': 'C',
                     'coordinates': coordinates})
    
    return row

def get_gliding_area_freq(area_name, aerodromes_json):
    
    area_name = area_name.split()[-1]
    
    if area_name == 'PAHKAJÄRVI':
        search_name = 'selänpää'
    elif area_name == 'VESIVEHMAA':
        search_name = 'lahti-vesivehmaa'
    else:
        search_name = area_name.lower()
    
    ad_names = [af['properties']['name'].lower() for af in aerodromes_json['features']]
    
    ad_inds = [ind for ind, name in enumerate(ad_names) if search_name in name]
    
    if not ad_inds:
        return ''
    
    return aerodromes_json['features'][ad_inds[0]]['properties']['comFreq']

def append_gliding_freqs(df, aerodromes_json):
    for ind, row in df.iterrows():
        if row.openair_AC == 'W':
            freq = get_gliding_area_freq(row['name'], aerodromes_json)
            df.loc[ind, 'freq'] = freq
    return df
    

def gliding_areas(df, aerodromes):
    for ind, row in df[df.openair_AC == 'W'].iterrows():
        # print(row['name'])
        pass
    
    D_names = list(df[df.openair_AC == 'W']['name'].str.split().apply(lambda x: x[-1]).unique())
    
    aerodrome_names = [af['properties']['name'].split()[-1] for af in aerodromes['features']]
    
    for dn in D_names:
        print(dn, get_gliding_area_freq(dn, aerodromes))
        
        
        # try:
            # print(dn, '-', aerodrome_names_lower.index(dn.lower()))
        # except:
            # print(dn, '-')
        
    print()
    
    # for an in aerodrome_names:
        # print(an.lower())
    
    # for aerodrome_feature in aerodromes['features']:
        # print(aerodrome_feature['properties']['name'])

airspaces_json = get_geojson('https://aviamaps.com/api/airspaces.geojson')
fir_json = get_geojson('https://aviamaps.com/api/finland.geojson')
aerodromes_json = get_geojson('https://aviamaps.com/api/aerodromes.geojson')


df = features_properties_coordinates_combine(airspaces_json['features'])
df = df.append(fir_to_series(fir_json), ignore_index=True)

df = append_gliding_freqs(df, aerodromes_json)

# openair_string = df_to_openair(df[df.openair_AC.isin(['W'])])
openair_string = df_to_openair(df)




# gliding_areas(df, aerodromes_json)



from pathlib import Path
Path(r'C:\Users\vostok\Documents\XCSoarData\openair.txt').write_text(openair_string)

# old_openair = requests.get('http://vostok.kapsi.fi/xcsoar/PIK_ilmatila_2018-05-24.txt').text