import argparse, traceback
from decimal import Decimal
from API_Request import *

def unleveredFCF(ebit, taxRate, nonCashCharges, currentWorkingCapital, capEx):
    """
    unleveredFCF -
    :param ebit:
    :param taxRate:
    :param nonCashCharges:
    :param currentWorkingCapital:
    :param capEx:
    :return:
    """
    return ebit * (1 - taxRate) + nonCashCharges + currentWorkingCapital + capEx

def enterpriseValueCalculator(incomeStatement, cashflowStatement, balanceSheet, period, discountRate,
                              earningsGrowthRate, capExGrowthRate, perpetualGrowthRate):
    """
    enterpriseValueCalculator -
    :param incomeStatement:
    :param cashflowStatement:
    :param balanceSheet:
    :param period:
    :param discountRate:
    :param earningsGrowthRate:
    :param capExGrowthRate:
    :param perpetualGrowthRate:
    :return:
    """
    if incomeStatement[0]['EBIT']:
        ebit = float(incomeStatement[0]['EBIT'])
    else:
        ebit = float(input(f'EBIT is missing, please enter EBIT on {incomeStatement[0]["date"]} or skip: '))

    taxRate = float(incomeStatement[0]['Income Tax Expense']) / float(incomeStatement[0]['Earnings before Tax'])
    nonCashCharges = float(cashflowStatement[0]['Depreciation & Amortization'])
    currentWorkingCapital = (float(balanceSheet[0]['Total assets']) - float(balanceSheet[0]['Total non-current assets'])) - \
          (float(balanceSheet[1]['Total assets']) - float(balanceSheet[1]['Total non-current assets']))
    capEx = float(cashflowStatement[0]['Capital Expenditure'])
    discount = discountRate

    flows = []
    #we're using manual printing instead of pandas dataframe because it's an expensive process.
    print(f'Forecasting cash flows for {period} years in future, starting at {incomeStatement[0]["date"]}.')
    print('\n         DFCF   |    EBIT   |    D&A    |    CWC     |   CAP_EX   | ')

    for year in range(1, period + 1):
        ebit = ebit * (1 + (year * earningsGrowthRate))
        nonCashCharges = nonCashCharges * (1 + (year * earningsGrowthRate))
        ############### need to dynamically evaluate current working capital rate
        currentWorkingCapital = currentWorkingCapital * 0.7
        capEx = capEx * (1 + (year * capExGrowthRate))

        flow = unleveredFCF(ebit, taxRate, nonCashCharges, currentWorkingCapital, capEx)
        PVFlow = flow / ((1 + discount) ** year)

        print(str(int(incomeStatement[0]['date'][0:4]) + year) + ' ',
              '%.2E' % Decimal(PVFlow) + ' | ',
              '%.2E' % Decimal(ebit) + ' | ',
              '%.2E' % Decimal(nonCashCharges) + ' | ',
              '%.2E' % Decimal(capEx) + ' | ')

    NPVFCF = sum(flows)

    #terminal value
    finalCashflow = flows[-1] * (1 + perpetualGrowthRate)
    TV = finalCashflow/(discount - perpetualGrowthRate)
    NPVTV = TV / (1 + discount) ** (1 + period)

    return NPVTV + NPVFCF

def equityValue(enterpriseValue, enterpriseValueStatement):
    """
    equityValue -
    :param enterpriseValue:
    :param enterpriseValueStatement:
    :return:
    """
    equityValue = enterpriseValue - enterpriseValueStatement['+ Total Debt']
    equityValue += enterpriseValueStatement['- Cash & Cash Equivalents']
    sharePrice = equityValue / float(enterpriseValueStatement['Number of Shares'])

    return equityValue, sharePrice

def getDiscountRate():
    """
    getDiscountRate -
    :return: WACC
    """
    ########### needs to be done properly ##############
    return 0.1

def DCF(ticker, enterpriseValueStatement, incomeStatement, balanceSheet, cashFlowStatement, discountRate, \
    forecast, earningGrowthRate, capitalExpenditureGrowthRate, perpetualGrowthRate):
    """
    DCF -
    :param ticker:
    :param enterpriseValueStatement:
    :param incomeStatement:
    :param balanceSheet:
    :param cashFlowStatement:
    :param discountRate:
    :param forecast:
    :param earningGrowthRate:
    :param capitalExpenditureGrowthRate:
    :param perpetualGrowthRate:
    :return:
    """
    enterpriseValue = enterpriseValueCalculator(incomeStatement, cashFlowStatement, balanceSheet, forecast, \
                                                discountRate, earningGrowthRate, capitalExpenditureGrowthRate, \
                                                perpetualGrowthRate)

    equityVal = sharePrice = equityValue(enterpriseValue, enterpriseValueStatement)

    print(f'\nEnterprise Value for {ticker}: ${"%.2E" % Decimal(str(enterpriseValue))}',
          f'\nEquity Value for {ticker}: ${"%.2E" % Decimal(str(equityVal))}',
          f'\nPer Share Value for {ticker}: ${"%.2E" % Decimal(str(sharePrice))}.')

    return {
        'date': incomeStatement[0]['date'],
        'enterpriseValue': enterpriseValue,
        'equityValue': equityVal,
        'sharePrice': sharePrice
    }

def historicalDCF(ticker, years, forecast, discountRate, earningsGrowthRate, capExGrowthRate, \
                  perpetualGrowthRate, interval='annual', apiKey=''):
    """
    historicalDCF -
    :param ticker:
    :param years:
    :param forecast:
    :param discountRate:
    :param earningsGrowthRate:
    :param capExGrowthRate:
    :param perpetualGrowthRate:
    :param interval:
    :param apiKey:
    :return:
    """
    DCFs = {}

    incomeStatement = getIncomeStatement(ticker=ticker, period=interval, apiKey=apiKey)['financials']
    balanceSheet = getBalanceSheet(ticker=ticker, period=interval, apiKey=apiKey)['financials']
    cashflowStatement = getCashFlowStatement(ticker=ticker, period=interval, apiKey=apiKey)['financials']
    enterpriseValueStatement = getEnterpriseValueStatement(ticker=ticker, period=interval, apiKey=apiKey)['enterpriseValues']

    if interval == 'quarter':
        intervals = years * 4
    else:
        intervals = years

    for interval in range(0, intervals):
        try:
            dcf = DCF(ticker, enterpriseValueStatement[interval], incomeStatement[interval:interval + 2], \
                      balanceSheet[interval:interval + 2], cashflowStatement[interval:interval + 2], \
                      discountRate, forecast, earningsGrowthRate, capExGrowthRate, perpetualGrowthRate)
        except (Exception, IndexError) as e:
            print(traceback.format_exc())
            print(f'Interval {interval} is(are) unavailable as historical statement is none.')
        else:
            DCFs[dcf['date']] = dcf
            print('-' * 60)

    return DCFs