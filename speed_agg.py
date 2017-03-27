########## Select correct directory
import os
import numpy as np
import pandas as pd
import plotly.plotly as py
import plotly.offline as po
import plotly.graph_objs as go

#### Example: Restrict to just April
#df = df.loc[lambda df: df['Month'] == 4]

########## Example: AGGREGATE 5-minute speeds and GROUP BY month, day, ap
#agg1 = {'speed' : {'avgSpeed' : 'mean'}}
#df15 = df.groupby(['tmc_code','Date','ap'], as_index=False).agg(agg1, as_index=False)
#pdf = df15[['tmc_code', 'tstamp', 'speed']]
#pdf.to_csv('I4_P_15min_Apr.csv', index=False)

def extract_vals(date_str):
    is_approx = False
    date, time, ampm = date_str.split(' ')
    hour, minute, second = time.split(':')
    
    if ampm.endswith('*'): # Check if is approximated (has an *) and remove '*'
        is_approx = True
        ampm = ampm[:2]

    is_pm = ampm.lower() == 'pm'
    ap = (int(hour) % 12) * 4 + int(minute) // 15 + (48 if is_pm else 0)
    return date, ap, is_approx

def create_columns(data):
    dates, aps, is_approxs = zip(*data)
    return list(dates), list(aps), list(is_approxs)

def percentile(n):
    def percentile_(x):
        return np.percentile(x,n)
    percentile_.__name__='percentile_%s' % n
    return percentile_

########## Changing to the correct directory
os.chdir('C:\\Users\ltrask\Documents\BlueMac Data')    

########## Load 5-minute csv into pandas dataframe
numLinesToSkip = 0
f = open('DIGI145_to_DIGI157.csv', 'r')
for line in f:
    tokens = line.split(',')
    if tokens[0] == "Start Time":
        break
    numLinesToSkip+=1

df = pd.read_csv('DIGI145_to_DIGI157.csv', skiprows=numLinesToSkip)
#df['Date'] = [dStr.split(' ')[0] for dStr in df['Start Time']]
#df['AP'] = [extract_ap_from_time(dStr) for dStr in df['Start Time']]
df['Date'], df['AP'], df['is_approx'] = create_columns([extract_vals(dStr) for dStr in df['Start Time']])

######### Aggregating for RL Data
apGroup = df.groupby(['AP'])
speedCol = apGroup['Average Speed(mph)']
dfRL=speedCol.agg([np.mean, percentile(95), percentile(5)])

timeStamps = ['2000-01-01 ' +str(apIdx // 4)+':'+str((apIdx % 4)*15)+':00' for apIdx in dfRL.index]

data = [
    go.Scatter(
        x=timeStamps, 
        y=dfRL['mean'],
        fill = 'tonexty',
        fillcolor = '#B0C4DE',
        line=dict(color='rgb(205,92,92)'),
        name='Average'
    ),
    go.Scatter(
        x=timeStamps, 
        y=dfRL['percentile_95'],
        line=dict(color='rgb(176,196,222)'),
        fillcolor = '#B0C4DE',
        fill = 'tonexty',
        name='95th Percentile'
    ),
    go.Scatter(
        x=timeStamps, 
        y=dfRL['percentile_5'],
        fillcolor = '#FFFFFF',
        fill = 'tozeroy',
        line=dict(color='rgb(176,196,222)'),
        name='5th Percentile'
    )
]

layout = go.Layout(
    title='Average Speed Across All Days',
    yaxis=dict(title='Speed (mph)'),
    xaxis=dict(title='Analysis Period', tickformat="%I:%M%p")
)

fig = go.Figure(data=data, layout=layout)

po.init_notebook_mode()
po.iplot(fig, filename='stacked-area')

