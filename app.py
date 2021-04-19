import datetime
import pandas as pd
import numpy as np
import pandas_datareader.data as web
import plotly.express as px
import dash
import time
import dash_html_components as html

from datetime import date
from datetime import datetime
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

app = dash.Dash(__name__)

start = datetime(2000, 1, 1)
today = date.today()

symb = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'FB']
AAPL = web.DataReader('AAPL', 'yahoo', start, today)['Adj Close']
data = pd.DataFrame(index=AAPL.index)
data['AAPL'] = AAPL

for x in symb[1:]:
    globals()[x] = web.DataReader(x, 'yahoo', start, today)['Adj Close']
    data[x] = globals()[x]

app.config.suppress_callback_exceptions = True
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        <div></div>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
            <p>By: 
            <a href="https://hpquynhuw.github.io/">Quynh Huynh</a> <br>
            Last Updated: April 19, 2021 </p>
        </footer>
        
    </body>
</html>
'''

years = list(range(2000, 2022, 1))
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def give_monthly_returns(series):
    dat = series.groupby(series.index.strftime('%Y-%m')).mean()
    lag = dat.shift(1)
    returns = dat / lag - 1
    return returns


def give_weekly_returns(series):
    dat = series.resample('W').mean()
    lag = dat.shift(1)
    returns = dat / lag - 1
    return returns


for x in symb:
    globals()[x + '_weekly_returns'] = give_weekly_returns(globals()[x])
    globals()[x + '_monthly_returns'] = give_monthly_returns(globals()[x])
    globals()[x + '_daily_returns'] = globals()[x].pct_change()

all_daily_returns = data.pct_change()

dropdowns = dcc.Dropdown(
    id='selectors',
    options=[
        {'label': 'Apple Inc.', 'value': 'AAPL'},
        {'label': 'Microsoft Corp.', 'value': 'MSFT'},
        {'label': 'Facebook Inc.', 'value': 'FB'},
        {'label': 'Amazon.com Inc.', 'value': 'AMZN'},
        {'label': 'Tesla Inc.', 'value': 'TSLA'}
    ],
    value=['AAPL'],
    multi=True)

dropdown = dcc.Dropdown(
    id='selector',
    options=[
        {'label': 'Apple Inc.', 'value': 'AAPL'},
        {'label': 'Microsoft Corp.', 'value': 'MSFT'},
        {'label': 'Facebook Inc.', 'value': 'FB'},
        {'label': 'Amazon.com Inc.', 'value': 'AMZN'},
        {'label': 'Tesla Inc.', 'value': 'TSLA'}
    ],
    value='AAPL', )

dropdown1 = dcc.Dropdown(
    id='selector1',
    options=[
        {'label': 'Apple Inc.', 'value': 'AAPL'},
        {'label': 'Microsoft Corp.', 'value': 'MSFT'},
        {'label': 'Facebook Inc.', 'value': 'FB'},
        {'label': 'Amazon.com Inc.', 'value': 'AMZN'},
        {'label': 'Tesla Inc.', 'value': 'TSLA'}
    ],
    value='AAPL')


@app.callback(
    Output("yr-options", "options"),
    Input("selector", "value"),
)
def render_years(comp):
    ind = globals()[comp].index.strftime('%Y-%m')[0][2:4]
    return [{"label": x, "value": str(x)} for x in years[int(ind):]]


@app.callback(
    Output('graph1', 'figure'),
    Input('selector', 'value'))
def update_graph1(comp):
    returns = globals()[comp + '_monthly_returns']  # insert index slice for time range here
    months_index = returns.index
    pos = 100 * returns[returns >= 0]
    neg = 100 * returns[returns < 0]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months_index[returns < 0], y=neg, marker_color='crimson', name=''))
    fig.add_trace(go.Bar(x=months_index[returns >= 0], y=pos, marker_color='lightslategrey', name=''))
    fig.update_layout(showlegend=False, template='plotly_white', title=comp + ' Monthly Returns History')
    fig.update_yaxes(range=[-40, 40], title_text='Returns %')
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_traces(hovertemplate='Returns: %{y:.2f}%  <br>Date: %{x}')
    fig.update_layout(hovermode="x unified")
    fig.update_layout(margin={'l': 10, 'b': 40, 't': 60, 'r': 10})
    return fig


@app.callback(
    Output('graph2', 'figure'),
    [Input('yr-options', 'value')],
    Input('selector', 'value')
)
def update_graph2(yrs, comp):
    ans = globals()[comp + '_monthly_returns'].reset_index()
    fig = go.Figure()
    for yr in yrs:
        y = ans[ans['Date'].str.slice(0, 4) == yr]
        if yr == '2021':
            fig.add_trace(go.Scatter(x=months[0:today.month], y=100 * y['Adj Close'],
                                     mode='lines+markers', name=yr))
        else:
            fig.add_trace(go.Scatter(x=months, y=100 * y['Adj Close'],
                                     mode='lines+markers', name=yr))
    fig.update_layout(showlegend=True, template='plotly_white',
                      title='Comparing ' + comp + ' monthly returns between years')
    fig.update_xaxes(title_text='Months')
    fig.update_yaxes(title_text='Returns %')
    fig.update_traces(hovertemplate='Returns: %{y:.2f}%')
    fig.update_layout(hovermode="x unified")
    fig.update_layout(legend_x=0, legend_y=1)
    fig.update_layout(height=180, margin={'l': 30, 'b': 30, 'r': 0, 't': 50})
    return fig


@app.callback(
    Output('graph3', 'figure'),
    Input('selector', 'value'),
    Input('selector1', 'value'),
    Input('year', 'value'))
def update_graph3(comp1, comp2, year):
    pdf = pd.DataFrame()
    pdf.columns.name = 'company'
    pdf[comp1] = 100*globals()[comp1 + '_weekly_returns'][year]
    pdf[comp2] = 100*globals()[comp2 + '_weekly_returns'][year]
    fig = px.area(pdf, facet_col="company", facet_col_wrap=1)
    title = "Weekly Returns of " + comp1 + " and " + comp2 + ' in ' + year
    fig.update_layout(xaxis_rangeslider_visible=True, title_text=title)
    fig.update_layout(template='plotly_white')
    fig.update_traces(hovertemplate='Returns: %{y:.2f}% <br>Date: %{x}')
    fig.update_layout(hovermode="x unified")
    fig.update_layout(legend_x=0, legend_y=1)
    fig.update_layout(height=260, margin={'l': 30, 'b': 30, 'r': 0, 't': 50})
    return fig


app.layout = dbc.Container(
    [html.H1('Portfolio Visualizer'),
     html.Hr(),
     # html.Div(children = [
     #      dcc.Store(id="figstore", data=go.Figure()),
     #      dcc.Store(id="patchstore", data={}),
     #      dcc.Store(id="patchstore2", data={})]),
     html.H2('A Python interactive dashboard for simulating portfolio diversification.',
             style={'padding-bottom': '0.5rem'}),
     dbc.Tabs(
         [
             dbc.Tab(label="Prices", tab_id="price"),
             dbc.Tab(label="Returns", tab_id="returns"),
         ],
         id="tabs",
         active_tab="price",
     ),
     html.Div(id="tab-content"),
     html.Div(id="page-content",
              children=[dbc.Row(
                  [
                      dbc.Col(children=[
                          dbc.Row([dbc.Col(children=[
                              dbc.Label("Portfolio start date")], width=6),
                              dbc.Col(children=[
                                  dbc.Label("Investment amount at start date",
                                            style={'float': 'right', 'display': 'inline-block', 'margin-right': '0'})
                              ], width=6)]),
                          dbc.Row([dbc.Col(children=[
                              dcc.DatePickerSingle(
                                  id='portfolio-date',
                                  min_date_allowed=date(2000, 1, 1),
                                  max_date_allowed=today,
                                  initial_visible_month=date(2010, 1, 1),
                                  date=date(2010, 1, 1),
                                  style={'width': '49%'}
                              )], width=6),
                              dbc.Col(children=[
                                  dcc.Input(
                                      id="fund1", type="number", value=0,
                                      debounce=False, className='input-custom',
                                      style={'float': 'right', 'display': 'inline-block'}
                                  )], width=6)
                          ]),
                          dbc.Label("Select portfolio weight(s) for each ticker",
                                    style={'display': 'block'}),
                          dbc.Row([dbc.Col(children=[
                              dbc.Label("AAPL"),
                              dcc.Input(
                                  id="w1", type="number", value=0, debounce=False,
                                  className='input-custom')]
                              , width=4),
                              dbc.Col(children=[
                                  dbc.Label("MSFT"),
                                  dcc.Input(
                                      id="w2", type="number", value=0, debounce=False,
                                      className='input-custom',
                                  )], width=4),
                              dbc.Col(children=[
                                  dbc.Label("TSLA"),
                                  dcc.Input(
                                      id="w3", type="number", value=0, debounce=False,
                                      className='input-custom',
                                  )], width=4)]),
                          dbc.Row([
                              dbc.Col(children=[
                                  dbc.Label("AMZN"),
                                  dcc.Input(
                                      id="w4", type="number", value=0, debounce=False,
                                      className='input-custom',
                                  )], width=4),
                              dbc.Col(children=[
                                  dbc.Label("FB"),
                                  dcc.Input(
                                      id="w5", type="number", value=0, debounce=False,
                                      className="input-custom"
                                  )], width=4),
                              dbc.Col(children=[
                                  html.Button(id='submit-button', type='button',
                                              className='btn btn-primary',
                                              n_clicks=0, children='Submit')
                              ], style={'padding-top': '30px'}, width=4)
                          ])
                      ], width=6),
                      dbc.Col(children=[
                          dcc.Checklist(
                              options=[
                                  {'label': 'Show Efficient Frontier with max Sharpe ratio', 'value': 'max'},
                                  {'label': 'Show Efficient Frontier with min volatility', 'value': 'min'},
                              ],
                              value=[],
                              id='optimized-opts',
                              labelStyle={'display': 'block'}
                          ),
                          html.P('Only invest in', style={'padding-top': '5px'}),
                          dcc.Checklist(
                              options=[
                                  {'label': 'Apple Inc.', 'value': 'AAPL'},
                                  {'label': 'Microsoft Corp.', 'value': 'MSFT'},
                                  {'label': 'Tesla Inc.', 'value': 'TSLA'},
                                  {'label': 'Amazon.com Inc.', 'value': 'AMZN'},
                                  {'label': 'Facebook Inc.', 'value': 'FB'}
                              ],
                              id='no-div',
                              value=[],
                              labelStyle={'display': 'in-line block'}
                          ),

                      ],
                          style={'width': '49%', 'float': 'right', 'display': 'inline-block'},
                          width=6)
                  ],
                  style={
                      'borderBottom': 'thin lightgrey solid',
                      'backgroundColor': 'rgb(250, 250, 250)',
                      'padding': '20px'},
                  align='center'),
                  dcc.Graph(id='port-graph')],
              style={'padding-top': '20px'}
              )]
)


#
# deep_merge = """
# function batchAssign(patches) {
#     function recursiveAssign(input, patch){
#         var outputR = Object(input);
#         for (var key in patch) {
#             if(outputR[key] && typeof patch[key] == "object") {
#                 outputR[key] = recursiveAssign(outputR[key], patch[key])
#             }
#             else {
#                 outputR[key] = patch[key];
#             }
#         }
#         return outputR;
#     }
#
#     return Array.prototype.reduce.call(arguments, recursiveAssign, {});
# }
# """
#
# app.clientside_callback(
#     deep_merge,
#     Output('price-graph', 'figure'),
#     [Input('figstore', 'data'),
#      Input('patchstore', 'data'),
#      Input('patchstore2', 'data')])


def calc_custom_port(val0, weights, rets):
    calc = [val0]
    for i in range(1, len(rets)):
        ret0 = 1
        for j in symb:
            ret0 += weights[j] * rets[j][i]
        calc.append(calc[i - 1] * ret0)
    return calc


@app.callback(Output('port-graph', 'figure'),
              Input('submit-button', 'n_clicks'),
              State('portfolio-date', 'date'),
              State('fund1', 'value'),
              State('w1', 'value'),
              State('w2', 'value'),
              State('w3', 'value'),
              State('w4', 'value'),
              State('w5', 'value'),
              State('optimized-opts', 'value'),
              State('no-div', 'value'))
def port_graph(n_clicks, day0, fund, w1, w2, w3, w4, w5, pts, singles):
    dt = datetime.strptime(day0, '%Y-%m-%d')
    idx = data.index.get_loc(dt, method='nearest')
    rets = all_daily_returns[idx:].fillna(0)
    weights = {'AAPL': w1,
               'MSFT': w2,
               'TSLA': w3,
               'AMZN': w4,
               'FB': w5}

    calc = calc_custom_port(fund, weights, rets)
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=rets.index, y=calc,
                             mode='lines', name='Custom Portfolio Value'))

    if singles:
        fig = add_line(fig, singles, fund, rets)

    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Value $')
    fig.update_layout(legend_x=0, legend_y=1, template='plotly_white')
    fig.update_traces(hovertemplate='Value: $%{y:.2f} <br>Date: %{x}')
    fig.update_layout(hovermode="x unified", title='Portfolio Growth')

    fig.update_xaxes(rangeslider_visible=True)
    return fig


def add_line(fig, comps, fund, rets):
    for company in comps:
        a = symb[:]
        a.remove(company)
        wts = {k: 0.0 for k in a}
        wts[company] = 1.0
        calc = calc_custom_port(fund, wts, rets)
        fig.add_trace(go.Scatter(x=rets.index, y=calc,
                                 mode='lines', name='Only invest in ' + company))
    return fig


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
)
def render_tab_content(active_tab):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab == "price":
        return dbc.Row([
            dbc.Col(children=[
                html.Div(children=[
                    dbc.Label("Select company(s) to view prices history", style={'font-size': '1rem'}),
                    dropdowns
                ],
                    style={'align': 'right', 'text-align': 'right', 'padding': '20px 100px 10px'}),
                dcc.Graph(id='price-graph')]
            )],
            align='center')
    elif active_tab == "returns":
        return [dbc.Row(
            [
                dbc.Col(children=[
                    dbc.Label("Company"),
                    dropdown,
                    dcc.RadioItems(
                        id='return-type',
                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    )
                ], width=6),
                dbc.Col(children=[
                    dbc.Label("Select year(s) to compare monthly returns between years"),
                    dcc.Dropdown(id="yr-options", value=['2019', '2020'], multi=True),
                    dbc.Label("Select company and year to compare returns with",
                              style={'display': 'block'}),
                    html.Div([dropdown1], style={'width': '49%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(id="year", value='2020',
                                     options=[{"label": x, "value": str(x)} for x in years])
                    ],
                        style={'width': '49%', 'float': 'right', 'display': 'inline-block'}),
                ], width=6)
            ],
            style={
                'borderBottom': 'thin lightgrey solid',
                'backgroundColor': 'rgb(250, 250, 250)',
                'padding': '5px'
            }, align='center'
        ),
            html.Div([
                html.Div([dcc.Graph(id='graph1')],
                         style={'width': '49%', 'display': 'inline-block', 'padding': '20 10'}),
                html.Div([
                    dcc.Graph(id='graph2'),
                    dcc.Graph(id='graph3'),
                ], style={'display': 'inline-block', 'width': '49%', 'padding': '50 0'})
            ])
        ]
    return "No tab selected"


@app.callback(
    Output('price-graph', 'figure'),
    [Input('selectors', 'value')], )
def update_price_history(selects):
    fig = go.Figure()

    for x in selects:
        fig.add_trace(go.Scatter(x=data.index, y=data[x],
                                 mode='lines', name=x))

    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Value $')
    fig.update_layout(legend_x=0, legend_y=1, template='plotly_white', title='Stock Prices History')
    fig.update_traces(hovertemplate='Price: $%{y:.2f} <br>Date: %{x}')
    fig.update_layout(hovermode="x unified")

    fig.update_xaxes(rangeslider_visible=True)
    return fig


#
# @app.callback(Output('patchstore2', 'data'), [Input('selectors', 'value')])
# def update_price_history(selects):
#     fig = go.Figure()
#
#     for x in selects:
#         fig.add_trace(go.Scatter(x=data.index, y=data[x],
#                                  mode='lines', name=x))
#
#     fig.update_xaxes(title_text='Date')
#     fig.update_yaxes(title_text='Value $')
#     fig.update_layout(legend_x=0, legend_y=1, template='plotly_white', title='Stock Prices History')
#     fig.update_traces(hovertemplate='Price: $%{y:.2f} <br>Date: %{x}')
#     fig.update_layout(hovermode="x unified")
#
#     fig.update_xaxes(rangeslider_visible=True)
#     return fig


if __name__ == '__main__':
    app.run_server(debug=True)
