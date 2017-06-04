import argparse
import json
import os
import re
from urllib.request import urlretrieve
from http_handler import get_access_token
from http_handler import get_response


def print_progress_bar(iteration, total):
    length = 50
    fill = '#'
    prefix = 'Progress'
    percent = '{0:.1f}'.format(100 * (iteration / float(total)))
    current_length = int(length * iteration // total)
    bar = fill * current_length + '-' * (length - current_length)
    print('\r%s |%s| %s%%' % (prefix, bar, percent), end='', flush=True)


def save_pictures(pictures, directory):
    for picture in pictures:
        filename = picture.split('/')[-1]
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                print('Cannot create folder {}'.format(directory))
        urlretrieve(picture, '{}/{}'.format(directory, filename))
        yield ''


def get_pictures_paths(picture_params):
    paths = []
    for param in picture_params:
        if param.startswith('photo') or param.startswith('src'):
            paths.append(picture_params[param])
    return paths


def get_pictures(json_data):
    attachments = json_data['response'][0]['attachments']
    pictures = []
    for attachment in attachments:
        if attachment['type'] == 'photo':
            pictures += get_pictures_paths(attachment['photo'])
    return pictures


def parse_post_id(url):
    pattern = 'wall(-?[0-9]+_[0-9]+)'
    regex = re.compile(pattern)
    result = regex.search(url)
    if result is None:
        return result
    return result.groups()[0]


def main(arguments):
    access_token = get_access_token()
    post_id = parse_post_id(arguments.url)
    response = get_response(post_id, access_token)
    json_data = json.loads(response)
    pictures = get_pictures(json_data)

    iteration = 0
    print_progress_bar(iteration, len(pictures))
    for progress in save_pictures(pictures, arguments.directory):
        iteration += 1
        print_progress_bar(iteration, len(pictures))


def parse_arguments():
    parser = argparse.ArgumentParser('Fetch images from vk publication')
    parser.add_argument('url', help='Publication url. Example: https://vk.com/wallNUMBER1_NUMBER2.')
    parser.add_argument('--directory', default='Images', help='Directory to save images to.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    try:
        main(args)
    except KeyboardInterrupt:
        pass
