#!/usr/bin/env python
#
# The MIT License
# 
# Copyright (c) 2010 Kyle Conroy
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

# requires json module

import os
import sys
import json
import getopt
import urllib2, urllib
import re

from multiprocessing import Pool

# Need to remove this dependency 
try :
    from django.template.defaultfilters import slugify
except ImportError:
    slugify = standalone_slugify
    
def standalone_slugify(inStr):
    removelist = ["a", "an", "as", "at", "before", "but", "by", "for","from","is", "in", "into", "like", "of", "off", "on", "onto","per","since", "than", "the", "this", "that", "to", "up", "via","with"];
    for a in removelist:
        aslug = re.sub(r'\b'+a+r'\b','',inStr)
    aslug = re.sub('[^\w\s-]', '', aslug).strip().lower()
    aslug = re.sub('\s+', '-', aslug)
    return aslug

def usage():
    print """
    python scrapebook.py -t AUTH_TOKEN
    
    To get your authtoken, head over to http://developers.facebook.com/docs/api,
    click on the https://graph.facebook.com/me/photos link, and copy the auth
    token in the url to the command line
    """
    
def save_photo(url, filename, debug):
    if debug:
        print "Saving" + filename
    try:
        urllib.urlretrieve(url, filename)
    except urllib.HTTPError:
        print "Could not open url:%s" % url

class Scrapebook(object):
    
    def __init__(self):
        self.token = None
        self.debug = False
        self.base = "https://graph.facebook.com"
        self.pool = None
        
    def api_request(self, path, limit=10000):
        limit = 10000 #Too big? Nah.....
        url = "https://graph.facebook.com/%s?access_token=%s&limit=%d" % \
            (path, self.token, limit)
        try:
            data = urllib2.urlopen(url)
            data = json.loads(data.read())
        except urllib2.HTTPError:
            data = {}
            
        return data
            
        
        
    
    def setup(self):
        scrape_dir = os.path.join(os.curdir,"facebook")
    
        try:
            print "Creating facebook directory...."
            os.mkdir(scrape_dir)
        except OSError:
            # Folder already exists, continue on
            pass
            
        self.pool = Pool(processes=35)
    
    def scrape_photos(self):
        # Setup directory to store photos
        scrape_dir = os.path.join(os.curdir,"facebook")
        photos_dir = os.path.join(scrape_dir,"photos")
        me_dir = os.path.join(photos_dir,"me")
    
        for d in [photos_dir, me_dir]:
            try:
                print "Creating %s directory...." % d
                os.mkdir(d)
            except OSError:
                # Folder already exists, continue on
                pass
        
        graph = self.api_request("/me/photos")
        
        try: 
            ps = graph["data"]
        except:
            ps = []
    
        print "Downloading %d photos of you...." % len(ps)
    
        for i, photo in enumerate(ps):
            purl = photo["source"]
            filename = os.path.join(me_dir, "myself_%s.jpg" % i)
            self.pool.apply_async(save_photo, [purl, filename, self.debug])
            
        albums = self.api_request("/me/albums")
        
        try:
            albums = albums["data"]
        except:
            albums = []
        
        for album in albums:
            try:
                albumd = slugify(album["name"])
                album_dir = os.path.join(photos_dir,albumd)
                print "Creating %s directory...." % album_dir
                os.mkdir(album_dir)
            except OSError:
                # Folder already exists, continue on
                pass
            
            photos = self.api_request("/%s/photos" % album["id"])
            try:
                photos = photos["data"]
            except:
                photos = []
                
            for i, photo in enumerate(photos):
                purl = photo["source"]
                filename = os.path.join(album_dir, "%s_%d.jpg" % (albumd, i))
                self.pool.apply_async(save_photo, [purl, filename, self.debug])
        

        
    def run(self):
        self.setup()
        
        self.scrape_photos()
        
        self.pool.close()
        self.pool.join()
        
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:hd", ["token", "help", "debug"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if not len(opts):
        usage()
        sys.exit(2)
        
    scraper = Scrapebook()

    for o, a in opts:
        if o in ("-t", "--token"):
            scraper.token = a
        if o in ("-d"):
            scraper.debug = True
        else:
            usage()
            
    if scraper.token:
        scraper.run()


if __name__ == '__main__':
    main()

    