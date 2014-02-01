#-*- coding: utf-8 -*-
import hashlib
import os
import re

from PIL import Image
from PIL.ExifTags import TAGS
from Crypto import Random
from Crypto.Cipher import AES

from .crypto import AESCipher
from . import logger


class Theme(object):
    name = None
    basedir = None
    template = None

    def __init__(self, name):
        self.name = name

        # set and check for tpl dir
        self.basedir = '%s%sthemes%s%s%s' % (
            os.path.dirname(os.path.abspath(__file__)), os.sep, os.sep, self.name, os.sep)
        if not os.path.exists(self.basedir):
            logger.error('Theme %s (%s) does not exist.' % (self.name, self.basedir))
            exit(1)
        else:
            logger.info('Using theme %s (%s).' % (self.name, self.basedir))

        # set and check template.html in tpl dir
        self.template = '%sindex.html' % (self.basedir)
        if not os.path.exists(self.template):
            logger.error('Template file %s does not exist.' % (self.template))
            exit(1)
        else:
            logger.debug('Using template file %s.' % (self.template))


class Album(object):
    basedir = None
    photos_dir = None
    assets_dir_name = 'assets'
    html_file = None
    password = None
    password_hashed = None

    @property
    def assets_dir(self):
        return self.basedir + self.assets_dir_name + os.sep

    def __init__(self, basedir, password=None):
        self.basedir = basedir
        self.photos_dir = '%sphotos%s' % (self.basedir, os.sep)
        if not os.path.exists(self.photos_dir):
            os.mkdir(self.photos_dir)
        if not os.path.exists(self.assets_dir):
            os.mkdir(self.assets_dir)

        self.html_file = '%sindex.html' % (self.basedir)
        self.password = password

        if self.password:
            # md5 hash password to get len 32 key
            self.password_hashed = hashlib.md5(self.password).hexdigest()


class Photo(object):
    image_file_original = None
    album = None
    thumbnail_file = None
    image_file = None

    def __init__(self, image_file_original, album):
        self.image_file_original = image_file_original
        self.album = album

        image_file_splitted = os.path.splitext(self.image_file_original)
        self.thumbnail_file = '%s%s%s%s' % (
            self.album.photos_dir, os.path.basename(image_file_splitted[0]), '_thumb', image_file_splitted[1])

        self.image_file = '%s%s' % (
            self.album.photos_dir, os.path.basename(self.image_file_original))

    @property
    def exif_date(self):
        """Get date from exif data"""
        exif_data = {}
        try:
            image = Image.open(self.image_file_original)
            raw = image._getexif()
            for tag, value in raw.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
        except AttributeError:
            return None

        date_taken = None
        if 'DateTimeOriginal' in exif_data.keys():
            exif_date = re.sub(r':', '-', exif_data['DateTimeOriginal'], count=2)
            if exif_date:
                date_taken = '%s+01:00' % exif_date
        return date_taken

    @property
    def basename(self):
        """Returns the image file name"""
        return os.path.basename(self.image_file_original)

    @classmethod
    def __encrypt(cls, file_2_encrypt, album):
        header_item_bytes = 40
        iv = Random.new().read(AES.block_size)
        encryptor = AESCipher(album.password_hashed, iv)

        with open(file_2_encrypt, 'rb') as infile:
            file_content = infile.read()
            file_sha1 = hashlib.sha1(file_content.encode('hex')).hexdigest()

            file_encrypted = '%s.enc' % (file_2_encrypt)
            with open(file_encrypted, 'wb') as outfile:
                # header
                out = '1'.rjust(header_item_bytes)  # yasgg enc file version info
                out += file_sha1.rjust(header_item_bytes)  # 40 byte sha1 checksum of original file
                out += iv.encode('hex').rjust(header_item_bytes)  # 16 byte initialization vector

                # write file content hex encoded because ajax calls can not fetch binary data
                out += encryptor.encrypt(file_content).encode('hex')
                outfile.write(out)

                return file_encrypted

    def create_thumbnail(self):
        """ Takes an image, resizes the longest size to thumbnail_size and crops the middle. """

        logger.info('Creating thumbnail %s' % (self.thumbnail_file))

        thumbnail_size = 600

        img = Image.open(self.image_file_original)
        img_ratio = img.size[0] / float(img.size[1])

        if img_ratio < 1:  # Portrait (crop vertical middle)
            img = img.resize((thumbnail_size, int(round(thumbnail_size * img.size[1] / img.size[0]))), Image.ANTIALIAS)
            box = (0, int(round((img.size[1] - thumbnail_size) / 2)), img.size[0], int(round((img.size[1] + thumbnail_size) / 2)))
            img = img.crop(box)
        elif img_ratio > 1:  # Landscape (crop horizontal middle)
            img = img.resize((int(round(thumbnail_size * img.size[0] / img.size[1])), thumbnail_size), Image.ANTIALIAS)
            box = (int(round((img.size[0] - thumbnail_size) / 2)), 0, int(round((img.size[0] + thumbnail_size) / 2)), img.size[1])
            img = img.crop(box)
        else:  # Square (doesn't need to be cropped)
            img = img.resize((thumbnail_size, thumbnail_size), Image.ANTIALIAS)

        if img.format == 'JPEG':
            quality = 'keep'
        else:
            quality = 100
        img.save(self.thumbnail_file, 'jpeg', quality=quality, optimize=True, progressive=True)

        # Encrypt if requested
        if self.album.password:
            thumbnail_file = Photo.__encrypt(file_2_encrypt=self.thumbnail_file, album=self.album)
            os.unlink(self.thumbnail_file)
        else:
            thumbnail_file = self.thumbnail_file

        return {
            'thumbnail_file': thumbnail_file
        }

    def provide(self):
        logger.info('Providing image as %s' % (self.image_file))

        img = Image.open(self.image_file_original)
        img.thumbnail([1920, 1080], Image.ANTIALIAS)
        if img.format == 'JPEG':
            quality = 'keep'
        else:
            quality = 100
        img.save(self.image_file, 'jpeg', quality=quality, optimize=True, progressive=True)
        size = img.size

        # encrypt if requested
        if self.album.password:
            photo_file = Photo.__encrypt(file_2_encrypt=self.image_file, album=self.album)
            os.unlink(self.image_file)
        else:
            photo_file = self.image_file

        return {
            'file': photo_file,
            'width': size[0],
            'height': size[1]
        }
