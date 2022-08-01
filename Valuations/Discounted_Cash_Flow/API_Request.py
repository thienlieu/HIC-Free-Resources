from urllib.request import urlopen
import json, traceback
from configuration import APIKey

def API_Getter(dataWanted, ticker, period, apiKey):
    """
    API_Getter - from the set of inputs, return appropriate url.
    :param dataWanted: type of data input
    :param ticker: stock ticker
    :param period: annual vs quarter
    :param FMPAPIKey: financialmodelingprep API key
    :return: url
    """
    if period == 'annual':
        url = 'https://financialmodelingprep.com/api/v3/{requested_data}/{ticker}?apikey={apikey}'.format(
            requested_data=dataWanted, ticker=ticker, apikey=apiKey)

    elif period == 'quarter':
        url = 'https://financialmodelingprep.com/api/v3/{requested_data}/{ticker}?period=quarter&apikey={apikey}'.format(
            requested_data=dataWanted, ticker=ticker, apikey=apiKey)

    else:
        raise ValueError('Input period is not accepted. Please try again other than ' + str(period))

    return url

def getJsonparsedData(url):
    """
    getJsonparsedData -
    :param url: desired url
    :return: json dumped data
    """
    try: response = urlopen(url)

    except Exception as e:
        print(f'Error raised while retrieving {url}')
        try: print('\t%s'%e.read().decode())
        except: pass
        raise

    data = response.read().decode('utf-8')
    jsonOutput = json.loads(data)

    if 'Error Message' in jsonOutput:
        raise ValueError("Error raised while requesting data from '{url}'. Error Message: '{errMsg}'.".format(url=url, errMsg=jsonOutput['Error Message']))

    return jsonOutput

def getEnterpriseValueStatement(ticker, period='annual', apiKey=f''):
    """
    getEnterpriseValueStatement - requests EV statement
    """
    url = API_Getter('enterprise-value', ticker=ticker, period=period, apiKey=apiKey)
    return getJsonparsedData(url)

def getIncomeStatement(ticker, period='annual', apiKey=f''):
    """
    getIncomeStatement - requests income statement
    """
    url = API_Getter('financials/income-statement', ticker=ticker, period=period, apiKey=apiKey)
    return getJsonparsedData(url)

def getCashFlowStatement(ticker, period='annual', apiKey=f''):
    """
    getCashFlowStatement - requests cash flow statement
    """
    url = API_Getter('financials/cash-flow-statement', ticker=ticker, period=period, apiKey=apiKey)
    return getJsonparsedData(url)

def getBalanceSheet(ticker, period='annual', apiKey=f''):
    """
    getBalanceSheet - requests balance sheet
    """
    url = API_Getter('financials/balance-sheet-statement', ticker=ticker, period=period, apiKey=apiKey)
    return getJsonparsedData(url)

def getStockPrice(ticker, apiKey=f''):
    """
    getStockPrice - requests stock price
    """
    url = 'https://financialmodelingprep.com/api/v3/stock/real-time-price/{ticker}?apikey={apiKey}'.format(
        ticker=ticker, apiKey=apiKey)
    return getJsonparsedData(url)

def getBatchStockPrice(tickers, apiKey=f''):
    """
    getBatchStockPrice - calculates batch stock price
    """
    prices = {}
    for ticker in tickers:
        prices[ticker] = getStockPrice(ticker=ticker, apiKey=apiKey)['price']
    return prices

def getHistoricalSharePrices(ticker, dates, apiKey=''):
    """
    getHistoricalSharePrices - requests historical share price by input date
    :return:
    """
    prices = {}
    for date in dates:
        try: date_start, date_end = date[0:8] + str(int(date[8:]) - 2), date
        except:
            print(f'Error occurred while parsing "{date}" to date.')
            print(traceback.format_exc())
            continue
        url = 'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={date_start}&to={date_end}&apikey={apiKey}'.format(
            ticker=ticker, date_start=date_start, date_end=date_end, apiKey=apiKey)
        try:
            prices[date_end] = getJsonparsedData(url)['historical'][0]['close']
        except IndexError:
            try:
                prices[date_start] = getJsonparsedData(url)['historical'][0]['close']
            except IndexError:
                print(date + ' ', getJsonparsedData(url))
    return prices

if __name__ == '__main__':
    ticker = 'MSFT'
    apiKey=f'{APIKey}'
    data = getCashFlowStatement(ticker=ticker, apiKey=apiKey)
    print(data)