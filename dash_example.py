# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 11:35:38 2019

@author: CS08
"""

import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd


input_dir = r"C:\Users\cs08\Documents\Projects\twitter_extractions\\"
mapbox_access_token  = pd.read_csv(input_dir + "mapbox_key.txt")["key"].item()
#this loads a mapbox access token from a text file

df = pd.read_csv(input_dir + "sample.csv")

labels =["global fishing watch"]
data = [df]

#can add  many datasets so long as they are loaded 
#correctly and in same format as sample.csv

#live version connects to tables within database and auto retrieves.
#this version uses csv for demo purposes

dataframes = dict(zip(labels,data))


app = dash.Dash()
app.layout = html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': i, 'value': i} for i in dataframes]
    ),
    
    html.Div([
        html.Div(dcc.Graph(id='graph-1'), className="six columns"),
        html.Div(dcc.Graph(id='graph-2'), className="six columns"),
    ], className="row"),

    html.Div([
        html.Div(dcc.Graph(id='graph-3'), className="six columns"),
        html.Img(id="image",style={"width":800,"height":600}),
        html.P(id="gap"),
        html.Button('Left', id='button',n_clicks =0,n_clicks_timestamp=0),
        html.Button('Right', id='button2',n_clicks=0,n_clicks_timestamp=0),
        html.P(id="placeholder2",style={"display":"none"}),
    ], className="row")

])

#this creates the html aspects of the web page and key elements such as
#graphs, images etc.



#dash works best by defining structure and elements then populating 
#said elements using decorator fucntions. You can hard code info instead,
#but will lose reproducaibilty and will run into concurrency issues with
#multiple users



#decorator function allows outputs, inputs and states to be defined
@app.callback(Output('graph-1', 'figure'), [Input('dropdown', 'value')])    
def update_line_graph(value):
    
    ''' This function will take a drop down value from user input ,
    retrieve the appropriate dataframe , aggregate tweets by month 
    then return a json dataset which will populate the graph-1 figure,
    thus rendering a line graph'''
    

    df = dataframes[value] 
    #live version uses value as an argument to sql retrieval function
    # = dynamic laoding of new data
    
    df.index = pd.DatetimeIndex(df["my_date"])   
    all_count=pd.DataFrame(df['count'].resample('M', how='sum'))    
    all_count["date"] = all_count.index
    
    all_count=all_count['20110101':'20200301']
    #json defined data
    
    return {'data': [{'x': all_count["date"], 'y': all_count["count"],
                              'type': 'line', 'name': 'SF'}],
            'layout': {
                'title': 'Tweets aggregated by month',
                "height":600,"width":1000}}



@app.callback(Output('graph-2', 'figure'), [Input('dropdown', 'value')])
def update_map(value):
    
    ''' This function parses the dataset for XY information then returns 
        a map with tweet locations'''
    
    
    df = dataframes[value]
    
    return {
            "data": [
                dict(
                    type = "scattermapbox",
                    lat = df["lat"].tolist(),
                    lon = df["lon"].tolist(),
                    mode = "markers",
                    marker=dict(size=8,color='rgb(253,191,111)'),
                    showlegend=False)],
            'layout': dict(
                autosize = False,
                hovermode = "closest",
                title = "Home location of tweets",
                width=800,height=600,
                mapbox = dict(
                    accesstoken = mapbox_access_token,
                    bearing = 0,
                    center = dict(lat = 53.8, lon = -3),
                    pitch = 0,
                    zoom = 4
                    
                )
            )
        }

@app.callback(Output('graph-3', 'figure'), [Input('dropdown', 'value')])
def update_piechart(value):
    
    ''' This function filters the dataset for the top 10 retweeted tweets.
        It then creates an intercctive piechart allowing the user to be
        directed to thetweet on twitter and see any associated text or media'''

    
    df = dataframes[value]
    

    top_10_tweets = df.sort_values("retweets",ascending=False)[0:10]
    top_10_tweets = top_10_tweets[["retweets","favorites","solo_date","url"]]
    top_10_tweets.columns = ["Total Retweets","Total Likes","Date","TweetLink"]
    
    top_10_tweets["label"] = '<a href="' + top_10_tweets["TweetLink"]+\
                             '"style="color: #000">'+\
                             top_10_tweets["Date"].astype(str)
    
    return {
            "data": [
                dict(
                    type = "pie",
                    labels = top_10_tweets['label'],
                    values = top_10_tweets['Total Likes'],
                    textinfo='label+value',
                    textfont=dict(size=12),
                    textposition="inside",
                    marker=dict(line=dict(width=2)))],
                        
            'layout': {
                'title': 'Top 10 Retweets',
                "height":800,"width":800,"showlegend":False}}   
    
    
 
@app.callback(Output('placeholder2', 'children'),
              [Input('dropdown','value')])

def picList(value):
    
    ''' This uses a hidden div to store a dataframe in json so can be shared,
    among functions. Its purpose is to retrieve URLS of pics associated with 
    tweets'''    
        
    df = dataframes[value]
       
    pics=df[~df["true_pic"].isnull()] 
    pics = pics[["true_pic","retweets"]]
    
    json_pics=pics.to_json()
    
    return json_pics
    
    
   
@app.callback(Output('image', 'src'),
              [Input('button', 'n_clicks_timestamp'),
               Input('button2', 'n_clicks_timestamp'),
               Input('button', 'n_clicks'),
               Input('button2', 'n_clicks'),
               Input('placeholder2', 'children')])
    
def display(btn1, btn2,forward_clicks,back_clicks,json_pics):
    
    '''This fucntion retrieves the picture links and converts from json to df.
    It then traverses throught the list of pcitures based on forward or
    backward clicks from buttons'''
    
    #uses stored json df and gets list of pics from it
    pics = pd.read_json(json_pics)
    pics = pics.sort_values(["retweets"],ascending=False)
    pics = pics["true_pic"].tolist()
    
    try:
        pic=button_logic(btn1, btn2,forward_clicks,back_clicks,pics)
        return pic
    except IndexError:
        btn1, btn2,forward_clicks,back_clicks=0,0,0,0
        pic=button_logic(btn1, btn2,forward_clicks,back_clicks,pics)
        
        return pic
    


def button_logic(btn1, btn2,forward_clicks,back_clicks,pics):
    
    '''Logic determining pciture display order. Very fiddly could be 
    improved if functionality for detecting clicks is added by dash'''
    

    back_clicks = -1 * back_clicks  
        
    if btn1 > btn2:
        forward_clicks = forward_clicks  + back_clicks
        print(forward_clicks)
        
        return pics[forward_clicks]
      
    elif btn2 > btn1:
        
        back_clicks = back_clicks + forward_clicks
        print(back_clicks)
        
        return pics[back_clicks]

    
    else:
        return pics[0]     
    
    


app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
#css styling
    
if __name__ == '__main__':
    app.run_server(debug=True)
    
    