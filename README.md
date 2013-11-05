YASGG
=====

**Yet Another Static Gallery Generator**

## Overview

YASGG is a static gallery generator with encryption support written in python.

If a password is chosen, the gallery generator encrypts the images with AES 256 bit.
On the browser side the decryption process is done by the chosen password in JavaScript.
As encrypted you can upload your gallery to any service that delivers static content like GitHub Pages, Amazon S3,
Dropbox, Google Drive and so on with no privacy concerns.

## Demo

* Link: http://nomnomnom.github.io/YASGG/demo/
* Password: 21f3a7f6373ccb42631b5671db4f5a5a60aed6dedf8e7b71d27e55288f41f6dc

## Features

* encryption (client side decryption of images)
* responsive default theme
* themeable

## Installation

### PyPI

    pip install yasgg
    yasggctl -h

### From source

    git clone git@github.com:nomnomnom/yasgg.git
    cd yasgg
    pip install -r requirements.txt
    yasgg/bin/yasggctl -h

## Example

The build command creates a new album in the current working directory.

    yasggctl build --recrusive 1 --photos-import-dir /tmp/photos_dir_2_import --album-name "YASGG demo album" -p 21f3a7f6373ccb42631b5671db4f5a5a60aed6dedf8e7b71d27e55288f41f6dc
    cd yasgg_demo_album
    yasggctl serve

## Usage

    Usage: yasggctl build -n <album-name> -i <photos-import-dir> [-t <theme>] [-p <password>] [-r <recrusive>]
           yasggctl serve [-o <port>] [-b <bind>]
           yasggctl [-h] [-v]


    Build command:
      Creates a new album in the current working directory.
      Example: yasggctl build --recrusive 1 --photos-import-dir ./tests/sample --album-name "foo bar" --theme default

      -n <ablum-name>, --album-name <album-name>                        Name of the new album.
      -i <photos-import-dir>, --photos-import-dir <photos-import-dir>   Directory of photos to import.
      -p <password>, --password <password>                              Use encryption of images. Use a _STRONG_ password!
      -r {0,1}, --recrusive                                             Search recrusive for photos into --photos-import-dir [default: 0]
      -t {default, galleria_classic}, --theme                           The theme to use. [default: default]


    Serve command:
      Serves a created album.
      Example: yasggctl serve -o 9000 -b 0.0.0.0

      -o <port>, --port <port>                                          Name of the new album. [default: 9000]
      -b <bind>, --bind <bind>                                          Address to run the test server on [default: 127.0.0.1]


    Global options:
      -h, --help                                                        Show this help message and exit.
      -v, --version                                                     Show program's version number and exit.

## License
[Beerware](https://raw.github.com/nomnomnom/yasgg/master/LICENSE)

## Contact
* [@x3_nom](https://twitter.com/x3_nom)
* nomnomnom [at] secure-mail.cc

---
Enjoy!
