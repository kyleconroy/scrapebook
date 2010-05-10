# Scrapebook - Because Facebook shouldn't own your soul

Scrapebook uses Facebook's Graph API to download all your data from Facebook to your personal computer. Currently, the script only downloads photos, but I may add support for notes and statuses in the future. 

### Requirements

Python 2.6

### Usage

Since the Graph API uses OAuth 2.0, this script requires an extra step. Log into Facebook and head over to <http://developers.facebook.com/docs/api>. Click on the "Photos: http://graph.facebook.com/me/photos" link, and copy the access_token variable from the address bar. Simply pass this value into the script as shown 

    python scrapebook.py -t AUTH_TOKEN
    
and all your data will be downloaded into a folder titled "facebook" in the current directory

**LONG LIVE DATA LIBERATION**


