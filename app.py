from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas_datareader as dr
import utils


## Set up the app
external_stylesheets = ['https://github.com/plotly/dash-app-stylesheets/blob/master/dash-goldman-sachs-report.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.title = 'B3 Value Investing'

## Set up the layout
app.layout = html.Div([
    html.Div([
        dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type='circle'),
        html.H1('B3 Value Investing'),
        # Create the ticker dropdown
        html.H3('Escolha uma ação'),
        dcc.Dropdown(
            id='tickers-dropdown',
            options=utils.GetTickers(),
            value='PETR4.SA'
        ),
        html.H3('Gráfico de preço das ações em 5 anos'),
        dcc.Graph(id='stock-graph'),
        html.P('')
    ], style={'width': '40%', 'display': 'inline-block'}),
    html.Div([
        html.H3('Variáveis Críticas e Índices'),
        html.H5('Valores em milhões de Reais.'),
        dash_table.DataTable(
            id='data-table',
            columns=[
                {'id': 'Year', 'name': 'Ano', 'type': 'numeric',},
                {'id': 'Diluted Normalized EPS', 'name': 'EPS Diluído Normalizado', 'type': 'numeric',},
                {'id': 'EPS Growth', 'name': 'Crescimento do EPS', 'type': 'numeric', },
                {'id': 'Net Income', 'name': 'Lucro Líquido', 'type': 'numeric', },
                {'id': 'Shareholders Equity', 'name': 'Patrimônio Líquido', 'type': 'numeric',},
                {'id': 'ROA', 'name': 'ROA', 'type': 'numeric',},
                {'id': 'Total Long Term Debt', 'name': 'Dívida de Longo Prazo', 'type': 'numeric',},
                {'id': 'ROE', 'name': 'ROE', 'type': 'numeric',},
                {'id': 'EBIT', 'name': 'EBIT', 'type': 'numeric',},
            ],
            # style table
            # style_table={
            #     'maxHeight': '40ex',
            #     'overflowY': 'scroll',
            #     'width': '100%',
            #     'minWidth': '100%',
            # },
            # style cell
            style_cell={
                'fontFamily': 'Open Sans',
                'textAlign': 'right',
                'height': '8px',
                'padding': '1px 10px',
                'whiteSpace': 'inherit',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            # style header
            style_header={
                'fontWeight': 'bold',
                'backgroundColor': 'blue',
                'color': 'white',
            },
            # style data
            style_data_conditional=[
                {
                    # stripped rows
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
            ],
        ),
        html.P(''),
        html.H3('Alertas'),
        dash_table.DataTable(
            id='reason-list',
            columns=[
                {'id': 'reason', 'name': 'Razões', 'type': 'text',},
            ],
            style_cell={
                'fontFamily': 'Open Sans',
                'textAlign': 'left',
                'height': '8px',
                'padding': '1px 10px',
                'whiteSpace': 'inherit',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            # style header
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'left',
                'backgroundColor': 'blue',
                'color': 'white',
            },
            # style data
            style_data_conditional=[
                {
                    # stripped rows
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
            ],
        ),
        html.P(''),
        html.H3('Inflação Prevista Para os Próximos 5 anos'),
        dcc.Slider(
            id='discountrate-slider',
            min=0,
            max=1,
            value=0.15,
            step=0.05,
            marks={i: f'{i:.2f}' for i in np.arange(0, 1, 0.05)}
        ),
        html.H3('Margem de Erro na Estimativa da Inflação'),
        dcc.Slider(
            id='marginrate-slider',
            min=0,
            max=1,
            value=0.15,
            step=0.05,
            marks={i: f'{i:.2f}' for i in np.arange(0, 1, 0.05)}
        ),
    ], style={'width': '59%', 'float': 'right', 'display': 'inline-block'}),
    html.Div([
        dash_table.DataTable(
            id='future-price-table',
            columns=[
                {'id': 'annual_growth_rate', 'name': 'Taxa de Crescimento Anual', 'type': 'numeric', },
                {'id': 'last_eps', 'name': 'Último EPS', 'type': 'numeric', },
                {'id': 'future_eps', 'name': 'EPS Futuro', 'type': 'numeric', },
                {'id': 'pe_ratio', 'name': 'Taxa P/E', 'type': 'numeric', },
                {'id': 'FV', 'name': 'Est Valor Ação 10 anos', 'type': 'numeric', },
                {'id': 'PV', 'name': 'Preço Alvo Atual da Ação', 'type': 'numeric', },
                {'id': 'margin_price', 'name': 'Valor Marginal', 'type': 'numeric', },
                {'id': 'last_share_price', 'name': 'Últ Valor Ação', 'type': 'numeric', },
                {'id': 'decision', 'name': 'Decisão', 'type': 'text', },
            ],
            style_cell={
                'fontFamily': 'Open Sans',
                'textAlign': 'left',
                'height': '8px',
                'padding': '1px 10px',
                'whiteSpace': 'inherit',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            # style header
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'left',
                'backgroundColor': 'blue',
                'color': 'white',
            },
        )], style={'width': '95%', 'float': 'right', 'display': 'inline-block'}
    )
])


## Set up the callbacks

# Stock graph callback
@app.callback(
    Output(component_id='stock-graph', component_property='figure'),
    [Input(component_id='tickers-dropdown', component_property='value')]
)
def UpdateStockGraph(selected_dropdown_value):
    selected_stock_df = dr.DataReader(
        selected_dropdown_value,
        data_source='yahoo',
        start=(dt.now() - relativedelta(years=5)),
        end=dt.now())

    yAxisLabel = 'Valor da ação em BRL'

    return {
        'data': [{
            'open': selected_stock_df.Open,
            'high': selected_stock_df.High,
            'low': selected_stock_df.Low,
            'close': selected_stock_df.Close,
            'x': selected_stock_df.index,
            'type': 'candlestick'
        }],
        'layout': {
                'title': selected_dropdown_value,
                'xaxis': {
                    'title': 'Data'
                },
                'yaxis': {
                    'title': yAxisLabel
                }
            }
        }

# Data table callback
@app.callback(
    Output(component_id='data-table', component_property='data'),
    [Input(component_id='tickers-dropdown', component_property='value')]
)
def UpdateTable(selected_dropdown_value):
    df = utils.GetFiancialReport(selected_dropdown_value)
    return df.to_dict('records')

# Reason table callback
@app.callback(
    Output(component_id='reason-list', component_property='data'),
    [Input(component_id='data-table', component_property='data')]
)
def CreateReasonList(data_table):
    return utils.CheckWarningFlags(data_table)

# Reason table callback
@app.callback(
    Output(component_id='future-price-table', component_property='data'),
    [Input(component_id='tickers-dropdown', component_property='value'),
     Input(component_id='data-table', component_property='data'),
     Input(component_id='discountrate-slider', component_property='value'),
     Input(component_id='marginrate-slider', component_property='value'),
     ]
)
def CreateDecision(ticker, data_table, discount_rate, margin_rate):
    return utils.FuturePricing(ticker, data_table, discount_rate, margin_rate)


if __name__ == '__main__':
    app.run_server(debug=True)


# %%