"""Plotly Dash App"""

import asyncio
import concurrent.futures
import threading
from threading import Lock

import pandas as pd
from dash import Dash
from dash import dcc, html, dash_table
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

from gen import generate_prompt_generations

app = Dash(__name__)

# Global data store for generated prompt generations
data = [{"prompt": "This is a prompt", "generation": "This is a generation"}]
data_lock = Lock()

# Flag to indicate if data generation is in progress
generating_data: bool = False


def generate_data_thread(base_prompt, keywords):
    """Generate data asynchronously and save to a given store."""
    # Run the asyncio loop and the async function
    print("generate_data_thread", base_prompt, keywords)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        generate_prompt_generations(base_prompt, keywords)
    )
    print("generate_data_thread", result)

    # Add the result to the global memory
    with data_lock:
        data.append(result)


def generate_data(quantity, base_prompt, keywords, max_threads=10):
    """Generate data and save to a given store."""
    global generating_data
    generating_data = True

    print("generate_data", quantity, base_prompt, keywords)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        for _ in range(quantity):
            executor.submit(generate_data_thread, base_prompt, keywords)

    generating_data = False


@app.callback(
    Output('interval-component', 'n_intervals'),
    Input('btn-generate', 'n_clicks'),
    [State('input-base-prompt', 'value'), State('input-keywords', 'value'), State('input-quantity', 'value')]
)
def generate_handler(n, base_prompt, keywords, quantity):
    """Generate button handler"""
    if n is None:
        raise PreventUpdate

    if quantity is None or quantity <= 0:
        raise PreventUpdate("Please enter a valid quantity")

    if base_prompt is None or base_prompt == "":
        raise PreventUpdate("Please enter a valid base prompt")

    if keywords is None or keywords == "":
        raise PreventUpdate("Please enter a valid keyword")

    global generating_data
    if generating_data:
        raise PreventUpdate("Data generation already in progress")

    threading.Thread(target=generate_data, args=(quantity, base_prompt, keywords)).start()

    return n


@app.callback(
    Output('results-table', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_table(n):
    return data


input_form_field_style = {
    "display": "flex",
    "flex-direction": "row",
    "align-items": "center",
    "justify-content": "space-between",
    "width": "100%",
    "margin-bottom": "10px",
}

input_form_input_style = {
    "height": "2rem",
    "width": "75%",
}

input_form = html.Div(
    className="input-form",
    children=[
        html.Div(
            className="prompt-div",
            children=[
                html.P("Base Prompt"),
                dcc.Input(
                    id="input-base-prompt",
                    className="input-base-prompt",
                    style=input_form_input_style,
                    value="Base prompt to generate using"
                )
            ],
            style=input_form_field_style
        ),
        html.Div(
            className="keywords-div",
            children=[
                html.P("Keywords"),
                dcc.Input(
                    id="input-keywords",
                    className="input-keywords",
                    style=input_form_input_style,
                    value="keywords, to, generate, with"
                )
            ],
            style=input_form_field_style
        ),
        html.Div(
            className="quantity-div",
            children=[
                html.P("Quantity"),
                dcc.Input(
                    id="input-quantity",
                    className="input-quantity",
                    style=input_form_input_style,
                    type='number', min=1, max=100, step=1,
                    value=5,
                )
            ],
            style=input_form_field_style
        ),
        html.Button("Generate", id="btn-generate", disabled=generating_data)
    ],
    style={
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "space-between",
        "align-items": "center",
        "width": "50%",
        "margin": "auto",
        "padding": "1rem",
    }
)

results_table = html.Div(
    dash_table.DataTable(
        id='results-table',
        columns=[{"name": i, "id": i} for i in data[0].keys()],
        data=data,
        style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'left'
        },
        style_table={
            'overflowX': 'auto',
            'width': '100%',
        },
        style_data={
            'width': 'auto',
            'minWidth': '100px',
        },
        style_cell_conditional=[
            {'if': {'column_id': 'prompt'}, 'width': '33%'},
            {'if': {'column_id': 'generation'}, 'width': '66%'},
        ],
    ),
    style={'width': '100%'}
)

download_button = html.Button("Download", id="btn-download-data")


@app.callback(
    Output("download-data", "data"),
    Input("btn-download-data", "n_clicks"),
    prevent_initial_call=True,
)
def download_handler(n_clicks):
    """Download button handler"""

    global generating_data
    if generating_data:
        raise PreventUpdate("Data generation in progress, please wait")

    df = pd.DataFrame(data)
    csv_string = df.to_csv(index=False, encoding="utf-8")
    return dict(content=csv_string, filename="data.csv")


# main layout
app.layout = html.Div(
    className="main-container",
    children=[
        html.H1(children="Prompt-Generations Generator"),
        input_form,
        dcc.Store(id='store', data=data),
        results_table,
        download_button,
        dcc.Download(id="download-data"),
        dcc.Interval(
            id='interval-component',
            interval=250,
            n_intervals=0
        ),
    ],
    style={
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "space-between",
        "align-items": "center",
        "width": "80%",
        "margin": "auto",
        "padding": "1rem",
    }
)

if __name__ == '__main__':
    app.run(debug=True)
