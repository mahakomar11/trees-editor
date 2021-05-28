import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_table
import numpy as np
# from googlesheets_utils import SpreadTable
from excel_utils import ExcelTable

# Load table
table = ExcelTable('Cell_hierarchy_try.xlsx')

app = dash.Dash(__name__, suppress_callback_exceptions=True)

################ Style ####################
cytoscape_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'width': '15px',
            'height': '15px',
            'label': 'data(label)',
            'font-size': '11px',
            'text-valign': 'bottom'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'width': '1px'
        }
    }
]

################ Load Sheets ####################
tree_names = ['big_tree', 'Myeloid_cells', 'B_cells', 'CD4', 'CD8', 'gd_NK_NKT']
# Create dictionary with sheets trees and urls
trees_info = {}
for tree_name in tree_names:
    trees_info[tree_name] = {}
    trees_info[tree_name]['tree'] = table.read_sheet(tree_name).set_index('BG_population')
    # Add url or path
    if hasattr(table , 'spread'):
        trees_info[tree_name]['url'] = \
            f'https://docs.google.com/spreadsheets/d/{table.spread.id}/edit#gid={table.spread.worksheet(tree_name).id}'
    else:
        trees_info[tree_name]['url'] = table.path



################ Functions ####################
def write_positions_tree(tree, tree_name):
    """
    Write tree with updated positions to Google Sheet.
    tree: pd.DataFrame
    tree_name: str, name of sheet to write to
    """
    tree_to_write = tree.reset_index()
    tree_to_write = tree_to_write[['index', 'BG_population', 'Parent', 'posX', 'posY', 'BG_label']]
    table.write_to_sheet(tree_name, tree_to_write)


def change_positions_in_tree(elements, tree):
    """
    Get positions of elements of Cytoscape graph and write it to tree.
    elements: dict, argument of cyto.Cytoscape
    tree: pd.DataFrame, tree to write to
    :return: tree: pd.DataFrame with new positions
    """
    for el in elements:
        if 'position' not in el:
            continue
        bg_pop = el['data']['id']
        pos_x = el['position']['x']
        pos_y = el['position']['y']
        tree.at[bg_pop, 'posX'] = round(pos_x, 2)
        tree.at[bg_pop, 'posY'] = - round(pos_y, 2)
    return tree


def create_cytoscape_elements(tree):
    """
    Get tree and create from it elements for Cytoscape graph.
    tree: pd.DataFrame
    :return: element: dict, argument for cyto.Cytoscape
    """
    elements = []
    for index, row in tree.iterrows():
        node = {'data': {'id': index,
                         'label': row['BG_label']}
                }

        if row['posX'] != '' and row['posY'] != '':
            node['position'] = {'x': row['posX'], 'y': -row['posY']}
        elements.append(node)
        if row['Parent'] != '' and row['Parent'] is not np.nan and row['Parent'] in tree.index:
            edge = {'data':
                        {'source': row['Parent'],
                         'target': index}
                    }
            elements.append(edge)
    return elements


################ Dash Layout ####################
app.layout = html.Div([dcc.Tabs(id='tabs', value='big_tree', children=[
    dcc.Tab(label='Main tree', value='big_tree'),
    dcc.Tab(label='Myeloid cells', value='Myeloid_cells'),
    dcc.Tab(label='B cells', value='B_cells'),
    dcc.Tab(label='CD4', value='CD4'),
    dcc.Tab(label='CD8', value='CD8'),
    dcc.Tab(label='gd, NK, NKT', value='gd_NK_NKT')]),
                       html.Div(id='tabs-content')])


################ Callbacks ####################
@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    """
    Render content depended on what tab is open.
    tab: name of opened tab = name of tree
    """
    elements = create_cytoscape_elements(trees_info[tab]['tree'])
    url = trees_info[tab]['url']

    return _render_content_tab(tab, elements, url)


def _render_content_tab(tab, elements, url):
    """
    Create <div> with adding tab to ids of children.
    tab: name of tab = name of tree
    elements: dict, argument for cyto.Cytoscape
    url: str, link to tree to show
    """
    return html.Div([
        html.Div('Drag nodes and when you like the tree, press "Save positions"', style={
            'font-size': '24px'
        }),
        cyto.Cytoscape(
            id=f'nodes-{tab}',
            layout={'name': 'preset'},
            style={'width': '80%', 'height': '70vh',
                   'border': '1px black solid',
                   'margin': '10px auto 10px'},
            elements=elements,
            boxSelectionEnabled=True,
            minZoom=0.5,
            stylesheet=cytoscape_stylesheet
        ),
        html.Div('Spreadsheet with positions:'),
        html.A(href=url, children=url, target='_blank', style={
            'margin-bottom': '20px'
        }),
        html.Div(id=f'message-{tab}'),
        html.Button(id=f'submit-{tab}', n_clicks=0, children='Save positions', style={
            'width': '200px',
            'margin-bottom': '20px'
        }),
        dash_table.DataTable(id=f'table-{tab}'),
    ], style={
        'display': 'flex',
        'flex-direction': 'column'
    })


for tab in tree_names:
    @app.callback(Output(f'message-{tab}', 'children'),
                  Output(f'table-{tab}', 'columns'),
                  Output(f'table-{tab}', 'data'),
                  Input(f'submit-{tab}', 'n_clicks'),
                  State(f'nodes-{tab}', 'elements'),
                  State(f'tabs', 'value'))
    def save_nodes_positions(n_clicks, elements, tab):
        """
        Print new positions in table and write its to Google Sheet.
        n_clicks: number of clicks on submit button
        elements: state of elements of Cytoscape component
        tab: name of opened tab = name of tree
        :return:
            message to display
            columns for table
            data for table
        """
        tree = trees_info[tab]['tree']
        if n_clicks != 0:
            new_tree = change_positions_in_tree(elements, tree)
            write_positions_tree(new_tree, tab)
            return 'Positions saved', \
                   [{"name": i, "id": i} for i in new_tree.reset_index().drop('index', axis=1).columns], \
                   new_tree.reset_index().drop('index', axis=1).to_dict('records')
        else:
            new_tree = tree.copy()
            return 'Press button to save positions of nodes', \
                   [{"name": i, "id": i} for i in new_tree.reset_index().drop('index', axis=1).columns], \
                   new_tree.reset_index().drop('index', axis=1).to_dict('records')

if __name__ == '__main__':
    # app.run_server(host='0.0.0.0', debug=True, dev_tools_hot_reload=True)
    app.run_server(debug=True, dev_tools_hot_reload=True)
