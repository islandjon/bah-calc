import dash
from dash import dcc, html, Input, Output
import pandas as pd

# Load data
zip_to_mha = pd.read_csv('./sorted_zipmha24.txt', delim_whitespace=True, header=None, names=['ZIP', 'MHA'])
bahw24 = pd.read_csv('./bahw24.txt', header=None)
bahwo24 = pd.read_csv('./bahwo24.txt', header=None)
bah_2025 = pd.read_excel('./2025 BAH Rates.xlsx')

# Rename columns for clarity
bahw24.columns = ["MHA"] + [f"E{i}" for i in range(1, 11)] + [f"O{i}" for i in range(1, 8)]
bahwo24.columns = bahw24.columns

# Process 2025 data (assuming similar structure)
bah_2025.columns = ["MHA"] + [f"E{i}_2025" for i in range(1, 11)] + [f"O{i}_2025" for i in range(1, 8)]

# Merge 2024 and 2025 rates
bah_combined = pd.merge(bahw24, bahwo24, on="MHA", suffixes=("_with", "_without"))
bah_combined = pd.merge(bah_combined, bah_2025, on="MHA", how="left")

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("BAH Rate Calculator"),

    dcc.Input(id='zip-code', type='text', placeholder='Enter ZIP Code'),
    dcc.Input(id='pay-grade', type='text', placeholder='Enter Pay Grade (e.g., E5)'),

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
    if pay_grade_col not in bah_combined.columns:
        return "Invalid pay grade."

    rate_with = bah_combined.loc[bah_combined['MHA'] == mha, f"{pay_grade_col}_with"].values[0]
    rate_without = bah_combined.loc[bah_combined['MHA'] == mha, f"{pay_grade_col}_without"].values[0]
    rate_with_2025 = bah_combined.loc[bah_combined['MHA'] == mha, f"{pay_grade_col}_2025"].values[0]

    # Calculate changes
    change_with = rate_with_2025 - rate_with
    change_without = rate_with_2025 - rate_without
    pct_change_with = (change_with / rate_with) * 100 if rate_with else 0
    pct_change_without = (change_without / rate_without) * 100 if rate_without else 0

    return html.Div([
        html.H3(f"BAH Rates for MHA {mha} ({zip_code}):"),
        html.P(f"With Dependents: $ {rate_with:.2f} (2025: $ {rate_with_2025:.2f}, Change: $ {change_with:.2f}, {pct_change_with:.2f}%)"),
        html.P(f"Without Dependents: $ {rate_without:.2f} (Change: $ {change_without:.2f}, {pct_change_without:.2f}%)")
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
