# Tumbledee

A simple Tumblr download utility, can download Tumblr photo and text posts and likes from account.

Must have a Tumblr API key, see https://www.tumblr.com/docs/en/api/v2 for details. Replace place holder in ".credentials_example.json" with working API key and rename file to ".credentials.json".

## Requirements

Python 3 -interpreter, PIP-packagemanager. Developed with Python 3.8.0, should work with Python versions >= 3.6.

Libraries needed:

beautifulsoup4
requests

## Use instructions

Run in command window: python tumbledee.py

Use and command line options: python tumbledee.py -h

Content is downloaded into a subdirectory under current directory, subdirectory name is account given. Image files are stored with their unique Tumblr file name, text posts go into HTML files, post id as name. Reblogs downloaded can have both a text HTML file and an image file.

Verbosity option -v displays information about account url and subdirectory and logs download progress. Verbosity option -vv also displays Tumblr API response in idented beautified format.