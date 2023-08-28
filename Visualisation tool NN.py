from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import dash_daq as daq
import random

# <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
# <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>


NN = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

dark_theme = {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
}

# upload the scatter plot data sets
df_scatter = pd.read_csv('G:/My Drive/Diss modelling/df_test.csv',index_col='index')

# upload MLP and histogram data sets
df_shortlist = pd.read_csv('G:/My Drive/Diss modelling/df_shortlist.csv',index_col='index')
df_shortlist_scaled = pd.read_csv('G:/My Drive/Diss modelling/df_shortlist_scaled.csv',index_col='index')

df_probs = pd.read_csv('G:/My Drive/Diss modelling/df_probs_2022.csv',index_col='index')
df_metrics = pd.read_csv('G:/My Drive/Diss modelling/df_metrics_2022.csv',index_col='index')

# define features
Features = df_scatter.drop(columns=['Event','totalWeight']).columns.to_list()
featX = 'ETmiss'
# define events
Events_sim = df_scatter["Event"].unique() 
Events_real = Events_sim.copy()
Events_real[-1] = 'unknown'

#####################################################################################
#####################################################################################
## Scatter plot components

# defines radioitems group to choose Y-feature
Y_options = Features.copy()
Y_options.remove(featX)
ChooseY = dbc.RadioItems(id='ChooseY',
                         options=Y_options,
                         value = "dRll",
                         style={'font-family':'Coustard Black', 'font-size':12, 'color':'SteelBlue'}, 
                        )


# define slider controls along X
min_value = df_scatter[f'{featX}'].min().round(2)
max_value = df_scatter[f'{featX}'].max().round(2)
SliderX = dcc.RangeSlider(id='SliderX',
                          min=min_value, 
                          max=max_value,
                          value = [min_value, max_value],
                          #updatemode='drag',
                          persistence = True 
                          )



# define slider controls along Y
SliderY = dcc.RangeSlider(id='SliderY',                          
                          min=0, max=1,
                          vertical=True, verticalHeight=400,
                          #updatemode='drag',
                          persistence=True
                          )
# this updates the Y-slider
@callback(
          Output("SliderY", "min"),
          Output("SliderY", "max"),
          Output("SliderY", "value"),
          Input("ChooseY", "value"),
          )
def range_slider_y(featY):
    # define the data set to plot
    df = df_scatter.copy()
    # set values
    min_value = df[f'{featY}'].min().round(2)
    max_value = df[f'{featY}'].max().round(2)
    value = [min_value, max_value]
    return min_value, max_value, value



# define tabs
Tabs = dbc.Tabs([dbc.Tab(label="Simulated data", tab_id="tab-0"),
                 dbc.Tab(label="Experimental data", tab_id="tab-1")],
                 id="Tabs",
                 active_tab="tab-0",
                 style={'font-family':'Coustard Black', 'font-size':14},
                )


# define events' checklist
Pallete_legend = ['SkyBlue','Salmon','LimeGreen','SandyBrown','RoyalBlue']
Legend_Scat = dbc.Checklist(
                            id="Legend_Scat", value=Events_sim,
                            #labelStyle={"display": "flex", "align-items": "right"},
                            )   
# this updates the Scatter plot's Legend
@callback(
          Output("Legend_Scat", "options"),
          Input("Tabs", "active_tab")
          )
def update_legend(tab):
    options = [{"label": html.Div([event], style={'color':color, 'font-size':13, 'font-family':'Coustard Black'}),
                "value": event} for event,color in zip(Events_sim,Pallete_legend)]  

    if tab=="tab-1":
        options = [{"label": html.Div([event_real], style={'color':color, 'font-size':13, 'font-family':'Coustard Black', 'text-opacity':1}),
                    "value": event_sim, "disabled": True} for event_real,color,event_sim in zip(Events_real,Pallete_legend,Events_sim)]

    return options


#####################################################################################
#####################################################################################
## Neural Network model components


# data selector
Shortlist = []  # [{'label':'All Data', 'value':'data'}]
for i in df_shortlist.index:
    single_option = {}
    single_option['label']=f'{i} - '+df_shortlist.Event[i]
    single_option['value']=i
    Shortlist.append(single_option)
Data_Dropdown = dcc.Dropdown(id='Data_Dropdown',
                             options = Shortlist,
                             optionHeight=18,
                             clearable = False,
                             maxHeight = 500,
                             style={'font-family':'Coustard Black', 'font-size':10, 'color':'SlateGrey'}
                            )


# scaler switch
Scaler_Switch = daq.BooleanSwitch(id='Scaler_Switch',
                                  on=False, 
                                  labelPosition="bottom",
                                  #vertical=True, #persistence=True 
                                  )
@callback(Output('Scaler_Switch', 'label'),
          Output('Scaler_Switch', 'disabled'),
          Input('Scaler_Switch', 'on'),
          Input('Data_Dropdown', 'value'))
def update_switch(on, value):
    if value is None:
        state = True
        label = dict(label='select event', style={'font-family':'Segoe Print', 'color':'grey'})
    elif value is not None and on==True:
        state = False
        label=dict(label='scaled', style={'font-family':'Segoe Print', 'color':'#00EA64'})
    else:
        state = False
        label=dict(label='NOT scaled', style={'font-family':'Segoe Print', 'color':'FireBrick'})
    return label, state


# power button
Power_Button = daq.PowerButton(id='Power_Button',
                               on=False,
                               color=dark_theme['primary'],                
                               )
@callback(Output('Power_Button', 'disabled'),
          Input('Data_Dropdown', 'value'))
def power_button_state(value):
    if value is None:
        state = True
    else:
        state = False
    return state


# number of hidden layers selector
NN_Depth = dbc.RadioItems(id='NN_Depth', 
                          options=[1,2,3], 
                          value=1,
                          className="btn-group",
                          inputClassName="btn-check",
                          labelClassName="btn btn-outline-primary",
                          labelCheckedClassName="active",
                          #style={'size':'md'},
                          inline=True,                
                          )


# selector for Hidden Layer 1
HL1_Gauge = daq.Gauge(id='HL1_Gauge',
                      color={"gradient":True, "ranges":{'white':[0,1],"palegreen":[1,4],"limegreen":[4,8],"darkgreen":[8,10]}},
                      max=10, min=0, size=130, 
                      label=dict(label='Size of Layer 1', style={'font-size':10, 'marginBottom': 0, 'color':'Navy'}),                      
                      style={'font-family':'ROG Fonts'},
                      scale=dict(custom={f'{i}':{'label':f'{i}', 'style':{'font-size':8}} for i in range(1,11)})
                      )
HL1_Selector = daq.Slider(id='HL1_Selector',
                          min=1, max=10, value=4, step=1, size=130,
                          handleLabel=dict(label="neurons", color='DarkGreen'),  
                          marks={f'{i}':{'label':f'{i}', 'style':{'font-family':'ROG Fonts', 'font-size':8}} for i in range(1,11,9)},
                          color={"gradient":True, "ranges":{"palegreen":[1,5],"limegreen":[5,9],"darkgreen":[9,10]}},
                          )
@callback(Output('HL1_Gauge', 'value'), 
          Input('HL1_Selector', 'value'))
def update_gauge1(value):
    return value


# selector for Hidden Layer 2
HL2_Gauge = daq.Gauge(id='HL2_Gauge',                        
                      max=10, min=0, size=130,
                      scale=dict(custom={f'{i}':{'label':f'{i}', 'style':{'font-family':'ROG Fonts', 'font-size':8}} for i in range(1,11)}),
                      style={'font-family':'ROG Fonts'}
                      )
HL2_Selector = daq.Slider(id='HL2_Selector',
                          min=1, max=10, value=8, size=130,
                          marks={f'{i}':{'label':f'{i}', 'style':{'font-family':'ROG Fonts', 'font-size':8}} for i in range(1,11,9)},
                          )
@callback(Output('HL2_Gauge', 'value'), 
          Input('HL2_Selector', 'value'))
def update_gauge2(value):
    return value


# selector Hidden Layer 3
HL3_Gauge = daq.Gauge(id='HL3_Gauge',                        
                      max=10, min=0, size=130,
                      scale=dict(custom={f'{i}':{'label':f'{i}', 'style':{'font-family':'ROG Fonts', 'font-size':8}} for i in range(1,11)}),
                      style={'font-family':'ROG Fonts'}
                      )
HL3_Selector = daq.Slider(id='HL3_Selector',
                          min=1, max=10, value=4, size=130,                          
                          marks={f'{i}':{'label':f'{i}', 'style':{'font-family':'ROG Fonts', 'font-size':8}} for i in range(1,11,9)},
                          )
@callback(Output('HL3_Gauge', 'value'), Input('HL3_Selector', 'value'))
def update_gauge3(value):
    return value


# control state of the selectors
@callback(Output("HL2_Gauge", "disabled"),
          Output("HL2_Gauge", "color"),
          Output("HL2_Gauge", "label"),
          Output("HL2_Selector", "disabled"),
          Output("HL2_Selector", "color"),
          Output("HL2_Selector", "handleLabel"),           
          Output("HL3_Gauge", "disabled"),
          Output("HL3_Gauge", "color"),
          Output("HL3_Gauge", "label"),
          Output("HL3_Selector", "disabled"),
          Output("HL3_Selector", "color"),
          Output("HL3_Selector", "handleLabel"),         
          Input("NN_Depth", "value"))
def active_selectors(number):
    state_gauge2 = state_selector2 = state_gauge3 = state_selector3 = True
    color_gauge2 = color_selector2 = color_gauge3 = color_selector3 = 'WhiteSmoke'
    label_gauge2 = dict(label='Size of Layer 2', style={'font-size':10, 'marginBottom':0, 'color':'WhiteSmoke'})
    label_gauge3 = dict(label='Size of Layer 3', style={'font-size':10, 'marginBottom':0, 'color':'WhiteSmoke'})
    handleLabel2 = handleLabel3 = dict(label="neurons", color='WhiteSmoke')
    if number >=2:
        state_gauge2 = state_selector2 = False
        color_gauge2 =    {"gradient":True, "ranges":{'White':[0,1],"skyblue":[1,5],"royalblue":[5,8],"navy":[8,10]}}
        color_selector2 = {"gradient":True, "ranges":{         "lightskyblue":[1,7],"royalblue":[7,9],"navy":[9,10]}}
        label_gauge2 = dict(label='Size of Layer 2', style={'font-size':10, 'marginBottom':0, 'color':'Navy'})
        handleLabel2 = dict(label="neurons", color='Blue')
        if number ==3:
            state_gauge3 = state_selector3 = False
            color_gauge3 =    {"gradient":True, "ranges":{"Lavenderblush":[0,5],"Orchid":[5,8],"Purple":[8,10]}}
            color_selector3 = {"gradient":True, "ranges":{"Lavenderblush":[1,7],"Violet":[7,9],"Purple":[9,10]}}
            label_gauge3 = dict(label='Size of Layer 3', style={'font-size':10, 'marginBottom':0, 'color':'Navy'})            
            handleLabel3 = dict(label="neurons", color='Purple')
            
    return state_gauge2, color_gauge2, label_gauge2, state_selector2, color_selector2, handleLabel2, \
           state_gauge3, color_gauge3, label_gauge3, state_selector3, color_selector3, handleLabel3


# accuracy indicator
Accuracy_LED = daq.LEDDisplay(id='Accuracy_LED',
                              size=35,
                              color=dark_theme['primary'],
                              backgroundColor='white', #dark_theme['secondary'],
                              label=dict(label='Accuracy:', 
                                  style={'color':'Navy', 'font-size':11, 'font-family':'ROG Fonts', }),
                              )
F1_LED = daq.LEDDisplay(id='F1_LED',
                        size=35,
                        color=dark_theme['primary'],
                        backgroundColor='white', #dark_theme['secondary'],
                        label=dict(label='F1-score:', 
                                  style={'color':'Navy', 'font-size':11, 'font-family':'ROG Fonts', }),
                        )
@callback(
          Output("Accuracy_LED", "value"),
          Output("Accuracy_LED", "color"), 
          Output("F1_LED", "value"),
          Output("F1_LED", "color"),          
          Input('Scaler_Switch', 'on'),
          Input('Power_Button', 'on'),
          Input("NN_Depth", "value"),
          Input("HL1_Selector", "value"),
          Input("HL2_Selector", "value"),
          Input("HL3_Selector", "value"),
          )
def update_led_values(scaler, power, number_hl, HL1_size, HL2_size, HL3_size):
        
    Nhl = number_hl   # number of hidden layers (1 to 3)    
    hl1 = int(HL1_size) if HL1_size%2==0 else int(HL1_size+1)  # number of nods in the hidden layers
    hl2 = int(HL2_size) if HL2_size%2==0 else int(HL2_size+1)
    hl3 = int(HL3_size) if HL3_size%2==0 else int(HL3_size+1)
    design = f'({hl1},)'  # design of MLP
    if Nhl == 2:
        design = f'({hl1}, {hl2})'
    elif Nhl == 3:
        design = f'({hl1}, {hl2}, {hl3})'

    if scaler==True and power==True:
        accuracy = df_metrics[design].Accuracy.round(2)
        f1_score = df_metrics[design]['f1-score'].round(2)
        color = dark_theme['primary']
    else:
        accuracy = f1_score = "00.00"
        color = 'Maroon'
    return accuracy, color, f1_score, color


#####################################################################################
#####################################################################################
## Histogram components


# slider controling histogram cut
Hist_Slider = daq.Slider(id='Hist_Slider',
                          min=0, max=1, value=0., step=0.05,
                          size=497,
                          #marks={f'{i}':{'label':f'{i}', 'style':{'font-family':'Coustard', 'font-size':8}} for i in [0,.5,1.]},
                          updatemode = 'drag',                          
                          labelPosition='bottom',                          
                          )
@callback(
          Output("Hist_Slider", "disabled"),
          Output("Hist_Slider", "color"),
          Output("Hist_Slider", "handleLabel"),
          Input('Scaler_Switch', 'on'),
          Input('Power_Button', 'on'),
          )
def activate_hist_slider(scaler, power):
    if scaler!=True or power!=True:
        status=True
        color='WHiteSmoke'
        handleLabel=dict(label='Cut', color='WhiteSmoke')
    else:
        status=False
        color={"gradient":True, "ranges":{"SteelBlue":[0.,.5],"WhiteSmoke":[0.5,0.8],"Orange":[.8,1.]}}
        handleLabel=dict(label='Cut', color='Maroon')
    return status, color, handleLabel


# Label showing significance value    
Signif_Hist = dbc.Label(id='Signif_Hist', 
                       style={'font-size':26, 'font-family':'Coustard Black'})
@callback(
          Output("Signif_Hist", "children"),
          Output("Signif_Hist", "color"), 
          Input('Scaler_Switch', 'on'),
          Input('Power_Button', 'on'),
          Input("NN_Depth", "value"),
          Input("HL1_Selector", "value"),
          Input("HL2_Selector", "value"),
          Input("HL3_Selector", "value"),
          Input("Hist_Slider", "value"),
          )
def update_signif_hist(scaler, power, number_hl, HL1_size, HL2_size, HL3_size, cut):
        
    Nhl = number_hl             # number of hidden layers (1 to 3)    
    hl1 = int(HL1_size) if HL1_size%2==0 else int(HL1_size+1)  # number of nods in the hidden layers
    hl2 = int(HL2_size) if HL2_size%2==0 else int(HL2_size+1)
    hl3 = int(HL3_size) if HL3_size%2==0 else int(HL3_size+1)
    design = f'({hl1},)'        # design of MLP
    if Nhl == 2:
        design = f'({hl1}, {hl2})'
    elif Nhl == 3:
        design = f'({hl1}, {hl2}, {hl3})'

    # make cut and calculate significance
    df = df_probs[['Event','Weight',design]]
    selection = df[df[design]>=cut]

    W_sig = sum(selection[selection['Event']==1.0]['Weight'])
    W_bkg = sum(selection['Weight']) - W_sig
    S = (W_sig/np.sqrt(W_bkg)).round(2)

    if scaler==True and power==True:
        significance = S
        color = 'Green' #dark_theme['primary']
    else:
        significance = float(0)
        color = 'Maroon'
    return significance, color



# define custom legend for the histogram
Legend_Hist = dbc.Checklist(
                            id="Legend_Hist", value=[0, 1],
                            #labelStyle={"display": "flex", "align-items": "right"},
                            )   
@callback(
    Output("Legend_Hist", "options"),
    Input('Scaler_Switch', 'on'),
    Input('Power_Button', 'on'),
    Input("NN_Depth", "value"),
    Input("HL1_Selector", "value"),
    Input("HL2_Selector", "value"),
    Input("HL3_Selector", "value"),
    Input("Hist_Slider", "value"),
    )
def legend_hist_update(scaler, power, number_hl, HL1_size, HL2_size, HL3_size, cut):
    
    Nhl = number_hl             # number of hidden layers (1 to 3)    
    hl1 = int(HL1_size) if HL1_size%2==0 else int(HL1_size+1)  # number of nods in the hidden layers
    hl2 = int(HL2_size) if HL2_size%2==0 else int(HL2_size+1)
    hl3 = int(HL3_size) if HL3_size%2==0 else int(HL3_size+1)
    design = f'({hl1},)'        # design of MLP
    if Nhl == 2:
        design = f'({hl1}, {hl2})'
    elif Nhl == 3:
        design = f'({hl1}, {hl2}, {hl3})'

    # make selection and calculate number of events (sum of weights)
    df = df_probs[['Event','Weight',design]]
    selection = df[df[design]>=cut]

    now_sig = round(sum(selection[selection['Event']==1.0]['Weight']), 1)
    now_bkg = round((sum(selection['Weight']) - now_sig), 1)
    full_sig = round(sum(df[df['Event']==1.0]['Weight']), 1)
    full_bkg = round((sum(df['Weight']) - full_sig), 1)

    if scaler==True and power==True:
        status = False
        now_sig = round(sum(selection[selection['Event']==1.0]['Weight']), 1)
        now_bkg = round((sum(selection['Weight']) - now_sig), 1)
        full_sig = round(sum(df[df['Event']==1.0]['Weight']), 1)
        full_bkg = round((sum(df['Weight']) - full_sig), 1)
    else:
        status = True
        now_sig = now_bkg = full_sig = full_bkg = 50
    
    options = [
        {"label": html.Div([dbc.Col([f'Background'], style={'color':'SteelBlue', 'font-size':13, 'font-family':'Coustard Black'}),
                            dbc.Label([f'{now_bkg}'], style={'color':'SteelBlue', 'font-size':13, 'font-family':'Coustard Black'}),
                            dbc.Label([f'/'], style={'color':'White', 'font-size':13}),
                            dbc.Label([f'/ {full_bkg}'], style={'color':'SteelBlue', 'font-size':13, 'font-family':'Coustard'})]),
         "value": 0, "disabled": status},
        {"label": html.Div([dbc.Col([f'Signal'], style={'color':'SandyBrown', 'font-size':13, 'font-family':'Coustard Black'}), 
                            dbc.Label([f'{now_sig}'], style={'color':'SandyBrown', 'font-size':13, 'font-family':'Coustard Black'}),
                            dbc.Label([f'/'], style={'color':'White', 'font-size':13}),
                            dbc.Label([f'/ {full_sig}'], style={'color':'SandyBrown', 'font-size':13, 'font-family':'Coustard'})]),
         "value": 1, "disabled": status},
              ]
    return options


####################################################################################################################################################
####################################################################################################################################################
## App layout


NN.layout = dbc.Container([
    
    #####################  Scatter plot section ############################################    
    
    html.Br(),
    dbc.Row(dbc.Col(html.H4('When cut-optimisation is struggling...',
                            style={'font-family':'Coustard Black', 'color':'DarkSlateGrey'}),
                    width={"size": 8, "offset": 2})),
    html.Br(),
    dbc.Row(dbc.Col(
                    dcc.Markdown(
                          "In some cases, bold cut-optimisation approach can be challenging. \
                          Suppose we are searching for a *dark matter* particle among results of a proton-proton collision. \
                          We assume that *dark matter* is made of hypothetical particles - WIMPs (weakly interacting massive particles). \
                          They are produced when Z-boson decays into a pair of WIMPs and a dilepton pair. \
                          Such event would leave traces similar to other processes, which we know do happen. \
                          On a graph below, try to play with different combinations of parameters. \
                          As you may find, the dark matter traces can be easily distinguished from **Non-resonant dilepton** and **Z+jets** processes. \
                          However, **WZ** and **ZZ** events have such large variety, that they practically hinder the other processes.",

                          style={'font-size':14, 'font-family':'Coustard'}),
                          
                    width={"size": 8, "offset": 2})),

    dbc.Row([
            dbc.Col([
                      dbc.Label('Select Y-parameter:',
                                style={'font-size':16, 'marginBottom':20, 'font-family':'Coustard Black', 'color':'DimGray'}), 
                      ChooseY,
                      ], 
                    width={"size": 2, "offset": 0},
                    style={'marginTop':100},
                    align='start'
                    ),
            dbc.Col(SliderY, 
                      width={"size": 1, "offset": 0},
                      style={'width':50,
                            'margin-left':20, 'marginBottom':58},
                      align='end'
                      ),
            dbc.Col([
                    dbc.Col([Tabs,
                            dcc.Graph(id="Scatter",                                      
                                      config={
                                              'displayModeBar':False,
                                              #'modeBarButtonsToRemove': ['zoom2d'],
                                              #'scrollZoom': True,
                                              }                            
                                      ),
                            ]),
                    dbc.Col(SliderX, 
                            style={
                                  'width':630, 
                                  'margin-left':15}),                                
                      ],
                    width={"size": 7, "offset": 0}, #, md=7)
                    ),
            dbc.Col([
                     #dbc.Label('Events:', style={'font-size':16, 'marginBottom':20, 'font-family':'Coustard Black', 'color':'DimGray'}),
                     Legend_Scat,
                     ], 
                    width={"size": 2, "offset": 0},
                    style={'marginTop':145, 'marginLeft':5},
                    align='start'
                    ) 
            ],
            align="center",
            className="g-0",                   
            ), 

    html.Br(),
    dbc.Row(dbc.Col([
            dcc.Markdown("For convenience, we can approximate our complex 10-dimensional data set to a 2D projection. \
                         Popular algorithms for such visualisation are UMAP, PCA and t-SNE (check the tabs). \
                         Now there is no need to go through multiple combinations of parameters. \
                         However, the setback is that we sacrificied data variance.\
                         And still hardly can isolate the signal (Dark Matter) by optimising the cut(s).",

                         style={'font-size':14, 'font-family':'Coustard'}),
            html.Br(),
            dcc.Markdown("Imagine there are not 10, but 40+ parameters to consider... In such case machine learning inventory can come handy. \
                         Machine learning algorithms are capable of identifying (very) complex patterns and classifying the Signal (dark matter) from the Background (the other events). \
                         Among different algorithms, *neural networks* (NN) often produce the best results in HEP. \
                         Below you can find a model of NN: Multilayer Perceptron (MLP). \
                         It is pre-trained on Monte Carlo simulated data, and you can tinker with its configuration to check the difference in output. \
                         Select the number of hidden layers (NN depth) and vary the amount of neurons. \
                         Then, choose a specific event from the dropdown menu and press the *power button*. \
                         But don't forget to turn on the *scaler switch* - NN work best with normalised data.",

                         style={'font-size':14, 'font-family':'Coustard'}),
                    ],                                        
                     width={"size": 8, "offset": 2})),
    html.Br(),   

    ####################################################################
    #####################  NN model section ############################

    dbc.Row(dbc.Col(html.H4('Play with Neural Network design',
                            style={'font-family':'Coustard Black', 'color':'DarkSlateGrey'}),
                    width={"size": 8, "offset": 2})),

    html.Hr(),
    dbc.Row([
        dbc.Col([dbc.Card([dbc.Label('Select event:',
                                    style={'font-size':11, 'marginBottom':20, 'font-family':'ROG fonts', 'color':'Navy'}),
                        #html.Hr(),
                        daq.DarkThemeProvider(theme=dark_theme, children=Data_Dropdown)], body=True),
                dbc.Row([dbc.Col(dbc.Card([html.Center(dbc.Label('Scale data:',
                                                     style={'font-size':11, 'marginBottom':20, 'font-family':'ROG fonts', 'color':'Navy'})),
                                          #html.Hr(),
                                          daq.DarkThemeProvider(theme=dark_theme, children=Scaler_Switch)], body=True)),
                        dbc.Col(dbc.Card([html.Center(dbc.Label('Start NN:',
                                                    style={'font-size':11, 'marginBottom':20, 'font-family':'ROG fonts', 'color':'Navy'})),
                                          #html.Hr(),
                                          daq.DarkThemeProvider(theme=dark_theme, children=Power_Button)], body=True))]),
                ],
                width=3),
    
        dbc.Col(dbc.Card([
                dbc.Row(dbc.Col([html.Center(dbc.Label('Number of Hidden Layers:',
                                            style={'font-size':11, 'marginBottom':20, 'font-family':'ROG fonts', 'color':'Navy'})),
                                #html.Br(),
                                html.Center(NN_Depth)], 
                                width='auto'), 
                        justify='center'),
                html.Br(),
                dbc.Row([
                        dbc.Col([HL1_Gauge, 
                                 html.Center(HL1_Selector)],                                               
                                width='auto'),                                        
                        dbc.Col([HL2_Gauge,
                                 html.Center(HL2_Selector)],
                                width='auto'),
                        dbc.Col([HL3_Gauge, 
                                 html.Center(HL3_Selector)], 
                                width='auto')
                        ], justify='evenly'),
                    ], body=True),
                width={"size": 7, "offset": 0}),                    

        dbc.Col([dbc.Card([Accuracy_LED,
                            html.Br(),
                            F1_LED], 
                            body=True),
                            #daq.DarkThemeProvider(theme=dark_theme, children=Accuracy_LED)], body=True),
                ],
                width=2),
            ], align='center'),
    
    # Sankey diagramm section
    dbc.Row(
            dbc.Col(dcc.Graph(id="MLP", config={'displayModeBar':False}),
                    #width={"size": 10, "offset": 1}
                    )
            ),

    ####################################################################
    #####################  Histogram section ###########################


    dbc.Row([dbc.Col([
                    dbc.Col(dcc.Graph(id="Hist", config={'displayModeBar':False}),
                            ),
                    html.Br(),
                    dbc.Col(Hist_Slider, 
                            style={'margin-left':104}),                             
                    ],
                    width={"size": 6, "offset": 2}),
            dbc.Col([
                     dbc.Label('Events:', style={'font-size':16, 'marginBottom':20, 'font-family':'Coustard Black', 'color':'DimGray'}),
                     Legend_Hist,
                     html.Br(),
                     dbc.Label('Significance:', style={'font-size':16, 'marginBottom':20, 'font-family':'Coustard Black', 'color':'DimGray'}),
                     html.Br(),
                     dbc.Col(Signif_Hist, style={'margin-left':50})
                     ],
                    width={"size": 2, "offset": 0},
                    style={'margin-top':60},
                    align='start')
            ],
            align='center'),

    # text after the histogram
    html.Br(),
    html.Br(),
    dbc.Row(dbc.Col([
                    dcc.Markdown(
                            'Histogram above shows distribution of the NN outputs of the whole data set. \
                            Move the slider to select the (signal) data to the right cutting out (background) data to the left',

                            style={'font-size':14, 'font-family':'Coustard'}),

                            ], width={"size": 8, "offset": 2}),
                    align='center'),
    html.Br(),
    html.Br(),
    ])

####################################################################################################################################################
####################################################################################################################################################
## Scatter plot updates


@callback(
          Output("Scatter", "figure"),
          Input("ChooseY", "value"),
          Input('SliderX', 'value'),
          Input('SliderY', 'value'),
          Input("Tabs", "active_tab"),
          Input("Legend_Scat", "value"),    
          )
def update_scatter(featY, sliderX, sliderY, active_tab, events):
    
    # define the data set to plot
    df = df_scatter.copy()
    Pallete = {'Non-resonant_ll':'skyblue', 'Z+jets':'salmon', 'WZ':'lightgreen', 'ZZ':'wheat', 'DM_300':'navy'}
    #featX = 'ETmiss'
    Hover = 'closest'
    #Hover_data = {'Event':True, featX:True, featY:True}
    #Color_counts = 'SteelBlue'
    if active_tab == "tab-0":        
        Title = "Events in simulated data"        
    elif active_tab == "tab-1":
        Title = "Events in 'real' data"
        #Color_counts = 'White'
        Pallete = {'Non-resonant_ll':'DimGray', 'Z+jets':'DimGray', 'WZ':'DimGray', 'ZZ':'DimGray', 'DM_300':'DimGray'}
        Hover = False
        #Hover_data = {'Event':False, featX:True, featY:True}

    # enable cuts with the sliders
    Xlow, Xhigh = sliderX
    Ylow, Yhigh = sliderY    
    mask = (df[f'{featX}'] >= Xlow) & (df[f'{featX}'] <= Xhigh) & (df[f'{featY}'] >= Ylow) & (df[f'{featY}'] <= Yhigh)
    df_masked=df[mask]
    df_filt = df_masked[df_masked["Event"].isin(events)]
  
    fig = px.scatter(
                      df_filt, x=featX, y=featY, color='Event',
                      #size='follyWeight', #size_max=10,
                      labels={'color': 'Event'},    
                      opacity = 0.5,
                      template = 'plotly_white', #'simple_white',
                      color_discrete_map=Pallete,
                      range_x=[Xlow-(Xhigh-Xlow)*0.01, Xhigh+(Xhigh-Xlow)*0.01],
                      range_y=[Ylow-(Yhigh-Ylow)*0.01, Yhigh+(Yhigh-Ylow)*0.01],
                      #hover_data=Hover_data - does not work?
                      )
    
    # customize font, etc.
    fig.update_layout(
                      font_family="Coustard", font_size=11, font_color="SlateGrey",
                      showlegend=False,
                      title=dict(text=Title, font=dict(family='Coustard Black', size=20), x=0.44, y=0.95),
                      # legend_title=dict(font=dict(family='Coustard Black',color='DimGrey')),
                      # legend_uirevision='foo',
                      #paper_bgcolor="#303030",
                      #width=700,
                      margin=dict(l=0, r=130, b=0, t=50),
                      hovermode=Hover
                      )

    fig.update_traces(marker={'line':{'width':2, 'color':'white'},
                              'size':9
                              },
                      )
    

    # define significance through MC weights
    W_sig = sum(df_filt[df_filt['Event']=='DM_300']['totalWeight'])
    W_bkg = sum(df_filt['totalWeight']) - W_sig
    S = (W_sig/np.sqrt(W_bkg)).round(2)

    # significance score - header
    fig.add_shape(type="rect", xref="paper", yref="paper",
                  fillcolor="White", line_color="White", line_width=0.25,
                  x0=1.08-0.04, x1=1.27-0.04, y0=0.3-0.035, y1=0.3+0.035,    
                  label=dict(text='Significance:', textposition='middle right', font_size=16, font_family='Coustard Black', font_color='DimGrey'),
                  ) 
    # significance score - box and value
    fig.add_shape(type="rect", xref="paper", yref="paper",
                  fillcolor="White", line_color="White", line_width=0.25,
                  x0=1.08-0.04, x1=1.27-0.04, y0=0.2-0.035, y1=0.2+0.035,                  
                  label=dict(text=S, textposition='middle right', font_size=18, font_family='Coustard Black', font_color='SeaGreen') #00EA64')
                  ) 

    # counts - header
    fig.add_shape(type="rect", xref="paper", yref="paper",
                  fillcolor="White", line_color="White", line_width=0.25,
                  x0=1.08-0.04, x1=1.27-0.04, y0=0.94-0.035, y1=0.94+0.035,    
                  label=dict(text='Events:', textposition='middle right', font_size=16, font_family='Coustard Black', font_color='DimGrey'),
                  ) 
    # counts of events
    for z,event in enumerate(Events_sim):
        now = round(sum(df_filt[df_filt['Event']==event]['totalWeight']),1)
        full = round(sum(df[df['Event']==event]['totalWeight']),1)
        fig.add_shape(type="rect", xref="paper", yref="paper",
                      fillcolor="White", line_color="White", line_width=0.25,
                      x0=1.08-0.04, x1=1.17-0.04, y0=0.88-0.074*(z+1)-0.03, y1=0.88-0.074*(z+1)+0.03,                  
                      label=dict(text=f'{now}', textposition='middle right', font_size=13, font_color='SteelBlue', font_family='Coustard Black',) 
                      )
        fig.add_shape(type="rect", xref="paper", yref="paper",
                      fillcolor="White", line_color="White", line_width=0.25,
                      x0=1.17-0.04, x1=1.27-0.04, y0=0.88-0.074*(z+1)-0.03, y1=0.88-0.074*(z+1)+0.03,                  
                      label=dict(text=f'({full})', textposition='middle left', font_size=13, font_color='SteelBlue', font_family='Coustard',) 
                      )      
    
    return fig


#####################################################################################
#####################################################################################
## NN model updates


@callback(
          Output("MLP", "figure"), 
          Input('Data_Dropdown', 'value'),
          Input('Scaler_Switch', 'on'),
          Input('Power_Button', 'on'),
          Input("NN_Depth", "value"),
          Input("HL1_Selector", "value"),
          Input("HL2_Selector", "value"),
          Input("HL3_Selector", "value"),
          )
def update_MLP(id, scaled, power, number_hl, HL1_size, HL2_size, HL3_size): 
    
    ### Inputs 
    f=len(Features)      # number of input features
    o=2                  # number of output nods = 2
    folly = 1            # folly hidden node(s) (for technical purposes)
    Nhl = number_hl      # number of hidden layers (1 to 3)    
    hl1 = int(HL1_size)  # number of nods in the hidden layers (1 to 10)
    hl2 = hl3 = 0
    a = int(HL1_size) if HL1_size%2==0 else int(HL1_size+1)
    b = int(HL2_size) if HL2_size%2==0 else int(HL2_size+1)
    c = int(HL3_size) if HL3_size%2==0 else int(HL3_size+1)
    design = f'({a},)' # type of 'design' string
    if Nhl == 2:
        hl2 = int(HL2_size)
        design = f'({a}, {b})'
    elif Nhl == 3:
        hl2 = int(HL2_size)
        hl3 = int(HL3_size)
        design = f'({a}, {b}, {c})'    
        

    ### design logic

    # initiate label array with input features
    # Label = [f'F{i+1}' for i in range(f)]
    # HL1 = [f'HL1.{i+1}' for i in range(hl1)]
    # HL2 = [f'HL2.{i+1}' for i in range(hl2)]
    # HL3 = [f'HL3.{i+1}' for i in range(hl3)]
    # #O = ['Signal', 'Background']
    # Label = Label + HL1 + HL2 + HL3 + O

    # x
    x_pad=0.10
    if Nhl == 1:
        X = f*[x_pad] + hl1*[x_pad+(1-x_pad)/2] + o*[1.0] + folly*[1.2, 1.5]
    elif Nhl == 2:
        X = f*[x_pad] + hl1*[x_pad+(1-x_pad)/3] + hl2*[x_pad+2*(1-x_pad)/3] + o*[1.0] + folly*[1.2, 1.5]
    elif Nhl == 3:
        X = f*[x_pad] + hl1*[x_pad+(1-x_pad)/4] + hl2*[x_pad+(1-x_pad)/2] + hl3*[x_pad+3*(1-x_pad)/4]+ o*[1.0] + folly*[1.2, 1.5]
    
    # y
    Yf = [(i+1)/(f+1) for i in range(f)]  # initialise with features' Y-coordinates
    Yhl1 = [(i+1)/(hl1+1) for i in range(hl1)]
    Yhl2 = [(i+1)/(hl2+1) for i in range(hl2)]
    Yhl3 = [(i+1)/(hl3+1) for i in range(hl3)]
    Yo = [(i+1)/(o+1) for i in range(o)]
    Y = Yf + Yhl1 + Yhl2 + Yhl3 + Yo + folly*[0.5, 0.5]

    # source
    SourceF = np.array([hl1*[i] for i in range(f)]).flatten() # links 'features - HL1'
    if Nhl==1:
        SourceHL1 = np.array([o*[i] for i in range(f,f+hl1)]).flatten()
        Source = np.concatenate((SourceF,SourceHL1))
    elif Nhl==2:
        SourceHL1 = np.array([hl2*[i] for i in range(f,f+hl1)]).flatten()
        SourceHL2 = np.array([o*[i] for i in range(f+hl1,f+hl1+hl2)]).flatten() 
        Source = np.concatenate((SourceF,SourceHL1,SourceHL2))
    elif Nhl==3:
        SourceHL1 = np.array([hl2*[i] for i in range(f,f+hl1)]).flatten()
        SourceHL2 = np.array([hl3*[i] for i in range(f+hl1,f+hl1+hl2)]).flatten() 
        SourceHL3 = np.array([o*[i] for i in range(f+hl1+hl2,f+hl1+hl2+hl3)]).flatten() 
        Source = np.concatenate((SourceF,SourceHL1,SourceHL2,SourceHL3)) 
    Sfolly = np.array([Source[-1]+1,Source[-1]+2,Source[-1]+3]).flatten()
    Source = np.concatenate((Source, Sfolly))  # append source with folly nodes

    # target
    Target1 = f*[i for i in range(f,f+hl1)] # links 'features - HL1' 
    if Nhl==1:
        TargetO = hl1*[i for i in range(f+hl1,f+hl1+o)]
        Target = Target1 + TargetO
    elif Nhl==2:
        Target2 = hl1*[i for i in range(f+hl1,f+hl1+hl2)]
        TargetO = hl2*[i for i in range(f+hl1+hl2,f+hl1+hl2+o)]
        Target = Target1 + Target2 + TargetO
    elif Nhl==3:
        Target2 = hl1*[i for i in range(f+hl1,f+hl1+hl2)]
        Target3 = hl2*[i for i in range(f+hl1+hl2,f+hl1+hl2+hl3)]
        TargetO = hl3*[i for i in range(f+hl1+hl2+hl3,f+hl1+hl2+hl3+o)]
        Target = Target1 + Target2 + Target3 + TargetO 
    Tfolly = np.array([Target[-1]+1,Target[-1]+1,Target[-1]+2]).flatten()
    Target = np.concatenate((Target, Tfolly))  # add source for folly

    # value
    Value = [round(random.uniform(0.005, 1),2) for _ in range(len(Source)-o-1)] +[0.0, 0.0, 1000.0]

    # line color
    Pos = random.sample(Value[:-(o+1)], int((len(Source)-o-1)/2))
    Color_on = []  # links' colour
    Weights = []  # links' info
    for v in Value:
        if v in Pos:
            Color_on.append('Bisque')  # positive connectiions painted 'warm'
            Weights.append(v)
        elif v==0.0 or v==1000.0:
            Color_on.append('White')  # folly connections painted white
            Weights.append(v)            
        else:
            Color_on.append('PowderBlue')  # negative connectiions painted 'cold'
            Weights.append(-v)
    # for color in Color_on[-(o+1):]:
    #     color = 'White'  
  
    Color_off = ['WhiteSmoke' for color in Color_on[:-(o+1)]]+(o+1)*['White']
    Color_red = ['MistyRose' for color in Color_on[:-(o+1)]]+(o+1)*['White']

    if power == True and scaled == True:
        Color = Color_on
    elif power == True and scaled == False:
        Color = Color_red  
    else:
        Color = Color_off


    ########################################################### 
    # display figure
    MLP = go.Figure(go.Sankey(
                    arrangement='fixed',
                    node=dict(
                              pad = 10000,
                              thickness = 10,
                              #label = Label,
                              x = X,
                              y = Y,
                              hoverinfo='skip',
                              color=len(X)*['white'], line=dict(color='white')
                              ),
                    link=dict(
                              arrowlen=25,
                              color=Color,
                              customdata=Weights,
                              hovertemplate = 'weight is %{customdata} <extra></extra>',
                              source = Source,
                              target = Target,
                              value = Value
                              )
                    ))
    ###########################################################


    # add title (and control canvas)
    MLP.update_layout(
        margin=dict(b=0), #l=20, r=20, t=0,
        title='Hidden layers:', title_x=x_pad+(1-x_pad)/2-0.005, title_y=0.95,
        font_family='ROG Fonts',
        font_size=11,
        #paper_bgcolor="#303030",
        height=520
        )


    # custom input nodes
    if id is not None and scaled==True:
        event = df_shortlist_scaled.loc[id]
        color_input="ForestGreen"       
    elif id is not None and scaled==False:
        event = df_shortlist.drop(columns=['Event','totalWeight']).loc[id]
        color_input='FireBrick'           
    else:
        event = df_shortlist_scaled.iloc[0]
        color_input='WhiteSmoke'  # hides figures to imitate empty input

    for i in range(f):  
        # input nodes shapes and values
        MLP.add_shape(type="rect",
                      xref="paper", yref="paper",
                      fillcolor="WhiteSmoke",
                      x0=x_pad-0.01, y0=(i+1)/(f+1)-0.03, x1=x_pad+0.035, y1=(i+1)/(f+1)+0.03,
                      line_color="navy", line_width=0.25,
                      label=dict(text=event[-i+(f-1)].round(2), font=dict(size=10, color=color_input))
                      )
        # input feautures labels
        MLP.add_shape(type="rect", xref="paper", yref="paper",
                      fillcolor="white",
                      x0=-0.06, y0=(i+1)/(f+1)-0.03, x1=0.08, y1=(i+1)/(f+1)+0.03,
                      line_color="white",
                      label=dict(text=Features[-i+(f-1)], textposition="middle right", 
                                font=dict(size=11, color='SteelBlue', family='Coustard Black'))
                      )
    # input header
    MLP.add_shape(type="rect", xref="paper", yref="paper",
                  fillcolor="white", line_color="white",
                  x0=x_pad-0.055, x1=x_pad+0.04, y0=1.0, y1=1.05,            
                  label=dict(text='Input Layer:', font_size=11)
                  )    
      

    # custom output nodes
    if id is not None and scaled==True and power==True:
        sig_prob = df_probs[design][id]
        bkg_prob = (1-sig_prob).round(2)
        if sig_prob>=0.5:
            Sig_Color="Bisque"
            Bkg_Color='WhiteSmoke'
            Sig_Size=16
            Bkg_Size=12
        else:
            Sig_Color="WhiteSmoke"
            Bkg_Color='PaleTurquoise'
            Sig_Size=12
            Bkg_Size=16
        true_label=df_probs['Event'][id]
        if (sig_prob>=0.5 and true_label==1) or (sig_prob<0.5 and true_label==0):
            Text_Color='ForestGreen'
        else:
            Text_Color='FireBrick'           
    else:
        sig_prob = '-'
        bkg_prob = '-'
        Sig_Color=Bkg_Color="WhiteSmoke"
        Sig_Size=Bkg_Size=12
        Text_Color='Navy'
    # signal ouput    
    MLP.add_shape(type="rect", xref="paper", yref="paper",
                  fillcolor=Sig_Color,
                  x0=1-0.045, x1=1+0.045, y0=1/(o+1)-0.06, y1=1/(o+1)+0.06,
                  line_color="Navy", line_width=0.25,
                  label=dict(text=sig_prob, font=dict(color=Text_Color,size=Sig_Size))
                  )
    # background output
    MLP.add_shape(type="rect", xref="paper", yref="paper",
                  fillcolor=Bkg_Color,
                  x0=1-0.045, x1=1+0.045, y0=2/(o+1)-0.06, y1=2/(o+1)+0.06,
                  line_color="Navy", line_width=0.25,
                  label=dict(text=bkg_prob, font=dict(color=Text_Color,size=Bkg_Size))
                  ) 
    # output header
    MLP.add_shape(type="rect", xref="paper", yref="paper",
        fillcolor="white", line_color="white",
        x0=1-0.055, x1=1+0.055, y0=1.0, y1=1.05,    
        label=dict(text='Output Layer:', font_size=11)
        ) 
    # signal header
    MLP.add_shape(type="rect", xref="paper", yref="paper",
        fillcolor="white", line_color="white",
        x0=1-0.05, x1=1+0.05, y0=1/(o+1)+0.08, y1=1/(o+1)+0.12,   
        label=dict(text='Signal probability:', font_size=11, font_family='Segoe Print')
        ) 
    # background header
    MLP.add_shape(type="rect", xref="paper", yref="paper",
        fillcolor="white", line_color="white",
        x0=1-0.06, x1=1+0.06, y0=2/(o+1)+0.08, y1=2/(o+1)+0.12,    
        label=dict(text='Background probability:', font_size=11, font_family='Segoe Print')
        ) 
    
        
    # custom hidden nodes
    for i in range(hl1):
        MLP.add_shape(type="circle",
                    xref="paper", yref="paper",
                    fillcolor="LightGreen",
                    x0=x_pad+(1-x_pad)/(Nhl+1)-0.015, x1=x_pad+(1-x_pad)/(Nhl+1)+0.015,
                    y0=(i+1)/(hl1+1)-0.04,  y1=(i+1)/(hl1+1)+0.04,
                    line_color="PaleGreen", line_width=2,
                    label=dict(text=f'{-i+hl1}', font=dict(color='whitesmoke'))
                    )
    # hidden layer 1 header
    MLP.add_shape(type="rect", xref="paper", yref="paper",
            fillcolor="white", line_color="white",
            x0=x_pad+(1-x_pad)/(Nhl+1)-0.03, x1=x_pad+(1-x_pad)/(Nhl+1)+0.03, y0=1.0, y1=1.05,            
            label=dict(text='Layer 1', font_size=11, font_color='darkgreen')
            ) 
        
    if Nhl>=2:
        for i in range(hl2):
            MLP.add_shape(type="circle",
                        xref="paper", yref="paper",
                        fillcolor="lightskyblue",
                        x0=x_pad+2*(1-x_pad)/(Nhl+1)-0.015, x1=x_pad+2*(1-x_pad)/(Nhl+1)+0.015, 
                        y0=(i+1)/(hl2+1)-0.04, y1=(i+1)/(hl2+1)+0.04,
                        line_color="paleturquoise", line_width=2,
                        label=dict(text=f'{-i+hl2}', font=dict(color='whitesmoke'))
                    )
        # hidden layer 2 header
        MLP.add_shape(type="rect", xref="paper", yref="paper",
                fillcolor="white", line_color="white",
                x0=x_pad+2*(1-x_pad)/(Nhl+1)-0.03, x1=x_pad+2*(1-x_pad)/(Nhl+1)+0.03, y0=1.0, y1=1.05,            
                label=dict(text='Layer 2', font_size=11, font_color='mediumblue')
                ) 
        if Nhl==3:
            for i in range(hl3):
                MLP.add_shape(type="circle",
                            xref="paper", yref="paper",
                            fillcolor="Plum",
                            x0=x_pad+3*(1-x_pad)/(Nhl+1)-0.015, x1=x_pad+3*(1-x_pad)/(Nhl+1)+0.015, 
                            y0=(i+1)/(hl3+1)-0.04, y1=(i+1)/(hl3+1)+0.04,
                            line_color="thistle", line_width=2,
                            label=dict(text=f'{-i+hl3}', font=dict(color='WhiteSmoke'))
                        )
            # hidden layer 3 header
            MLP.add_shape(type="rect", xref="paper", yref="paper",
                    fillcolor="White", line_color="White",
                    x0=x_pad+3*(1-x_pad)/(Nhl+1)-0.03, y0=1.0, x1=x_pad+3*(1-x_pad)/(Nhl+1)+0.03, y1=1.05,            
                    label=dict(text='Layer 3', font_size=11, font_color='Purple')
                    ) 

    # highlight            
    MLP.add_shape(type="rect",
                xref="paper", yref="paper",
                x0=x_pad+(1-x_pad)/(Nhl+1)-0.08, y0=0.98,
                x1=x_pad+Nhl*(1-x_pad)/(Nhl+1)+0.08, y1=1.2,
                opacity=0.1,
                fillcolor="Silver",
                line_color="Navy", line_width=1,
                )
    

    return MLP


#####################################################################################
#####################################################################################
## Histogram updates


@callback(
          Output("Hist", "figure"), 
          Input('Scaler_Switch', 'on'),
          Input('Power_Button', 'on'),
          Input("NN_Depth", "value"),
          Input("HL1_Selector", "value"),
          Input("HL2_Selector", "value"),
          Input("HL3_Selector", "value"),
          Input('Hist_Slider', 'value'),
          Input("Legend_Hist", "value"),
          )
def update_hist(scaled, power, number_hl, HL1_size, HL2_size, HL3_size, cut, events): 
    
    Nhl = number_hl             # number of hidden layers (1 to 3)    
    hl1 = int(HL1_size) if HL1_size%2==0 else int(HL1_size+1)  # number of nods in the hidden layers
    hl2 = int(HL2_size) if HL2_size%2==0 else int(HL2_size+1)
    hl3 = int(HL3_size) if HL3_size%2==0 else int(HL3_size+1)
    design = f'({hl1},)'             # design of MLP
    if Nhl == 2:
        design = f'({hl1}, {hl2})'
    elif Nhl == 3:
        design = f'({hl1}, {hl2}, {hl3})'


    if scaled==True and power==True:
        df = df_probs.copy()
        df_on = df[df["Event"].isin(events)]
        X = df_on[design]
        Color=['Signal' if i==1. else 'Background' for i in df_on['Event']]
        Title='Output of the Neural Network'
        Y=df_on['Weight']

    else:
        df = pd.DataFrame({'Event':np.array([0.]*50+[1.]*50),'v':np.array([0.02]*50+[0.98]*50),'w':np.array([1]*100)})
        df_on = df[df["Event"].isin(events)]
        X=df_on['v']
        Color=['Signal' if i==0.98 else 'Background' for i in df_on['v']] 
        Title='Ideal output. Activate MLP for reality'
        Y=df_on['w']


    # plot the histogram
    hist = px.histogram( x=X, y=Y, color=Color,    #data_frame=df,                    
                        #labels={'color': 'Event', f'{0.}':'Background', 1.:'Signal'},
                        color_discrete_map={'Background':'SteelBlue','Signal':'Orange'},                        
                        template = 'simple_white',
                        log_y=True,
                        barmode='overlay',                                                                
                        )
   
    # control layout
    hist.update_layout(
                        margin=dict(b=0, r=10),
                        title=dict(text=Title, font=dict(family='Coustard Black', size=14), x=0.6, y=0.95),
                        font_family='Coustard', font_size=11, font_color='SlateGrey',
                        height=400,
                        #paper_bgcolor="black",
                        xaxis_title_text='Classification: 0 - background, 1 - signal', 
                        yaxis_title_text='weight (log)', 
                        transition_duration=500,
                        showlegend=False,
                        hovermode=False
                        )
    
    hist.update_traces(
                      #  lambda trace: trace.update(marker=dict(line=dict(color='Orange', width=0),
                      #                                           pattern=dict(shape='', fgopacity=0.5, ))) if X <= cut else (),
                       xbins=dict(size=0.05, start=0.0, end=1.0),
                       )
    
    # hist.for_each_trace(
    #                     # lambda trace: trace.update(marker=dict(line=dict(color='Orange', width=0),
    #                     #                                        pattern=dict(shape='', fgopacity=0.5, ))) if trace.name == 'Signal' 
    #                     # else trace.update(marker=dict(
    #                     #                               line=dict(color='steelblue', width=0),
    #                     #                               pattern=dict(shape='', fgopacity=0.5, fillmode='overlay'))),
    #                     lambda trace: [trace.update(marker=dict(opacity=0.1,
    #                                                pattern=dict(fgopacity=0.5, ))) for x in trace.x if x<cut],   
    #                     )
    
    hist.update_xaxes(tick0=0., dtick=0.1,
                      range=[-0.05,1.05],
                      fixedrange=True)
    
    # cut line            
    hist.add_vline(x=cut, line_width=2, 
                   line_dash="dash", line_color="Maroon",
                   opacity=.8)


    # # counts - header
    # hist.add_shape(type="rect", xref="paper", yref="paper",
    #               fillcolor="White", line_color="White", line_width=0.25,
    #               x0=1.08, x1=1.27, y0=0.96-0.035, y1=0.96+0.035,    
    #               label=dict(text='Events:', textposition='middle right', font_size=16, font_family='Coustard Black', font_color='DimGrey'),
    #               ) 
    # # counts of events
    # for z,event in enumerate([0,1]):
    #     now = len(df_filt[df_filt['Event']==event])
    #     full = len(df[df['Event']==event])
    #     hist.add_shape(type="rect", xref="paper", yref="paper",
    #                   fillcolor="White", line_color="White", line_width=0.25,
    #                   x0=1.08, x1=1.12, y0=0.885-0.084*(z+1)-0.035, y1=0.885-0.084*(z+1)+0.035,                  
    #                   label=dict(text=f'{now}', textposition='middle right', font_size=13, font_color='SteelBlue', font_family='Coustard Black',) 
    #                   )
    #     hist.add_shape(type="rect", xref="paper", yref="paper",
    #                   fillcolor="White", line_color="White", line_width=0.25,
    #                   x0=1.12, x1=1.2, y0=0.885-0.084*(z+1)-0.035, y1=0.885-0.084*(z+1)+0.035,                  
    #                   label=dict(text=f'({full})', textposition='middle left', font_size=13, font_color='SteelBlue', font_family='Coustard',) 
    #                   )      
    return hist



NN.run_server(debug=True, port=7777)