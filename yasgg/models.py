#-*- coding: utf-8 -*-
import codecs
import sys
import os
import hashlib
import re
import markdown

from PIL import Image
from PIL.ExifTags import TAGS
from Crypto import Random
from Crypto.Cipher import AES
from slugify import slugify
from zipfile import ZipFile

from yasgg.settings import IMAGE_FILE_EXTENSIONS_2_IMPORT
from yasgg.utils import walkdir, ensure_dir

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
    ALBUM_INFO_FILE = 'info.md'

    # Visible meta data
    title = None
    slug = None
    basedir = None
    description = None
    thumbnail = None
    date_range = None  # TODO: Get date range from info file, else from exif data.

    # File handling
    import_dir = None
    photos_dir = None
    photos = {}
    zip_file = None
    assets_dir_name = 'assets'  # TODO: This should be non-relevant for the album, shouldn't it?

    # Crypto
    password = None
    password_hashed = None

    # Template
    html_file = None
    photos_for_tpl = []

    @property
    def assets_dir(self):
        return self.basedir + self.assets_dir_name + os.sep

    def __init__(self, import_dir):
        if os.path.exists(import_dir):
            self.import_dir = import_dir
        else:
            logger.error('The directory to import (%s) does not exist. No album creation is possible and I\'ve to exit' % import_dir)
            sys.exit(0)

        self.get_self_informed()

        ensure_dir(self.basedir)
        ensure_dir(self.photos_dir)

    def get_self_informed(self):
        """
        Collects all info an album can get from self.ALBUM_INFO_FILE as far as possible
        and fills the rest with fallback values.
        """

        # Look for the album info file.
        info_file = os.path.join(self.import_dir, self.ALBUM_INFO_FILE)
        if os.path.isfile(info_file):
            with codecs.open(info_file, "r", "utf-8") as f:
                text = f.read()
            md = markdown.Markdown(extensions=['meta'])
            html = md.convert(text)

            md_title = md.Meta.get('title', [''])[0]
            md_description = html
            md_thumbnail = md.Meta.get('thumbnail', [''])[0]
            md_date = md.Meta.get('date', [''])[0]
            md_password = md.Meta.get('password', [''])[0]

            # Set values from album info file
            if md_title:
                self.title = md_title
            if md_description:
                self.description = md_description
            if md_thumbnail:
                self.thumbnail = md_thumbnail
            if md_date:
                self.date_range = md_date
            if md_password:
                self.password = md_password

        # Fill with fallback values
        if not self.title:
            self.title = self.import_dir.split(os.sep).pop()

        # Create slug
        self.slug = slugify(self.title)

        # Set directories
        self.basedir = os.path.abspath('.%s%s' % (os.sep, self.slug)) + os.sep
        self.photos_dir = '%sphotos%s' % (self.basedir, os.sep)

        # Set template file
        self.html_file = '%sindex.html' % self.basedir

        # Build md5 hash of password to get len 32 key
        if self.password:
            self.password_hashed = hashlib.md5(self.password).hexdigest()

    def create_zipped_version(self):
        """
        Creates a zip of all self.photos if self is not encrypted and returns the relative path of the zip
        """

        if not self.password:
            zip_file_name = '%s%s.zip' % (self.photos_dir, self.slug)

            with ZipFile(zip_file_name, 'w') as album_zip:
                for file_name in self.photos.itervalues():
                    arc_name = file_name.split('/').pop()
                    album_zip.write(file_name, arcname=arc_name)

            # Make relative path
            self.zip_file = os.sep.join(zip_file_name.split(os.sep)[-2:])

    def import_photos(self):
        logger.info('Searching for photos in %s' % self.import_dir)
        self.photos = {}
        exif_date_for_all_photos = True
        for photo_2_import in walkdir(dir_2_walk=self.import_dir):
            extension = os.path.splitext(photo_2_import)[1][1:]
            if extension.lower() not in IMAGE_FILE_EXTENSIONS_2_IMPORT:
                continue
            photo = Photo(image_file_original=photo_2_import, album=self)
            exif_date = photo.exif_date
            if exif_date:
                self.photos[exif_date + photo_2_import] = photo_2_import
            else:
                exif_date_for_all_photos = False
                self.photos[photo_2_import] = photo_2_import

        # If there is not an exif date on all photos, use path instead
        if not exif_date_for_all_photos:
            for photo_key, photo_file in self.photos.items():
                del self.photos[photo_key]
                self.photos[photo_file] = photo_file

        for photo_key in sorted(self.photos.iterkeys()):
            logger.debug('Processing %s' % (photo_2_import))
            photo_2_import = self.photos[photo_key]
            photo = Photo(image_file_original=photo_2_import, album=self)

            # create thumbnail and main image
            thumbnail_data = photo.create_thumbnail()
            image_file_data = photo.provide()

            # make photo path relative
            thumbnail_data['thumbnail_file'] = os.sep.join(thumbnail_data['thumbnail_file'].split(os.sep)[-2:])
            image_file_data['file'] = os.sep.join(image_file_data['file'].split(os.sep)[-2:])

            # merge two data dicts into one
            tpl_photo_data = dict(thumbnail_data.items() + image_file_data.items())

            self.photos_for_tpl.append(tpl_photo_data)


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
