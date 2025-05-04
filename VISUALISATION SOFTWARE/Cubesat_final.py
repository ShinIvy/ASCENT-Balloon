import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import serial
import re
import numpy as np

# Initialisation sécurisée du port série
try:
    ser = serial.Serial('COM10', 9600, timeout=1)
except serial.SerialException as e:
    print(f"Erreur d'ouverture du port série : {e}")
    ser = None  # Empêcher les erreurs si le port est inaccessible

# Création de l'application Dash
app = dash.Dash(__name__)

# Fonction de création de la modélisation 3D du CubeSat
def create_cubesat_figure(rotation_matrix=None):
    vertices = np.array([  # Définitions des sommets du CubeSat
        [-5, -5, -10], [5, -5, -10], [5, 5, -10], [-5, 5, -10],
        [-5, -5, 10], [5, -5, 10], [5, 5, 10], [-5, 5, 10]
    ])
    if rotation_matrix is not None:
        vertices = np.dot(vertices, rotation_matrix.T)  # Appliquer la rotation aux vertices

    edges = [[vertices[i], vertices[j]] for i, j in [  # Définitions des arêtes du CubeSat
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]]

    traces = [go.Scatter3d(x=[e[0][0], e[1][0]], y=[e[0][1], e[1][1]], z=[e[0][2], e[1][2]], mode='lines',
                           line=dict(color='rgba(255, 165, 0, 0.8)', width=4)) for e in edges]

    layout = go.Layout(
        scene=dict(
            xaxis=dict(title='X (cm)', showgrid=True, gridcolor='rgba(0, 255, 255, 0.3)'),
            yaxis=dict(title='Y (cm)', showgrid=True, gridcolor='rgba(0, 255, 255, 0.3)'),
            zaxis=dict(title='Z (cm)', showgrid=True, gridcolor='rgba(0, 255, 255, 0.3)'),
            camera=dict(eye=dict(x=2, y=2, z=1.25)),
        ),
        paper_bgcolor='black', plot_bgcolor='black'
    )

    return go.Figure(data=traces, layout=layout)

def get_rotation_matrix(roll, pitch, yaw):
    roll, pitch, yaw = np.radians([roll, pitch, yaw])  # Conversion des angles en radians
    Rx = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
    Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]])
    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
    return np.dot(Rz, np.dot(Ry, Rx))

# Stockage des données
donnees = {
    'temperature': [], 'pressure': [], 'humidity': [], 'roll': [], 'pitch': [], 'yaw': [],
    'gps_time': [], 'gps_latitude': [], 'gps_longitude': [], 'gps_speed': [], 'acceleration_x': [], 'acceleration_y': [], 'acceleration_z' :[],
    'timestamps': []
}

def extraire_donnees(ligne):
    donnees = {}

    # Liste des capteurs et leurs unités
    patterns = {
        "Temperature": r"Temperature\s*=\s*([\d.]+)\s*°C",
        "Humidity": r"Humidity\s*=\s*([\d.]+)\s*%",
        "Pressure": r"Pressure\s*=\s*([\d.]+)\s*kPa",
        "Illuminance": r"Illuminance\s*=\s*([\d.]+)\s*lx",
        "Accelerometer": r"aX\s*=\s*([\d.]+)\s*aY\s*=\s*([\d.]+)\s*aZ\s*=\s*([\d.]+)",
        "Gyroscope": r"gX\s*=\s*([\d.]+)\s*gY\s*=\s*([\d.]+)\s*gZ\s*=\s*([\d.]+)",
        "GPS Latitude": r"GPS latitude\s*=\s*([\d.]+)",
        "GPS Longitude": r"GPS longitude\s*=\s*([\d.]+)",
        "GPS Speed": r"GPS speed\s*=\s*([\d.]+)",
        "GPS Time": r"GPS time \(UNIX\)\s*=\s*([\d]+)"
    }

    # Parcours des patterns pour extraire les valeurs
    for key, pattern in patterns.items():
        match = re.search(pattern, ligne)
        if match:
            if "Accelerometer" in key or "Gyroscope" in key:
                # Convertir en liste de 3 valeurs
                donnees[key] = [float(match.group(1)), float(match.group(2)), float(match.group(3))]
            elif "GPS Time" in key:
                donnees[key] = int(match.group(1))  # GPS Time est un entier UNIX
            else:
                donnees[key] = float(match.group(1))  # Autres valeurs en float
    
    return donnees


def read_serial_data():
    if not ser:
        return None  # Éviter les erreurs si le port n'est pas ouvert
    try:
        line = ser.readline()
        print(f"Brut: {line}")  # Debugging pour voir ce qui arrive
        line = line.decode('utf-8', errors='ignore').strip()

        # Supprimer la condition de filtrage
        return extraire_donnees(line)  
    except (serial.SerialException, UnicodeDecodeError) as e:
        print(f"Erreur série : {e}")
    return None


# Mise en page de l'application
app.layout = html.Div([
    html.H1("CubeSat Dashboard"),
    dcc.Graph(id='3d-cubesat', figure=create_cubesat_figure()),
    dcc.Graph(id='temperature-graph'),
    dcc.Graph(id='pressure-graph'),
    dcc.Graph(id='humidity-graph'),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
])


def stylize_graph(fig, line_color, title):
    fig.update_layout(
        paper_bgcolor="#121212",  # Fond global
        plot_bgcolor="#1A1A1A",   # Fond du graphe
        font=dict(color="#E63946"),  # Couleur du texte (rouge Bebop)
        title=dict(
            text=title,
            font=dict(color=line_color),  # Titre du graphique avec la couleur de la ligne
            x=0.5,  # Centré
        ),
        xaxis=dict(
            title=dict(text="Time (s)", font=dict(color=line_color)),  # Couleur de l'axe X
            gridcolor="rgba(255, 94, 0, 0.3)",  # Quadrillage orange subtil
            zerolinecolor="#FF5E00",  # Axe 0 en orange vif
            showline=True, linewidth=2, linecolor="#FF5E00",
        ),
        yaxis=dict(
            title=dict(text=title, font=dict(color=line_color)),  # Couleur de l'axe Y
            gridcolor="rgba(255, 94, 0, 0.3)",
            zerolinecolor="#FF5E00",
            showline=True, linewidth=2, linecolor="#FF5E00",
        ),
    )
    fig.update_traces(line=dict(color=line_color, width=2))
    return fig


@app.callback(
    [Output('temperature-graph', 'figure'), Output('pressure-graph', 'figure'), Output('humidity-graph', 'figure'),
     Output('gps-time-graph', 'figure'), Output('gps-latitude-graph', 'figure'), Output('gps-longitude-graph', 'figure'), Output('gps-speed-graph', 'figure'),
     Output('gyroscope-roll-graph', 'figure'), Output('gyroscope-pitch-graph', 'figure'), Output('gyroscope-yaw-graph', 'figure'),  
     Output('acceleration-x-graph', 'figure'), Output('acceleration-y-graph', 'figure'),
     Output('acceleration-z-graph', 'figure'), Output('3d-cubesat', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    new_data = read_serial_data()

    # Ajout des nouvelles données
    if new_data:
        donnees['timestamps'].append(n)
        if "Temperature" in new_data:
            donnees['temperature'].append(new_data["Temperature"])
        if "Pressure" in new_data:
            donnees['pressure'].append(new_data["Pressure"])
        if "Humidity" in new_data:
            donnees['humidity'].append(new_data["Humidity"])
        if "GPS Time" in new_data:
            donnees['gps_time'].append(new_data["GPS Time"])
        if "GPS Latitude" in new_data:
            donnees['gps_latitude'].append(new_data["GPS Latitude"])
        if "GPS Longitude" in new_data:
            donnees['gps_longitude'].append(new_data["GPS Longitude"])
        if "GPS Speed" in new_data:
            donnees['gps_speed'].append(new_data["GPS Speed"])
        if "Accelerometer" in new_data:
            aX, aY, aZ = new_data["Accelerometer"]
            donnees['acceleration_x'].append(aX)
            donnees['acceleration_y'].append(aY)
            donnees['acceleration_z'].append(aZ)
    
    # Calcul de la matrice de rotation avec les derniers angles Roll, Pitch, Yaw
    roll = donnees['roll'][-1] if donnees['roll'] else 0
    pitch = donnees['pitch'][-1] if donnees['pitch'] else 0
    yaw = donnees['yaw'][-1] if donnees['yaw'] else 0
    rotation_matrix = get_rotation_matrix(roll, pitch, yaw)

    # Création des graphiques
    def create_figure(y_data, name, color):
        title = f"{name}"
        y_axis_title = name.replace("Graph", "")
        fig = go.Figure(data=[go.Scatter(x=donnees['timestamps'], y=y_data, mode='lines+markers', name=name, line=dict(color=color))],
                         layout=go.Layout(title=name, xaxis={'title': 'Timestamp'}, yaxis={'title': y_axis_title}))
        return stylize_graph(fig, color, title)

    # Retour des graphiques stylisés
    return (
        create_figure(donnees['temperature'], "Temperature (°C)", "#E63946"),
        create_figure(donnees['pressure'], "Pressure (kPa)", "#FFD700"),
        create_figure(donnees['humidity'], "Humidity (%)", "#40E0D0"),
        create_figure(donnees['gps_time'], "GPS Time", "#FF00FF"),
        create_figure(donnees['gps_latitude'], "GPS Latitude", "#E63946"),
        create_figure(donnees['gps_longitude'], "GPS Longitude", "#40E0D0"),
        create_figure(donnees['gps_speed'], "GPS Speed", "#FFD700"),
        create_figure(donnees['roll'], "Gyroscope Roll (°)", "#E63946"),
        create_figure(donnees['pitch'], "Gyroscope Pitch (°)", "#FFD700"),
        create_figure(donnees['yaw'], "Gyroscope Yaw (°)", "#40E0D0"),
        create_figure(donnees['acceleration_x'], "Acceleration X (m/s²)", "#E63946"),
        create_figure(donnees['acceleration_y'], "Acceleration Y (m/s²)", "#FFD700"),
        create_figure(donnees['acceleration_z'], "Acceleration Z (m/s²)", "#40E0D0"),
        create_cubesat_figure(rotation_matrix)
    )


app.layout = html.Div([

    # Nom de mission et logo
    html.Div(className="header", style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin': '20px', "background": "white"}, children=[
        html.Img(src='/assets/ASCENT_logo.jpg', className="logo", style={'height': '120px', 'paddingRight': '10px'}),
        html.H1("ASCENT"),
    ]),

    # Sous-titre
    html.P("Attitude and Signal Control for Enhanced Networking and Tracking"),

    # 🔹 Sections des graphiques
    html.H2("3D Modeling of the CubeSat", style={'fontWeight': 'bold'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='3d-cubesat', figure=create_cubesat_figure())]),  # Modélisation 3D CubeSat
    
    html.H2("Environmental Data", style={'fontWeight': 'bold'}),
    html.H3("Temperature", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='temperature-graph', figure=go.Figure())]),
    html.H3("Pressure ", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='pressure-graph', figure=go.Figure())]),
    html.H3("Humidity", style={'color': '#40E0D0'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='humidity-graph', figure=go.Figure())]),

    html.H2("GPS Data", style={'fontWeight': 'bold'}),
    html.H3("GPS Time", style={'color': '#FF00FF'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-time-graph', figure=go.Figure())]),
    html.H3("GPS Latitude", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-latitude-graph', figure=go.Figure())]),
    html.H3("GPS Longitude", style={'color': '#40E0D0'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-longitude-graph', figure=go.Figure())]),
    html.H3("GPS Speed", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gps-speed-graph', figure=go.Figure())]),

    html.H2("Gyroscope Data", style={'fontWeight': 'bold'}),
    html.H3("Roll Angle", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gyroscope-roll-graph', figure=go.Figure())]),
    html.H3("Pitch Angle", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gyroscope-pitch-graph', figure=go.Figure())]),
    html.H3("Yaw Angle", style={'color': '#40E0D0'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='gyroscope-yaw-graph', figure=go.Figure())]),

    html.H2("Accelerometer Data", style={'fontWeight': 'bold'}),
    html.H3("X axis Acceleration", style={'color': '#E63946'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='acceleration-x-graph', figure=go.Figure())]),
    html.H3("Y axis Acceleration", style={'color': '#FFD700'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='acceleration-y-graph', figure=go.Figure())]),
    html.H3("Z axis Acceleration", style={'color': '#40E0D0'}),
    html.Div(className="graph-container", children=[dcc.Graph(id='acceleration-z-graph', figure=go.Figure())]),

    dcc.Interval(
        id='interval-component',
        interval=1000,  # Mise à jour toutes les secondes (1000 ms)
        n_intervals=0  # Démarrer l'intervalle dès le début
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
