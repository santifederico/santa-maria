import streamlit as st
import folium
from streamlit.components.v1 import html
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd

st.set_page_config(layout="wide")

# --- Carga de Datos ---
@st.cache_data
def load_data(path):
    """Carga los datos de un archivo GeoJSON."""
    return gpd.read_file(path)

gdf_data_consolidado_full = load_data("data/santa-maria-consolidado.geojson")

# --- Funciones Auxiliares ---

def plot_radar_chart(df_data, category_col, value_col, radar_range=[0, 4]):
    """Genera un gráfico de radar de Plotly."""
    categorias = df_data[category_col].tolist()
    valores = df_data[value_col].tolist()

    if not categorias:
        st.warning("No hay categorías para mostrar en el gráfico de radar.")
        return
        
    categorias += [categorias[0]]
    valores += [valores[0]]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            name=value_col,
            line=dict(color='#FF4B4B')
        )
    )

    fig.update_layout(
        width=300,
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=radar_range,
                tickvals=[0, 4, 8, 12, 16, 20] if radar_range[1] == 20 else [0, 1, 2, 3, 4],
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
    colores = ["#ffffff", "#FFD0CB", "#FD8D89", "#FF4B4B", "#A40000"]
    try:
        return colores[int(valor)] if 0 <= int(valor) < len(colores) else "#ffffff"
    except (ValueError, TypeError):
        return "#ffffff"

def create_folium_map(gdf, selected_variable, zoom_start, tooltip_fields, tooltip_aliases):
    """Crea y muestra un mapa de Folium."""
    filtered_gdf = gdf.copy()
    if not filtered_gdf.empty:
        try:
            centro = filtered_gdf.geometry.union_all().centroid
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

    existing_fields = [field for field in tooltip_fields if field in filtered_gdf.columns]
    
    existing_aliases = []
    for field in existing_fields:
        try:
            index = tooltip_fields.index(field)
            existing_aliases.append(tooltip_aliases[index])
        except ValueError:
            if field == 'VALOR':
                existing_aliases.append(f"{selected_variable}:")
            elif field == 'VARIABLE':
                existing_aliases.append("Variable:")

    folium.GeoJson(
        filtered_gdf.to_json(),
        name=selected_variable,
        tooltip=folium.GeoJsonTooltip(
            fields=existing_fields,
            aliases=existing_aliases
        ),
        style_function=lambda feature: {
            "fillColor": color_map(feature["properties"]["VALOR"]),
            "color": "#A40000",
            "weight": 2,
            "fillOpacity": 0.5,
        }
    ).add_to(m)

    folium.LayerControl().add_to(m)
    html(m._repr_html_(), height=600)

def display_data_and_charts(df_data, value_col="VALOR"):
    """Muestra la tabla de datos y el gráfico de radar."""
    
    variable_display_names = {
    "d-a1": "Seguridad en la tenencia del suelo", "d-a2": "Sin hacinamiento en la vivienda",
    "d-a3": "Vivienda construida con materiales permanentes", "d-a4": "Vivienda con baño propio",
    "d-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "d-b1":"Provisión de agua potable disponible", "d-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "d-b3":"Disponibilidad de drenajes que eviten inundación", "d-b4":"Conexión de energía (electricidad y gas)",
    "d-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "d-c1":"Espacios verdes públicos disponibles y mantenidos", "d-c2":"Escuelas pre-escolares, primarias y secundarias",
    "d-c3":"Hospitales y centros de salud de atención primaria disponibles", "d-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "d-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "d-d1":"Calzadas disponibles permitiendo movimiento vehicular", "d-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "d-d3":"Servicio transporte público guiado disponible a precios accesibles", "d-d4":"Servicios de colectivos, taxis y motos disponibles",
    "d-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "d-e1":"Seguridad alimentaria disponible", "d-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "d-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "d-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "d-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",

    "os-a1": "Seguridad en la tenencia del suelo", "os-a2": "Sin hacinamiento en la vivienda",
    "os-a3": "Vivienda construida con materiales permanentes", "os-a4": "Vivienda con baño propio",
    "os-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "os-b1":"Provisión de agua potable disponible", "os-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "os-b3":"Disponibilidad de drenajes que eviten inundación", "os-b4":"Conexión de energía (electricidad y gas)",
    "os-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "os-c1":"Espacios verdes públicos disponibles y mantenidos", "os-c2":"Escuelas pre-escolares, primarias y secundarias",
    "os-c3":"Hospitales y centros de salud de atención primaria disponibles", "os-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "os-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "os-d1":"Calzadas disponibles permitiendo movimiento vehicular", "os-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "os-d3":"Servicio transporte público guiado disponible a precios accesibles", "os-d4":"Servicios de colectivos, taxis y motos disponibles",
    "os-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "os-e1":"Seguridad alimentaria disponible", "os-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "os-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "os-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "os-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",

    "op-a1": "Seguridad en la tenencia del suelo", "op-a2": "Sin hacinamiento en la vivienda",
    "op-a3": "Vivienda construida con materiales permanentes", "op-a4": "Vivienda con baño propio",
    "op-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "op-b1":"Provisión de agua potable disponible", "op-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "op-b3":"Disponibilidad de drenajes que eviten inundación", "op-b4":"Conexión de energía (electricidad y gas)",
    "op-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "op-c1":"Espacios verdes públicos disponibles y mantenidos", "op-c2":"Escuelas pre-escolares, primarias y secundarias",
    "op-c3":"Hospitales y centros de salud de atención primaria disponibles", "op-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "op-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "op-d1":"Calzadas disponibles permitiendo movimiento vehicular", "op-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "op-d3":"Servicio transporte público guiado disponible a precios accesibles", "op-d4":"Servicios de colectivos, taxis y motos disponibles",
    "op-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "op-e1":"Seguridad alimentaria disponible", "op-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "op-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "op-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "op-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",

    "n-a1": "Seguridad en la tenencia del suelo", "n-a2": "Sin hacinamiento en la vivienda",
    "n-a3": "Vivienda construida con materiales permanentes", "n-a4": "Vivienda con baño propio",
    "n-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "n-b1":"Provisión de agua potable disponible", "n-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "n-b3":"Disponibilidad de drenajes que eviten inundación", "n-b4":"Conexión de energía (electricidad y gas)",
    "n-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "n-c1":"Espacios verdes públicos disponibles y mantenidos", "n-c2":"Escuelas pre-escolares, primarias y secundarias",
    "n-c3":"Hospitales y centros de salud de atención primaria disponibles", "n-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "n-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "n-d1":"Calzadas disponibles permitiendo movimiento vehicular", "n-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "n-d3":"Servicio transporte público guiado disponible a precios accesibles", "n-d4":"Servicios de colectivos, taxis y motos disponibles",
    "n-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "n-e1":"Seguridad alimentaria disponible", "n-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "n-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "n-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "n-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",
    }
    
    df_chart_data = df_data.copy()
    if 'VARIABLE' in df_chart_data.columns:
        df_chart_data['VARIABLE'] = df_chart_data['VARIABLE'].map(variable_display_names)
    
    df_display_for_table = df_chart_data.copy()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Matriz de la Brújula")
        if not df_display_for_table.empty:
            columns_to_display = [col for col in ["COD", "DEPARTAMENTO", "MUNICIPIO", "LOCALIDAD", "MANZANERO", "VARIABLE", value_col] if col in df_display_for_table.columns]
            st.dataframe(df_display_for_table[columns_to_display])
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

# --- Streamlit UI ---
st.title("PLATAFORMA DE LA BRÚJULA")
st.divider()
st.markdown("**Etapa de aplicación de La Brújula**")
with st.container():
    ancho_imagen = 80
    col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 14])
    with col1:
        st.image("./assets/img/ins-brujula.jpg", width=ancho_imagen)
    with col2:
        st.image("./assets/img/ins-participlan.jpg", width=ancho_imagen)
    with col3:
        st.image("./assets/img/ins-posplan.jpg", width=ancho_imagen)
    with col4:
        st.image("./assets/img/ins-migraplan.jpg", width=ancho_imagen)

st.caption("BRÚJULA | Pre-diagnóstico")
st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    izq, centro, der = st.columns([0.5, 18 , 0.5])
    with centro:
        st.image("./assets/img/portada.jpg")

tabs = ["VIVIENDA Y SUELO", "INFRAESTRUCTURAS", "EQUIPAMIENTOS", "ACCESIBILIDAD", "DESARROLLO LOCAL", "BRÚJULA CONSOLIDADA"]
st.divider()
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tabs)

dimension_vars = {
    "VIVIENDA Y SUELO": ["a1", "a2", "a3", "a4", "a5"],
    "INFRAESTRUCTURAS": ["b1", "b2", "b3", "b4", "b5"],
    "EQUIPAMIENTOS": ["c1", "c2", "c3", "c4", "c5"],
    "ACCESIBILIDAD": ["d1", "d2", "d3", "d4", "d5"],
    "DESARROLLO LOCAL": ["e1", "e2", "e3", "e4", "e5"],
}

indicador_prefix = {
    "Derechos": "d-",
    "Obras públicas": "op-",
    "Organización social": "os-",
    "Normas": "n-"
}

variable_map_for_display = {
    "d-a1": "Seguridad en la tenencia del suelo", "d-a2": "Sin hacinamiento en la vivienda",
    "d-a3": "Vivienda construida con materiales permanentes", "d-a4": "Vivienda con baño propio",
    "d-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "d-b1":"Provisión de agua potable disponible", "d-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "d-b3":"Disponibilidad de drenajes que eviten inundación", "d-b4":"Conexión de energía (electricidad y gas)",
    "d-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "d-c1":"Espacios verdes públicos disponibles y mantenidos", "d-c2":"Escuelas pre-escolares, primarias y secundarias",
    "d-c3":"Hospitales y centros de salud de atención primaria disponibles", "d-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "d-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "d-d1":"Calzadas disponibles permitiendo movimiento vehicular", "d-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "d-d3":"Servicio transporte público guiado disponible a precios accesibles", "d-d4":"Servicios de colectivos, taxis y motos disponibles",
    "d-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "d-e1":"Seguridad alimentaria disponible", "d-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "d-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "d-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "d-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",

    "os-a1": "Seguridad en la tenencia del suelo", "os-a2": "Sin hacinamiento en la vivienda",
    "os-a3": "Vivienda construida con materiales permanentes", "os-a4": "Vivienda con baño propio",
    "os-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "os-b1":"Provisión de agua potable disponible", "os-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "os-b3":"Disponibilidad de drenajes que eviten inundación", "os-b4":"Conexión de energía (electricidad y gas)",
    "os-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "os-c1":"Espacios verdes públicos disponibles y mantenidos", "os-c2":"Escuelas pre-escolares, primarias y secundarias",
    "os-c3":"Hospitales y centros de salud de atención primaria disponibles", "os-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "os-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "os-d1":"Calzadas disponibles permitiendo movimiento vehicular", "os-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "os-d3":"Servicio transporte público guiado disponible a precios accesibles", "os-d4":"Servicios de colectivos, taxis y motos disponibles",
    "os-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "os-e1":"Seguridad alimentaria disponible", "os-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "os-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "os-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "os-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",

    "op-a1": "Seguridad en la tenencia del suelo", "op-a2": "Sin hacinamiento en la vivienda",
    "op-a3": "Vivienda construida con materiales permanentes", "op-a4": "Vivienda con baño propio",
    "op-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "op-b1":"Provisión de agua potable disponible", "op-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "op-b3":"Disponibilidad de drenajes que eviten inundación", "op-b4":"Conexión de energía (electricidad y gas)",
    "op-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "op-c1":"Espacios verdes públicos disponibles y mantenidos", "op-c2":"Escuelas pre-escolares, primarias y secundarias",
    "op-c3":"Hospitales y centros de salud de atención primaria disponibles", "op-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "op-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "op-d1":"Calzadas disponibles permitiendo movimiento vehicular", "op-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "op-d3":"Servicio transporte público guiado disponible a precios accesibles", "op-d4":"Servicios de colectivos, taxis y motos disponibles",
    "op-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "op-e1":"Seguridad alimentaria disponible", "op-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "op-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "op-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "op-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",

    "n-a1": "Seguridad en la tenencia del suelo", "n-a2": "Sin hacinamiento en la vivienda",
    "n-a3": "Vivienda construida con materiales permanentes", "n-a4": "Vivienda con baño propio",
    "n-a5": "Generación de oferta de vivienda y alquiler a precios accesibles",
    "n-b1":"Provisión de agua potable disponible", "n-b2":"Servicio sanitarios o pozos disponibles sin contaminación",
    "n-b3":"Disponibilidad de drenajes que eviten inundación", "n-b4":"Conexión de energía (electricidad y gas)",
    "n-b5":"Conexión servicios de telecomunicaciones, Internet, etc.",
    "n-c1":"Espacios verdes públicos disponibles y mantenidos", "n-c2":"Escuelas pre-escolares, primarias y secundarias",
    "n-c3":"Hospitales y centros de salud de atención primaria disponibles", "n-c4":"Servicios seguridad policial, bomberos, templos y DC disponibles",
    "n-c5":"Servicios de alumbrado, barrido y limpieza disponibles",
    "n-d1":"Calzadas disponibles permitiendo movimiento vehicular", "n-d2":"Aceras disponibles permitiendo circulación peatonal y ciclística con seguridad vial, iluminadas y limpias",
    "n-d3":"Servicio transporte público guiado disponible a precios accesibles", "n-d4":"Servicios de colectivos, taxis y motos disponibles",
    "n-d5":"Posibilidad de acceso de ambulancias, bomberos, policía y defensa civil",
    "n-e1":"Seguridad alimentaria disponible", "n-e2":"Disponibilidad de trabajo, ingresos, medios de sustento y previsión social",
    "n-e3":"Capacidad de ahorro y re-inversión en mejoras de la vivienda y el barrio", "n-e4":"Tolerancia y aceptación entre grupos sociales diferentes",
    "n-e5":"Acciones de prevención y reducción de riesgos de contaminación y desastres vigentes",
}

def create_tab_content(tab_name, gdf_data_full):
    """Genera el contenido para cada pestaña de la brújula."""
    
    dimension_vars = {
        "VIVIENDA Y SUELO": ["a1", "a2", "a3", "a4", "a5"],
        "INFRAESTRUCTURAS": ["b1", "b2", "b3", "b4", "b5"],
        "EQUIPAMIENTOS": ["c1", "c2", "c3", "c4", "c5"],
        "ACCESIBILIDAD": ["d1", "d2", "d3", "d4", "d5"],
        "DESARROLLO LOCAL": ["e1", "e2", "e3", "e4", "e5"],
    }
    
    escalas_cod = {
        "Departamento de Santa María": "DPTO-",
        "Municipio de Santa María": "MUN-1",
        "Municipio de San José": "MUN-2",
        "Localidades y áreas rurales del Departamento de Santa María": "LOC-",
        "Manzanas del Departamento de Santa María": "MAN-"
    }
    
    opciones_escala = list(escalas_cod.keys())
    selected_escala = st.selectbox("Seleccionar una escala", opciones_escala, key=f"{tab_name}_escala_select")
    st.link_button(
        "Ver metodología de definición de escalas",
        "https://santifederico.github.io/plataforma-brujula/pages/metodologia.html", type="primary"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader(f"Métricas generales del {selected_escala}")
    with st.container():
        col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 5])

        with col1:
            st.metric(label="Superficie (km2)", value="5491,89")
        with col2:
            st.metric(label="Personas*", value="26822", delta="19,4 %")
        with col3:
            st.metric(label="Hogares*", value="8495", delta="42,01 %")
        with col4:
            st.metric(label="Viviendas particulares*", value="10370", delta="88,09 %")
    st.caption("*Variación intercensal.")

    with st.container():
            # Define el ancho de las imágenes
            ancho_imagen = 800

            # Crea 4 columnas para las imágenes
            _, col1, col2, col3, _ = st.columns([0.01, 0.825, 1, 0.825, 0.01])

            with col1:
                st.image("./assets/img/carretel-lateral-1.jpg")
            with col2:
                st.image("./assets/img/carretel-1.jpg")
            with col3:
                st.image("./assets/img/carretel-lateral-3.jpg")
        
    st.divider()
    
    cod_prefijo = escalas_cod[selected_escala]
    filtered_gdf = gdf_data_full[gdf_data_full['COD'].str.startswith(cod_prefijo)].copy()
    
    if filtered_gdf.empty:
        st.warning("No se encontraron datos para la escala y el indicador seleccionados.")
        return

    st.subheader(f"Resultados generales de La Brújula del {selected_escala}")
    
    dimension_vars_names = dimension_vars.get(tab_name)
    
    data_for_table = {
        "Variable": [f"d-{v}" for v in dimension_vars_names],
        "Derechos": [filtered_gdf[f"d-{v}"].mean() for v in dimension_vars_names],
        "Obras públicas": [filtered_gdf[f"op-{v}"].mean() for v in dimension_vars_names],
        "Organización social": [filtered_gdf[f"os-{v}"].mean() for v in dimension_vars_names],
        "Normas": [filtered_gdf[f"n-{v}"].mean() for v in dimension_vars_names],
    }
    
    df_preview = pd.DataFrame(data_for_table)
    
    df_preview['Variable'] = df_preview['Variable'].map(variable_map_for_display)
    
    # Calcular la suma de cada columna para el gráfico de radar y la fila de totales
    totales = df_preview.drop('Variable', axis=1).sum().to_dict()
    totales_df = pd.DataFrame({
        "Indicador": list(totales.keys()),
        "Suma": list(totales.values())
    })
    
    # Añadir la fila de totales a la tabla
    totales['Variable'] = 'Totales'
    df_preview = pd.concat([df_preview, pd.DataFrame([totales])], ignore_index=True)
    df_preview = df_preview.round(2)

    col_table, col_chart = st.columns(2)
    with col_table:
        st.markdown("Matriz de La Brújula")
        st.dataframe(
            df_preview,
            hide_index=True,
            column_config={
                "Variable": st.column_config.TextColumn("Variable", width="medium")
            }
        )
    with col_chart:
        st.markdown("Gráfico de La Brújula")
        plot_radar_chart(totales_df, "Indicador", "Suma", radar_range=[0, 20])

    st.divider()

    st.subheader(f"Resultados particulares de La Brújula por dimensión del {selected_escala}")

    selected_indicador = st.selectbox(
        "Seleccionar tipo de indicador",
        list(indicador_prefix.keys()),
        key=f"{tab_name}_indicador_select"
    )

    dimension_variables = dimension_vars.get(tab_name)
    if not dimension_variables:
        st.warning("No hay variables definidas para esta dimensión.")
        return

    prefix = indicador_prefix[selected_indicador]
    selected_variables = [f"{prefix}{var}" for var in dimension_variables]
    
    existing_selected_variables = [var for var in selected_variables if var in filtered_gdf.columns]
    
    if not existing_selected_variables:
        st.warning("No se encontraron variables para la combinación seleccionada de escala e indicador.")
        return
    
    df_for_charts = filtered_gdf[existing_selected_variables].mean().reset_index()
    df_for_charts.columns = ['VARIABLE', 'VALOR']
    
    with st.container():
        display_data_and_charts(
            df_for_charts,
            value_col="VALOR"
        )
    st.link_button(
        "Ver fichas de las variables",
        "https://santifederico.github.io/plataforma-brujula/pages/metodologia.html", type="primary"
    )
    st.divider()

    st.subheader("Conclusiones preliminares")
    st.markdown("**Seguridad en la tenencia del suelo.**")
    st.text("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
    st.markdown("**Sin hacinamiento en la vivienda.**")
    st.text("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
    st.markdown("**Vivienda construida con materiales permanentes.**")
    st.text("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
    st.markdown("**Vivienda con baño propio.**")
    st.text("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
    st.markdown("**Generación de oferta de vivienda y alquiler a precios accesibles.**")
    st.text("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
    st.link_button(
        "Ver hipótesis de trabajo",
        "https://santifederico.github.io/plataforma-brujula/pages/metodologia.html", type="primary"
    )
    st.divider()

    st.subheader("Territorialización de los indicadores de la Brújula")
    
    vars_to_display = {key: variable_map_for_display[key] for key in existing_selected_variables}
    
    selected_display_name = st.selectbox(
        "Seleccionar una variable para su visualización", 
        options=list(vars_to_display.values()), 
        key=f"var_select_{tab_name}_{selected_indicador}"
    )
    
    selected_variable_column = next(key for key, value in vars_to_display.items() if value == selected_display_name)

    gdf_map_data = filtered_gdf.copy()
    if selected_variable_column not in gdf_map_data.columns:
        st.error(f"La columna '{selected_variable_column}' no se encuentra en los datos filtrados.")
        return
        
    gdf_map_data["VALOR"] = gdf_map_data[selected_variable_column]
    gdf_map_data["VARIABLE"] = selected_display_name

    selected_tile = st.selectbox(
        "Seleccionar mapa base",
        list(TILE_OPTIONS.keys()),
        key=f"tile_select_{tab_name}_{selected_indicador}"
    )
    st.session_state['current_tile_selection'] = selected_tile 
    
    tooltip_fields = ["COD", "DEPARTAMENTO", "MUNICIPIO", "LOCALIDAD", "MANZANERO", "VALOR"]
    tooltip_aliases = ["Código:", "Departamento:", "Municipio:", "Localidad:", "Manzanero:", f"{selected_display_name}:"]

    create_folium_map(
        gdf_map_data,
        selected_display_name,
        9,
        tooltip_fields,
        tooltip_aliases
    )

    # Contenido del footer
    col1, col2, col3 = st.columns([5, 10, 2])
    with col1:
        st.markdown("**Realizado con Streamlit por Santaigo Federico |** © 2025")
    with col3:
        st.markdown("[Contacto por LinkedIn](https://www.linkedin.com/in/santiago-federico/)")

with tab1:
    create_tab_content("VIVIENDA Y SUELO", gdf_data_consolidado_full)

with tab2:
    create_tab_content("INFRAESTRUCTURAS", gdf_data_consolidado_full)

with tab3:
    create_tab_content("EQUIPAMIENTOS", gdf_data_consolidado_full)

with tab4:
    create_tab_content("ACCESIBILIDAD", gdf_data_consolidado_full)

with tab5:
    create_tab_content("DESARROLLO LOCAL", gdf_data_consolidado_full)

with tab6:
    st.subheader("BRÚJULA CONSOLIDADA")
    st.markdown("En esta pestaña puedes ver el resultado consolidado de todas las dimensiones en una sola visualización.")
    
    st.subheader("Filtros de Nivel Jerárquico")
    escalas_cod_con = {
        "Departamento de Santa María": "DPTO-",
        "Municipio de Santa María": "MUN-1",
        "Municipio de San José": "MUN-2",
        "Localidades y áreas rurales del Departamento de Santa María": "LOC-",
        "Manzanas del Departamento de Santa María": "MAN-"
    }
    
    opciones_escala_con = list(escalas_cod_con.keys())
    selected_escala_con = st.selectbox("Seleccionar una escala", opciones_escala_con, key=f"con_escala_select")
    
    cod_prefijo_con = escalas_cod_con[selected_escala_con]
    filtered_gdf_con = gdf_data_consolidado_full[gdf_data_consolidado_full['COD'].str.startswith(cod_prefijo_con)].copy()

    if not filtered_gdf_con.empty:
        st.subheader("Tabla Resumen por Dimensión y Tipo de Indicador")
        data_consolidada = {
            "Dimensión": list(dimension_vars.keys()),
            "Derechos": [filtered_gdf_con[[f"d-{v}" for v in dimension_vars[dim_name]]].mean().mean() for dim_name in dimension_vars],
            "Obras públicas": [filtered_gdf_con[[f"op-{v}" for v in dimension_vars[dim_name]]].mean().mean() for dim_name in dimension_vars],
            "Organización social": [filtered_gdf_con[[f"os-{v}" for v in dimension_vars[dim_name]]].mean().mean() for dim_name in dimension_vars],
            "Normas": [filtered_gdf_con[[f"n-{v}" for v in dimension_vars[dim_name]]].mean().mean() for dim_name in dimension_vars],
        }
        df_consolidado_preview = pd.DataFrame(data_consolidada)
        df_consolidado_preview = df_consolidado_preview.round(2)

        # Calcular la suma de cada columna para el gráfico de radar y la fila de totales
        totales_consolidado = df_consolidado_preview.drop('Dimensión', axis=1).sum().to_dict()
        totales_consolidado_df = pd.DataFrame({
            "Indicador": list(totales_consolidado.keys()),
            "Suma": list(totales_consolidado.values())
        })

        totales_consolidado['Dimensión'] = 'SUMA'
        df_consolidado_preview = pd.concat([df_consolidado_preview, pd.DataFrame([totales_consolidado])], ignore_index=True)
        
        col_table_con, col_chart_con = st.columns(2)
        with col_table_con:
            st.markdown("Promedio por Dimensión")
            st.dataframe(df_consolidado_preview, hide_index=True)
        with col_chart_con:
            st.markdown("Suma por tipo de indicador")
            plot_radar_chart(totales_consolidado_df, "Indicador", "Suma", radar_range=[0, 20])

        st.divider()
        
        selected_indicador_con = st.selectbox(
            "Seleccionar tipo de indicador (consolidado)",
            list(indicador_prefix.keys()),
            key="con_indicador_select"
        )
        
        prefix_con = indicador_prefix[selected_indicador_con]
        
        df_consolidado_brújula = pd.DataFrame({
            'Dimensión': ['VIVIENDA Y SUELO', 'INFRAESTRUCTURAS', 'EQUIPAMIENTOS', 'ACCESIBILIDAD', 'DESARROLLO LOCAL'],
            'VALOR': [
                filtered_gdf_con[[f"{prefix_con}{var}" for var in dimension_vars['VIVIENDA Y SUELO']]].mean().mean(),
                filtered_gdf_con[[f"{prefix_con}{var}" for var in dimension_vars['INFRAESTRUCTURAS']]].mean().mean(),
                filtered_gdf_con[[f"{prefix_con}{var}" for var in dimension_vars['EQUIPAMIENTOS']]].mean().mean(),
                filtered_gdf_con[[f"{prefix_con}{var}" for var in dimension_vars['ACCESIBILIDAD']]].mean().mean(),
                filtered_gdf_con[[f"{prefix_con}{var}" for var in dimension_vars['DESARROLLO LOCAL']]].mean().mean(),
            ]
        })
        
        df_consolidado_brújula.rename(columns={'Dimensión': 'VARIABLE'}, inplace=True)
        
        display_data_and_charts(
            df_consolidado_brújula,
            value_col="VALOR"
        )
    else:
        st.warning("No se encontraron datos consolidados para la selección de escala.")
    
    # Contenido del footer
    col1, col2, col3 = st.columns([5, 10, 2])
    with col1:
        st.markdown("**Realizado con Streamlit por Santaigo Federico |** © 2025")
    with col3:
        st.markdown("[Contacto por LinkedIn](https://www.linkedin.com/in/santiago-federico/)")