import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import flask
# initialize the Dash app using Flask
server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Load data
zip_to_mha = pd.read_csv('./sorted_zipmha24.txt', delim_whitespace=True, header=None, names=['ZIP', 'MHA'])
bah_2024_with = pd.read_excel('./2024 BAH Rates.xlsx', header=1, sheet_name="With")
bah_2024_without = pd.read_excel('./2024 BAH Rates.xlsx', header=1, sheet_name="Without")
bah_2025_with = pd.read_excel('./2025 BAH Rates.xlsx', header=1, sheet_name="With")
bah_2025_without = pd.read_excel('./2025 BAH Rates.xlsx', header=1, sheet_name="Without")


# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("BAH Rate Calculator"),

    dcc.Dropdown(id='zip-code', options=[{'label': str(zip_code), 'value': zip_code} for zip_code in zip_to_mha['ZIP'].unique()], placeholder='Select ZIP Code'),
    dcc.Dropdown(id='pay-grade', options=[{'label': grade, 'value': grade} for grade in bah_2025_without.columns if grade.startswith('E') or grade.startswith('O') or grade.startswith('W')], placeholder='Select Pay Grade'),

    html.Button('Submit', id='submit-button', n_clicks=0),

    html.Div(id='output-container')
])

@app.callback(
    Output('output-container', 'children'),
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('zip-code', 'value'),
     dash.dependencies.State('pay-grade', 'value')]
)
def update_output(n_clicks, zip_code, pay_grade):
    if not zip_code or not pay_grade:
        return "Please enter both ZIP code and pay grade."

    # Get MHA from ZIP code
    zip_code = int(zip_code)
    mha_row = zip_to_mha[zip_to_mha['ZIP'] == zip_code]
    if mha_row.empty:
        return "Invalid ZIP code."
    mha = mha_row.iloc[0]['MHA']

    # Retrieve rates
    pay_grade_col = pay_grade
    if pay_grade_col not in bah_2025_without.columns:
        return "Invalid pay grade."

    rate_with = bah_2024_with.loc[bah_2024_with['MHA'] == mha, f"{pay_grade_col}"].values[0]
    rate_without = bah_2024_without.loc[bah_2024_without['MHA'] == mha, f"{pay_grade_col}"].values[0]
    rate_with_2025 = bah_2025_with.loc[bah_2025_with['MHA'] == mha, f"{pay_grade_col}"].values[0]
    rate_without_2025 = bah_2025_without.loc[bah_2025_without['MHA'] == mha, f"{pay_grade_col}"].values[0]


    # Calculate changes
    change_with = rate_with_2025 - rate_with
    change_without = rate_without_2025 - rate_without
    pct_change_with = (change_with / rate_with) * 100 if rate_with else 0
    pct_change_without = (change_without / rate_without) * 100 if rate_without else 0

    return html.Div([
        html.H3(f"BAH Rates for MHA {mha} ({zip_code}):"),
        html.P(f"With Dependents: $ {rate_with:.2f} (2025: $ {rate_with_2025:.2f}, Change: $ {change_with:.2f}, {pct_change_with:.2f}%)"),
        html.P(f"Without Dependents: $ {rate_without:.2f} (2025: $ {rate_with_2025:.2f}, Change: $ {change_without:.2f}, {pct_change_without:.2f}%)")
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
