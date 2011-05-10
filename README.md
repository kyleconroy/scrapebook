# Scrapebook - Because Facebook shouldn't own your soul

Scrapebook uses Facebook's Graph API to download all your data from Facebook to your personal computer. Currently, the script downloads:

* Photos
* Notes
* Videos
* Limited Friend Information

Events are next

### Limitations

Due to Facebook's policies, I cannot download your friend's email addresses, instant messaging usernames, or physical addresses. If you want this to change, please send a complaint to Facebook.

### Requirements

Python **2.7 or 3.2** which can be found here: <http://www.python.org/download/>

### Usage

Since the Graph API uses OAuth 2.0, this script requires an extra step. Log into Facebook and head over to <http://developers.facebook.com/docs/api>. Click on the "Photos: http://graph.facebook.com/me/photos" link, and copy the access_token variable from the address bar. Simply pass this value into the script as shown

    python scrapebook.py -t "AUTH_TOKEN"

and all your data will be downloaded into a folder titled "facebook" in the current directory

Note: The quotes around the access token are very important

**LONG LIVE DATA LIBERATION**


