import requests
from bs4 import BeautifulSoup as bs
import os
import json
import logging
import argparse
import sys

CREDENTIALS_FILE='.credentials.json'
# max 50 posts should be requested at one time
MAX_NUMBER_OF_POSTS = 50
TOTAL_MAX_NUMBER_OF_POSTS = 500

def get_api_url(account):
    """construct Tumblr API url"""
    blog_name = account
    if '.' not in blog_name:
        blog_name += '.tumblr.com'
    return 'https://api.tumblr.com/v2/blog/%s/%s' % (
        blog_name, 'likes' if args.likes else 'posts'
    )

def print_dict_tree(d, level):
    """traverse dict tree and print out tree structure"""
    if isinstance(d, dict):
        for v in d:
            print(' ' * (level * 2) + v) 
            print_dict_tree(d[v], level+1)
    elif isinstance(d, list):
        for l in d:
            print_dict_tree(l, level)
    elif isinstance(d, str):
        print(' ' * (level * 2) + d)
    elif isinstance(d, int):
        print(' ' * (level * 2) + str(d))

def search_dict_tree(d, key):
    """traverse dict tree and find search key"""
    if isinstance(d, dict):
        for v in d:
            if v == key:
                return d[v]
            s = search_dict_tree(d[v], key)
            if isinstance(s, dict) or isinstance(s, list):
                return s
    elif isinstance(d, list):
        for l in d:
            s = search_dict_tree(l, key)
            if isinstance(s, dict) or isinstance(s, list):
                return s

def process_photos(d):
    """process photos found"""
    if isinstance(d, dict):
        for v in d:
            # only process 'original_size' of images
            if v == 'alt_sizes':
                return
            if v == 'url':
                try:
                    url = d[v]
                    source = requests.get(url)
                    if source.status_code == 200:
                        output_file = url[url.rfind('/')+1:]
                        if args.verbosity >= 1:
                            logging.info("* Requesting image: %s", url)
                        with open(output_file, 'wb') as f:
                            f.write(requests.get(d[v]).content)
                            f.close()
                    else:
                        logging.error("* Error in image request, status_code: %s - %s",
                            source.status_code, source.reason)
                except (requests.exceptions.RequestException) as e:
                    logging.error("* Error in image request %s - %s",
                            url, e)
                    continue
            process_photos(d[v])
    elif isinstance(d, list):
        for l in d:
            process_photos(l)

def process_text(post):
    """process post type 'text'"""
    # contents can be found under key 'body'
    # create a html file for post containing post body
    output_html = f"\
<html>\
<head>Post id {post['id']}</head>\
<body>{post['body']}</body>\
</html>"
    output_file = str(post['id']) + '.html'
    if args.verbosity >= 1:
        logging.info("* Processing text post: %s", output_file)
    with open(output_file, 'wb') as f:
        f.write(bytes(output_html.encode()))
        f.close()
    
    # process all possible image elements in body
    body_soup = bs(post['body'], 'html.parser')
    image_tags = body_soup.findAll('img')

    for image in image_tags:
        try:
            url = image['src']
            source = requests.get(url)
            if source.status_code == 200:
                output_file = url[url.rfind('/')+1:]
                if args.verbosity >= 1:
                    logging.info("* Requesting image: %s", url)
                with open(output_file, 'wb') as f:
                    f.write(requests.get(url).content)
                    f.close()
            else:
                logging.error("* Error in image request, status_code: %s - %s",
                    source.status_code, source.reason)
        except (requests.exceptions.RequestException) as e:
            logging.error("* Error in image request %s - %s",
                    url, e)
            continue

def download_posts(url, limit, offset=0):
    """download limited number of posts starting with offset given"""
    payload = {'api_key': config['api_key'], 'limit': limit, 'reblog_info': 'true'}
    if offset > 0:
            payload['offset'] = offset
    r = requests.get(api_url, params=payload)

    if (r.status_code == 200):

        r_dict=json.loads(r.text)
        if args.verbosity >= 2:
            print_dict_tree(r_dict, 0)

        # iterate through posts
        # - posts typically start with 'type' key and end with 'display_avatar' key
        posts = search_dict_tree(r_dict, 'liked_posts' if args.likes else 'posts')
        if isinstance(posts, list):
            for post in posts:
                if post['type'] == 'photo':               
                    process_photos(post['photos'])
                elif post['type'] == 'text':
                    process_text(post)
                else:
                    if args.verbosity >= 1:
                        logging.info("* No handling for post type: %s", post['type'])
        else:
            if args.verbosity >= 1:
                logging.info("* No posts found")        
    else:
        logging.error("* Error in request: %s - %s",
            r.status_code, r.reason)
        # if args.verbosity >= 1:
        #     r_dict=json.loads(r.text)
        #     print_dict_tree(r_dict, 0)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

try:
    with open(os.path.expanduser(CREDENTIALS_FILE)) as fh:
        config = json.load(fh)
except FileNotFoundError:
    logging.error("* Credentials file %s not found", os.path.expanduser(CREDENTIALS_FILE))
    sys.exit(1)

parser = argparse.ArgumentParser(description='Tumbledee - a Tumblr download utility.')
parser.add_argument('account',
                    help="single blog-name to be processed")
parser.add_argument('-l', '--likes', dest='likes', action='store_true',
                    help="get likes instead of posts")
parser.add_argument('-v', '--verbosity', action='count', default=0,
                    help='output verbosity, levels -v, -vv')
parser.add_argument('-o', '--outdir', help='set output directory - default = account')
parser.add_argument('-n', '--number', type=int, default=1,
                    help='number of posts or likes to download')
parser.add_argument('-s', '--offset', type=int, default=0,
                    help='offset - post number where to start, newest = 0')

args = parser.parse_args()

account = args.account
if args.verbosity >= 1:
    logging.info("* Account: %s", account)

api_url = get_api_url(account)
if args.verbosity >= 1:
    logging.info("* API url: %s", api_url)

if args.outdir is None:
    if '.' in account:
        output_directory = account[:account.find('.')]
    else:
        output_directory = account
else:
    output_directory = args.outdir
if args.verbosity >= 1:
    logging.info("* Output directory: %s", output_directory)

number_of_posts = args.number
if number_of_posts > TOTAL_MAX_NUMBER_OF_POSTS:
    number_of_posts = TOTAL_MAX_NUMBER_OF_POSTS
    if args.verbosity >= 1:
        logging.info("* Limiting number of posts to total max %d",
            number_of_posts)

# post number to start with
# posts are in reverse chronological order
# - post #0 is most recent one
offset = args.offset

number_of_posts_left = number_of_posts

# get json entries from Tumblr API
try:
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    os.chdir(output_directory)

    while number_of_posts_left > 0:

        if number_of_posts_left > MAX_NUMBER_OF_POSTS:
            limit = MAX_NUMBER_OF_POSTS
        else:
            limit = number_of_posts_left

        if args.verbosity >= 1:
            logging.info("* Downloading %d %s with offset %d, %d remaining",
                limit, 'likes' if args.likes else 'posts', offset,
                number_of_posts_left)
        download_posts(api_url, limit, offset)

        number_of_posts_left = number_of_posts_left - limit
        offset = offset + limit

    os.chdir('..')

except (KeyboardInterrupt):
        sys.exit(1)

sys.exit(0)