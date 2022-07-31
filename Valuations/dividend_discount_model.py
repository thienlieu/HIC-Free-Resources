#Dividend Discount Model (DDM) is method to predict the price of company's stock based on theory that
#today's price is worth the sum of all future dividend payments when discounted back to their present value. 
#This valuation model is almost only useful for mature companies with stable growth rates (proven track records). 

import yfinance as yf
import pandas as pd
import numpy as np

#data acquisition from Yahoo Finance
ticker = yf.Ticker('t')
stock = ticker.actions

#stock splits per quarter.
stockSplit = stock['Stock Splits'].to_numpy()
stockSplitModified = np.where(stockSplit == 0, 1, stockSplit)

#multiply each num by previous one & save for each array's value.
stockSplitCompound = np.cumprod(stockSplitModified, axis = 0)
stock['Stock Split Compounded'] = stockSplitCompound.tolist()

#adjusted dividends = dividends * adjusted stock split (compounded)
stock['Dividend Adjusted'] = stock['Dividends'] * stock['Stock Split Compounded']

#total dividends per year
stock['year'] = stock.index.year
stockGroup = stock.groupby(by=['year']).sum()

#calculate annual percent change
stockGroup['Dividend % Change'] = stockGroup['Dividend Adjusted'].pct_change(fill_method='ffill')
print(stockGroup.tail(20))

#extract median dividends growth
medianGrowth = stockGroup['Dividend % Change'].median()
print(medianGrowth)

#last dividend
lastDividend = stockGroup.at[2021, 'Dividends']
print(lastDividend)

#expected future dividend
expectedFutureDividend = round(lastDividend * (1 + medianGrowth), 2)

#get beta
beta = ticker.info['beta']
print(beta)

#assumptions
riskFreeRate = 0.03
marketReturn = 0.11
marketRiskPremium = marketReturn - riskFreeRate

#cost of equity
costOfEquity = round(beta * marketRiskPremium + riskFreeRate, 4)
print(f'Cost of Equity: {costOfEquity}')

#fair share price
fairSharePrice = round(expectedFutureDividend / (costOfEquity - medianGrowth), 2)
print(f'Fair Share Price: {fairSharePrice}')

#closing stock price
stockPrice = ticker.history(period='today')
stockPriceClose = round(stockPrice.iloc[0]['Close'], 4)
print(f'Closing Stock Price: {stockPriceClose}')

#expected gain/loss
expectedGainLoss = fairSharePrice/stockPriceClose - 1
expectedGainLoss = '{:.0%}'.format(expectedGainLoss)
print(f'Expected gain: {expectedGainLoss}')

#ending note1: a dividend growth rate (constant) has to differ organization by organizatgion.
#ending note2: output is very sensitive to inputs (alternative needed)
#ending note3: if rate of return < dividend growth rate --> model fails if company pay dividends although losing money/decreasing earnings.
