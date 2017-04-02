import pandas as pd
import re
import requests


_domen = input('Type a domen:') or 'https://habrahabr.ru'
settings = {
    'domen': _domen,
    'size': 15,
    'regexp': r'href="(?:%s([\w/]+)|/)"' % _domen,
    'number_iteration': 35,
    'dampening_factor': 0.85,
}

def find_urls(url):
    url = settings['domen'] + url
    try:
        page = requests.get(url).text
    except Exception:
        page = ''
    urls = re.findall(settings['regexp'], page)
    urls = ['/' if not url else url for url in urls]
    return set(urls)


def generate_binding_matrix(adjacency_matrix):
    """ 
    {'/': {'users': 1, '/': 1}, 'q': {'/': 1}}
    """
    urls = adjacency_matrix.keys()
    url_ids = {url: position for position, url in enumerate(urls)}
    res = []
    for url in urls:
        res.append([])
        for link in adjacency_matrix[url]:
            if link in url_ids.keys():
                res[-1].append(url_ids[link])
    with open(u'Степенной метод %s.txt' % settings['domen'].replace('https://', ''), 'w') as f:
        f.write('\n'.join("%d. %s" % (pos, url) for url, pos in sorted(url_ids.items(), key=lambda e: e[1])))
        f.write('\n\n')
        f.write('\n'.join(("%s: " % url) + str(values) for url, values in zip(urls, res)))


def generate_adjacency_matrix():
    pages_to_parse = []
    pages_passed = set()
    adjacency_matrix = {}
    pages_to_parse.append('/')
    print('Pages passed: ')
    while len(pages_passed) != settings['size'] and len(pages_to_parse) != 0:
        print(len(pages_passed))
        current_url = pages_to_parse.pop(0)
        adjacency_matrix[current_url] = {}
        urls = find_urls(current_url)
        for url in urls:
            adjacency_matrix[current_url][url] = 1
            if url not in pages_passed and url not in pages_to_parse:
                pages_to_parse.append(url)
        pages_passed.add(current_url)
    # binding matrix (optionally for demo)
    generate_binding_matrix(adjacency_matrix)
    # generate pandas.DataFrame from dict of dicts
    index = pd.Index(sorted(list(adjacency_matrix.keys())))
    adjacency_matrix = pd.DataFrame(adjacency_matrix, index=index, columns=index).fillna(0).astype(int)
    return adjacency_matrix


def generate_csv_matrix(matrix):
    matrix.to_csv('result_%s.csv' % settings['domen'].replace('https://', ''))


def pagerank(matrix):
    D = settings['dampening_factor']
    N = settings['number_iteration']
    input_values = {page: 1 for page in matrix}
    init_sum_values = {page: 1-D for page in matrix}
    count_links = matrix.eq(1).sum(1).to_dict()
    sum_values = init_sum_values.copy()
    print('Pagerank: ')
    for i in range(N):
        print(i, end=': ')
        print(input_values)
        for page_from in input_values:
            for page_to in matrix[page_from][matrix[page_from] == 1].index:
                sum_values[page_to] += input_values[page_from] * D / count_links[page_from]
        sum_values = {key: value+(1-D) for key, value in sum_values.items()}
        # normalization value/max {0, 1}
        maximum = max(sum_values.values())
        sum_values = {key: value/maximum for key, value in sum_values.items()}
        input_values = sum_values.copy()
    return input_values


def generate_file_rating(pagerank_rating):
    with open('rating_%s.txt' % settings['domen'].replace('https://', ''), 'w') as f:
        for index, (page, value) in enumerate(sorted(pagerank_rating.items(), key=lambda i: i[1], reverse=True)):
            f.write('%d. %s: %f\n' % (index, page, value))


def main():
    adjacency_matrix = generate_adjacency_matrix()
    generate_csv_matrix(adjacency_matrix)
    pagerank_rating = pagerank(adjacency_matrix)
    generate_file_rating(pagerank_rating)

if __name__ == '__main__':
    main()
