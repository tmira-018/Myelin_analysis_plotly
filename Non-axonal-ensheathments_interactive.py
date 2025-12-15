
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback_context, no_update
from dash.exceptions import PreventUpdate
import numpy as np
import os
from skimage import io
from flask import Flask

server = Flask(__name__)

app = Dash(__name__, 
           server=server,
           suppress_callback_exceptions= True)

#--------------------------------------------------------------------------------
# Plot function
def myelin_line_plot(df, column, range_y = [0, 50]):
    single_cell_fig = px.line(df,
                    x = 'cell_age', y = column,
                    markers = True,
                    hover_data = {'cell_ID': False,
                                column: True,
                                'cell_age': True,
                                'cond': False},
                                range_y = range_y)
    single_cell_fig.update_layout(title = f'{column} across cell age',
                    xaxis = dict(showline = True,
                                 showgrid= False,
                                 linecolor= 'black',
                                 linewidth = 2,
                                 tickvals = np.arange(1,4,1)),
                    yaxis = dict(showline = True,
                                         showgrid = False,
                                         linecolor= 'black',
                                         linewidth = 2,
                                         rangemode = 'tozero'),
                    plot_bgcolor = 'white',
                    height = 350,
                    margin = dict(l=50, r=20, t=50, b=50))
    single_cell_fig.update_traces(line_color = '#3E000C')
    return single_cell_fig

# Img directory
img_dir = 'Figure_5_images/'

# --------------------------------------------------------------------------------------
# Import data


path = ('DataSheets/WIN_single_cell.xlsx')
ol_df = pd.read_excel(path)

ol_analysis= ol_df[ol_df['cell_ID'].map(ol_df['cell_ID'].value_counts()) > 1]

#removes cells that were treated with 0.5 um WIN and cell age 4
ol_analysis2 = ol_df[ol_df.cond != 0.5]
ol_analysis2 = ol_analysis2[ol_analysis2.cell_age != 4]
ol_analysis2 = ol_analysis2.dropna(subset=['aberrant'])


ol_analysis3 = ol_analysis2[ol_analysis2['cell_ID'].map(ol_analysis2['cell_ID'].value_counts()) == 3].copy()   
ol_analysis3.loc[:,'aberrant_bool'] = (ol_analysis3['aberrant']>=1).astype(int)
ol_analysis3['cell_ID_norm'] = (ol_analysis3['cell_ID']
    .astype(str)
    .str.strip()
    .str.lower())

#pivot table used for heatmap
dmso_ol_analysis = ol_analysis3[ol_analysis3['cond'] == 0.0]
win_ol_analysis = ol_analysis3[ol_analysis3['cond'] == 1.0]
dmso_pivot = dmso_ol_analysis.pivot_table(index='cell_ID', 
                                           columns='cell_age', 
                                           values='aberrant')
win_pivot = win_ol_analysis.pivot_table(index='cell_ID',
                                        columns = 'cell_age',
                                        values = 'aberrant')



dmso_fig = px.imshow(dmso_pivot,
                labels = dict(x = 'Cell Age', y = 'Cell ID', color = 'Non-axonal Ensheathments'),
                x = dmso_pivot.columns,
                y = dmso_pivot.index,
                title = 'DMSO Treated Cells',
                zmin = 0, zmax = 3,
                color_continuous_scale = ['rgb(218, 235, 255)', 'rgb(143, 160, 218)',
                                           'rgb(68, 85, 143)', 'rgb(0, 10, 68)'])

win_fig = px.imshow(win_pivot,
                    labels = dict(x = 'Cell Age', y = 'Cell ID', color = 'Non-axonal Ensheathments'),
                    x = win_pivot.columns,
                    y = win_pivot.index,
                    title = 'WIN Treated Cells',
                    color_continuous_scale = ['rgb(246,224,233)', 'rgb(245,164,201)', 
                                             'rgb(247,37,133)', 'rgb(144,9,70)'])

#--------------------------------------------------------------------------------------

# App Layout
app.layout = html.Div([
    html.H1('Non-axonal Ensheathments', style = {'text-align': 'center'}),
    html.Br(),
    html.Div('Click on a Heatmap cell to see individual OL myelin data'),
                    
    html.Div(id = 'output_container', children = []),
    html.Br(),

#Heatmaps
    html.Div([
        dcc.Graph(id = 'dmso_heatmap_graph', figure = dmso_fig, style = {'width': '49%'}),
        dcc.Graph(id = 'win_heatmap_graph', figure=win_fig, style = {'width': '49%'})],
        style = {'width': '100%','display': 'flex', 'margin': '0 auto'}),
    html.Br(),

# Line plots
    html.Div('Hover over points to see cell age and value'),
    html.Div([
        dcc.Graph(id = 'no_sheaths_graph', figure ={}, style = {'width': '32%'}),
        dcc.Graph(id = 'avg_sheath_len_graph', figure = {}, style = {'width': '32%'}),
        dcc.Graph(id = 'total_output_graph', figure = {}, style = {'width': '32%'}),], 
        style = {'width': '100%', 'display':'flex', 
                 'flex-direction': 'row', 
                 'gap': '20px',
                 'margin-bottom': '20px',
                 'min-height': '400px'}),
   
    html.Br(),
    html.Hr(),
    html.Br(),

    html.Div([
        dcc.Graph(id = 'd1_img', style = {'width': '33%'}),
        dcc.Graph(id = 'd2_img', style = {'width': '33%'}),
        dcc.Graph(id = 'd3_img', style = {'width': '33%'}),],
        style = {'width': '100%', 'display':'flex', 
                  'flex-direction': 'row', 
                  'gap': '10px',
                  'margin-top': '20px',
                  'min-height': '400px'})
])

#--------------------------------------------------------------------------------------
# Connect Plotly graphs with Dash Components
@app.callback(
    [Output(component_id = 'no_sheaths_graph', component_property = 'figure'),
     Output(component_id = 'avg_sheath_len_graph', component_property = 'figure'),
     Output(component_id = 'total_output_graph', component_property = 'figure'),
     Output(component_id = 'd1_img', component_property = 'figure'),
     Output(component_id = 'd2_img', component_property = 'figure'),
     Output(component_id = 'd3_img', component_property = 'figure')],
    [Input(component_id = 'dmso_heatmap_graph', component_property = 'clickData'),
     Input('win_heatmap_graph', component_property='clickData')],
     prevent_initial_call= True
)


def update_graph_and_imgs(dmso_click, win_click):
    ctx = callback_context
    empty_img = px.imshow([[0]])
    empty_img.update_layout(title = 'Click a cell to view data')
    if not ctx.triggered:
        # No clicks yet, return empty figures
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"Triggered by: {trigger_id}")
    cell_id = None

# ----------------------------------------------------------------------
# Loading images
# ----------------------------------------------------------------------

    if trigger_id == 'dmso_heatmap_graph':
        if dmso_click is not None:
            cell_id = dmso_click['points'][0]['y']
            print(f'DMSO cell_id clicked: {cell_id}')
            condition = 0.0
        else: 
            raise PreventUpdate

    elif trigger_id == 'win_heatmap_graph':
        if win_click is not None:
            cell_id = win_click['points'][0]['y']
            print(f'WIN cell_id clicked: {cell_id}')
            condition = 1.0
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate

    img_figs = []
    for day in range(1,4):
        img_path = os.path.join(img_dir, f'MAX_{cell_id}_d{day}.jpg')
        #print(img_path)
        if os.path.exists(img_path):
            img_read = io.imread(img_path)
            #print(img_read.shape)
            img_show = px.imshow(img_read)
            img_show.update_layout(title = f'Cell ID: {cell_id} Day {day}')
            
        else:
            img_show = px.imshow([[0]])
            img_show.update_layout(title = f'Image for day {day} not found')

        img_figs.append(img_show)
        
#----------------------------------------------------------------------
# Making line plots 
# ----------------------------------------------------------------------
    single_cell_data = ol_analysis3[ol_analysis3['cell_ID'] == cell_id].copy()
    if len(single_cell_data) > 0:
            # Remove rows with missing data
            single_cell_data = single_cell_data.dropna(subset=['avg_sheath_len', 'no_sheaths', 'total_output'])
            
            if len(single_cell_data) > 0:
                no_sheaths_fig = myelin_line_plot(single_cell_data, 'no_sheaths')
                avg_sheath_len_fig = myelin_line_plot(single_cell_data, 'avg_sheath_len')
                total_output_fig = myelin_line_plot(single_cell_data, 'total_output', range_y=[0, 950])
            else:
                # All data was NaN
                no_sheaths_fig = px.line().update_layout(title=f'No data for {cell_id}')
                avg_sheath_len_fig = px.line().update_layout(title=f'No data for {cell_id}')
                total_output_fig = px.line().update_layout(title=f'No data for {cell_id}')
    else:
            # Cell not found in data
            no_sheaths_fig = px.line().update_layout(title=f'Cell {cell_id} not found in data')
            avg_sheath_len_fig = px.line().update_layout(title=f'Cell {cell_id} not found in data')
            total_output_fig = px.line().update_layout(title=f'Cell {cell_id} not found in data')
        
    return no_sheaths_fig, avg_sheath_len_fig, total_output_fig, img_figs[0], img_figs[1], img_figs[2]
#--------------------------------------------------------------------------------------
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
