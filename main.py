import time
import pylab as pl
import pygraphviz as pyv
from itertools import combinations

ws_all = {}  # all ws with input and output in each data set
valid = []  # the set of ws unselected
req_input = []  # input given by user
req_output = []  # output expected to get

precond = lambda ws_num: ws_all[ws_num][0]
effects = lambda ws_num: ws_all[ws_num][1]


def read_ws(ws_file):
    for line in file(ws_file).readlines():
        number, para_in, para_out = [s.replace(' ', '') for s in line.split('|')]
        ws_all[int(number)] = [list(para_in), list(para_out.strip())]
        valid.append(int(number))


def read_req(req_file):
    global req_input, req_output
    req_input, req_output = [s.split(',') for s in file(req_file).readline()[1:-1].split('},{')]


def expand(parameters, ws_selected):
    ws_adding, para_adding = [], parameters[-1]  # new ws and paras will be added

    for ws_num in valid[:]:
        if set(precond(ws_num)).issubset(para_adding):
            ws_adding.append(ws_num)
            valid.remove(ws_num)
    if not ws_adding:
        return False

    for ws_num in ws_adding[:]:  # delete ws won't contribute new paras
        if set(effects(ws_num)).issubset(para_adding):
            ws_adding.remove(ws_num)
        else:
            para_adding = set(para_adding).union(effects(ws_num))
        if set(req_output).issubset(para_adding):
            for ws in ws_adding[:]:
                temp = set(effects(ws)).intersection(req_output)
                if not temp:
                    ws_adding.remove(ws)
            break

    unused = True
    if ws_selected[-1]:  # delete ws whose output won't be used
        para_ins = [precond(ws_num) for ws_num in ws_adding]
        for ws_num in ws_selected[-1][:]:
            for para_in in para_ins:
                if set(effects(ws_num)).intersection(para_in):
                    unused = False
                    break
            if unused:
                ws_selected[-1].remove(ws_num)
                valid.append(ws_num)
            unused = True

    parameters.append(para_adding)
    ws_selected.append(ws_adding)
    return True


def backward(ws_selected):
    result = {}  # last result of ws selected
    ws_level = {}  # save the level of cross level ws
    paras = set(req_output[:])  # paras need satisfying in each level
    get_min_ws = False  # found optimal solution this level

    for level in xrange(len(ws_selected) - 1, 0, -1):
        ws_cross_level = []
        ws_candidate = ws_selected[level]
        for cross_level in xrange(1, level):
            temp = filter(lambda ws: set(effects(ws)).intersection(paras),
                          ws_selected[cross_level])
            ws_cross_level.extend(temp)
            for ws in temp:
                ws_level[ws] = cross_level

        ws_candidate.extend(ws_cross_level)
        for size in xrange(1, len(ws_candidate) + 1):
            for group in combinations(ws_candidate, size):
                group = set(group).union(result.get(level, []))
                if paras.issubset(
                        reduce(lambda s1, s2: s1.union(s2),
                               map(lambda ws: set(effects(ws)), group))):

                    ws_this_level = group.difference(ws_cross_level)
                    result[level] = ws_this_level

                    paras = reduce(lambda s1, s2: s1.union(s2),
                                   map(lambda ws: set(precond(ws)),
                                       ws_this_level))

                    ws_cross_level = group.intersection(ws_cross_level)
                    for ws in ws_cross_level:
                        if ws_level[ws] in result:
                            result[ws_level[ws]].append(ws)
                        else:
                            result[ws_level[ws]] = [ws]

                    get_min_ws = True
                    break
            if get_min_ws:
                get_min_ws = False
                break

    return result

def draw_flow_chart(result):
    ws_all[', '.join(req_input)] = [[], req_input]  # add user's input
    ws_all[', '.join(req_output)] = [req_output, []]  # add expected output
    result[0] = [', '.join(req_input)]
    result[len(result)] = [', '.join(req_output)]

    flow_chart = pyv.AGraph(directed=True, strict=True, rankdir='LR')

    for level in xrange(len(result) - 1, 0, -1):
        for ws_num_back in result[level]:
            paras = set(precond(ws_num_back))
            for level_before in xrange(level):
                for ws_num_front in result[level_before]:
                    label_set = \
                        set(effects(ws_num_front)).intersection(paras)
                    if label_set:
                        paras = paras.difference(label_set)
                        flow_chart.add_edge(ws_num_front, ws_num_back, label=', '.join(label_set))

    flow_chart.layout(prog='dot')
    flow_chart.draw(str(ws_file) + '.jpg', format='jpg')


def draw_line_chart(x, y):
    pl.plot(x, y, 'bo-')

    pl.title('Running Time on Different Data Set')
    pl.xlabel('Data Set (Number of Service)')
    pl.ylabel('Running Time (ms)')

    pl.xlim(0, 20000)
    pl.ylim(0.0, 0.5)
    pl.xticks(xrange(0, 20001, 2000))
    pl.yticks(map(lambda n: n / 100.0, xrange(0, 51, 5)))

    pl.show()


if __name__ == '__main__':
    running_time = []  # save running time for line chart
    read_req('Func_Req.txt')  # read in req of user
    data_set = [200, 1000, 2000, 20000]

    for ws_file in data_set:
        start = time.clock()  # start time

        ws_all.clear()  # clear for next data set
        valid = []  # ditto ...
        read_ws(str(ws_file) + '.txt')  # read in all ws info

        ws_selected = []  # ws in each level of planning graph
        parameters = []  # paras ...
        ws_selected.append([])
        parameters.append(req_input)

        for level in xrange(20000):  # forward chaining
            if not expand(parameters, ws_selected):
                print 'reach fixed point'
                exit()
            elif set(req_output).issubset(set(parameters[-1])):
                break

        result = backward(ws_selected)  # solution extraction
        running_time.append(time.clock() - start)  # end time

        draw_flow_chart(result)  # draw flow chart for each data set

    # draw line chart for all four data set
    draw_line_chart(data_set, running_time)
