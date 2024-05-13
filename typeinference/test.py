import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, display_html
data = pd.read_csv("../data/prices.csv")
data[data.symbol == "FB"].head()
len(data.symbol.unique())
# Variation of AAPL Stock
# Ref: https://plot.ly/python/ohlc-charts/


aapl = data[data.symbol == "AAPL"]
trace = go.Ohlc(x=aapl['date'],
                open=aapl['open'],
                high=aapl['high'],
                low=aapl['low'],
                close=aapl['close'],
                increasing=dict(line=dict(color= '#17BECF')),
                decreasing=dict(line=dict(color= '#7F7F7F')))

layout = {
    'title' : 'AAPL Stock Variation',
    'yaxis' : {'title': 'Stock Value'},
    'xaxis' : {'title' : 'Year'},
    'shapes': [{
        'x0': '2014-06-09', 'x1': '2014-06-09',
        'y0': 0, 'y1': 1, 'xref': 'x', 'yref': 'paper',
        'line': {'color': 'rgb(30,30,30)', 'width': 1}
    }],
     'annotations': [{
        'x': '2014-06-09', 'y': 0.05, 'xref': 'x', 'yref': 'paper',
        'showarrow': False, 'xanchor': 'left',
        'text': 'Steep Drop in Stock Price'
    }]
}

data_aapl = [trace]
fig = dict(data=data_aapl, layout=layout)

py.iplot(fig, filename='simple_ohlc')
