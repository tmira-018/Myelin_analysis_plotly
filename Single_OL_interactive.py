
import pandas as pd
import plotly.express as px
import numpy as np

from flask import Flask
from dash import Dash, dcc, html, Input, Output

server = Flask(__name__)

app = Dash(__name__, 
           server=server,
           suppress_callback_exceptions= True)

# ------------------------------------------------------------------------------------
# Import Data


# Load data, this is the original dataframe with cell age 
cellage_path = ('WIN_single_cell.xlsx')
cellage_df = pd.read_excel(cellage_path)

#--------------------------------------------------------------------------------------
def plot_metric(df, metric, option_selected, title):
        df_plot = df.copy()
        df_plot = df_plot[df_plot.cond != 0.5]

        if option_selected != 'both':
            df_plot = df_plot[df_plot['cond'] == option_selected]
            df_plot = df_plot.dropna(subset=[metric])

        if option_selected == 'both':
            df_avg = df_plot.groupby(['cell_age', 'cond'])[metric].mean().reset_index()
            color_by = 'cond'
            color_map = {0.0: '#1768AC', 1.0: '#F72585'}
            plot_data = df_avg
            hover_dict = {metric: True,
                        'cell_age': False,
                        'cond': True}
        else:
            color_by = 'cell_ID'
            color_map = None
            plot_data =df_plot 
            hover_dict = {'cell_ID': True,
                        metric: True,
                        'cell_age': True,
                        'cond': False}
            
        fig = px.line(plot_data,
                    x = 'cell_age', y = metric,
                    color = color_by,
                    markers= True,
                    hover_data = hover_dict,
                    color_discrete_map = {0.0: '#1768AC', 1.0: '#F72585'},
                    labels = {'cell_age': 'Cell Age (days)'}
                    )
        
        fig.update_layout(title= title,
                                xaxis = dict(showline = True,
                                            showgrid = False,
                                            linecolor = 'black',
                                            linewidth = 2, 
                                            tickvals = np.arange(1,5,1)),
                                yaxis = dict(showline = True,
                                            showgrid = False,
                                            linecolor= 'black',
                                            linewidth = 2),
                                plot_bgcolor = 'white'
                                )
    
        
        return fig


#--------------------------------------------------------------------------------------

# App Layout
app.layout = html.Div([
    html.H1('Myelin Sheath Analysis', style = {'text-align': 'center'}),
    dcc.Dropdown( id= 'select_cond',
                 options = [
                     {'label': 'DMSO', 'value': 0.0},
                     {'label':'WIN 1.0', 'value': 1.0},
                     {'label': 'BOTH', 'value': 'both'}],
                     multi = False,
                     value = 'both',
                     clearable = False,
                     style = {'width': '40%'}),
                    
    html.Div(id = 'output_container', children = []),
    html.Br(),
    html.Div([
        dcc.Graph(id = 'no_sheaths_graph', figure={},
              style = {'width': '80%', 'margin': '0 auto', 'padding': '0 10'}),
        
        dcc.Graph(id = 'avg_sheath_graph', figure={},
                  style = {'width': '80%', 'margin': '0 auto', 'padding': '0 10'}),
        
        dcc.Graph(id = 'total_output_graph', figure={},
                  style = {'width': '80%', 'margin': '0 auto', 'padding': '0 10'})
    ])
])

#--------------------------------------------------------------------------------------
# Connect Plotly graphs with Dash Components
@app.callback(
    [Output(component_id = 'output_container', component_property = 'children'),
     Output(component_id = 'no_sheaths_graph', component_property = 'figure'),
     Output(component_id = 'avg_sheath_graph', component_property = 'figure'),
     Output(component_id = 'total_output_graph', component_property = 'figure')],
     [Input(component_id = 'select_cond', component_property = 'value')])


def update_graph(option_selected):
    print(option_selected)
    print(type(option_selected))

    container= 'Condition chosen: {}'.format(option_selected)
    no_sheath = plot_metric(cellage_df, 'no_sheaths', option_selected, 'Number of Sheaths across Cell Age')
    avg_sheaths = plot_metric(cellage_df, 'avg_sheath_len', option_selected, 'Average Sheath Length across Cell Age')
    total_output = plot_metric(cellage_df, 'total_output', option_selected, 'Total Output across Cell Age')
    container = f'Showing results for condition: {option_selected}'

    return container, no_sheath, avg_sheaths, total_output

    
#--------------------------------------------------------------------------------------
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

# --------------------------------------------------------------------------------------

    
