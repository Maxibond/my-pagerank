import time
import multiprocessing as mp
import matplotlib.pyplot as plt
from main import generate_adjacency_matrix, pagerank, settings

# 15 pages - sp: 0.3s, mp: 30s
# 100 pages - sp: 1s, mp: 22s
# 250 pages - sp: 2s, mp: 75s
# 1000 pages - ????????


def mp_pagerank_worker(queue, ns):
    # рабочая функция для pagerank
    while True:
        job = queue.get()  # процесс берёт задачу
        if job is None:
            break
        page = job
        # смотреть в main.py
        for page_to in ns.matrix[page][ns.matrix[page] == 1].index:
            ns.sum_values[page_to] += ns.input_values[page] * ns.D / ns.count_links[page]
        ns.sum_values[page] = ns.sum_values[page] + (1 - ns.D)
        # помечаем, что выполнили задачу
        queue.task_done()
    queue.task_done()


def mp_pagerank(matrix):
    # читать комментарии в main.py, тут только объяснение параллелинга
    D = settings['dampening_factor']
    N = settings['number_iteration']

    input_values = {page: 1 for page in matrix}
    sum_values = {page: 1-D for page in matrix}
    count_links = matrix.eq(1).sum(1).to_dict()

    # подготавливаем общее рабочее пространство
    manager = mp.Manager()
    ns = manager.Namespace()
    ns.matrix = matrix
    ns.count_links = count_links
    ns.sum_values = sum_values
    ns.input_values = input_values
    ns.D = D

    nCPU = mp.cpu_count()  # число ядер

    for iteration in range(N):
        print(iteration)
        # для каждой итерации мы будем создавать задачи для наших процессов
        queue = mp.JoinableQueue()
        for page in matrix:
            queue.put(page)  # для каждой страницы создаём задачу
        for _ in range(nCPU):
            queue.put(None)  # делаем отметки, чтобы процессы прекратили работу

        # создаём процессы с нашей очередью задач и пространством объектов
        for i in range(nCPU):
            worker = mp.Process(target=mp_pagerank_worker,
                                args=(queue, ns))
            worker.start()
        # на этом месте синхронизируем, чтобы мы смогли нормировать результы
        # также тут связанность, любой процесс будет нуждаться во всех данных прошлой итерации
        queue.join()

        maximum = max(ns.sum_values.values())
        ns.sum_values = {key: value / maximum for key, value in ns.sum_values.items()}
        ns.input_values = ns.sum_values.copy()
    return dict(ns.input_values)


def compareTimes():
    # сравниваем результаты single process и multi process

    # сначала строим матрицу смежности
    domen = input('Type a domen:') or 'https://habrahabr.ru'
    settings['domen'] = domen
    settings['regexp'] = r'href="(?:%s([\w/]+)|/)"' % domen
    adjacency_matrix = generate_adjacency_matrix(settings['size'], binding_matrix=False)

    # последовательно
    t0 = time.time()
    pagerank(adjacency_matrix)
    t1 = time.time()
    print("single process time: {:.3f} s.".format(t1 - t0))

    # параллельно
    t0 = time.time()
    mp_pagerank(adjacency_matrix)
    t1 = time.time()
    print("multiple processes time: {:.3f} s.".format(t1 - t0))


def main():
    compareTimes()
    # showTimePlot()


if __name__ == '__main__':
    main()