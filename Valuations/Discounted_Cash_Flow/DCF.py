import argparse, traceback
from decimal import Decimal
from API_Request import *

def unleveredFCF(ebit, taxRate, nonCashCharges, currentWorkingCapital, capEx):
    """
    unleveredFCF - formulates to prompt unlevered free cash flow.
    :param ebit: earnings before interest and tax --> revenue - COGS - operating expenses
    :param taxRate: input tax rate
    :param nonCashCharges:
    :param currentWorkingCapital: annual change in net working capital
    :param capEx: capital expenditures
    :return: unlevered free cash flow
    """
    return ebit * (1 - taxRate) + nonCashCharges + currentWorkingCapital + capEx

def enterpriseValueCalculator(incomeStatement, cashflowStatement, balanceSheet, period, discountRate,
                              earningsGrowthRate, capExGrowthRate, perpetualGrowthRate):
    """
    enterpriseValueCalculator - calculate enterprise value by Net Present Value of FCF + NPV Terminal Value (WACC discounted).
    :param incomeStatement: income statement
    :param cashflowStatement: cash flow statement
    :param balanceSheet: balance sheet
    :param period: years in future to be calculated
    :param discountRate: input discount rate
    :param earningsGrowthRate: projected YoY earning growth rate
    :param capExGrowthRate: projected YoY capital expenditure growth rate
    :param perpetualGrowthRate: projected YoY terminal value perpetuity growth rate
    :return: enterprise value
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
    equityValue - calculates value of company's shares & loands that shareholders made available to company
    :param enterpriseValue: EV = market cap + total debt - cash
    :param enterpriseValueStatement: enterprise value statement (abt debt & cash)
    :return: equityValue (EV - debt + cash), sharePrice (EV / shares outstanding)
    """
    equityValue = enterpriseValue - enterpriseValueStatement['+ Total Debt']
    equityValue += enterpriseValueStatement['- Cash & Cash Equivalents']
    sharePrice = equityValue / float(enterpriseValueStatement['Number of Shares'])

    return equityValue, sharePrice

def getDiscountRate():
    """
    getDiscountRate - calculate WACC (Weighted Average Cost of Capital) // has to be dynamically calculated.
    :return: WACC
    """
    ########### needs to be done properly ##############
    return 0.1

def DCF(ticker, enterpriseValueStatement, incomeStatement, balanceSheet, cashFlowStatement, discountRate, \
    forecast, earningGrowthRate, capitalExpenditureGrowthRate, perpetualGrowthRate):
    """
    DCF - calculates Discounted Cash Flow model without dynamic implementation of discount rate and CWC rate
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
    historicalDCF - calculates historical (desired period) Discounted Cash Flows
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