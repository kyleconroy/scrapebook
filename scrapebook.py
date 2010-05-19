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
from multiprocessing import Pool

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:h", ["token", "help"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
        
    if not len(opts):
        usage()
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-t", "--token"):
            token = a
            scrape_photos(token)
        else:
            usage()

def usage():
    print """
    python scrapebook.py -t AUTH_TOKEN
    
    To get your authtoken, head over to http://developers.facebook.com/docs/api,
    click on the https://graph.facebook.com/me/photos link, and copy the auth
    token in the url to the command line
    """
    
def save_photo(url, filename):
    print "Saving" + filename
    try:
        urllib.urlretrieve(url, filename)
    except urllib.HTTPError:
        print "Could not open url:%s" % url 
    
def scrape_photos(token):
    # Setup directory to store photos
    scrape_dir = os.path.join(os.curdir,"facebook")
    
    try:
        os.mkdir(scrape_dir)
    except OSError:
        # Folder already exists, continue on
        pass
    
    limit = 10000 #Too big? Nah.....
    url = "http://graph.facebook.com/me/photos?access_token=%s&limit=%d" % \
        (token, limit)
    try:
        data = urllib2.urlopen(url)
    except urllib2.HTTPError:
        print "Please check to make sure you have properly copied over your auth token and put it in quotes"
        sys.exit(1);
        
    graph = json.loads(data.read())
    
    pool = Pool(processes=25)
    
    for i, photo in enumerate(graph["data"]):
        purl = photo["source"]
        filename = os.path.join(scrape_dir, "facebook_%s.jpg" % i)
        pool.apply_async(save_photo, [purl, filename])
        
    pool.close()
    pool.join()
        


if __name__ == '__main__':
    main()

    