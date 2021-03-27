import datetime
import pandas as pd
import numpy as np
import pandas_datareader.data as web
import plotly.express as px
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

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


def give_returns(series):
    dat = series.groupby(series.index.strftime('%Y-%m')).mean()
    lag = dat.shift(1)
    returns = dat / lag - 1
    return returns


dropdowns = dcc.Dropdown(
    id='selector',
    options=[
        {'label': 'Apple Inc.', 'value': 'AAPL'},
        {'label': 'Microsoft Corp.', 'value': 'MSFT'},
        {'label': 'Facebook Inc.', 'value': 'FB'},
        {'label': 'Amazon.com Inc.', 'value': 'AMZN'},
        {'label': 'Tesla Inc.', 'value': 'TSLA'}
    ],
    value=['AAPL'],
    multi=True)

controls = dbc.Card(
    [dbc.FormGroup(
        [dbc.Label("Company"),
         dropdowns,
         ]
    ),
        dbc.FormGroup(
            [dbc.Label("View"),
             dcc.Dropdown(
                 id="options",
                 options=[
                     {"label": "Returns history", "value": 'all'},
                     {"label": 'Compare yearly trends', 'value': 'monthly'}
                 ],
                 value="all",
             ),
             ]),
        dbc.FormGroup(html.Div(id="year-options")),
    ],
    body=True,
)

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
    Output("year-options", "children"),
    Input("options", "value"),
)
def render_year_content(value):
    if value == 'all':
        return [dbc.Label("Select year range"), html.Br(),
                dcc.Input(id="year1", type="text", placeholder=""),
                dcc.Input(id="year2", type="text", placeholder=""), ]
    else:
        return [
            dbc.Label("Select year(s)"),
            dcc.Dropdown(
                id="options",
                options=[
                    {"label": x, "value": x} for x in years
                ],
                multi=True
            )]


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
                html.Div(children=[dropdowns],
                         style={'align': 'right', 'text-align': 'right', 'padding': '20px 100px 10px'}),
                dcc.Graph(id='output-graph-range-slider', style={'padding': '0.5rem'}),
                html.P('Adjust slider to specify time range', style={'font-size': '1.5rem', 'padding-left': '0.5rem'}),
                dcc.RangeSlider(
                    id='my-range-slider',
                    min=2000, max=2021, step=1,
                    marks={
                        2000: {'label': '2000', 'style': {'color': '#77b0b1', 'display': 'inline'}},
                        2001: {'label': '2001'},
                        2002: {'label': '2002'},
                        2003: {'label': '2003'},
                        2004: {'label': '2004'},
                        2005: {'label': '2005'},
                        2006: {'label': '2006'},
                        2007: {'label': '2007'},
                        2008: {'label': '2008'},
                        2009: {'label': '2009'},
                        2010: {'label': '2010', 'style': {'display': 'inline'}},
                        2011: {'label': '2011'},
                        2012: {'label': '2012'},
                        2013: {'label': '2013'},
                        2014: {'label': '2014'},
                        2015: {'label': '2015'},
                        2016: {'label': '2016'},
                        2017: {'label': '2017'},
                        2018: {'label': '2018'},
                        2019: {'label': '2019'},
                        2020: {'label': '2020'},
                        2021: {'label': '2021', 'style': {'display': 'inline'}}
                    }, value=[2000, 2021], allowCross=False)
            ])],
            align='center')
    elif active_tab == "returns":
        return dbc.Row(
            [
                dbc.Col(controls, width=4),
                dbc.Col(dcc.Graph(id='output-graph-range-slider', style={'padding': '0.5rem'}), width=8),
            ]
        )
    return "No tab selected"


@app.callback(
    Output('output-graph-range-slider', 'figure'),
    [Input('selector', 'value')],
    [Input('my-range-slider', 'value')])
def update_output(selects, range_slider):
    dat1 = str(range_slider[0])
    dat2 = str(range_slider[1])
    dat = data[dat1:dat2]

    y = []
    for x in selects:
        y.append(dat[x])

    fig = px.line(x=dat.index, y=y, title="Stock Prices " + dat1 + "-" + dat2, template='plotly_white')

    i = 0
    for x in selects:
        fig.data[i].name = x
        i = i + 1

    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Value $')
    fig.update_layout(legend_x=0, legend_y=1)
    fig.update_traces(hovertemplate='Price: $%{y:.2f} <br>Date: %{x}')
    fig.update_layout(hovermode="x unified")
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
