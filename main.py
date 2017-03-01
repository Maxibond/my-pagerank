import pandas as pd
import re
import requests
from queue import Queue


settings = {}
settings['domen'] = input('Type a domen:') or 'https://habrahabr.ru'
settings['size'] = 100
settings['regexp'] = r'href="(?:%s([\w/]+)|/)"' % settings['domen']
settings['index'] = True


def find_urls(url):
    url = settings['domen'] + url
    try:
        page = requests.get(url).text
    except Exception:
        page = ''
    urls = re.findall(settings['regexp'], page)
    urls = ['/' if not url else url for url in urls]
    return set(urls)


def generate_adjacency_matrix():
    pages_to_parse = Queue()
    pages_passed = set()
    adjacency_matrix = {}
    pages_to_parse.put('/')
    while len(pages_passed) != settings['size']:
        print(len(pages_passed))
        current_url = pages_to_parse.get()
        adjacency_matrix[current_url] = {}
        urls = find_urls(current_url)
        for url in urls:
            adjacency_matrix[current_url][url] = 1
            if url not in pages_passed:
                pages_to_parse.put(url)
        pages_passed.add(current_url)
    # generate pandas.DataFrame from dict of dicts
    if settings['index']:
        index = pd.Index(sorted(list(adjacency_matrix.keys())))
    else:
        index = None
    adjacency_matrix = pd.DataFrame(adjacency_matrix, index=index, columns=index).fillna(0).astype(int)
    return adjacency_matrix


def main():
    adjacency_matrix = generate_adjacency_matrix()
    print(adjacency_matrix)
    adjacency_matrix.to_csv('result.csv')

if __name__ == '__main__':
    main()
