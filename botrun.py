import time

from aiogram import Bot, Dispatcher, executor, types
import config
from divergenz_calc import DivergenzCalc

bot = Bot(config.BOT)
dp = Dispatcher(bot)

bitcoin_bt = types.InlineKeyboardButton('BTC USD track', callback_data='btc')


'''
    bot starts with a message and shows a button for tracking begin
'''
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.row(bitcoin_bt)

    await message.answer("Track BTC/USD with DIVERGENCE", reply_markup=markup)

''' 
    after button click the calculation begins, new data is provided hourly
    user get a divergence notification if it was computed
'''
@dp.callback_query_handler(text=['btc'])
async def callback(callback_query: types.CallbackQuery):
    if callback_query.data == 'btc':
        div_calc = DivergenzCalc()
        while (True):
            new_data, new_timestamp = div_calc.hourly_price_historical('BTC', 'USD', 1, 1)
            if new_timestamp > div_calc.last_timestamp:
                div_calc.get_new_hour(new_timestamp, new_data[0])
                if div_calc.div_message:
                    #information for console
                    print(f"{div_calc.div_message}")
                    print(f'rsi ma: {div_calc.rsi_ma_list}')
                    print(f'high list: {div_calc.high_list}')
                    print(f'low list: {div_calc.low_list}')
                    print(f'hist prices: {div_calc.historical_prices}')

                    await callback_query.message.answer(f"{div_calc.div_message}")
                    div_calc.div_message = None
            #check every 10 minutes if new hour is started
            time.sleep(600)
    else:
        await callback_query.message.answer('Error')


executor.start_polling(dp)