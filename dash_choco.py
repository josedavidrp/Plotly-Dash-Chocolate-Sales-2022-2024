import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

from dash import Dash

app = Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
server = app.server

df = pd.read_csv('choco.csv')
df['Amount'] = df['Amount'].replace('[$,]', '', regex=True)
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
df['Date'] = pd.to_datetime(df['Date'],format="%d/%m/%Y")
df['Year'] = df['Date'].dt.year

dropdown_options = [
    {'label': 'All Countries', 'value': 'ALL'}
]
for country in df['Country'].unique():
    dropdown_options.append({'label': country, 'value': country})


app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1('Global Chocolate Sales Performance (2022-2025)',
                        className='text-center text-primary mb-4'),
                width=12)
    ]),
    dbc.Row([
        # Sidebar for controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Filters", className="card-title"),
                    html.P("Year range:", className="card-text font-weight-bold"),
                    dcc.RangeSlider(
                        id='year_range',
                        min=df['Year'].min(),
                        max=df['Year'].max(),
                        step=None,
                        marks={str(year): str(year) for year in df['Year'].unique()},
                        value=[df['Year'].min(), df['Year'].max()],
                    ),
                    html.Br(),
                    html.P("Select the country:", className="card-text font-weight-bold"),
                    dcc.Dropdown(
                        id='country_dropdown',
                        options=dropdown_options,
                        value='ALL',
                        placeholder="Select a Country here",
                        searchable=True
                    ),
                ])
            ], className="mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.H4("About the Data", className="card-title"),
                    html.P(
                        "Sales of chocolate between 2022 and 2025 for Australia, "
                        "Canada, India, New Zealand, UK, USA.",
                        className="card-text",
                    ),
                ])
            ], className="mb-4")
        ], width=12, lg=3, id='sidebar'),

        # Main content for graphs
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='plot1')
                        ])
                    ])
                ], width=12, className="mb-4"),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='plot2')
                        ])
                    ])
                ], width=12, className="mb-4"),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='plot3')
                        ])
                    ])
                ], width=12, className="mb-4"),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='plot4')
                        ])
                    ])
                ], width=12, className="mb-4")
            ])
        ], width=12, lg=9)
    ])
], fluid=True)



@app.callback(
    [Output(component_id='plot1', component_property='figure'),
     Output(component_id='plot2', component_property='figure'),
     Output(component_id='plot3', component_property='figure'),
     Output(component_id='plot4', component_property='figure')],
    [Input(component_id='country_dropdown', component_property='value'),
     Input(component_id="year_range", component_property="value")]
)
def basicGraph(country, year_range):
    min_year, max_year = year_range
    filtered_base = df[df['Year'].between(min_year, max_year)].copy()

    title = f"Sales between {min_year}-{max_year}"
    if country != 'ALL':
        filtered_base = filtered_base[filtered_base['Country'] == country]
        title += f" in {country}"
    else:
        title += " in all countries"

    fig1_df = filtered_base.groupby(['Country', 'Year'], as_index=False)['Amount'].sum()
    fig1_df['Amount_M'] = (fig1_df['Amount'] / 1_000_000).round(2)
    fig1_df["Year"] = fig1_df["Year"].astype(str)

    if fig1_df.empty:
        fig1 = px.bar(title=f"No data available for {title}", template='plotly_dark')
        fig2 = px.sunburst(title="No data", template='plotly_dark')
        fig3 = px.line(title="No data", template='plotly_dark')
        fig4 = px.bar(title="No data", template='plotly_dark')
        return [fig1, fig2, fig3, fig4]

    fig1 = px.bar(fig1_df, x='Country', y='Amount_M',
                  title=title,
                  color="Year",
                  labels={"Country": "Country", "Amount_M": "Sales in millions"},
                  barmode="stack",
                  template='plotly_dark'
                  )

    fig2 = px.sunburst(filtered_base, path=['Country', 'Product', 'Sales Person'],
                     values='Amount', color='Product',
                     maxdepth=2,
                     template='plotly_dark')

    monthly_sales = filtered_base.groupby(['Country', pd.Grouper(key='Date', freq='ME')])['Amount'].sum().reset_index()
    fig3 = px.line(monthly_sales, x='Date', y='Amount', color='Country',
                   title='Monthly Sales Trend by Country',
                   labels={'Date': 'Month', 'Amount': 'Total Sales'},
                   template='plotly_dark')

    # New stacked bar plot for top 3 sellers
    filtered_base['Quarter'] = filtered_base['Date'].dt.to_period('Q').astype(str)
    sales_by_person = filtered_base.groupby(['Country', 'Quarter', 'Sales Person'])['Amount'].sum().reset_index()
    top_sellers = sales_by_person.sort_values('Amount', ascending=False).groupby(['Country', 'Quarter']).head(3)
    
    if top_sellers.empty:
        fig4 = px.bar(title="No Top Seller Data Available", template='plotly_dark')
    else:
        fig4 = px.bar(top_sellers, x='Quarter', y='Amount', color='Sales Person',
                    title='Top 3 Sellers by Country and Quarter',
                    labels={'Quarter': 'Quarter', 'Amount': 'Total Sales'},
                    facet_col='Country',
                    barmode='stack',
                    template='plotly_dark',
                    category_orders={"Quarter": sorted(top_sellers['Quarter'].unique())})
        fig4.update_xaxes(matches=None)


    return [fig1, fig2, fig3, fig4]


if __name__ == '__main__':
    app.run()
