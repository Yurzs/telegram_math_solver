import math
import re
import signal
from contextlib import contextmanager
import config
from aiogram import types, executor
import random

class BracesMatchError(Exception):
    def __init__(self):
        self.message = 'Wrong braces count'


class TimeoutException(Exception):
    message = "You have a syntax error or computation took way longer than expected!"


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

action_priority = {
    'pi': {
        'func': lambda *args: math.pi,
        'search_regexp': r'^pi|[+-/*]pi',
        'arg_regexp': lambda s: re.findall(r'pi', s),
        'replace': lambda s: s[1:] if len(s) > 2 else s,
    },
    'e': {
        'func': lambda *args: math.e,
        'search_regexp': r'^e|[+-/*]e',
        'arg_regexp': lambda s: re.findall(r'e', s),
        'replace': lambda s: s[1] if len(s) > 1 else s,
    },
    'logN': {
        'func': lambda x, y: math.log(float(y), float(x)),
        'search_regexp': r'^log[0-9.]+\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-\/*]log[0-9.]+\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^log[0-9.]+\((?:pi|e)?\)|[+-\/*]log[0-9.]+\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall(r'(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s.replace('log', '')),
        'replace': lambda s: s,
    },
    'log': {
        'func': lambda x: math.log10(float(x),),
        'search_regexp': r'^log\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]log\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^log\((?:pi|e)?\)|[+-/*]log\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall(r'(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    'sin': {
        'func': lambda x: math.sin(float(x),),
        'search_regexp': r'^sin\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]sin\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^sin\((?:pi|e)?\)|[+-/*]sin\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall(r'(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    'sinh': {
        'func': lambda x: math.sin(float(x),),
        'search_regexp': r'^sinh\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]sinh\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^sinh\((?:pi|e)?\)|[+-/*]sinh\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall(r'(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    'cos': {
        'func': lambda x: math.cos(float(x),),
        'search_regexp': r'^cos\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]cos\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^cos\((?:pi|e)?\)|[+-/*]cos\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall('(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    'cosh': {
        'func': lambda x: math.cos(float(x),),
        'search_regexp': r'^cosh\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]cosh\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^cosh\((?:pi|e)?\)|[+-/*]cosh\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall('(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    'tan': {
        'func': lambda x: math.tan(float(x),),
        'search_regexp': r'^tan\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]tan\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^tan\((?:pi|e)?\)|[+-/*]tan\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall('(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    'atan': {
        'func': lambda x: math.tan(float(x),),
        'search_regexp': r'^atan\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|[+-/*]atan\((?:[\-0-9\.]+(?:[Ee]\+\d+)?)\)|^atan\((?:pi|e)?\)|[+-/*]atan\((?:pi|e)?\)',
        'arg_regexp': lambda s: re.findall('(?:[-]?[0-9\.]+(?:[Ee]\+\d+)?)|(?:pi|e)', s),
        'replace': lambda s: s,
    },
    '\*\*': {'func': lambda x, y: float(x) ** float(y),
             'search_regexp': r'[\-0-9\.]+(?:[Ee]\+\d+)?{action}[\-0-9\.]+(?:[Ee]\+\d+)?',
             'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
             'replace': lambda s: s},
    '\*': {'func': lambda x, y: float(x) * float(y),
           'search_regexp': r'[\-0-9\.]+(?:[Ee]\+\d+)?{action}[\-0-9\.]+(?:[Ee]\+\d+)?',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
           'replace': lambda s: s},
    '\/': {'func': lambda x, y: float(x) / float(y),
           'search_regexp': r'[\-0-9\.]+(?:[Ee]\+\d+)?{action}[\-0-9\.]+(?:[Ee]\+\d+)?',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
           'replace': lambda s: s},
    '\+': {'func': lambda x, y: float(x) + float(y),
           'search_regexp': r'[\-0-9\.]+(?:[Ee]\+\d+)?{action}[\-0-9\.]+(?:[Ee]\+\d+)?',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', s),
           'replace': lambda s: s},
    '\-': {'func': lambda x, y: float(x) - float(y),
           'search_regexp': r'[\-0-9\.]+(?:[Ee]\+\d+)?{action}[\-0-9\.]+(?:[Ee]\+\d+)?',
           'arg_regexp': lambda s: re.findall(r'[-]?[0-9\.]+(?:[Ee]\+\d+)?', replace_first(s, '-')),
           'replace': lambda s: s},
}


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




def solve(query):
    with time_limit(2):
        return solver(query)

@check_braces
def solver(query):
    tmp_query = query.replace(' ', '')
    fl = True
    while fl:
        fl = False
        subq = re.search('[A-z0-9]+\([\-0-9epi\*\-\+\/\ \.]+\)', tmp_query)
        if subq:
            tmp_query = tmp_query.replace(subq.group(0), in_braces(subq.group(0)))
            fl = True
            continue
        elif re.search('\([\-0-9epi\*\-\+\/\ \.]+\)', tmp_query):
            subq = re.search('\([\-0-9epi\*\-\+\/\ \.]+\)', tmp_query)
            tmp_query = tmp_query.replace(subq.group(0), in_braces(subq.group(0)[1:-1]))
            fl = True
            continue
        else:
            return in_braces(tmp_query)


@config.dp.message_handler(commands='start', state='*')
async def welcome(message: types.Message):
    funclist = ", ".join([x.replace("\\", '') for x in action_priority.keys()])
    example_query = f'{random.randint(1,10)} ** log{random.randint(11,90)}({random.choice(["pi", "e"])}) + {random.randint(11,90)}'
    await message.reply(text=f'Welcome to math solver bot\nList of currently available functions:\n{funclist}\nExample: {example_query}\nResult: {solve(example_query)}')


@config.dp.message_handler()
async def solve_request(message: types.Message):
    print(message.text)
    try:
        result = solve(message.text.lower())
        await message.reply(result)
    except TimeoutException as e:
        await message.reply(e.message)
    except OverflowError as e:
        await message.reply('Result is too big to handle')


if __name__ == '__main__':
    # migrations()
    # config.loop.run_until_complete(config.db.gino.drop_all())  # You know what to do
    # config.loop.run_until_complete(config.db.gino.create_all())
    executor.start_polling(config.dp, skip_updates=False, loop=config.loop)
