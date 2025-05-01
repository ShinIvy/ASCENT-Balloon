import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import queue
import threading
import time

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# File d’attente pour stocker les données
data_queue = queue.Queue()

# Chargement du fichier CSV
csv_filename = "DATA.txt"  # Remplace par ton fichier CSV
#df = pd.read_csv(csv_filename, header=None, encoding='ISO-8859-1')  # Assurez-vous que le fichier n'a pas d'en-têtes

# Chargement des 250 dernières lignes du fichier CSV
csv_filename = "DATA.txt"  # Remplace par ton fichier
df = pd.read_csv(csv_filename, header=None, names=[
    "time", "temperature", "roll", "pitch", "yaw", 
    "accX", "accY", "accZ", "humidity", "gps_time", "gps_lat", "gps_lon", "gps_speed", "illuminance"], skiprows=lambda x: x < sum(1 for _ in open(csv_filename)) - 250)

# Nommer les colonnes selon les données
df.columns = ['timestamp', 'temperature', 'pressure', 'roll', 'pitch', 'yaw', 
              'accX', 'accY', 'accZ', 'humidity', 'gps_time', 'gps_lat', "gps_lon", "gps_speed"]

# Fonction pour lire les 100 dernières lignes du fichier CSV
def read_data_stream():
    """Simule la lecture en continu des 100 dernières lignes depuis un flux (CSV ici)."""
    for index in range(len(df)):
        row = df.iloc[index]
        data_point = {
            "time": row["timestamp"],
            "temperature": row["temperature"],
            "pressure": row["pressure"],
            "roll": row["roll"],
            "pitch": row["pitch"],
            "yaw": row["yaw"],
            "accX": row["accX"],
            "accY": row["accY"],
            "accZ": row["accZ"],
            "humidity": row["humidity"],
            "gps_lat": row["gps_lat"],
            "gps_lon":row["gps_lon"],
            "gps_speed":row["gps_speed"]
        }
        data_queue.put(data_point)  # On ajoute la donnée à la queue
        time.sleep(0.005)  # Simule un intervalle de 50 ms (20 Hz)

# Lancer le thread en arrière-plan
threading.Thread(target=read_data_stream, daemon=True).start()

def create_cubesat_figure(rotation_matrix=None):
    # Ajustement des dimensions du CubeSat : 10x10x20 cm
    vertices = np.array([ 
        [-5, -5, -10], [5, -5, -10], [5, 5, -10], [-5, 5, -10], 
        [-5, -5, 10], [5, -5, 10], [5, 5, 10], [-5, 5, 10]
    ])
    if rotation_matrix is not None:
        vertices = np.dot(vertices, rotation_matrix.T)
    
    # Définition des arêtes
    edges = [[vertices[i], vertices[j]] for i, j in [
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), 
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]]
    
    # Tracé du CubeSat avec un effet néon orange
    traces = [go.Scatter3d(x=[e[0][0], e[1][0]], y=[e[0][1], e[1][1]], z=[e[0][2], e[1][2]], mode='lines',
                           line=dict(color='rgba(255, 165, 0, 0.8)', width=4)) for e in edges]  # Orange néon

    # Configuration des axes avec une grille et des couleurs néon
    layout = go.Layout(
        scene=dict(
            xaxis=dict(
                title='X (cm)',
                title_font=dict(color='rgba(255, 0, 0, 1)', size=14), 
                tickmode='array',
                tickvals=[-5, 0, 5],
                ticktext=['-5 cm', '0 cm', '5 cm'],
                showgrid=True,
                gridcolor='rgba(0, 255, 255, 0.3)',  # Grille en néon bleu clair
                gridwidth=1,
                zeroline=True,
                zerolinecolor='rgba(0, 255, 255, 0.3)',  # Ligne centrale en rouge néon
                zerolinewidth=2,
                tickcolor='rgba(255, 0, 0, 1)',  # Texte des axes en rouge néon
                tickfont=dict(color='rgba(255, 0, 0, 1)', size=12)
            ),
            yaxis=dict(
                title='Y (cm)',
                title_font=dict(color='rgba(0, 255, 0, 1)', size=14), 
                tickmode='array',
                tickvals=[-5, 0, 5],
                ticktext=['-5 cm', '0 cm', '5 cm'],
                showgrid=True,
                gridcolor='rgba(0, 255, 255, 0.3)',  
                gridwidth=1,
                zeroline=True,
                zerolinecolor='rgba(0, 255, 255, 0.3)',  # Ligne centrale en vert néon
                zerolinewidth=2,
                tickcolor='rgba(0, 255, 0, 1)',  # Texte des axes en vert néon
                tickfont=dict(color='rgba(0, 255, 0, 1)', size=12)
            ),
            zaxis=dict(
                title='Z (cm)',
                title_font=dict(color='rgba(0, 0, 255, 1)', size=14), 
                tickmode='array',
                tickvals=[-10, 0, 10],
                ticktext=['-10 cm', '0 cm', '10 cm'],
                showgrid=True,
                gridcolor='rgba(0, 255, 255, 0.3)',  
                gridwidth=1,
                zeroline=True,
                zerolinecolor='rgba(0, 255, 255, 0.3)',  # Ligne centrale en bleu néon
                zerolinewidth=2,
                tickcolor='rgba(0, 0, 255, 1)',  # Texte des axes en bleu néon
                tickfont=dict(color='rgba(0, 0, 255, 1)', size=12)
            ),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)  # Dézoom léger en éloignant la caméra
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor='black',  # Fond noir
        plot_bgcolor='black',  # Fond noir
    )
    
    return go.Figure(data=traces, layout=layout)


# Fonction pour calculer la matrice de rotation
def get_rotation_matrix(roll, pitch, yaw):
    roll, pitch, yaw = np.radians([roll, pitch, yaw])
    Rx = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
    Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]])
    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
    return np.dot(Rz, np.dot(Ry, Rx))

def stylize_graph(fig, line_color, xaxis_title='X', yaxis_title='Y', xaxis_title_color='rgba(255, 0, 0, 1)', yaxis_title_color='rgba(0, 255, 0, 1)', grid_color='rgba(255, 94, 0, 0.3)', tick_color='rgba(255, 0, 0, 1)'):
    fig.update_layout(
        paper_bgcolor="#121212",  # Fond global
        plot_bgcolor="#1A1A1A",   # Fond du graphe
        font=dict(color="#E63946"),  # Couleur du texte (rouge Bebop)
        xaxis=dict(
            title=xaxis_title,
            title_font=dict(color=xaxis_title_color, size=14),
            gridcolor=grid_color,  # Quadrillage coloré
            zerolinecolor="#FF5E00",  # Axe 0 en orange vif
            showline=True, linewidth=2, linecolor="#FF5E00",
            tickcolor=tick_color  # Couleur des ticks
        ),
        yaxis=dict(
            title=yaxis_title,
            title_font=dict(color=yaxis_title_color, size=14),
            gridcolor=grid_color,
            zerolinecolor="#FF5E00",
            showline=True, linewidth=2, linecolor="#FF5E00",
            tickcolor=tick_color
        ),
    )
    fig.update_traces(line=dict(color=line_color, width=2))
    return fig


# Dictionnaire global pour stocker l'historique des valeurs
historical_data = {
    "time": [],
    "roll": [],
    "pitch": [],
    "yaw": [],
    "temperature": [],
    "pressure": [],
    "humidity": [],
    "accX": [],
    "accY": [],
    "accZ": [],
    "gps_lat": [],
    "gps_lon": [],
    "gps_speed": []
}

@app.callback(
    [Output('3d-cubesat', 'figure'),
     Output('roll-graph', 'figure'),
     Output('pitch-graph', 'figure'),
     Output('yaw-graph', 'figure'),
     Output('temperature-graph', 'figure'),
     Output('pressure-graph', 'figure'),
     Output('humidity-graph', 'figure'),
     Output('acc-x-graph', 'figure'),
     Output('acc-y-graph', 'figure'),
     Output('acc-z-graph', 'figure'),
     Output('gps-lat-graph', 'figure'),
     Output('gps-lon-graph', 'figure'),
     Output('gps-speed-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n_intervals):
    if not data_queue.empty():
        data_point = data_queue.get()

        # Ajouter les nouvelles données à l'historique
        for key in historical_data:
            historical_data[key].append(data_point[key])
        
        # Limiter l'historique à 100 points
        for key in historical_data:
            if len(historical_data[key]) > 100:
                historical_data[key].pop(0)

    rotation_matrix = get_rotation_matrix(historical_data["roll"][-1], 
                                          historical_data["pitch"][-1], 
                                          historical_data["yaw"][-1])
    cubesat_fig = create_cubesat_figure(rotation_matrix)

    # Créer les graphiques pour chaque paramètre
    roll_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                      y=historical_data["roll"], 
                                                      mode='lines')),  "#E63946", 
    xaxis_title="Time (s)", 
    yaxis_title="Roll (°)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)" ) # Exemple : couleur des ticks en rouge)

    pitch_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                       y=historical_data["pitch"], 
                                                       mode='lines')), "#FFD700" ,
    xaxis_title="Time (s)", 
    yaxis_title="Pitch (°)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)" ) # Exemple : couleur des ticks en rouge)

    yaw_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                     y=historical_data["yaw"], 
                                                     mode='lines')), "#4682B4", 
  xaxis_title="Time (s)", 
  yaxis_title="Yaw (°)",
  xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
  yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
  grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
  tick_color="rgba(255, 0, 0, 1)" )

    temperature_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                            y=historical_data["temperature"], 
                                                            mode='lines')), "#E63946", 
    xaxis_title="Time (s)", 
    yaxis_title="Temperature (°C)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    pressure_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                          y=historical_data["pressure"], 
                                                          mode='lines')), "#FFD700", 
    xaxis_title="Time (s)", 
    yaxis_title="Presssure (hPa)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    humidity_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                          y=historical_data["humidity"], 
                                                          mode='lines')), "#4682B4", 
    xaxis_title="Time (s)", 
    yaxis_title="Humidity (%)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    acc_x_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                        y=historical_data["accX"], 
                                                        mode='lines')), "#E63946", 
    xaxis_title="Time (s)", 
    yaxis_title="X axis Acceleration (°C)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    acc_y_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                        y=historical_data["accY"], 
                                                        mode='lines')), "#FFD700", 
    xaxis_title="Time (s)", 
    yaxis_title="Y axis acceleration (m/s-2)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    acc_z_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                        y=historical_data["accZ"], 
                                                        mode='lines')), "#4682B4", 
    xaxis_title="Time (s)", 
    yaxis_title="Z axis Acceleration (m/s-2)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    gps_lat_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                          y=historical_data["gps_lat"], 
                                                          mode='lines')), "#E63946", 
    xaxis_title="Time (s)", 
    yaxis_title="GPS latitude (°)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    gps_lon_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                          y=historical_data["gps_lon"], 
                                                          mode='lines')), "#FFD700", 
    xaxis_title="Time (s)", 
    yaxis_title="GPS longitude (°)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)
    
    gps_speed_fig = stylize_graph(go.Figure(data=go.Scatter(x=historical_data["time"], 
                                                          y=historical_data["gps_speed"], 
                                                          mode='lines')), "#4682B4", 
    xaxis_title="Time (s)", 
    yaxis_title="GPS Speed (s)",
    xaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre X en rouge
    yaxis_title_color="rgba(255, 0, 0, 1)",  # Exemple : titre Y en vert
    grid_color="rgba(255, 94, 0, 0.3)",  # Exemple : couleur de la grille orange
    tick_color="rgba(255, 0, 0, 1)"  # Exemple : couleur des ticks en rouge
)

    return (cubesat_fig, roll_fig, pitch_fig, yaw_fig, temperature_fig, pressure_fig, humidity_fig,
            acc_x_fig, acc_y_fig, acc_z_fig, gps_lat_fig, gps_lon_fig, gps_speed_fig)

app.layout = html.Div([  # (Rest of the layout code remains unchanged)
    # Nom de mission et logo
    html.Div(className="header", style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin': '20px', "background": "white"}, children=[
        html.Img(src='/assets/ASCENT_logo.jpg', className="logo", style={'height': '120px', 'paddingRight': '10px'}),
        html.H1("ASCENT"),
    ]),

    # Sous-titre
    html.P("Attitude and Signal Control for Enhanced Networking and Tracking"),

    # Modélisation 3D
    html.H2("3D Modeling of the CubeSat"),
    html.Div(className="graph-container", children=[dcc.Graph(id='3d-cubesat')]),

    # Graphiques des données environnementales
    html.H2("Environmental Data"),
    html.H3("Temperature in Celsius", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='temperature-graph')]),
    html.H3("Pressure in bar", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='pressure-graph')]),
    html.H3("Humidity in percentage", style={'color': '#4682B4'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='humidity-graph')]),

    # Graphiques des données environnementales
    html.H2("GPS"),
    html.H3("Latitude of the GPS", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-lat-graph')]),
    html.H3("Longitude of the GPS", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-lon-graph')]),
    html.H3("Speed of the GPS", style={'color': '#4682B4'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-speed-graph')]),

    # Graphiques des angles de rotation
    html.H2("Rotation Angles"),
    html.H3("Roll Angle", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='roll-graph')]),
    html.H3("Pitch Angle", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='pitch-graph')]),
    html.H3("Yaw Angle", style={'color': '#4682B4'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='yaw-graph')]),

    # Graphiques des données environnementales
    html.H2("Linear Acceleration"),
    html.H3("X axis Acceleration", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='acc-x-graph')]),
    html.H3("Y axis Acceleration", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='acc-y-graph')]),
    html.H3("Z axis Acceleration", style={'color': '#4682B4'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='acc-z-graph')]),

    # Interval pour mise à jour
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
])

if __name__ == '__main__':
    app.run_server(debug=True)
