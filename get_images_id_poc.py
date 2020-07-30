import geopandas as gpd
import numpy as np
import pandas as pd
import requests


def get_api_key(filename):
    with open(filename) as f:
        key = f.read()
    return key


def load_europe():
    """
    Returns Geopandas DataFrame of European countries used in GeoGuesser
    """
    geo = pd.read_html('https://www.geoguessr.com/explorer')[0]
    eur, na = geo.loc[geo[0] == 'Europe'].index[0], \
        geo.loc[geo[0] == 'North America'].index[0]
    european = geo.iloc[eur + 1: na]  # index to only European countries
    european.columns = ['country']

    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    europe = world.loc[world.name.isin(european.country)]

    return europe


def sample_points(europe_df, country_name, n=5000):
    """
    Returns a random sample of lat, long coordinates within a country.
    The number of points returned will be less than n.
    """
    polygon = europe_df.loc[europe_df.name == country_name].geometry
    x_min, y_min, x_max, y_max = polygon.total_bounds
    # randomly sample N x,y (lat, long) points within the max rectangle bounds
    x_samp = np.random.uniform(x_min, x_max, size=n)
    y_samp = np.random.uniform(y_min, y_max, size=n)
    # convert numpy points to GeoSeries
    geo_points = gpd.GeoSeries(gpd.points_from_xy(x_samp, y_samp))
    # only keep those points within the country polygon union
    geo_points = geo_points[geo_points.within(polygon.unary_union)]
    # return list of (long, lat) as floats
    return [(point.x, point.y) for point in geo_points]


def get_valid_pano_ids(api_key, europe_df, country_name, n_valid):
    """
    Returns List of Lists of n_valid unique Geo Locations randomly sampled
    within a country
    """
    metadata = "https://maps.googleapis.com/maps/api/streetview/metadata"
    params = {
        "radius": 1000,
        "key": api_key,
    }
    country_list = []
    pano_ids = set()
    while len(pano_ids) < n_valid:
        points = sample_points(europe_df, country_name)
        for long, lat in points:
            if len(pano_ids) >= n_valid:
                return country_list
            params["location"] = f"{lat},{long}"
            r = requests.get(metadata, params=params)
            j = r.json()
            if j['status'] == 'OK':
                p_id = j['pano_id']
                if p_id not in pano_ids:
                    pano_ids.add(p_id)
                    geo_location = [country_name, j['location']['lat'],
                                    j['location']['lng'], p_id]
                    country_list.append(geo_location)
    return country_list


if __name__ == "__main__":
    GOOGLE_KEY = get_api_key('api/google_key.txt')

    europe_data = load_europe()

    full_list = []
    for country in ['Spain', 'France', 'Italy']:
        country_ids = get_valid_pano_ids(GOOGLE_KEY, europe_data, country, 1000)
        full_list.extend(country_ids)
        print(f"{country} done.")

    df = pd.DataFrame(full_list, columns=['Country', 'Latitude', 'Longitude',
                                          'Pano_Id'])
    df.to_csv('data/POC_metadata.csv', index=False)
