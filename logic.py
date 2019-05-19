import re
import inspect
import math
from functools import reduce
import signal
from contextlib import contextmanager

class BracesMatchError(Exception):
    def __init__(self):
        self.message = 'Wrong braces count'


class TimeoutException(Exception):
    message = "You have a syntax error or computation took way longer than expected!"


class Variable:
    def __init__(self, s):
        match = re.match(r'(?<![A-z0-9])([0-9]+)([A-z]+)', s)
        self.num = type_string_format(match.group(1))
        self.name = match.group(2)

    @property
    def value(self):
        return f'{self.num}{self.name}'

    def __add__(self, other):
        if isinstance(other, Variable):
            if other.name == self.name:
                return f'{self.num + other.num}{self.name}'
            else:
                f'{self.value}+{other}'
        else:
            return f'{self.value}+{other}'

    def __iadd__(self, other):
        if isinstance(other, Variable):
            if other.name == self.name:
                return f'{self.num + other.num}{self.name}'
            else:
                f'{self.value}+{other}'
        else:
            return f'{self.value}+{other}'

    def __repr__(self):
        return self.value

    def __sub__(self, other):
        if isinstance(other, Variable):
            if other.name == self.name:
                return f'{self.num - other.num}{self.name}'
            else:
                f'{self.value}-{other}'
        else:
            return f'{self.value}-{other}'

    def __isub__(self, other):
        if isinstance(other, Variable):
            if other.name == self.name:
                return f'{self.num - other.num}{self.name}'
            else:
                f'{self.value}-{other}'
        else:
            return f'{self.value}-{other}'


def replace_first(s, match):
    rs = ''
    fl = False
    for c in s:
        if c == match and not fl:
            fl = True
            rs += ' '
            continue
        else:
            rs += c
    return rs

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def lambdagenerator(func):
    return lambda *args, **kwargs: func(*args, **kwargs)


def capture_args_regexp_generator(str, func_name):
    print(str, func_name)
    str = str.replace(func_name, '')
    return str[1:-1].split(',')

def type_string_format(s):
    if '.' in s:
        return float(s)
    else:
        return int(s)

action_priority = {
    'pi': {
        'func': lambda *args: math.pi,
        'search_regexp': '(?<![\w!()])({action})(?![\w!()])',
        'arg_regexp': lambda s: re.findall(r'pi', s),
        'replace': lambda s: s[1:] if len(s) > 2 else s,
        'doc': math.pi.__doc__
    },
    'e': {
        'func': lambda *args: math.e,
        'search_regexp': '(?<![\w!()])({action})(?![\w!()])',
        'arg_regexp': lambda s: re.findall(r'e', s),
        'replace': lambda s: s[1] if len(s) > 1 else s,
        'doc': math.e.__doc__
    },
    **{fname: {
        'func': lambdagenerator(getattr(math, fname)),
        'search_regexp': r'(?<![A-z0-9])({action}\([A-z0-9,.-]+\))(?![!A-z])',
        'arg_regexp': lambdagenerator(lambda s: [type_string_format(x) for x in capture_args_regexp_generator(s, s.split('(')[0])]),
        'replace': lambdagenerator(lambda s: s),
        'doc': getattr(math, fname).__doc__
    } for fname in math.__dict__ if inspect.isbuiltin(getattr(math, fname))},
    'logN': {
        'func': lambda x, y: math.log(float(y), float(x)),
        'search_regexp': r'^log[0-9.]+\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-\/*]log[0-9.]+\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^log[0-9.]+\((?:pi|e)?\)|[+-\/*]log[0-9.]+\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall(r'(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s.replace('log', '')),
        'replace': lambda s: s,
        'doc': 'Alias for log(x, y) => logY(x)'
    },
    '\!': {'func': lambda x: math.factorial(type_string_format(x)),
             'search_regexp': r'(?<![A-z0-9])([0-9.]+{action})(?![!A-z])',
             'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
             'replace': lambda s: s,
             'doc': f'Alias for ``` factorial \n {math.factorial.__doc__} ```'},
    '\!\!': {'func': lambda x: reduce(lambda x, y: x*y, [y for y in range(1, type_string_format(x) + 1) if y % 2 == type_string_format(x) % 2]),
             'search_regexp': r'(?<![A-z0-9])([0-9.]+{action})(?![!A-z])',
             'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
             'replace': lambda s: s,
             'doc': f'Alias for ``` semifactorial \n {math.factorial.__doc__} ```'},
    '\*\*': {'func': lambda x, y: float(x) ** float(y),
             'search_regexp': r'(?<![A-z0-9])([0-9.]+{action}[0-9.]+)',
             'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
             'replace': lambda s: s,
             'doc': 'X ** Y'},
    '\*': {'func': lambda x, y: float(x) * float(y),
           'search_regexp': r'(?<![A-z0-9])([0-9.]+{action}[0-9.]+)',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
           'replace': lambda s: s,
           'doc': 'X * Y'},
    '\/': {'func': lambda x, y: float(x) / float(y),
           'search_regexp': r'(?<![A-z0-9])([0-9.]+{action}[0-9.]+)',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
           'replace': lambda s: s,
           'doc': 'X / Y'},
    '\+': {'func': lambda x, y: float(x) + float(y),
           'search_regexp': r'(?<![A-z0-9])([0-9.]+{action}[0-9.]+)',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
           'replace': lambda s: s,
           'doc': 'X + Y'},
    '\-': {'func': lambda x, y: float(x) - float(y),
           'search_regexp': r'(?<![A-z0-9])([0-9.]+{action}[0-9.]+)',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', replace_first(s, '-')),
           'replace': lambda s: s,
           'doc': 'X - Y'},
}

doc_aliases = {k.replace('\\', ''): v for k, v in action_priority.items()}


def check_braces(func):
    def wrapper(query):
        counter = 0
        if ')(' in query:
            raise BracesMatchError()
        for c in query:
            if c == '(':
                counter += 1
            elif c == ')':
                counter -= 1
            if counter < 0:
                raise BracesMatchError()
        if counter > 0:
            raise BracesMatchError()
        return func(query)
    return wrapper


def in_braces(subquery):
    subq = re.search(r'\([\-0-9epi\*\-\+\/\ \.]+\)', subquery)
    if subq:
        if subquery[subq.start()-1] in '+-/*':
            subquery = subquery.replace(subq.group(0), f'{in_braces(subq.group(0)[1:-1])}')
        else:
            subquery = subquery.replace(subq.group(0), f'({in_braces(subq.group(0)[1:-1])})')
    fl = True
    while fl:
        fl = False
        for action, kwargs in action_priority.items():
            if re.search(kwargs.get('search_regexp').format(action=action), subquery):
                act = re.search(kwargs.get('search_regexp').format(action=action), subquery).group(0)
                subquery = subquery.replace(kwargs.get('replace')(act),
                                              str(kwargs.get('func')(*kwargs.get('arg_regexp')(act))))
                fl = True
                break
    return subquery


def preparse(func):
    def wrapper(query):
        for action, kwargs in {k:v for k,v in action_priority.items() if not k in ['\*', '\+', '\-', '\/']}.items():
            match = re.search('([0-9]+)({action})(\([0-9A-z.,]+\))|([0-9]+)({action})(?![A-z])'.format(action=action), query)
            if match:
                try:
                    query = query.replace(match.group(1), f'{match.group(1)}*')
                except TypeError:
                    query = query.replace(match.group(4), f'{match.group(4)}*')
        print(f'1  {query}')
        while re.search(r'([A-z]+\([A-z.,0-9]+\))([0-9.A-z]+)|(\([A-z0-9.,]+\))([A-z0-9.])', query):
            match = re.search(r'([A-z]+\([A-z.,0-9]+\))([0-9.A-z]+)|(\([A-z0-9.,]+\))([A-z0-9.])', query)
            if match.group(1):
                query = query.replace(match.group(1), f'{match.group(1)}*')
            elif match.group(3):
                query = query.replace(match.group(3), f'{match.group(3)}*')
        print(f'2  {query}')
        return func(query,  query)
    return wrapper


def solve(query):
    with time_limit(2):
        return solver(query)


@check_braces
@preparse
def solver(query, pretty_query):
    tmp_query = query.replace(' ', '')
    fl = True
    while fl:
        fl = False
        subq = re.search(r'[A-z0-9]+\([\-0-9epi\*\-\+\/\ \.]+\)', tmp_query)
        if subq:
            tmp_query = tmp_query.replace(subq.group(0), in_braces(subq.group(0)))
            fl = True
            continue
        elif re.search(r'\([\-0-9epi\*\-\+\/\ \.]+\)', tmp_query):
            subq = re.search(r'\([\-0-9epi\*\-\+\/\ \.]+\)', tmp_query)
            tmp_query = tmp_query.replace(subq.group(0), in_braces(subq.group(0)[1:-1]))
            fl = True
            continue
        else:
            return in_braces(tmp_query), pretty_query
