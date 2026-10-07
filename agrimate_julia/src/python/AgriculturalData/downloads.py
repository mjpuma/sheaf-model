
from io import BytesIO
import os
import requests
from zipfile import ZipFile


def download(url, savedir, filename, force=False):
    file = savedir.joinpath(filename)
    if not force and file.exists():
        return
    os.makedirs(savedir, exist_ok=True)
    print(f"Downloading {url}")
    r = requests.get(url, stream=True)
    with open(file, 'wb') as f:
        f.write(r.content)


def download_und_unzip(url, savedir, filename, rename=True, force=False):
    file = savedir.joinpath(filename)
    if not force and file.exists():
        return
    os.makedirs(savedir, exist_ok=True)
    print(f"Downloading and unzipping {url}")
    r = requests.get(url, stream=True)
    zip_file = ZipFile(BytesIO(r.content))
    zipped_filename = zip_file.namelist()[0]
    zip_file.extractall(path=savedir)
    if rename:
        os.rename(savedir.joinpath(zipped_filename), file)
    