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

def create_folium_map(gdf, selected_variable, zoom_start, tooltip_fields, tooltip_aliases):
    """Crea y muestra un mapa de Folium.
    """
    filtered_gdf = gdf[gdf["VARIABLE"] == selected_variable]

    if not filtered_gdf.empty:
        centro = filtered_gdf.geometry.union_all().centroid
    else:
        if not gdf.empty:
            try:
                centro = gdf.geometry.union_all().centroid
            except Exception:
                centro = (-26.779, -66.027)
        else:
            centro = (-26.779, -66.027)


    selected_tile_name = st.session_state.get('current_tile_selection', 'Fondo Mapa')

    m = folium.Map(location=[centro.y, centro.x], zoom_start=zoom_start, tiles=None)

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

    html(m._repr_html_(), height=600)

def display_data_and_charts(gdf_data, filter_col=None, filter_value=None, category_cols=None, value_col="DERECHOS"):
    """Muestra la tabla de datos y el gráfico de radar.
    
    category_cols: Lista de nombres de columnas a usar como categorías para el gráfico de radar.
                   Si es None, se usará 'VARIABLE'.
    value_col: Nombre de la columna que contiene los valores para el gráfico de radar.
    """
    
    # Define mapping for display names (used for both radar chart categories and table labels)
    variable_display_names = {
        "a1-d": "Seguridad en la tenencia del suelo",
        "a2-d": "Sin hacinamiento en la vivienda",
        "a3-d": "Vivienda construida con materiales permanentes",
        "a4-d": "Vivienda con baño propio",
        "a5-d": "Generación de oferta de vivienda y alquiler a precios accesibles",
        "b1-d":"Provisión de agua potable disponible",
        "b2-d":"Servicio sanitarios o pozos disponibles sin contaminación",
        "b3-d":"Disponibilidad de drenajes que eviten inundación",
        "b4-d":"Conexión de energía (electricidad y gas)",
        "b5-d":"Conexión servicios de telecomunicaciones, Internet, etc.",
        "c1-d":"Espacios verdes públicos disponibles y mantenidos",
        "c2-d":"Escuelas pre-escolares, primarias y secundarias",
        "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
        "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
        "c5-d":"Servicios de alumbrado, barrido y limpieza disponibles",
        "d1-d":"Calzadas disponibles permitiendo movimiento vehicular",
        "d2-d":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
        "d3-d":"Servicio transporte público guiado disponible a precios accesibles",
        "d4-d":"Servicios de colectivos, taxis y motos disponibles",
        "d5-d":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
        "e1-d":"Seguridad alimentaria disponible",
        "e2-d":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
        "e3-d":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio",
        "e4-d":"Tolerancia y aceptación entre grupos sociales diferentes",
        "e5-d":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",
    }

    if category_cols:
        # Melt the DataFrame for the radar chart and table display
        df_melted = gdf_data.drop("geometry", axis=1, errors='ignore').melt(
            id_vars=[col for col in gdf_data.columns if col not in category_cols and col != "geometry"],
            value_vars=category_cols,
            var_name='VARIABLE',
            value_name=value_col
        )
        
        # Apply friendly names to the 'VARIABLE' column for both chart and table
        df_chart_data = df_melted.copy()
        df_chart_data['VARIABLE'] = df_chart_data['VARIABLE'].map(variable_display_names)
        
        df_display_for_table = df_chart_data.copy() # Use the same named data for table

    else: # For other scales where 'VARIABLE' and 'DERECHOS' are already present
        df_display_for_table = gdf_data.drop("geometry", axis=1, errors='ignore').copy()
        if not all(col in df_display_for_table.columns for col in ["VARIABLE", value_col]):
            st.warning(f"Las columnas 'VARIABLE' o '{value_col}' no se encontraron en los datos.")
            df_chart_data = pd.DataFrame(columns=["VARIABLE", value_col])
        else:
            df_chart_data = df_display_for_table[["VARIABLE", value_col]].copy()


    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Matriz de la Brújula")
        if not df_display_for_table.empty:
            # Determine which columns to display in the table
            # If 'DEPARTAMENTO' is present in the melted data's id_vars, include it.
            # For the department level, 'DEPARTAMENTO' would be an id_var.
            columns_to_display = []
            if 'DEPARTAMENTO' in df_display_for_table.columns:
                columns_to_display.append('DEPARTAMENTO')
            columns_to_display.extend(["VARIABLE", value_col])

            st.markdown(
                df_display_for_table[columns_to_display].style.hide(axis='index').to_html(),
                unsafe_allow_html=True
            )
        else:
            st.info("No hay datos para mostrar en la matriz para esta selección.")
    with col2:
        st.markdown("Gráfico de la Brújula")
        if not df_chart_data.empty and "VARIABLE" in df_chart_data.columns and value_col in df_chart_data.columns:
            plot_radar_chart(df_chart_data, "VARIABLE", value_col)
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
gdf_data_departamento_consolidado_full = gpd.read_file("data/santa-maria-departamento.geojson")
gdf_data_municipios_consolidado_full = gpd.read_file("data/santa-maria-municipios.geojson")
gdf_data_localidades_consolidado_full = gpd.read_file("data/santa-maria-localidades.geojson")
gdf_data_manzanero_consolidado_full = gpd.read_file("data/santa-maria-manzanero.geojson")

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
        "Localidades y áreas rurales del Departamento de Santa María",
        "Manzanas del Departamento de Santa María"
    ]
    option_escala_viv_suelo = st.selectbox("Seleccionar una escala", escalas_viv_suelo, key="viv_suelo_escala_select")

    # --- Lógica para cada opción de escala (Vivienda y Suelo) ---
    if option_escala_viv_suelo == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        
        department_vars_viv_suelo = ["a1-d", "a2-d", "a3-d", "a4-d", "a5-d"]
        
        gdf_department_filtered_for_tab1 = gdf_data_departamento_consolidado_full[
            gdf_data_departamento_consolidado_full["DEPARTAMENTO"] == "Santa María"
        ][["DEPARTAMENTO", "geometry"] + department_vars_viv_suelo].copy()

        with st.container():
            display_data_and_charts(
                gdf_department_filtered_for_tab1,
                category_cols=department_vars_viv_suelo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "a1-d": "Seguridad en la tenencia del suelo",
            "a2-d": "Sin hacinamiento en la vivienda",
            "a3-d": "Vivienda construida con materiales permanentes",
            "a4-d": "Vivienda con baño propio",
            "a5-d": "Generación de oferta de vivienda y alquiler a precios accesibles"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_viv_suelo"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_department_filtered_for_tab1.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_viv_suelo"
        )
        st.session_state['current_tile_selection'] = selected_tile_viv_suelo 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", f"{selected_display_name}:"]
        )

    elif option_escala_viv_suelo == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        
        municipio_sm_vars_viv_suelo = ["a1-d", "a2-d", "a3-d", "a4-d", "a5-d"]
        
        gdf_municipio_sm_filtered_for_tab1 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "Santa María"
        ][["MUNICIPIO", "geometry"] + municipio_sm_vars_viv_suelo].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sm_filtered_for_tab1,
                category_cols=municipio_sm_vars_viv_suelo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "a1-d": "Seguridad en la tenencia del suelo",
            "a2-d": "Sin hacinamiento en la vivienda",
            "a3-d": "Vivienda construida con materiales permanentes",
            "a4-d": "Vivienda con baño propio",
            "a5-d": "Generación de oferta de vivienda y alquiler a precios accesibles"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_viv_suelo"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sm_filtered_for_tab1.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_viv_suelo"
        )
        st.session_state['current_tile_selection'] = selected_tile_viv_suelo 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )
    
    elif option_escala_viv_suelo == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        
        municipio_sj_vars_viv_suelo = ["a1-d", "a2-d", "a3-d", "a4-d", "a5-d"]
        
        gdf_municipio_sj_filtered_for_tab1 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "San José"
        ][["MUNICIPIO", "geometry"] + municipio_sj_vars_viv_suelo].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sj_filtered_for_tab1,
                category_cols=municipio_sj_vars_viv_suelo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "a1-d": "Seguridad en la tenencia del suelo",
            "a2-d": "Sin hacinamiento en la vivienda",
            "a3-d": "Vivienda construida con materiales permanentes",
            "a4-d": "Vivienda con baño propio",
            "a5-d": "Generación de oferta de vivienda y alquiler a precios accesibles"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_viv_suelo"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sj_filtered_for_tab1.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_viv_suelo"
        )
        st.session_state['current_tile_selection'] = selected_tile_viv_suelo 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )

    elif option_escala_viv_suelo == "Localidades y áreas rurales del Departamento de Santa María":
        st.subheader("Localidades y áreas rurales del Departamento de Santa María")
        localidades_disponibles = gdf_data_localidades_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_localidad = st.selectbox(
            "Selecciona una Localidad", 
            options=localidades_disponibles, 
            key="localidad_select_viv_suelo"
        )

        localidad_vars_viv_suelo = ["a1-d", "a2-d", "a3-d", "a4-d", "a5-d"]

        gdf_localidad_filtered_for_tab1 = gdf_data_localidades_consolidado_full[
            gdf_data_localidades_consolidado_full["LOCALIDAD"] == selected_localidad
        ][["LOCALIDAD", "geometry"] + localidad_vars_viv_suelo].copy()

        with st.container():
            display_data_and_charts(
                gdf_localidad_filtered_for_tab1,
                category_cols=localidad_vars_viv_suelo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "a1-d": "Seguridad en la tenencia del suelo",
            "a2-d": "Sin hacinamiento en la vivienda",
            "a3-d": "Vivienda construida con materiales permanentes",
            "a4-d": "Vivienda con baño propio",
            "a5-d": "Generación de oferta de vivienda y alquiler a precios accesibles"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_viv_suelo_localidad" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_localidad_filtered_for_tab1.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_viv_suelo_localidad" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_viv_suelo

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            12, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )

    elif option_escala_viv_suelo == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")
        manzanero_disponibles = gdf_data_manzanero_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_manzanero = st.selectbox(
            "Selecciona una Localidad", 
            options=manzanero_disponibles, 
            key="manzanero_select_viv_suelo"
        )

        manzanero_vars_viv_suelo = ["a1-d", "a2-d", "a3-d", "a4-d", "a5-d"]

        gdf_manzanero_filtered_for_tab1 = gdf_data_manzanero_consolidado_full[
            gdf_data_manzanero_consolidado_full["LOCALIDAD"] == selected_manzanero
        ][["LOCALIDAD", "geometry"] + manzanero_vars_viv_suelo].copy()

        #with st.container():
        #    display_data_and_charts(
        #        gdf_manzanero_filtered_for_tab1,
        #        category_cols=manzanero_vars_viv_suelo,
        #        value_col="DERECHOS"
        #    )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "a1-d": "Seguridad en la tenencia del suelo",
            "a2-d": "Sin hacinamiento en la vivienda",
            "a3-d": "Vivienda construida con materiales permanentes",
            "a4-d": "Vivienda con baño propio",
            "a5-d": "Generación de oferta de vivienda y alquiler a precios accesibles"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_viv_suelo_manzanero" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_manzanero_filtered_for_tab1.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_viv_suelo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_viv_suelo_manzanero" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_viv_suelo

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )


with tab2:
    st.header("Departamento de Santa María")

    escalas_infraestructuras = [
        "Departamento de Santa María",
        "Municipio de Santa María",
        "Municipio de San José",
        "Localidades y áreas rurales del Departamento de Santa María",
        "Manzanas del Departamento de Santa María"
    ]
    option_escala_infraestructuras = st.selectbox("Seleccionar una escala", escalas_infraestructuras, key="infraestructuras_escala_select")

    # --- Lógica para cada opción de escala (Vivienda y Suelo) ---
    if option_escala_infraestructuras == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_infraestructuras}")
        
        department_vars_infraestructuras = ["b1-d", "b2-d", "b4-d", "b5-d"]
        
        gdf_department_filtered_for_tab2 = gdf_data_departamento_consolidado_full[
            gdf_data_departamento_consolidado_full["DEPARTAMENTO"] == "Santa María"
        ][["DEPARTAMENTO", "geometry"] + department_vars_infraestructuras].copy()

        with st.container():
            display_data_and_charts(
                gdf_department_filtered_for_tab2,
                category_cols=department_vars_infraestructuras,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "b1-d":"Provisión de agua potable disponible",
            "b2-d":"Servicio sanitarios o pozos disponibles sin contaminación",
            #"b3-d":"Disponibilidad de drenajes que eviten inundación",
            "b4-d":"Conexión de energía (electricidad y gas)",
            "b5-d":"Conexión servicios de telecomunicaciones, Internet, etc."
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_infraestructuras"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_department_filtered_for_tab2.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_infraestructuras = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_infraestructuras"
        )
        st.session_state['current_tile_selection'] = selected_tile_infraestructuras 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", f"{selected_display_name}:"]
        )

    elif option_escala_infraestructuras == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_infraestructuras}")
        
        municipio_sm_vars_infraestructuras = ["b1-d", "b2-d", "b4-d", "b5-d"]
        
        gdf_municipio_sm_filtered_for_tab2 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "Santa María"
        ][["MUNICIPIO", "geometry"] + municipio_sm_vars_infraestructuras].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sm_filtered_for_tab2,
                category_cols=municipio_sm_vars_infraestructuras,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "b1-d":"Provisión de agua potable disponible",
            "b2-d":"Servicio sanitarios o pozos disponibles sin contaminación",
            #"b3-d":"Disponibilidad de drenajes que eviten inundación",
            "b4-d":"Conexión de energía (electricidad y gas)",
            "b5-d":"Conexión servicios de telecomunicaciones, Internet, etc."
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_infraestructuras"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sm_filtered_for_tab2.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_infraestructuras = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_infraestructuras"
        )
        st.session_state['current_tile_selection'] = selected_tile_infraestructuras 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )
    
    elif option_escala_infraestructuras == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_infraestructuras}")
        
        municipio_sj_vars_infraestructuras = ["b1-d", "b2-d", "b4-d", "b5-d"]
        
        gdf_municipio_sj_filtered_for_tab2 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "San José"
        ][["MUNICIPIO", "geometry"] + municipio_sj_vars_infraestructuras].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sj_filtered_for_tab2,
                category_cols=municipio_sj_vars_infraestructuras,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "b1-d":"Provisión de agua potable disponible",
            "b2-d":"Servicio sanitarios o pozos disponibles sin contaminación",
            #"b3-d":"Disponibilidad de drenajes que eviten inundación",
            "b4-d":"Conexión de energía (electricidad y gas)",
            "b5-d":"Conexión servicios de telecomunicaciones, Internet, etc."
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_infraestructuras"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sj_filtered_for_tab2.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_infraestructuras = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_infraestructuras"
        )
        st.session_state['current_tile_selection'] = selected_tile_infraestructuras 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )
    
    elif option_escala_infraestructuras == "Localidades y áreas rurales del Departamento de Santa María":
        st.subheader("Localidades y áreas rurales del Departamento de Santa María")
        localidades_disponibles = gdf_data_localidades_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_localidad = st.selectbox(
            "Selecciona una Localidad", 
            options=localidades_disponibles, 
            key="localidad_select_infraestructuras"
        )

        localidad_vars_infraestructuras = ["b1-d", "b2-d", "b4-d", "b5-d"]

        gdf_localidad_filtered_for_tab2 = gdf_data_localidades_consolidado_full[
            gdf_data_localidades_consolidado_full["LOCALIDAD"] == selected_localidad
        ][["LOCALIDAD", "geometry"] + localidad_vars_infraestructuras].copy()

        with st.container():
            display_data_and_charts(
                gdf_localidad_filtered_for_tab2,
                category_cols=localidad_vars_infraestructuras,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "b1-d":"Provisión de agua potable disponible",
            "b2-d":"Servicio sanitarios o pozos disponibles sin contaminación",
            #"b3-d":"Disponibilidad de drenajes que eviten inundación",
            "b4-d":"Conexión de energía (electricidad y gas)",
            "b5-d":"Conexión servicios de telecomunicaciones, Internet, etc."
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_infraestructuras_localidad" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_localidad_filtered_for_tab2.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_infraestructuras = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_infraestructuras_localidad" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_infraestructuras

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            12, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )

    elif option_escala_infraestructuras == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")
        manzanero_disponibles = gdf_data_manzanero_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_manzanero = st.selectbox(
            "Selecciona una Localidad", 
            options=manzanero_disponibles, 
            key="manzanero_select_infraestructuras"
        )

        manzanero_vars_infraestructuras = ["b1-d", "b2-d", "b4-d", "b5-d"]

        gdf_manzanero_filtered_for_tab2 = gdf_data_manzanero_consolidado_full[
            gdf_data_manzanero_consolidado_full["LOCALIDAD"] == selected_manzanero
        ][["LOCALIDAD", "geometry"] + manzanero_vars_infraestructuras].copy()

        #with st.container():
        #    display_data_and_charts(
        #        gdf_manzanero_filtered_for_tab2,
        #        category_cols=manzanero_vars_infraestructuras,
        #        value_col="DERECHOS"
        #    )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "b1-d":"Provisión de agua potable disponible",
            "b2-d":"Servicio sanitarios o pozos disponibles sin contaminación",
            #"b3-d":"Disponibilidad de drenajes que eviten inundación",
            "b4-d":"Conexión de energía (electricidad y gas)",
            "b5-d":"Conexión servicios de telecomunicaciones, Internet, etc."
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_infraestructuras_manzanero" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_manzanero_filtered_for_tab2.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_infraestructuras = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_infraestructuras_manzanero" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_infraestructuras

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )

with tab3:
    st.header("Departamento de Santa María")

    escalas_equipamientos = [
        "Departamento de Santa María",
        "Municipio de Santa María",
        "Municipio de San José",
        "Localidades y áreas rurales del Departamento de Santa María",
        "Manzanas del Departamento de Santa María"
    ]
    option_escala_equipamientos = st.selectbox("Seleccionar una escala", escalas_equipamientos, key="equipamientos_escala_select")

    # --- Lógica para cada opción de escala (Vivienda y Suelo) ---
    if option_escala_equipamientos == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_equipamientos}")
        
        department_vars_equipamientos = ["c1-d", "c2-d", "c3-d", "c4-d"]
        
        gdf_department_filtered_for_tab3 = gdf_data_departamento_consolidado_full[
            gdf_data_departamento_consolidado_full["DEPARTAMENTO"] == "Santa María"
        ][["DEPARTAMENTO", "geometry"] + department_vars_equipamientos].copy()

        with st.container():
            display_data_and_charts(
                gdf_department_filtered_for_tab3,
                category_cols=department_vars_equipamientos,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "c1-d":"Espacios verdes públicos disponibles y mantenidos",
            "c2-d":"Escuelas pre-escolares, primarias y secundarias",
            "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
            "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
            #"c5-d":"Servicios de alumbrado, barrido y limpieza disponibles"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_equipamientos"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_department_filtered_for_tab3.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_equipamientos = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_equipamientos"
        )
        st.session_state['current_tile_selection'] = selected_tile_equipamientos 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", f"{selected_display_name}:"]
        )

    elif option_escala_equipamientos == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_equipamientos}")
        
        municipio_sm_vars_equipamientos = ["c1-d", "c2-d", "c3-d", "c4-d"]
        
        gdf_municipio_sm_filtered_for_tab3 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "Santa María"
        ][["MUNICIPIO", "geometry"] + municipio_sm_vars_equipamientos].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sm_filtered_for_tab3,
                category_cols=municipio_sm_vars_equipamientos,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "c1-d":"Espacios verdes públicos disponibles y mantenidos",
            "c2-d":"Escuelas pre-escolares, primarias y secundarias",
            "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
            "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
            #"c5-d":"Servicios de alumbrado, barrido y limpieza disponibles"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_equipamientos"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sm_filtered_for_tab3.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_equipamientos = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_equipamientos"
        )
        st.session_state['current_tile_selection'] = selected_tile_equipamientos

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )
    
    elif option_escala_equipamientos == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_equipamientos}")
        
        municipio_sj_vars_equipamientos = ["c1-d", "c2-d", "c3-d", "c4-d"]
    
        gdf_municipio_sj_filtered_for_tab3 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "San José"
        ][["MUNICIPIO", "geometry"] + municipio_sj_vars_equipamientos].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sj_filtered_for_tab3,
                category_cols=municipio_sj_vars_equipamientos,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "c1-d":"Espacios verdes públicos disponibles y mantenidos",
            "c2-d":"Escuelas pre-escolares, primarias y secundarias",
            "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
            "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
            #"c5-d":"Servicios de alumbrado, barrido y limpieza disponibles"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_equipamientos"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sj_filtered_for_tab3.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_equipamientos = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_equipamientos"
        )
        st.session_state['current_tile_selection'] = selected_tile_equipamientos 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )

    elif option_escala_equipamientos == "Localidades y áreas rurales del Departamento de Santa María":
        st.subheader("Localidades y áreas rurales del Departamento de Santa María")
        localidades_disponibles = gdf_data_localidades_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_localidad = st.selectbox(
            "Selecciona una Localidad", 
            options=localidades_disponibles, 
            key="localidad_select_equipamientos"
        )

        localidad_vars_equipamientos = ["c1-d", "c2-d", "c3-d", "c4-d"]

        gdf_localidad_filtered_for_tab3 = gdf_data_localidades_consolidado_full[
            gdf_data_localidades_consolidado_full["LOCALIDAD"] == selected_localidad
        ][["LOCALIDAD", "geometry"] + localidad_vars_equipamientos].copy()

        with st.container():
            display_data_and_charts(
                gdf_localidad_filtered_for_tab3,
                category_cols=localidad_vars_equipamientos,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "c1-d":"Espacios verdes públicos disponibles y mantenidos",
            "c2-d":"Escuelas pre-escolares, primarias y secundarias",
            "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
            "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
            #"c5-d":"Servicios de alumbrado, barrido y limpieza disponibles"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_equipamientos_localidad" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_localidad_filtered_for_tab3.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_equipamientos = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_equipamientos_localidad" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_equipamientos

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            12, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )

    elif option_escala_equipamientos == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")
        manzanero_disponibles = gdf_data_manzanero_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_manzanero = st.selectbox(
            "Selecciona una Localidad", 
            options=manzanero_disponibles, 
            key="manzanero_select_equipamientos"
        )

        manzanero_vars_equipamientos = ["c1-d", "c2-d", "c3-d", "c4-d"]

        gdf_manzanero_filtered_for_tab3 = gdf_data_manzanero_consolidado_full[
            gdf_data_manzanero_consolidado_full["LOCALIDAD"] == selected_manzanero
        ][["LOCALIDAD", "geometry"] + manzanero_vars_equipamientos].copy()

        #with st.container():
        #    display_data_and_charts(
        #        gdf_manzanero_filtered_for_tab3,
        #        category_cols=manzanero_vars_equipamientos,
        #        value_col="DERECHOS"
        #    )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "c1-d":"Espacios verdes públicos disponibles y mantenidos",
            "c2-d":"Escuelas pre-escolares, primarias y secundarias",
            "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
            "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
            #"c5-d":"Servicios de alumbrado, barrido y limpieza disponibles"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_equipamientos_manzanero" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_manzanero_filtered_for_tab3.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_equipamientos = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_equipamientos_manzanero" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_equipamientos

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )


with tab4:
    st.header("Departamento de Santa María")

    escalas_accesibilidad = [
        "Departamento de Santa María",
        "Municipio de Santa María",
        "Municipio de San José",
        "Localidades y áreas rurales del Departamento de Santa María",
        #"Manzanas del Departamento de Santa María"
    ]
    option_escala_accesibilidad = st.selectbox("Seleccionar una escala", escalas_accesibilidad, key="accesibilidad_escala_select")

    # --- Lógica para cada opción de escala (Vivienda y Suelo) ---
    if option_escala_accesibilidad == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_accesibilidad}")
        
        department_vars_accesibilidad = ["d1-d", "d5-d"]
        
        gdf_department_filtered_for_tab4 = gdf_data_departamento_consolidado_full[
            gdf_data_departamento_consolidado_full["DEPARTAMENTO"] == "Santa María"
        ][["DEPARTAMENTO", "geometry"] + department_vars_accesibilidad].copy()

        with st.container():
            display_data_and_charts(
                gdf_department_filtered_for_tab4,
                category_cols=department_vars_accesibilidad,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "d1-d":"Calzadas disponibles permitiendo movimiento vehicular",
            #"d2-d":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
            #"d3-d":"Servicio transporte público guiado disponible a precios accesibles",
            #"d4-d":"Servicios de colectivos, taxis y motos disponibles",
            "d5-d":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_accesibilidad"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_department_filtered_for_tab4.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_accesibilidad = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_accesibilidad"
        )
        st.session_state['current_tile_selection'] = selected_tile_accesibilidad 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", f"{selected_display_name}:"]
        )
    
    elif option_escala_accesibilidad == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_accesibilidad}")
        
        municipio_sm_vars_accesibilidad = ["d1-d", "d5-d"]
        
        gdf_municipio_sm_filtered_for_tab4 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "Santa María"
        ][["MUNICIPIO", "geometry"] + municipio_sm_vars_accesibilidad].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sm_filtered_for_tab4,
                category_cols=municipio_sm_vars_accesibilidad,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "d1-d":"Calzadas disponibles permitiendo movimiento vehicular",
            #"d2-d":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
            #"d3-d":"Servicio transporte público guiado disponible a precios accesibles",
            #"d4-d":"Servicios de colectivos, taxis y motos disponibles",
            "d5-d":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_accesibilidad"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sm_filtered_for_tab4.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_accesibilidad = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_accesibilidad"
        )
        st.session_state['current_tile_selection'] = selected_tile_accesibilidad

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )
    
    elif option_escala_accesibilidad == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_accesibilidad}")
        
        municipio_sj_vars_accesibilidad = ["d1-d", "d5-d"]
    
        gdf_municipio_sj_filtered_for_tab4 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "San José"
        ][["MUNICIPIO", "geometry"] + municipio_sj_vars_accesibilidad].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sj_filtered_for_tab4,
                category_cols=municipio_sj_vars_accesibilidad,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "d1-d":"Calzadas disponibles permitiendo movimiento vehicular",
            #"d2-d":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
            #"d3-d":"Servicio transporte público guiado disponible a precios accesibles",
            #"d4-d":"Servicios de colectivos, taxis y motos disponibles",
            "d5-d":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_accesibilidad"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sj_filtered_for_tab4.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_accesibilidad = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_accesibilidad"
        )
        st.session_state['current_tile_selection'] = selected_tile_accesibilidad 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )

    elif option_escala_accesibilidad == "Localidades y áreas rurales del Departamento de Santa María":
        st.subheader("Localidades y áreas rurales del Departamento de Santa María")
        localidades_disponibles = gdf_data_localidades_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_localidad = st.selectbox(
            "Selecciona una Localidad", 
            options=localidades_disponibles, 
            key="localidad_select_accesibilidad"
        )

        localidad_vars_accesibilidad = ["c1-d", "c2-d", "c3-d", "c4-d"]

        gdf_localidad_filtered_for_tab4 = gdf_data_localidades_consolidado_full[
            gdf_data_localidades_consolidado_full["LOCALIDAD"] == selected_localidad
        ][["LOCALIDAD", "geometry"] + localidad_vars_accesibilidad].copy()

        with st.container():
            display_data_and_charts(
                gdf_localidad_filtered_for_tab4,
                category_cols=localidad_vars_accesibilidad,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "c1-d":"Espacios verdes públicos disponibles y mantenidos",
            "c2-d":"Escuelas pre-escolares, primarias y secundarias",
            "c3-d":"Hospitales y centros de salud de atención primaria disponibles",
            "c4-d":"Servicios seguridad policial, bomberos, templos y DC disponibles",
            #"c5-d":"Servicios de alumbrado, barrido y limpieza disponibles"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_accesibilidad_localidad" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_localidad_filtered_for_tab4.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_accesibilidad = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_accesibilidad_localidad" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_accesibilidad

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            12, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )

with tab5:
    st.header("Departamento de Santa María")

    escalas_desarrollo = [
        "Departamento de Santa María",
        "Municipio de Santa María",
        "Municipio de San José",
        "Localidades y áreas rurales del Departamento de Santa María",
        "Manzanas del Departamento de Santa María"
    ]
    option_escala_desarrollo = st.selectbox("Seleccionar una escala", escalas_desarrollo, key="desarrollo_escala_select")

    # --- Lógica para cada opción de escala (Vivienda y Suelo) ---
    if option_escala_desarrollo == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_desarrollo}")
        
        department_vars_desarrollo = ["e1-d", "e2-d", "e3-d", "e4-d"]
        
        gdf_department_filtered_for_tab5 = gdf_data_departamento_consolidado_full[
            gdf_data_departamento_consolidado_full["DEPARTAMENTO"] == "Santa María"
        ][["DEPARTAMENTO", "geometry"] + department_vars_desarrollo].copy()

        with st.container():
            display_data_and_charts(
                gdf_department_filtered_for_tab5,
                category_cols=department_vars_desarrollo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "e1-d":"Seguridad alimentaria disponible",
            "e2-d":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
            "e3-d":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio",
            "e4-d":"Tolerancia y aceptación entre grupos sociales diferentes",
            #"e5-d":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_desarrollo"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_department_filtered_for_tab5.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_desarrollo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_desarrollo"
        )
        st.session_state['current_tile_selection'] = selected_tile_desarrollo 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["DEPARTAMENTO", "DERECHOS"],
            ["Departamento:", f"{selected_display_name}:"]
        )

    elif option_escala_desarrollo == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_desarrollo}")
        
        municipio_sm_vars_desarrollo = ["e1-d", "e2-d", "e3-d", "e4-d"]
        
        gdf_municipio_sm_filtered_for_tab5 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "Santa María"
        ][["MUNICIPIO", "geometry"] + municipio_sm_vars_desarrollo].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sm_filtered_for_tab5,
                category_cols=municipio_sm_vars_desarrollo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "e1-d":"Seguridad alimentaria disponible",
            "e2-d":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
            "e3-d":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio",
            "e4-d":"Tolerancia y aceptación entre grupos sociales diferentes",
            #"e5-d":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_desarrollo"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sm_filtered_for_tab5.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_desarrollo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_desarrollo"
        )
        st.session_state['current_tile_selection'] = selected_tile_desarrollo

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )
    
    elif option_escala_desarrollo == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_desarrollo}")
        
        municipio_sj_vars_desarrollo = ["e1-d", "e2-d", "e3-d", "e4-d"]
    
        gdf_municipio_sj_filtered_for_tab5 = gdf_data_municipios_consolidado_full[
            gdf_data_municipios_consolidado_full["MUNICIPIO"] == "San José"
        ][["MUNICIPIO", "geometry"] + municipio_sj_vars_desarrollo].copy()

        with st.container():
            display_data_and_charts(
                gdf_municipio_sj_filtered_for_tab5,
                category_cols=municipio_sj_vars_desarrollo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "e1-d":"Seguridad alimentaria disponible",
            "e2-d":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
            "e3-d":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio",
            "e4-d":"Tolerancia y aceptación entre grupos sociales diferentes",
            #"e5-d":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes"
        }
        
        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización", 
            options=list(variable_map_for_display.values()), 
            key="dep_var_select_desarrollo"
        )
        
        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)
        
        gdf_map_data = gdf_municipio_sj_filtered_for_tab5.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_desarrollo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_desarrollo"
        )
        st.session_state['current_tile_selection'] = selected_tile_desarrollo 

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9,
            ["MUNICIPIO", "DERECHOS"],
            ["Municipio:", f"{selected_display_name}:"]
        )

    elif option_escala_desarrollo == "Localidades y áreas rurales del Departamento de Santa María":
        st.subheader("Localidades y áreas rurales del Departamento de Santa María")
        localidades_disponibles = gdf_data_localidades_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_localidad = st.selectbox(
            "Selecciona una Localidad", 
            options=localidades_disponibles, 
            key="localidad_select_desarrollo"
        )

        localidad_vars_desarrollo = ["e1-d", "e2-d", "e3-d", "e4-d"]

        gdf_localidad_filtered_for_tab5 = gdf_data_localidades_consolidado_full[
            gdf_data_localidades_consolidado_full["LOCALIDAD"] == selected_localidad
        ][["LOCALIDAD", "geometry"] + localidad_vars_desarrollo].copy()

        with st.container():
            display_data_and_charts(
                gdf_localidad_filtered_for_tab5,
                category_cols=localidad_vars_desarrollo,
                value_col="DERECHOS"
            )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "e1-d":"Seguridad alimentaria disponible",
            "e2-d":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
            "e3-d":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio",
            "e4-d":"Tolerancia y aceptación entre grupos sociales diferentes",
            #"e5-d":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_desarrollo_localidad" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_localidad_filtered_for_tab5.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_desarrollo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_desarrollo_localidad" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_desarrollo

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            12, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )

    elif option_escala_desarrollo == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")
        manzanero_disponibles = gdf_data_manzanero_consolidado_full["LOCALIDAD"].unique().tolist()
        
        # Permitir al usuario seleccionar una localidad
        selected_manzanero = st.selectbox(
            "Selecciona una Localidad", 
            options=manzanero_disponibles, 
            key="manzanero_select_desarrollo"
        )

        manzanero_vars_desarrollo = ["e1-d", "e2-d", "e3-d", "e4-d"]

        gdf_manzanero_filtered_for_tab5 = gdf_data_manzanero_consolidado_full[
            gdf_data_manzanero_consolidado_full["LOCALIDAD"] == selected_manzanero
        ][["LOCALIDAD", "geometry"] + manzanero_vars_desarrollo].copy()

        #with st.container():
        #    display_data_and_charts(
        #        gdf_manzanero_filtered_for_tab5,
        #        category_cols=manzanero_vars_desarrollo,
        #        value_col="DERECHOS"
        #    )

        st.subheader("Territorialización de los indicadores de la Brújula")
        variable_map_for_display = {
            "e1-d":"Seguridad alimentaria disponible",
            "e2-d":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
            "e3-d":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio",
            "e4-d":"Tolerancia y aceptación entre grupos sociales diferentes",
            #"e5-d":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes"
        }

        selected_display_name = st.selectbox(
            "Seleccionar una variable para su visualización",
            options=list(variable_map_for_display.values()),
            key="dep_var_select_desarrollo_manzanero" # Cambiado para evitar duplicación de claves
        )

        selected_variable_column = next(key for key, value in variable_map_for_display.items() if value == selected_display_name)

        gdf_map_data = gdf_manzanero_filtered_for_tab5.copy()
        gdf_map_data["DERECHOS"] = gdf_map_data[selected_variable_column]
        gdf_map_data["VARIABLE"] = selected_display_name

        selected_tile_desarrollo = st.selectbox(
            "Seleccionar mapa base",
            list(TILE_OPTIONS.keys()),
            key="tile_select_dep_desarrollo_manzanero" # Cambiado para evitar duplicación de claves
        )
        st.session_state['current_tile_selection'] = selected_tile_desarrollo

        create_folium_map(
            gdf_map_data,
            selected_display_name,
            9, # Puedes ajustar el nivel de zoom inicial si es necesario
            ["LOCALIDAD", "DERECHOS"],
            ["Localidad:", f"{selected_display_name}:"]
        )
