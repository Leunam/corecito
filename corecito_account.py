#!/usr/bin/env python3
import asyncio
import time
import cryptocom.exchange as cro
from cryptocom.exchange.structs import Pair
from cryptocom.exchange.structs import PrivateTrade
from binance.client import Client

class CorecitoAccount:
  """Configures and runs the right code based on the selected exchange in config"""
  def __init__(self, config=None):
    self.exchange = config['corecito_exchange']
    self.api_key = config['api_key']
    self.api_secret = config['api_secret']
    self.core_number = config['core_number']
    self.min_price_stop = config['min_price_stop'] if 'min_price_stop' in config else None
    self.max_price_stop = config['max_price_stop'] if 'max_price_stop' in config else None
    self.min_core_number_increase_percentage = config['min_core_number_increase_percentage']
    self.max_core_number_increase_percentage = config['max_core_number_increase_percentage']
    self.min_core_number_decrease_percentage = config['min_core_number_decrease_percentage']
    self.max_core_number_decrease_percentage = config['max_core_number_decrease_percentage']
    self.limit_core_number_wallet = config['limit_core_number_wallet'] if 'limit_core_number_wallet' in config else None
    self.max_core_number_wallet   = config['max_core_number_wallet']   if 'max_core_number_wallet'   in config else None
    self.increase_core_number_by  = config['increase_core_number_by']  if 'increase_core_number_by'  in config else None
    self.min_core_number_wallet   = config['min_core_number_wallet']   if 'min_core_number_wallet'   in config else None
    self.decrease_core_number_by  = config['decrease_core_number_by']  if 'decrease_core_number_by'  in config else None
    
    self.is_fiat = config['is_fiat']

    if self.exchange == 'crypto.com':
      self.account = cro.Account(api_key=self.api_key, api_secret=self.api_secret)
      self.cro_exchange = cro.Exchange()
      self.base_currency = config['cryptocom_base_currency']
      self.core_number_currency = config['cryptocom_core_number_currency']
      self.pair = eval('cro.pairs.' + config['cryptocom_trading_pair'])
      self.pair_name = self.pair.name.replace('_', '/')
      self.cro_coin_base_currency = eval('cro.coins.' + config['cryptocom_base_currency'])
      self.cro_coin_core_number_currency = eval('cro.coins.' + config['cryptocom_core_number_currency'])
      self.max_decimals_buy = config['cryptocom_max_decimals_buy']
      self.max_decimals_sell = config['cryptocom_max_decimals_sell']
    elif self.exchange == 'binance':
      binance = Binance(public_key = self.api_key, secret_key = self.api_secret, sync=True)
      self.account = binance.b
      self.pair = config['binance_trading_pair']
      self.pair_name = self.pair.replace('_', '/')
      self.base_currency = config['binance_base_currency']
      self.core_number_currency = config['binance_core_number_currency']
      self.max_decimals_buy = config['binance_max_decimals_buy']
      self.max_decimals_sell = config['binance_max_decimals_sell']

    if not self.account:
      raise Exception('Could not connect to the exchange account with provided keys!')

  async def get_tickers(self):
    # Get pair ticker info
    if self.exchange == 'crypto.com':
      tickers = await self.cro_exchange.get_tickers()
      ticker = tickers[self.pair]
      buy_price = ticker.buy_price
      sell_price = ticker.sell_price
    elif self.exchange == 'binance':
      tickers = self.account.get_orderbook_tickers()
      # Example Binance {'symbol': 'ETHBTC', 'bidPrice': '0.02706800', 'bidQty': '7.30000000', 'askPrice': '0.02707300', 'askQty': '24.00000000'} # Bid == BUY, ask == SELL
      ticker = next((x for x in tickers if x["symbol"] == self.pair), None)
      buy_price = float(ticker["bidPrice"])
      sell_price = float(ticker["askPrice"])
      await asyncio.sleep(0.5)

    return({'buy_price': buy_price, 'sell_price': sell_price})

  async def get_balances(self):
    # Get account balances
    if self.exchange == 'crypto.com':
      balances = await self.account.get_balance()
      base_currency_balance = balances[self.cro_coin_base_currency]
      base_currency_available = base_currency_balance.available
      core_number_currency_balance = balances[self.cro_coin_core_number_currency]
      core_number_currency_available = core_number_currency_balance.available
    elif self.exchange == 'binance':
      base_currency_balance = self.account.get_asset_balance(asset=self.base_currency) or 0.0
      if base_currency_balance == 0.0:
        base_currency_available = 0.0
      else:
        base_currency_available = float(base_currency_balance["free"])
      core_number_currency_balance = self.account.get_asset_balance(asset=self.core_number_currency) or 0.0
      if core_number_currency_balance == 0.0:
        core_number_currency_available = 0.0
      else:
        core_number_currency_available = float(core_number_currency_balance["free"])
      await asyncio.sleep(0.5)

    return({'base_currency_balance': base_currency_balance,
            'base_currency_available': base_currency_available,
            'core_number_currency_balance': core_number_currency_balance,
            'core_number_currency_available': core_number_currency_available})

  """Returns a dict with the core number wallet limits and the increase/decrease values to apply on the core number if limit_core_number_wallet is not None"""
  async def get_core_number_wallet_limits(self):
    if (self.limit_core_number_wallet is None):
        return False
    else:
        await asyncio.sleep(0.5)

        return({'max_core_number_wallet': self.max_core_number_wallet,
                'increase_core_number_by': self.increase_core_number_by,
                'min_core_number_wallet': self.min_core_number_wallet,
                'decrease_core_number_by': self.decrease_core_number_by})
    

  async def order_market_buy(self, tx_result, quantity=0.0):
    if self.exchange == 'crypto.com':
      # NOTE: We use tx_result instead of quantity here because Crypto.com has a weird behaviour: it uses ETH to denominate the transaction
      await self.account.buy_market(self.pair, tx_result)
    elif self.exchange == 'binance':
      self.account.order_market_buy(symbol=self.pair, quantity=quantity)
      await asyncio.sleep(0.5)

  async def order_market_sell(self, quantity=0.0):
    if self.exchange == 'crypto.com':
      await self.account.sell_market(self.pair, quantity)
    elif self.exchange == 'binance':
      self.account.order_market_sell(symbol=self.pair, quantity=quantity)
      await asyncio.sleep(0.5)

# This wrapper solves time-offset inconsistencies between local-PC time and Binance server time
class Binance:
  def __init__(self, public_key = '', secret_key = '', sync = False):
    self.time_offset = 0
    self.b = Client(public_key, secret_key)

    if sync:
      self.time_offset = self._get_time_offset()

  def _get_time_offset(self):
    res = self.b.get_server_time()
    return res['serverTime'] - int(time.time() * 1000)

  def synced(self, fn_name, **args):
    args['timestamp'] = int(time.time() - self.time_offset)
