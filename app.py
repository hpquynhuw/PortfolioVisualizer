import datetime
import pandas as pd
import numpy as np
import pandas_datareader.data as web
import plotly.express as px
import dash
import time
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go

app = dash.Dash(__name__)

start = datetime.datetime(2000, 1, 1)
end = datetime.datetime(2021, 3, 1)

symb = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'FB']
for x in symb:
    globals()[x] = web.DataReader(x, 'yahoo', start, end)['Adj Close']

data = pd.DataFrame(index=AAPL.index)
for x in symb:
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
        </footer>
        <div>Last Updated: March 24, 2021</div>
    </body>
</html>
'''

years = list(range(2000, 2021, 1))
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def give_returns(series):
    dat = series.groupby(series.index.strftime('%Y-%m')).mean()
    lag = dat.shift(1)
    returns = dat / lag - 1
    return returns


def give_monthly_returns(series):
    dat = series.groupby(series.index.strftime('%Y-%m')).mean()
    lag = dat.shift(1)
    returns = dat / lag - 1
    return returns.reset_index()


def give_weekly_returns(series):
    dat = series.resample('W').mean()
    lag = dat.shift(1)
    returns = dat / lag - 1
    return returns


for x in symb:
    globals()[x + '_returns'] = give_returns(globals()[x])
    globals()[x + '_monthly_returns'] = globals()[x + '_returns'].reset_index()

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
    value='AAPL', )

controls = dbc.Card(
    [dbc.FormGroup(
        [dbc.Label("Company"),
         dropdown,
         ]
    ),
        dbc.FormGroup(
            [dbc.Label("Select year(s) to compare returns"),
             dcc.Dropdown(id="yr-options", value=['2000', '2001'], multi=True),
             ]
        ),
        dbc.FormGroup(
            [dbc.Label("Select company and year to compare returns with"),
             dropdown1,
             dcc.Dropdown(id="year", value='2020',
                          options=[{"label": x, "value": str(x)} for x in years]),
             ]
        )
    ],
    body=True)


@app.callback(
    Output('graph3', 'figure'),
    Input('selector', 'value'),
    Input('selector1', 'value'),
    Input('year', 'value'))
def update_graph3(comp1, comp2, year):
    time.sleep(2)
    pdf = pd.DataFrame()
    pdf.columns.name = 'company'
    pdf[comp1] = give_weekly_returns(globals()[comp1][year])
    pdf[comp2] = give_weekly_returns(globals()[comp2][year])
    fig = px.area(pdf, facet_col="company", facet_col_wrap=1)
    title = "Weekly Returns of " + comp1 + " and " + comp2 + ' in ' + year
    fig.update_layout(xaxis_rangeslider_visible=True, title_text=title)
    return fig


@app.callback(
    Output('graph1', 'figure'),
    Input('selector', 'value'))
def update_graph1(comp):
    returns = globals()[comp + '_returns']  # insert index slice for time range here

    months_index = globals()[comp].index.strftime('%Y-%m').unique()
    pos = 100 * returns[returns >= 0]
    neg = 100 * returns[returns < 0]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months_index[returns < 0], y=neg, marker_color='crimson', name=''))
    fig.add_trace(go.Bar(x=months_index[returns >= 0], y=pos, marker_color='lightslategrey', name=''))
    fig.update_layout(showlegend=False, template='plotly_white', title=comp + ' Monthly Returns History')
    fig.update_yaxes(range=[-40, 40], title_text='Returns %')
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_traces(hovertemplate='Returns: %{y:.2f}%')
    fig.update_layout(hovermode="x unified")
    return fig


@app.callback(
    Output('graph2', 'figure'),
    [Input('yr-options', 'value')],
    Input('selector', 'value')
)
def update_graph2(yrs, comp):
    ans = give_monthly_returns(globals()[comp])
    fig = go.Figure()
    for yr in yrs:
        y = ans[ans['Date'].str.slice(0, 4) == yr]
        if yr == '2021':
            fig.add_trace(go.Scatter(x=months[0:3], y=100 * y['Adj Close'],
                                     mode='lines+markers', name=yr))
        else:
            fig.add_trace(go.Scatter(x=months, y=100 * y['Adj Close'],
                                     mode='lines+markers', name=yr))
    fig.update_layout(showlegend=True, template='plotly_white', title='Comparing ' + comp + ' annual monthly returns')
    fig.update_xaxes(title_text='Months')
    fig.update_yaxes(title_text='Returns %')
    fig.update_traces(hovertemplate='Returns: %{y:.2f}%')
    fig.update_layout(hovermode="x unified")
    return fig


app.layout = dbc.Container(
    [html.H1('Hello Dash'),
     html.Hr(),
     html.H2('Dash: A web application framework for Python.'),
     dbc.Tabs(
         [
             dbc.Tab(label="Prices", tab_id="price"),
             dbc.Tab(label="Returns", tab_id="returns"),
         ],
         id="tabs",
         active_tab="price",
     ),
     html.Div(id="tab-content")
     ]
)


@app.callback(
    Output("yr-options", "options"),
    Input("selector", "value"),
)
def render_years(comp):
    ind = globals()[comp].index.strftime('%Y-%m')[0][2:4]
    return [{"label": x, "value": str(x)} for x in years[int(ind):]]


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
                html.Div(children=[dbc.Label("Select company(s) to view prices history", style={'font-size': '1rem'}),
                                   dropdowns],
                         style={'align': 'right', 'text-align': 'right', 'padding': '20px 100px 10px'}),
                dcc.Graph(id='output-graph-range-slider')
            ])],
            align='center')
    elif active_tab == "returns":
        return [dbc.Row(
            [
                dbc.Col(controls, width=4),
                dbc.Col(children=[dcc.Graph(id='graph1')], width=8),
            ],
            align='center'),
            dbc.Row(
                [
                    dbc.Col(children=[dcc.Graph(id='graph2')], width=6),
                    dbc.Col(children=[dcc.Graph(id='graph3')], width=6)
                ],
                align='center')
        ]
    return "No tab selected"


@app.callback(
    Output('output-graph-range-slider', 'figure'),
    [Input('selectors', 'value')], )
def update_output(selects):
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


if __name__ == '__main__':
    app.run_server(debug=True)
