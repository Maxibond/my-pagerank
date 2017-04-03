import pandas as pd
import re
import requests


settings = {
    'size': 200,  # количество страниц
    'number_iteration': 10,  # количество итераций для pagerank
    'dampening_factor': 0.85,
}

def find_urls(url):
    # по ссылке на странице ищутся ссылки на другие страницы
    url = settings['domen'] + url
    try:
        page = requests.get(url).text  # запрашиваем страницу
    except Exception:
        page = ''
    urls = re.findall(settings['regexp'], page)  # по регулярному выражению вытаскиваем ссылки
    urls = ['/' if not url else url for url in urls]
    return set(urls)  # возвращаем уникальное множество


def generate_binding_matrix(adjacency_matrix):
    # степенной метод
    urls = adjacency_matrix.keys()
    # получаем для каждой ссылки их позиции, т.е. '/users/': 3
    url_ids = {url: position for position, url in enumerate(urls)}
    res = []
    for url in urls:  # проходим по каждой ссылке
        res.append([])  # создаём список
        for link in adjacency_matrix[url]:  # для каждой ссылки, которая есть на странице
            if link in url_ids.keys():
                res[-1].append(url_ids[link])  # добавляем её индекс в список
    # записываем в файл значения
    with open((u'Степенной метод %s.txt' % settings['domen']).replace('https://', ''), 'w') as f:
        f.write('\n'.join("%d. %s" % (pos, url) for url, pos in sorted(url_ids.items(), key=lambda e: e[1])))
        f.write('\n\n')
        f.write('\n'.join(("%s: " % url) + str(values) for url, values in zip(urls, res)))


def generate_adjacency_matrix(size, binding_matrix=True, use_pandas=True):
    # генерирование матрицы смежности
    # параметры: размер матрицы (количество страниц), строить ли матрицу степенным методом,
    # использовать ли pandas для таблицы (лучше не выключать)
    pages_to_parse = []  # очередь страниц для парсинга
    pages_passed = set()  # множество пройденных страниц
    adjacency_matrix = {}  # матрица смежности
    pages_to_parse.append('/')  # начинаем парсить с главной страницы
    print('Pages passed: ')
    while len(pages_passed) != size and len(pages_to_parse) != 0:  # пока количество пройденных страниц не превышает
        # количество необходимых и размер очереди не опустился до нуля
        print(len(pages_passed))
        current_url = pages_to_parse.pop(0)  # вытаскиваем из очереди страницу
        adjacency_matrix[current_url] = {}  # строим для неё словарь
        urls = find_urls(current_url)  # парсим её
        for url in urls:  # для каждой найденной ссылки
            adjacency_matrix[current_url][url] = 1  # записываем связь
            if url not in pages_passed and url not in pages_to_parse:  # если страницу ещё не прошли и ещё не добавили
                # в очередь, тогда добавляем
                pages_to_parse.append(url)
        pages_passed.add(current_url)  # указываем, что мы прошли текущию страницу
    if binding_matrix:
        # степенной метод (для демонстрации)
        generate_binding_matrix(adjacency_matrix)
    if use_pandas:
        # создаём pandas.DataFrame из словаря словарей
        index = pd.Index(sorted(list(adjacency_matrix.keys())))
        adjacency_matrix = pd.DataFrame(adjacency_matrix, index=index, columns=index).fillna(0).astype(int)
    return adjacency_matrix


def generate_csv_matrix(matrix):
    # pandas позволяет удобно записывать dataframe в файл
    matrix.to_csv('result_%s.csv' % settings['domen'].replace('https://', ''))


def pagerank(matrix):
    # принимает матрицу смежности и выдаёт рейтинг страниц
    D = settings['dampening_factor']
    N = settings['number_iteration']
    input_values = {page: 1 for page in matrix}  # входящие значения начинаются с 1
    sum_values = {page: 1-D for page in matrix}  # куда будут суммироваться значения
    count_links = matrix.eq(1).sum(1).to_dict()  # с помощью pandas делаем подсчёт сколько ссылок на каждой странице
    print('Pagerank: ')
    for i in range(N):  # по числу итераций (можно сделать по приближенному значению E)
        print(i, end=': ')
        print(input_values)
        for page_from in input_values:  # из каждой страницы
            for page_to in matrix[page_from][matrix[page_from] == 1].index:  # берём ту в которую текущая ссылается
                # основная формула в pagerank - складываем исходящее значение * D делённое на количество ссылок
                sum_values[page_to] += input_values[page_from] * D / count_links[page_from]
        # новые входящие значения
        # нормируем вектор {0, 1}
        maximum = max(sum_values.values())
        input_values = {key: value/maximum for key, value in sum_values.items()}
        # сбрасываем сумму
        sum_values = {page: 1 - D for page in matrix}
    return input_values


def generate_file_rating(pagerank_rating):
    # выводим файл рейтинга (результата Pagerank)
    with open('rating_%s.txt' % settings['domen'].replace('https://', ''), 'w') as f:
        for index, (page, value) in enumerate(sorted(pagerank_rating.items(), key=lambda i: i[1], reverse=True)):
            f.write('%d. %s: %f\n' % (index, page, value))


def main(size=settings['size']):
    domen = input('Type a domen (press Enter for: "https://habrahabr.ru"') or 'https://habrahabr.ru'  # спрашиваем домен, по умолчанию хабр
    settings['domen'] = domen
    settings['regexp'] = r'href="(?:([\w/]+)|/)"'
    adjacency_matrix = generate_adjacency_matrix(size)  # матрица смежности
    generate_csv_matrix(adjacency_matrix)  # выводим её в файл
    pagerank_rating = pagerank(adjacency_matrix)  # pagerank для матрицы
    generate_file_rating(pagerank_rating)  # выводим результат в файл

if __name__ == '__main__':
    main()
