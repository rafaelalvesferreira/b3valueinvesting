# %%
from collections import defaultdict
from datetime import datetime as dt
import urllib3
import certifi
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import numpy as np

import pandas_datareader as dr
from dateutil.relativedelta import relativedelta

#%%
def GetTickers():
    """Scrap the B3 stock tickers from Yahoo Finanças

    :return: [list of dictionaries for Dash dcc.dropdown]
    :rtype: [list]
    """
    # Constants used
    b3Industries = ['Energia-Petroleo-Gas',
                    'Industria-Financeira',
                    'Saude-Farmaceutica',
                    'Telecomunicacoes-Tecnologia',
                    'Industria-Alimenticia',
                    'Industria-Manufatureira',
                    'Servicos-diversos',
                    'Varejo',
                    'Construcao-Equipamentos',
                    'Bens-de-consumo',
                    'Industrias-em-geral']

    yahooFinanceUrl = 'https://br.financas.yahoo.com/industries/'

    # List to store the dropdown menu values
    # stockInfo = [{'value': '^BVSP', 'label': '^BVSP | Ibovespa'}]
    stockInfo = []

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                               ca_certs=certifi.where())

    for industry in b3Industries:
        page = http.request('GET', yahooFinanceUrl+industry)
        page_html = BeautifulSoup(page.data, 'lxml')
        for search in page_html.select(r"tbody a.Fw\(b\)"):
            if search['data-symbol'] != search['title']:
                stockInfo.append({'value': search['data-symbol'],
                                  'label': (
                                      search['data-symbol'] +
                                      ' | ' + search['title'])
                                  })

    return stockInfo


def ScrapTableValues(key_perf_indicator, driver, url):
    """The function opens the webpage and loop for the metric selected

    :param key_perf_indicator: metric to be found on the table
    :type key_perf_indicator: str
    :param driver: selenium webdriver
    :type driver: object
    :param url: url of page to be scrapped
    :type url: str
    :return: key value pair tuple on a list
    :rtype: list
    """
    kpi_data = []
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.XPATH,
             '//*[@id="__next"]/div/div[4]/div[1]/div/div/section/div[2]\
             /div[3]')))

        for index, kpi in enumerate(driver.find_elements_by_tag_name('tr th span'), start=1):
            if kpi.text == key_perf_indicator:
                for column in range(1, 6):
                    for value in driver.find_elements_by_xpath(f'//*[@id="__next"]/div/div[4]/div[1]/div/div/section/div[2]/div[3]/table/tbody/tr[{index}]/td[{column}]'):
                        try:
                            kpi_data.append(
                                (kpi.text, float(value.text.replace(',', ''))))
                        except ValueError:
                            try:
                                kpi_data.append((kpi.text, float(value.text.strip('()').replace(',', '')) * (-1)))
                            except ValueError:
                                kpi_data.append((kpi.text, 0))

    except TimeoutException:
        driver.quit()

    return kpi_data


def GetFiancialReport(ticker):
    """Scrap the financial data from Reuters webpage

    :param ticker: stock ticker
    :type ticker: str
    :return: dataframe with all data gathered
    :rtype: pandas dataframe
    """
    income_stat_annual = ['Net Income',
                          'Interest Exp.(Inc.),Net-Operating, Total',
                          'Diluted Normalized EPS',
                          'Net Income Before Taxes']

    balance_sheet_anual = ['Total Assets',
                           'Total Long Term Debt',
                           'Total Liabilities',
                           "Total Liabilities & Shareholders' Equity"]

    reuters_income_url = ('https://www.reuters.com/companies/' +
                          ticker + '/financials/' + 'income-statement-annual')

    reuters_balance_url = ('https://www.reuters.com/companies/' +
                           ticker + '/financials/' + 'balance-sheet-annual')

    data_scrapped = defaultdict(list)
    kpi_data = []
    column_year = []

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")

    driver = webdriver.Firefox(
        options=firefox_options,)
        # executable_path='/app/vendor/geckodriver/geckodriver')

    try:
        driver.get(reuters_income_url)
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.XPATH,
             '//*[@id="__next"]/div/div[4]/div[1]/div/div/section/div[2]\
             /div[3]')))

        for year in range(2, 7):
            column_year.append(driver.find_element_by_xpath(
                f'//*[@id="__next"]/div/div[4]/div[1]/div/div/section/div[2]\
                /div[3]/table/thead/tr/th[{year}]/time').text)

        for item in income_stat_annual:
            kpi_data += ScrapTableValues(item, driver, reuters_income_url)

        for item in balance_sheet_anual:
            kpi_data += ScrapTableValues(item, driver, reuters_balance_url)

    finally:
        driver.quit()

    # transforming the column_year in a datetime object
    column_year = [('Year', dt.strptime(item, '%d-%b-%y').year) for item in column_year]

    kpi_data += column_year

    # creating a defaultdict from the kpi_data list
    for key, value in kpi_data:
        data_scrapped[key].append(value)

    data_scrapped_df = pd.DataFrame.from_dict(data_scrapped,
                                              orient='columns')

    data_scrapped_df['EPS Growth'] = data_scrapped_df['Diluted Normalized EPS'].pct_change(-1).fillna(0).astype(float).map('{:.2%}'.format)
    data_scrapped_df['Shareholders Equity'] = (data_scrapped_df["Total Liabilities & Shareholders' Equity"] - data_scrapped_df['Total Liabilities'])
    data_scrapped_df['ROE'] = (data_scrapped_df['Net Income'] / data_scrapped_df['Shareholders Equity'].astype(float)).astype(float).map('{:.2f}'.format)
    data_scrapped_df['ROA'] = ((data_scrapped_df['Net Income'] / data_scrapped_df['Total Assets'])).astype(float).map('{:.2f}'.format)
    data_scrapped_df['Net Income Before Taxes'] = data_scrapped_df['Net Income Before Taxes'].astype(float).map('{:,.2f}'.format)
    data_scrapped_df['Net Income'] = data_scrapped_df['Net Income'].astype(float).map('{:,.2f}'.format)
    data_scrapped_df['Diluted Normalized EPS'] = data_scrapped_df['Diluted Normalized EPS'].astype(float).map('{:.2f}'.format)
    data_scrapped_df['Total Long Term Debt'] = data_scrapped_df['Total Long Term Debt'].astype(float).map('{:,.2f}'.format)
    data_scrapped_df['Shareholders Equity'] = data_scrapped_df['Shareholders Equity'].astype(float).map('{:,.2f}'.format)

    # Check a way to include a normalized IC Ratio
    # data_scrapped_df['Interest Coverage Ratio'] =
    # data_scrapped_df['Net Income Before Taxes'] /
    # data_scrapped_df['Interest Exp.(Inc.),Net-Operating, Total']

    data_scrapped_df = data_scrapped_df.rename(columns={
        'Net Income Before Taxes': 'EBIT'})

    return data_scrapped_df.loc[:, ['Year',
                                    'Diluted Normalized EPS',
                                    'EPS Growth',
                                    'Net Income',
                                    'Shareholders Equity',
                                    'ROA',
                                    'Total Long Term Debt',
                                    'EBIT',
                                    'ROE',]
                                ]


def CheckWarningFlags(data_table):
    """Get the data from the scrapped table and analyse it comparing to
    predefined rules.

    :param data_table: [Data Table from GetFinancialReport]
    :type data_table: [list]
    :return: [Warning Flags]
    :rtype: [list]
    """

    df = pd.DataFrame.from_dict(data_table)
    reason_dict_list = []

    # Checking EPS Growth positive gradient
    df['EPS Growth'] = df['EPS Growth'].map(lambda x: x.rstrip('%')).astype(float) / 100
    if df.loc[df['EPS Growth'].diff(-1) < 0].Year.tolist():
        warning_data = df.loc[df['EPS Growth'].diff(-1) < 0].Year.tolist()
        eps_string = ''

        for year in range(len(warning_data)-1, -1, -1):
            eps_string = eps_string + str(warning_data[year]) + ', '

        reason_dict_list.append(dict(reason=f'Há redução do crescimento em {eps_string}'))

    # Checking ROE mean
    df['ROE'] = df['ROE'].map(lambda x: float(x))
    if df.ROE.mean() < 0.15:
        reason_dict_list.append(dict(reason=f'A média do ROE é de {df.ROE.mean():.2f}, menor que 0,13'))

    # Checking ROA mean
    df['ROA'] = df['ROA'].map(lambda x: float(x))
    if df.ROA.mean() < 0.07:
        reason_dict_list.append(dict(reason=f'A média do ROA é de {df.ROA.mean():.2f}, menor que 0,07'))

    # Checking Long Term Debt is < 5 * net income
    df['Total Long Term Debt'] = df['Total Long Term Debt'].map(lambda x: x.replace(',', '')).astype(float)
    df['Net Income'] = df['Net Income'].map(lambda x: x.replace(',', '')).astype(float)

    if df['Total Long Term Debt'].head(1).values[0] > 5 * df['Net Income'].head(1).values[0]:
        reason_dict_list.append(dict(reason=f'A Dívida de Longo Prazo é cinco vezes o Lucro Líquido.'))

    return reason_dict_list


# %%
# # inputs
# ticker = 'PETR4.SA'
# dados = GetFiancialReport(ticker)
# # %%
# discount_rate = 0.15
# margin_rate = 0.15

# %%
def FuturePricing(ticker, data_table, discount_rate, margin_rate):
    df = pd.DataFrame.from_dict(data_table)

    years = 10
    margin_price = 0
    pv = float(df['Diluted Normalized EPS'].iloc[0]) # last EPS
    fv = float(df['Diluted Normalized EPS'].iloc[-1])

    annual_growth_rate = np.rate(5, 0, -pv, fv)

    future_eps = abs(np.fv(annual_growth_rate, years, 0, pv))

    # Finding the P/E Ratio
    selected_stock_df = dr.DataReader(
        ticker,
        data_source='yahoo',
        start=(dt.now() - relativedelta(years=5)),
        end=dt.now())

    selected_stock_df['year'] = pd.DatetimeIndex(selected_stock_df.index).year
    gframe = selected_stock_df.groupby('year').head(1).set_index('year').iloc[::-1]
    df.set_index('Year', inplace=True)

    price_by_year = pd.DataFrame()
    price_by_year['Close'] = gframe['Close']
    price_by_year['EPS'] = df['Diluted Normalized EPS'].astype(float)
    price_by_year['P/E Ratio'] = price_by_year['Close'] / price_by_year['EPS']

    pe_ratio = price_by_year['P/E Ratio'].min()

    FV = future_eps * pe_ratio
    PV = abs(np.pv(discount_rate, years, 0, FV))

    if FV > 0:
        margin_price = PV * (1 - margin_rate)

    last_share_price = selected_stock_df.Close.tail(1).values[0]

    decision = np.where(last_share_price < margin_price, 'COMPRAR', 'VENDER')

    answer = [dict(annual_growth_rate=np.round(annual_growth_rate, 2),
                  last_eps=np.round(pv, 2),
                  future_eps=np.round(future_eps, 2),
                  pe_ratio=np.round(pe_ratio, 2),
                  FV=np.round(FV, 2),
                  PV=np.round(PV, 2),
                  margin_price=np.round(margin_price, 2),
                  last_share_price=np.round(last_share_price, 2),
                  decision=decision)]

    return answer

# # %%
# ticker = 'PETR4.SA'
# dados = GetFiancialReport(ticker)
# # %%
# dados_up = dados.to_dict()

# # %%
# discount_rate = 0.15
# margin_rate = 0.15
# ans = FuturePricing(ticker, dados_up, discount_rate, margin_rate)

# # %%
# ans

# # %%
