import docker
import pandas as pd

from scripts.utils import strfdelta, bytes_to_hstring
from scripts.utils import strip_csv_from_md, csv_to_pd


def get_layers(image):
    df = pd.DataFrame(image.history()).convert_dtypes()
    df['CMD'] = df['CreatedBy']
    df['CMD'] = df['CMD'].str.replace('|', '', regex=False)
    df['CMD'] = df['CMD'].str.replace('/bin/bash -o pipefail -c', '', regex=False)
    df['CMD'] = df['CMD'].str.replace('#(nop)', '', regex=False)
    df['CMD'] = '`' + df['CMD'].str.strip() + '`'
    df['createdAt'] = pd.to_datetime(df['Created'], unit='s')
    df['hSize'] = df['Size'].apply(
        lambda x: bytes_to_hstring(x) if x > 100 else f'{x} B'
    )
    df['cumSize'] = df['Size'][::-1].cumsum()[::-1]
    df['hcumSize'] = df['cumSize'].apply(
        lambda x: bytes_to_hstring(x) if x > 100 else f'{x} B'
    )
    df_ordered = (
        df.loc[df['Tags'].notna()[::-1].cumsum()[::-1] > 0, :]
        .iloc[::-1, :]
        .reset_index(drop=True)
    )
    df_ordered['elapsed'] = df_ordered['createdAt'].diff()
    df_ordered.loc[1, 'elapsed'] = pd.Timedelta(0)
    df_ordered['elapsed'] = df_ordered['elapsed'].apply(strfdelta)
    return df_ordered


def get_layers_md_table(image, cli=docker.from_env()):
    layers = get_layers(cli.images.get(image))[['createdAt', 'CMD', 'hSize', 'hcumSize', 'elapsed', 'Tags']]
    layers.dropna(inplace=True)
    print(layers)
    return (layers.to_markdown())


def get_dependency(image):
    csv = strip_csv_from_md('wiki/Image Dependency.md')
    srs = csv_to_pd(csv)['dep']
    return srs[image]
