import streamlit as st
import folium
from streamlit.components.v1 import html
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd

st.set_page_config(layout="wide")

# --- Funciones Auxiliares ---

def plot_radar_chart(df_data, category_col, value_col):
    """Genera un gráfico de radar de Plotly."""
    categorias = df_data[category_col].tolist()
    valores = df_data[value_col].tolist()

    categorias += [categorias[0]]
    valores += [valores[0]]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            name='Derechos',
            line=dict(color='royalblue')
        )
    )

    fig.update_layout(
        width=350,
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, 4],
                tickvals=[0, 1, 2, 3, 4],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=11)
            )
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def color_map(valor):
    """Función para mapear 'derechos' a color (degradado de blanco a azul)."""
    colores = ["#ffffff", "#cce5ff", "#99ccff", "#3399ff", "#004c99"]
    return colores[int(valor)] if valor in range(5) else "#ffffff"

def create_folium_map(gdf, selected_variable, zoom_start, tooltip_fields, tooltip_aliases, selected_tile_name):
    """Crea y muestra un mapa de Folium."""
    filtered_gdf = gdf[gdf["VARIABLE"] == selected_variable]
    if not filtered_gdf.empty:
        # Si filtered_gdf tiene geometría, usar su centroide
        centro = filtered_gdf.geometry.union_all().centroid
    else:
        # Fallback si filtered_gdf está vacío, usar el centroide del gdf original o un valor predeterminado
        centro = gdf.geometry.union_all().centroid if not gdf.empty else ( -26.779, -66.027) # Coordenadas predeterminadas

    m = folium.Map(location=[centro.y, centro.x], zoom_start=zoom_start, tiles=None) # tiles=None para agregar el seleccionado después

    # Agregar el TileLayer seleccionado por el usuario
    tile_info = TILE_OPTIONS.get(selected_tile_name)
    if tile_info:
        if tile_info["type"] == "builtin":
            folium.TileLayer(tile_info["url_or_name"], name=selected_tile_name).add_to(m)
        elif tile_info["type"] == "custom":
            folium.TileLayer(
                tiles=tile_info["url_or_name"],
                attr=tile_info["attr"],
                name=selected_tile_name,
                overlay=False,
                control=True
            ).add_to(m)

    folium.GeoJson(
        filtered_gdf.to_json(),
        name=selected_variable,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases
        ),
        style_function=lambda feature: {
            "fillColor": color_map(feature["properties"]["DERECHOS"]),
            "color": "#013161",
            "weight": 2,
            "fillOpacity": 0.5,
        }
    ).add_to(m)

    # La línea folium.LayerControl ha sido eliminada para quitar las leyendas internas
    html(m._repr_html_(), height=600)

def display_data_and_charts(gdf_data, filter_col=None, filter_value=None, category_col=None):
    """Muestra la tabla de datos y el gráfico de radar."""
    df_display = gdf_data.drop(["geometry"], axis=1)
    if filter_col and filter_value:
        df_display = df_display[df_display[filter_col] == filter_value].copy() # Use .copy() to avoid SettingWithCopyWarning
        # Asegúrate de que las columnas 'VARIABLE' y 'DERECHOS' existan después del filtrado
        if not all(col in df_display.columns for col in ["VARIABLE", "DERECHOS"]):
            st.warning(f"Las columnas 'VARIABLE' o 'DERECHOS' no se encontraron en los datos filtrados para {filter_col}={filter_value}.")
            df_chart_data = pd.DataFrame(columns=["VARIABLE", "DERECHOS"]) # DataFrame vacío para evitar errores
        else:
            df_chart_data = df_display[["VARIABLE", "DERECHOS"]]
    else:
        if not all(col in df_display.columns for col in ["VARIABLE", "DERECHOS"]):
            st.warning("Las columnas 'VARIABLE' o 'DERECHOS' no se encontraron en los datos.")
            df_chart_data = pd.DataFrame(columns=["VARIABLE", "DERECHOS"]) # DataFrame vacío para evitar errores
        else:
            df_chart_data = df_display[["VARIABLE", "DERECHOS"]].copy() # Use .copy()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Matriz de la Brújula")
        if not df_chart_data.empty:
            st.markdown(
                df_chart_data.style.hide(axis='index').to_html(),
                unsafe_allow_html=True
            )
        else:
            st.info("No hay datos para mostrar en la matriz para esta selección.")
    with col2:
        st.markdown("Gráfico de la Brújula")
        if not df_chart_data.empty:
            plot_radar_chart(df_chart_data, "VARIABLE", "DERECHOS")
        else:
            st.warning("No hay datos para generar el gráfico de radar.")

# --- Definición de opciones de Tiles ---
TILE_OPTIONS = {
    "Fondo Satelital": {
        "url_or_name": 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        "attr": 'Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        "type": "custom"
    },
    "Fondo Mapa": {"url_or_name": "OpenStreetMap", "type": "builtin"}
}


# --- Carga de Datos ---
DATA_PATHS_VIVIENDA_SUELO = {
    "departamento": "data/vivienda-suelo/santa-maria-departamento.geojson",
    "municipios": "data/vivienda-suelo/santa-maria-municipios.geojson",
    "localidades": "data/vivienda-suelo/santa-maria-localidades.geojson",
    "manzanero": "data/vivienda-suelo/santa-maria-manzanero.geojson",
}
gdf_data_vivienda_suelo = {key: gpd.read_file(path) for key, path in DATA_PATHS_VIVIENDA_SUELO.items()}

DATA_PATHS_INFRAESTRUCTURAS = {
    "departamento": "data/infraestructuras/santa-maria-departamento.geojson",
    "municipios": "data/infraestructuras/santa-maria-municipios.geojson",
    "localidades": "data/infraestructuras/santa-maria-localidades.geojson",
    "manzanero": "data/infraestructuras/santa-maria-manzanero.geojson",
}
gdf_data_infraestructuras = {key: gpd.read_file(path) for key, path in DATA_PATHS_INFRAESTRUCTURAS.items()}


# --- Streamlit UI ---
st.title("PLATAFORMA DE LA BRÚJULA")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["VIVIENDA Y SUELO", "INFRAESTRUCTURAS", "EQUIPAMIENTOS", "ACCESIBILIDAD", "DESARROLLO LOCAL"])

st.divider()

with tab1:
    st.header("Departamento de Santa María")

    escalas_viv_suelo = [
        "Departamento de Santa María",
        "Municipio de Santa María",
        "Municipio de San José",
        "Localidades del Departamento de Santa María",
        "Manzanas del Departamento de Santa María"
    ]
    option_escala_viv_suelo = st.selectbox("Seleccionar una escala", escalas_viv_suelo, key="viv_suelo_escala_select")

    # --- Lógica para cada opción de escala (Vivienda y Suelo) ---
    if option_escala_viv_suelo == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        with st.container():
            display_data_and_charts(gdf_data_vivienda_suelo["departamento"])

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_vivienda_suelo["departamento"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="dep_var_select_viv_suelo")
        
        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_viv_suelo"
        )
        create_folium_map(
            gdf_data_vivienda_suelo["departamento"],
            selected_variable,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", "Derechos:"],
            selected_tile_viv_suelo
        )

    elif option_escala_viv_suelo == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        with st.container():
            display_data_and_charts(gdf_data_vivienda_suelo["municipios"], "MUNICIPIO", "Santa María")

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_vivienda_suelo["municipios"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="sm_mun_var_select_viv_suelo")
        
        filtered_gdf_municipio_sm = gdf_data_vivienda_suelo["municipios"][gdf_data_vivienda_suelo["municipios"]['MUNICIPIO'] == 'Santa María']
        
        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_sm_mun_viv_suelo"
        )
        create_folium_map(
            filtered_gdf_municipio_sm, # CORRECTO
            selected_variable,
            10, # Zoom ajustado
            ["DEPARTAMENTO", "MUNICIPIO", "DERECHOS"], # Tooltip ajustado
            ["Departamento:", "Municipio:", "Derechos:"], # Tooltip ajustado
            selected_tile_viv_suelo
        )

    elif option_escala_viv_suelo == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        with st.container():
            display_data_and_charts(gdf_data_vivienda_suelo["municipios"], "MUNICIPIO", "San José")

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_vivienda_suelo["municipios"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="sj_mun_var_select_viv_suelo")
        
        filtered_gdf_municipio_sj = gdf_data_vivienda_suelo["municipios"][gdf_data_vivienda_suelo["municipios"]['MUNICIPIO'] == 'San José']

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_sj_mun_viv_suelo"
        )
        create_folium_map(
            filtered_gdf_municipio_sj, # CORRECTO
            selected_variable,
            10, # Zoom ajustado
            ["DEPARTAMENTO", "MUNICIPIO", "DERECHOS"], # Tooltip ajustado
            ["Departamento:", "Municipio:", "Derechos:"], # Tooltip ajustado
            selected_tile_viv_suelo
        )

    elif option_escala_viv_suelo == "Localidades del Departamento de Santa María":
        st.subheader("Localidades del Departamento de Santa María")
        variables_localidades_sm = gdf_data_vivienda_suelo["localidades"]["LOCALIDAD"].unique()
        localidades_sm = st.selectbox("Seleccionar una localidad del Departamento de Santa María", options=variables_localidades_sm, key="loc_select_viv_suelo")

        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos de la localidad de {localidades_sm}")
        with st.container():
            display_data_and_charts(gdf_data_vivienda_suelo["localidades"], "LOCALIDAD", localidades_sm)

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_vivienda_suelo["localidades"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="loc_var_select_viv_suelo")
        
        filtered_gdf_localidades_selected = gdf_data_vivienda_suelo["localidades"][gdf_data_vivienda_suelo["localidades"]['LOCALIDAD'] == localidades_sm]

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_loc_viv_suelo"
        )
        create_folium_map(
            filtered_gdf_localidades_selected, # CORRECTO
            selected_variable,
            14, # Zoom ajustado
            ["DEPARTAMENTO", "MUNICIPIO", "LOCALIDAD", "DERECHOS"], # Tooltip ajustado
            ["Departamento:", "Municipio:", "Localidad:", "Derechos:"], # Tooltip ajustado
            selected_tile_viv_suelo
        )

    elif option_escala_viv_suelo == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")
        variables_manzanero = gdf_data_vivienda_suelo["manzanero"]["MUNICIPIO"].unique()
        manzanero_municipio = st.selectbox("Seleccionar un Municipio del Departamento de Santa María", options=variables_manzanero, key="man_mun_select_viv_suelo")

        st.subheader(f"Territorialización de los indicadores de la Brújula por manzana del Municipio de {manzanero_municipio}")
        variables = gdf_data_vivienda_suelo["manzanero"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="man_var_select_viv_suelo")
        
        filtered_gdf_manzanero_municipio = gdf_data_vivienda_suelo["manzanero"][gdf_data_vivienda_suelo["manzanero"]['MUNICIPIO'] == manzanero_municipio]

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_man_viv_suelo"
        )
        create_folium_map(
            filtered_gdf_manzanero_municipio, # CORRECTO
            selected_variable,
            12, # Zoom ajustado
            ["MUNICIPIO", "LOCALIDAD", "DERECHOS"], # Tooltip ajustado
            ["Municipio:", "Localidad:", "Derechos:"], # Tooltip ajustado
            selected_tile_viv_suelo
        )

with tab2:
    st.header("Departamento de Santa María")

    escalas_infraestructuras = [
        "Departamento de Santa María",
        "Municipio de Santa María",
        "Municipio de San José",
        "Localidades del Departamento de Santa María",
        "Manzanas del Departamento de Santa María"
    ]
    option_escala_infraestructuras = st.selectbox("Seleccionar una escala", escalas_infraestructuras, key="infra_escala_select")

    # --- Lógica para cada opción de escala (Infraestructuras) ---
    if option_escala_infraestructuras == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_infraestructuras}")
        with st.container():
            display_data_and_charts(gdf_data_infraestructuras["departamento"])

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_infraestructuras["departamento"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="dep_var_select_infra")
        
        selected_tile_infra = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_infra"
        )
        create_folium_map(
            gdf_data_infraestructuras["departamento"], # CORRECTO para la pestaña de Infraestructuras
            selected_variable,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", "Derechos:"],
            selected_tile_infra
        )

    elif option_escala_infraestructuras == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_infraestructuras}")
        with st.container():
            display_data_and_charts(gdf_data_infraestructuras["municipios"], "MUNICIPIO", "Santa María")

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_infraestructuras["municipios"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="sm_mun_var_select_infra")
        
        filtered_gdf_municipio_sm = gdf_data_infraestructuras["municipios"][gdf_data_infraestructuras["municipios"]['MUNICIPIO'] == 'Santa María']
        
        selected_tile_infra = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_sm_mun_infra"
        )
        create_folium_map(
            filtered_gdf_municipio_sm, # CORREGIDO: Ahora usa el GDF filtrado de infraestructuras
            selected_variable,
            10, # Zoom ajustado
            ["DEPARTAMENTO", "MUNICIPIO", "DERECHOS"], # Tooltip ajustado
            ["Departamento:", "Municipio:", "Derechos:"], # Tooltip ajustado
            selected_tile_infra
        )

    elif option_escala_infraestructuras == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_infraestructuras}")
        with st.container():
            display_data_and_charts(gdf_data_infraestructuras["municipios"], "MUNICIPIO", "San José")

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_infraestructuras["municipios"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="sj_mun_var_select_infra")
        
        filtered_gdf_municipio_sj = gdf_data_infraestructuras["municipios"][gdf_data_infraestructuras["municipios"]['MUNICIPIO'] == 'San José']

        selected_tile_infra = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_sj_mun_infra"
        )
        create_folium_map(
            filtered_gdf_municipio_sj, # CORREGIDO: Ahora usa el GDF filtrado de infraestructuras
            selected_variable,
            10, # Zoom ajustado
            ["DEPARTAMENTO", "MUNICIPIO", "DERECHOS"], # Tooltip ajustado
            ["Departamento:", "Municipio:", "Derechos:"], # Tooltip ajustado
            selected_tile_infra
        )

    elif option_escala_infraestructuras == "Localidades del Departamento de Santa María":
        st.subheader("Localidades del Departamento de Santa María")
        variables_localidades_sm = gdf_data_infraestructuras["localidades"]["LOCALIDAD"].unique()
        localidades_sm = st.selectbox("Seleccionar una localidad del Departamento de Santa María", options=variables_localidades_sm, key="loc_select_infra")

        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos de la localidad de {localidades_sm}")
        with st.container():
            display_data_and_charts(gdf_data_infraestructuras["localidades"], "LOCALIDAD", localidades_sm)

        st.subheader("Territorialización de los indicadores de la Brújula")
        variables = gdf_data_infraestructuras["localidades"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="loc_var_select_infra")
        
        filtered_gdf_localidades_selected = gdf_data_infraestructuras["localidades"][gdf_data_infraestructuras["localidades"]['LOCALIDAD'] == localidades_sm]

        selected_tile_infra = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_loc_infra"
        )
        create_folium_map(
            filtered_gdf_localidades_selected, # CORREGIDO: Ahora usa el GDF filtrado de infraestructuras
            selected_variable,
            14, # Zoom ajustado
            ["DEPARTAMENTO", "MUNICIPIO", "LOCALIDAD", "DERECHOS"], # Tooltip ajustado
            ["Departamento:", "Municipio:", "Localidad:", "Derechos:"], # Tooltip ajustado
            selected_tile_infra
        )

    elif option_escala_infraestructuras == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")
        variables_manzanero = gdf_data_infraestructuras["manzanero"]["MUNICIPIO"].unique()
        manzanero_municipio = st.selectbox("Seleccionar un Municipio del Departamento de Santa María", options=variables_manzanero, key="man_mun_select_infra")

        st.subheader(f"Territorialización de los indicadores de la Brújula por manzana del Municipio de {manzanero_municipio}")
        variables = gdf_data_infraestructuras["manzanero"]["VARIABLE"].unique()
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables, key="man_var_select_infra")
        
        filtered_gdf_manzanero_municipio = gdf_data_infraestructuras["manzanero"][gdf_data_infraestructuras["manzanero"]['MUNICIPIO'] == manzanero_municipio]

        selected_tile_infra = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_man_infra"
        )
        create_folium_map(
            filtered_gdf_manzanero_municipio, # CORREGIDO: Ahora usa el GDF filtrado de infraestructuras
            selected_variable,
            12, # Zoom ajustado
            ["MUNICIPIO", "LOCALIDAD", "DERECHOS"], # Tooltip ajustado
            ["Municipio:", "Localidad:", "Derechos:"], # Tooltip ajustado
            selected_tile_infra
        )

with tab3:
    st.header("Equipamientos")
    st.info("Contenido para Equipamientos...")

with tab4:
    st.header("Accesibilidad")
    st.info("Contenido para Accesibilidad...")

with tab5:
    st.header("Desarrollo Local")
    st.info("Contenido para Desarrollo Local...")