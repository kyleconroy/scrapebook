#!/usr/bin/env python
#
# The MIT License
#
# Copyright (c) 2010 Kyle Conroy
#
# (Python 3 compatability fixes made by Mark Nenadov)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys

PY3 = sys.version_info[0] == 3

import json
import logging
import multiprocessing
import os
import argparse
import urllib

if PY3:
    from urllib.request import urlretrieve
    from urllib.request import urlopen
    from urllib.error import HTTPError
    import urllib.parse as urlparse
else:
    from urllib import urlretrieve
    from urllib import urlopen
    from urllib2 import HTTPError
    from urlparse import urlparse

USER_FIELDS = [
    "first_name", "last_name", "gender", "username", "email",
    "about", "bio", "birthday", "education", "hometown", "sports",
    "relationship_status", "religion", "website", "work",
    ]

# Async Functions
def save_file(url, filename):
    """Save a photo.

    Args:
      url: The url of the photo
      filename: The filename of the new photo
    """
    logging.debug("Saving" + filename)
    try:
        urlretrieve(url, filename)
    except HTTPError:
        logging.error("Could not open url:%s" % url)


def save_note(note, filename):
    """Save a note

    Args:
      note: A note object from the Facebook Graph API
      filename: The path for the new note
    """
    logging.debug("Saving note %s" % filename)
    try:
        f = open(filename, 'w')
        f.write(note["subject"].encode('utf-8'))
        f.write("\n")
        f.write(note["message"].encode('utf-8'))
        f.close()
    except:
        logging.error("Could not save note %s" % filename)
        f.close()


class Scrapebook(object):
    """ Scrapebook downloads all your data from Facebook to your computer.

    Scrapebook connects to the Facebook Graph API.
    """

    def __init__(self, token, resources=None):
        """Create a new Scrape book object.

        Args:
          token: A long and unintelligible key for the Graph API
        """
        self.base = "https://graph.facebook.com"
        self.pool = multiprocessing.Pool(processes=35)
        self.token = token
        self.resources = resources or ["photos", "friends", "videos", "notes"]

    def _clean(self, s):
        """Returns a safe and clean filename for any given string

        Args:
          string: The string to be cleaned

        Returns:
          A cleaned strings, suitable for a filename
        """
        return "".join([x for x in s if x.isalpha() or x.isdigit()])

    def _create_dir(self, *args):
        """Create a directory inside the Facebook directory.

        Will not complain if the directory already exists.

        Args:
          Various directory names

        Returns:
          The path to the new directory
        """
        path = os.path.join(*args)
        path = os.path.join(os.curdir, path)

        if not os.path.isdir(path):
            logging.debug("Creating directory: %s" % path)
            os.mkdir(path)

        return path

    def api_request(self, path, limit=10000, params=None):
        """Perform a Facebook Graph API request and return the data.

        The returned JSON is parsed into native Python objects before being
        returned.

        Args:
          path: relative resource url
          limit: number of results to return. Default 10000

        Returns:
          A dictionary. If an error occured, the returned dictionary is empty
        """
        params = params or {}
        params["limit"] = 10000
        url = ("https://graph.facebook.com/%s?access_token=%s&%s" %
               (path, self.token, urllib.urlencode(params)))

        logging.debug(url)

        try:
            data = urlopen(url)
            if PY3:
                json_data = str(data.read(), 'utf-8')
            else:
                json_data = data.read()
            data = json.loads(json_data)
        except HTTPError:
            logging.error("Could not retreive %s" % url)
            data = {}

        if "error" in data:
            error = data["error"]
            logging.error("{}: {}".format(error["type"], error["message"]))
            data = {}

        return data

    def scrape_photos(self):
        """Scrape all tagged photos and uploaded albums"""
        photo_dir = self._create_dir("facebook", "photos")

        albums = self.api_request("/me/albums")

        if not albums:
            print "Error: Could not scrape photo data"
            return

        photo_albums = [("/%s/photos" % a["id"], a["name"])
                        for a in albums["data"]]
        photo_albums.append(("/me/photos", "me"))

        for album in photo_albums:
            url, name = album
            name = self._clean(name)

            album_dir = self._create_dir("facebook", "photos", name)

            photos = self.api_request(url)

            if not photos:
                print "Error: Could not download album"
                continue

            for i, photo in enumerate(photos["data"]):
                purl = photo["source"]
                filename = os.path.join(album_dir, "%s_%d.jpg" % (name, i))
                self.pool.apply_async(save_file, [purl, filename])

    def scrape_videos(self):
        """Scrape all tagged videos and uploaded videos"""
        videos_dir = self._create_dir("facebook", "videos")

        videos = self.api_request("/me/videos/uploaded")
        tags = self.api_request("/me/videos")

        if not videos or not tags:
            print "Error: Could not scrape your movies"
            return

        for video in videos["data"] + tags["data"]:
            name = self._clean(video["name"])
            fn, ext = os.path.splitext(urlparse(video["source"]).path)
            vurl = video["source"]
            filename = os.path.join(videos_dir, "%s%s" % (name, ext))
            self.pool.apply_async(save_file, [vurl, filename])

    def scrape_notes(self):
        """Scrape all notes a user composed or a user is tagged in."""
        notes_dir = self._create_dir("facebook", "notes")
        notes = self.api_request("/me/notes")

        if not notes:
            print "Error: Could not scrape your notes"
            return

        for n in notes["data"]:
            title = self._clean(n["subject"][:15])
            filename = os.path.join(notes_dir, "%s.txt" % title)
            self.pool.apply_async(save_note, [n, filename])

    def scrape_friends(self):
        """Scrape all friends. Stored in JSON objects"""
        friends_file = os.path.join("facebook", "friends.json")
        options = {"fields": ",".join(USER_FIELDS)}
        friends = self.api_request("/me/friends", params=options)

        if not friends:
            print "Error: Could not scrape your friends"
            return

        json.dump(friends["data"], open(friends_file, "w"))

    def run(self):
        self._create_dir("facebook")

        if "photos" in self.resources:
            self.scrape_photos()

        if "notes" in self.resources:
            self.scrape_notes()

        if "videos" in self.resources:
            self.scrape_videos()

        if "friends" in self.resources:
            self.scrape_friends()

        self.pool.close()
        self.pool.join()


def main():
    usage = ("To get your authtoken, head over to http://developers."
             "facebook.com/docs/api, click on the https://graph.facebook."
             "com/me/photos link, and copy the auth token in the url to "
             "the command line")

    parser = argparse.ArgumentParser(
        description="Facebook shouldn't own your soul")
    parser.add_argument("-t", "--token", dest="token", help=usage)
    parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                        help="Turn on debug information")
    parser.add_argument('resources', type=str, nargs='*',
                        default=None, help='resources to scrape')
    args = parser.parse_args()

    if not args.token:
        parser.error("option -t is required")

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    scraper = Scrapebook(args.token, resources=args.resources)
    scraper.run()


if __name__ == '__main__':
    main()
