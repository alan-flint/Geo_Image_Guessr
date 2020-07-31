import os, sys
import pandas as pd
import requests
from PIL import Image
from io import BytesIO


def get_api_key(filename):
    with open(filename) as f:
        key = f.read()
    return key


def load_metadata(filename):
    df = pd.read_csv(filename)
    return df


def download_panos(api, meta_df):
    """
    Retrieve and save streetview panoramas for a specific country
    """

    country = meta_df.Country.iloc[0]  # will all be the same, take first
    dir_name = os.getcwd()
    path = '/data/images/' + country + '/'
    if not os.path.exists(dir_name + path):
        os.makedirs(dir_name + path)

    img_url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": '300x200',
        "key": api,
    }

    filenames = []
    for i in range(len(meta_df)):  # iterate through all rows of meta DF
        path_ = path + f"{i:04d}" + '/'
        os.makedirs(dir_name + path_)
        id = meta_df.Pano_Id.iloc[i]
        for degree, direction in [(0, 'N'), (90, 'E'), (180, 'S'), (270, 'W')]:
            params['pano'] = id
            params['heading'] = degree
            r = requests.get(img_url, params, stream=True)
            img = Image.open(BytesIO(r.content))
            img.save(dir_name + path_ + direction + '.jpg')
        filenames.append(path_)

    return filenames


if __name__ == "__main__":
    GOOGLE_KEY = get_api_key('api/google_key.txt')
    meta = load_metadata('data/POC_metadata.csv')

    all_files = []
    for country in meta.Country.unique():
        sub_meta = meta.loc[meta.Country == country]
        files = download_panos(GOOGLE_KEY, sub_meta)
        all_files += files
        print(f"{country} done.")

    meta['Path'] = all_files
    meta.to_csv('data/POC_imagedata.csv')




