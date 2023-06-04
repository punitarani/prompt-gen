"""Plotly Dash App"""

import asyncio
import base64
import concurrent.futures
import threading
from threading import Lock

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash
from dash import dash_table
from dash import dcc, html
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

from gen import generate_prompt_generations
from loader import read_file, chunk_text

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc_css])

# Global data store for generated prompt generations
data = [
    {
        "chunk": "This is a chunk",
        "prompt": "This is a prompt",
        "generation": "This is a generation",
    }
]
data_lock = Lock()

# Flag to indicate if data generation is in progress
generating_data: bool = False

# Constants
QUANTITY_STEP = 10

# This is the subject context that is provided to the LLM
BASE_PROMPT = """
You are a scientifically accurate AI that has been tasked with generating a prompt and its generation.

The prompt should be a sentence or two that is grammatically correct and makes sense.
The prompt is the input to the AI by a human and is typically a question or a statement that is open-ended.

The generation can be anything that is factually accurate and grammatically correct.
The generation is the output of the AI and is typically a paragraph or two that answers the prompt.
However, the generation can be shorter or longer based on the prompt and its complexity.

Generate a prompt and its generation based on the subject context.
The subject context is provided below.
""".strip()

# This is appended to the end of the subject context to request a prompt and its generation in JSON format
REQUEST_PROMPT = """
Now, generate a prompt and its generation based on the subject context.
You must generate between 0 and 5 prompts and their generations.
Only generate multiple prompts and their generations if they are semantically unique.
""".strip()


def prompt(chunk: str):
    """Get the prompt to request a prompt and its generation in JSON format for a given chunk."""
    return f"""
    {BASE_PROMPT}
    
    Context: {chunk}
    
    {REQUEST_PROMPT}
    
    Output the prompt and its generation formatted as a JSON object.
    {{"response": [{{"prompt": "{BASE_PROMPT}", "generation": "{REQUEST_PROMPT}"}}]}}
    
    If you are unable to generate a prompt and its generation, output a JSON object with an empty list as the response.
    """.strip()


def generate_data_thread(prompt: str, chunk: str) -> None:
    """Generate data asynchronously and save to a given store."""
    # Run the asyncio loop and the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(generate_prompt_generations(prompt))

    # Add the chunk to the result
    for generation in result:
        generation["chunk"] = chunk

    # Add the result to the global memory
    with data_lock:
        data.extend(result)


def generate_data(quantity: int, files: dict[str, str], max_threads: int = 10) -> None:
    """Generate data and save to a given store."""
    global generating_data
    generating_data = True

    chunks = []

    for file in files:
        file_name = file["name"]
        file_content_64 = file["content"]

        # File content is base64 encoded, so decode it
        file_content_bytes = base64.b64decode(file_content_64)

        # Read the file content
        file_content = read_file(file_content_bytes, file_name.split(".")[-1])

        # Split the file content into chunks
        chunks.extend(chunk_text(file_content))

    # Trim the chunks to the quantity
    chunks = chunks[:quantity]

    # Generate the data in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        for chunk in chunks:
            executor.submit(generate_data_thread, prompt(chunk), chunk)

    generating_data = False


def valid_file(filename: str) -> bool:
    """Validate the file extension"""
    valid_extensions = (
        "pdf",
        "txt",
    )
    return filename.endswith(valid_extensions)


@app.callback(
    Output("interval-component", "n_intervals"),
    Input("btn-generate", "n_clicks"),
    State("input-base-prompt", "value"),
    State("input-quantity", "value"),
    State("upload-data-store", "data"),
)
def generate_handler(n, base_prompt, quantity, files):
    """Generate button handler"""
    if n is None:
        raise PreventUpdate("Button has not been clicked yet")

    if len(data) >= quantity:
        raise PreventUpdate("Already generated enough data")

    if quantity is None or quantity <= 0:
        raise PreventUpdate("Please enter a valid quantity")

    if base_prompt is None or base_prompt == "":
        raise PreventUpdate("Please enter a valid base prompt")

    global generating_data
    if generating_data:
        raise PreventUpdate("Data generation already in progress")

    threading.Thread(
        target=generate_data,
        args=((quantity - len(data)), files),
    ).start()

    return n


@app.callback(
    Output("upload-data-store", "data"),
    Input("upload-data", "filename"),
    Input("upload-data", "contents"),
    State("upload-data-store", "data"),
    prevent_initial_call=True,
)
def save_uploaded_data(list_of_names, list_of_contents, files) -> list:
    """
    Save uploaded data to a global store
    Append the new data to the existing data
    Save the data as is, without any processing
    """
    for name, content in zip(list_of_names, list_of_contents):
        if valid_file(name):
            files.append({"name": name, "content": content.split(",")[-1]})

    return files


@app.callback(
    Output("upload-files-list", "children"),
    Input("upload-data", "filename"),
    State("upload-files-list", "children"),
    prevent_initial_call=True,
)
def update_upload_files_list(list_of_names, children) -> list:
    """Update list of uploaded files"""
    if children is None:
        children = []

    for name in list_of_names:
        if valid_file(name):
            children.append(html.Li(name))

    return children


@app.callback(
    Output("results-progress", "value"),
    Output("results-progress", "max"),
    Output("results-progress", "label"),
    Input("interval-component", "n_intervals"),
    State("input-quantity", "value"),
    State("results-progress", "value"),
    prevent_initial_call=True,
)
def update_progress(n, quantity, progress):
    """Update progress bar with new data after a given interval"""
    if not generating_data and progress >= len(data):
        raise PreventUpdate("Data generation in progress, please wait")

    # Count unique chunks
    chunks = set()
    for item in data:
        chunks.add(item["chunk"])

    return len(chunks), quantity, f"{len(chunks)}/{quantity}" if quantity else ""


@app.callback(
    Output("results-table", "data"), Input("interval-component", "n_intervals")
)
def update_table(n):
    """Update table with new data after a given interval"""
    return data


@app.callback(
    Output("download-data", "data"),
    Input("btn-download", "n_clicks"),
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


@app.callback(
    Output("btn-generate", "disabled"),
    Input("interval-component", "n_intervals"),
)
def enable_disable_generate_button(n):
    """Enable or disable generate button based on data generation status"""
    if generating_data:
        return True
    return False


@app.callback(
    Output("btn-download", "disabled"),
    Input("interval-component", "n_intervals"),
)
def enable_disable_download_button(n):
    """Enable or disable download button based on data generation status"""
    if generating_data:
        return True
    return False


input_form_field_style = "flex m-2"

prompt_input = html.Div(
    children=[
        html.Div(
            [
                dbc.Label("Base Prompt", className="text-right px-2"),
                dbc.Textarea(
                    id="input-base-prompt",
                    value=BASE_PROMPT,
                    placeholder=BASE_PROMPT,
                    rows=12,
                    minLength=250,
                    maxLength=800,
                ),
                dbc.FormText(
                    "This is used as the base prompt prefixing the chunk from the files for generation."
                ),
            ],
            style={"margin": "2rem 0"},
        ),
        html.Div(
            [
                dbc.Label("Request Prompt", className="text-right px-2"),
                dbc.Textarea(
                    id="input-request-prompt",
                    value=REQUEST_PROMPT,
                    placeholder=REQUEST_PROMPT,
                    rows=6,
                    minLength=100,
                    maxLength=400,
                ),
                dbc.FormText(
                    "This is used as the request prompt suffixing the chunk from the files for generation."
                ),
            ],
            style={"margin": "2rem 0"},
        ),
    ],
    className="m-2 h-max",
)

files_input = html.Div(
    id="upload-files-container",
    children=[
        dbc.Label("Generation Context Files", className="text-right px-2"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                children=[
                    html.Div(
                        children=[
                            "Drag and Drop or Select Files",
                        ],
                        className="mb-1",
                        style={"display": "flex", "justify-content": "center"},
                    ),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "justify-content": "center",
                    "height": "100%",
                },
            ),
            className="mx-auto m-2 cursor-pointer text-center items-center justify-center",
            style={
                "width": "100%",
                "height": "5rem",
                "cursor": "pointer",
                "border": "1px dashed #ccc",
                "border-radius": "0.5rem",
            },
            multiple=True,
        ),
        dbc.FormText("Supports .pdf and .txt files"),
        html.Ul(id="upload-files-list"),
    ],
    style={"margin": "2rem 1rem"},
)

quantity_input = dbc.Col(
    html.Div(
        [
            dbc.Label("Number of chunks to process", className="mx-2"),
            dcc.Input(
                id="input-quantity",
                className="w-1/4 px-2 mx-2",
                type="number",
                min=10,
                max=100,
                step=QUANTITY_STEP,
                value=10,
            ),
        ],
        className="flex flex-row justify-center items-center",
    ),
)

generate_button = dbc.Col(
    dbc.Button("Generate", id="btn-generate", color="primary"),
)

quantity_generate_row = html.Div(
    dbc.Row(
        [
            quantity_input,
            generate_button,
        ],
    ),
    style={"margin": "2rem 1rem", "justify-content": "center", "align-items": "center"},
)

input_form = html.Div(
    dbc.Form(
        id="input-form",
        children=[
            prompt_input,
            files_input,
            quantity_generate_row,
        ],
        className="flex flex-col justify-center items-center",
    ),
    className="w-100",
)

results_table = html.Div(
    [
        dbc.Progress(id="results-progress", value=0, max=0, className="m-2"),
        dash_table.DataTable(
            id="results-table",
            columns=[{"name": i, "id": i} for i in data[0].keys()],
            data=data,
            page_action="native",
            page_size=QUANTITY_STEP,
            style_cell={"whiteSpace": "normal", "height": "auto", "textAlign": "left"},
            style_table={
                "overflowX": "auto",
                "width": "100%",
            },
            style_data={
                "width": "auto",
                "minWidth": "100px",
            },
            style_cell_conditional=[
                {"if": {"column_id": "chunk"}, "width": "25%"},
                {"if": {"column_id": "prompt"}, "width": "25%"},
                {"if": {"column_id": "generation"}, "width": "50%"},
            ],
        ),
    ],
    className="dbc",
    style={"width": "100%"},
)

download_button = dbc.Button(
    "Download", id="btn-download", color="primary", className="m-2"
)

# main layout
app.layout = html.Div(
    className="main-container",
    children=[
        html.H1(children="Prompt-Generations Generator"),
        dcc.Store(id="upload-data-store", data=[]),
        input_form,
        dcc.Store(id="store", data=data),
        results_table,
        download_button,
        dcc.Download(id="download-data"),
        dcc.Interval(id="interval-component", interval=250, n_intervals=0),
    ],
    style={
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "space-between",
        "align-items": "center",
        "width": "80%",
        "margin": "auto",
        "padding": "1rem",
    },
)

if __name__ == "__main__":
    app.run(debug=True)
