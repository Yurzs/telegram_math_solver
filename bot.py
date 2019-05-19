import config
from aiogram import types, executor
import random
from logic import action_priority, solve, TimeoutException, BracesMatchError, doc_aliases

@config.dp.message_handler(commands='start', state='*')
async def welcome(message: types.Message):
    funclist = ", ".join([x.replace("\\", '') for x in action_priority.keys()])
    rde = random.choice(list(doc_aliases.keys()))
    example_query = f'{random.randint(1,10)} ** log{random.randint(11,90)}({random.choice(["pi", "e"])}) + {random.randint(11,90)}'
    await message.reply(text=f'Welcome to math solver bot\nList of currently available functions:```\n{funclist}```\nExample: ``` {example_query} ```\nResult: ``` {solve(example_query)[0]} ``` \nTo know more about each function use /about\nExample: ``` /about {rde}``` \nResult: ``` {action_priority[rde]["doc"]} ```', parse_mode='Markdown')


@config.dp.message_handler(commands='about', state='*')
async def about(message: types.Message):
    func = ''.join(message.text.strip().lower().split('about')[1:]).strip()
    if func in doc_aliases:
        await message.reply(doc_aliases[func]['doc'], parse_mode='Markdown')
    else:
        await message.reply(f'Unknown function {func}')


@config.dp.message_handler()
async def solve_request(message: types.Message):
    print(message.text)
    try:
        result, pretty = solve(message.text.lower())
        result = f'Query: <code>{pretty}</code>\nResult: <code>{result}</code>'
        print(result)
    except TimeoutException as e:
        result = e.message
    except OverflowError:
        result = 'Result is too big to handle'
    except BracesMatchError as e:
        result = e.message
    except TypeError as e:
        result = str(e)
    except ValueError as e:
        result = str(e)
    await message.reply(result, parse_mode='HTML')

@config.dp.inline_handler(lambda inl: len(inl.query) == 0)
async def welcome_inline_query(inline: types.InlineQuery):
    await config.bot.answer_inline_query(inline.id, results=[], switch_pm_text='See instructions', switch_pm_parameter='start')



@config.dp.inline_handler(lambda inl: len(inl.query) > 0)
async def inline_math_query(inline: types.InlineQuery):
    try:
        pretty = inline.query
        result, pretty = solve(inline.query)
    except TimeoutException as e:
        result = e.message
    except OverflowError:
        result = 'Result is too big to handle'
    except BracesMatchError as e:
        result = e.message
    except TypeError as e:
        result = str(e)
    except ValueError as e:
        result = str(e)
    result_pretty = types.InputTextMessageContent(f'Query: <code>{pretty}</code>\nResult: <code>{result}</code>', parse_mode='HTML')
    item = types.InlineQueryResultArticle(id='1', title=result,
                                          input_message_content=result_pretty)
    await config.bot.answer_inline_query(inline.id, results=[item], cache_time=60)


if __name__ == '__main__':
    executor.start_polling(config.dp, skip_updates=False, loop=config.loop)
