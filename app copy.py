import streamlit as st
import folium
from streamlit.components.v1 import html
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd

st.set_page_config(layout="wide")

# Ruta a los archivos locales
path_manzanero = "data/vivienda-suelo/santa-maria-manzanero.geojson"
path_localidades = "data/vivienda-suelo/santa-maria-localidades.geojson"
path_municipios = "data/vivienda-suelo/santa-maria-municipios.geojson"
path_departamento = "data/vivienda-suelo/santa-maria-departamento.geojson"

# Leer el archivo

gdf_departamento = gpd.read_file(path_departamento)
gdf_municipios = gpd.read_file(path_municipios)
gdf_localidades = gpd.read_file(path_localidades)
gdf_manzanero = gpd.read_file(path_manzanero)

st.title("PLATAFORMA DE LA BRÚJULA")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["VIVIENDA Y SUELO", "INFRAESTRUCTURAS", "EQUIPAMIENTOS", "ACCESIBILIDAD", "DESARROLLO LOCAL"])

st.divider()

with tab1:
    st.header("Departamento de Santa María")

    escalas_viv_suelo = ["Departamento de Santa María", "Municipio de Santa María", "Municipio de San José", "Localidades del Departamento de Santa María", "Manzanas del Departamento de Santa María"]
    option_escala_viv_suelo = st.selectbox(
        "Seleccionar una escala",
        (escalas_viv_suelo)
    )

    if option_escala_viv_suelo == "Departamento de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        container = st.container(border=True)
        with st.container():
            col1, col2 = st.columns(2)
            df_departamento = gdf_departamento.drop(["geometry"], axis=1)
            df_departamento = df_departamento[["DEPARTAMENTO", "VARIABLE", "DERECHOS"]]
            with col1:
                st.markdown("Matriz de la Brújula")
                st.markdown(df_departamento.style
                    .hide(axis='index')  # Oculta el índice visualmente
                    .to_html(), unsafe_allow_html=True
                    )
            with col2:
                st.markdown("Gráfico de la Brújula")
                # Extraer los datos
                categorias = gdf_departamento["VARIABLE"].tolist()
                valores = gdf_departamento["DERECHOS"].tolist()

                # Cerrar el polígono del radar
                categorias += [categorias[0]]
                valores += [valores[0]]

                # Crear gráfico radar
                fig = go.Figure(
                    data=go.Scatterpolar(
                        r=valores,
                        theta=categorias,
                        fill='toself',
                        name='Derechos',
                        line=dict(color='royalblue')
                    )
                )

                # Ajustes de diseño
                fig.update_layout(
                    width=350,
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',   # Fondo general transparente
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

                # Mostrar en Streamlit
                st.plotly_chart(fig, use_container_width=True)
            

        st.subheader("Territorialización de los indicadores de la Brújula")

        # Obtener lista única de variables
        variables = gdf_departamento["VARIABLE"].unique()

        # Selector en Streamlit
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables)

        # Filtrar el GeoDataFrame según la variable seleccionada
        filtered_gdf = gdf_departamento[gdf_departamento["VARIABLE"] == selected_variable]
        centro = filtered_gdf.geometry.union_all().centroid

        # Crear el mapa base centrado
        m = folium.Map(location=[centro.y, centro.x], zoom_start=9, tiles=None)

        folium.TileLayer("CartoDB dark_matter", name="Fondo oscuro").add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            name='Fondo satelital',
            overlay=False,
            control=True
        ).add_to(m)

        # Función para mapear 'derechos' a color (degradé de blanco a azul)
        def color_map(valor):
            colores = ["#ffffff", "#cce5ff", "#99ccff", "#3399ff", "#004c99"]
            return colores[int(valor)] if valor in range(5) else "#ffffff"

        # Agregar capa filtrada
        folium.GeoJson(
            filtered_gdf.to_json(),
            name=selected_variable,
            tooltip=folium.GeoJsonTooltip(
                fields=["DEPARTAMENTO", "DERECHOS"],
                aliases=["Departamento:", "Derechos:"]
            ),
            style_function=lambda feature: {
                "fillColor": color_map(feature["properties"]["DERECHOS"]),
                "color": "#013161",
                "weight": 2,
                "fillOpacity": 0.5,
            }
        ).add_to(m)

        # Agregar control de capas
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # MOSTRAR el mapa después de agregar todas las capas
        html(m._repr_html_(), height=600)
            
    if option_escala_viv_suelo == "Municipio de Santa María":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        
        container = st.container(border=True)
        with st.container():
            col1, col2 = st.columns(2)

            df_municipios = gdf_municipios.drop(["geometry"], axis=1)
            df_municipios = df_municipios[["MUNICIPIO","VARIABLE", "DERECHOS"]]
            df_municipios_sm = df_municipios[df_municipios['MUNICIPIO'] == 'Santa María']
            with col1:
                st.markdown("Matriz de la Brújula")
                st.markdown(df_municipios_sm.style
                    .hide(axis='index')  # Oculta el índice visualmente
                    .to_html(), unsafe_allow_html=True
                    )
            with col2:
                st.markdown("Gráfico de la Brújula")
                # Extraer los datos
                categorias = df_municipios_sm["VARIABLE"].tolist()
                valores = df_municipios_sm["DERECHOS"].tolist()

                # Cerrar el polígono del radar
                categorias += [categorias[0]]
                valores += [valores[0]]

                # Crear gráfico radar
                fig = go.Figure(
                    data=go.Scatterpolar(
                        r=valores,
                        theta=categorias,
                        fill='toself',
                        name='Derechos',
                        line=dict(color='royalblue')
                    )
                )

                # Ajustes de diseño
                fig.update_layout(
                    width=350,
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',   # Fondo general transparente
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

                # Mostrar en Streamlit
                st.plotly_chart(fig, use_container_width=True)


        st.subheader("Territorialización de los indicadores de la Brújula")

        # Obtener lista única de variables
        variables = gdf_municipios["VARIABLE"].unique()

        # Selector en Streamlit
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables)

        # Filtrar el GeoDataFrame según la variable seleccionada
        gdf_municipios_sm = gdf_municipios[gdf_municipios['MUNICIPIO'] == 'Santa María']
        filtered_gdf = gdf_municipios_sm[gdf_municipios_sm["VARIABLE"] == selected_variable]
        centro = gdf_municipios_sm.geometry.union_all().centroid

        # Crear el mapa base centrado
        m = folium.Map(location=[centro.y, centro.x], zoom_start=10, tiles=None)

        folium.TileLayer("CartoDB dark_matter", name="Fondo oscuro").add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            name='Fondo satelital',
            overlay=False,
            control=True
        ).add_to(m)

        # Función para mapear 'derechos' a color (degradé de blanco a azul)
        def color_map(valor):
            colores = ["#ffffff", "#cce5ff", "#99ccff", "#3399ff", "#004c99"]
            return colores[int(valor)] if valor in range(5) else "#ffffff"

        # Agregar capa filtrada
        folium.GeoJson(
            filtered_gdf.to_json(),
            name=selected_variable,
            tooltip=folium.GeoJsonTooltip(
                fields=["DEPARTAMENTO", "MUNICIPIO", "DERECHOS"],
                aliases=["Departamento:", "Municipio:", "Derechos:"]
            ),
            style_function=lambda feature: {
                "fillColor": color_map(feature["properties"]["DERECHOS"]),
                "color": "#013161",
                "weight": 2,
                "fillOpacity": 0.5,
            }
        ).add_to(m)

        # Agregar control de capas
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # MOSTRAR el mapa después de agregar todas las capas
        html(m._repr_html_(), height=600)

    if option_escala_viv_suelo == "Municipio de San José":
        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos del {option_escala_viv_suelo}")
        
        container = st.container(border=True)
        with st.container():
            col1, col2 = st.columns(2)

            df_municipios = gdf_municipios.drop(["geometry"], axis=1)
            df_municipios = df_municipios[["MUNICIPIO","VARIABLE", "DERECHOS"]]
            df_municipios_sj = df_municipios[df_municipios['MUNICIPIO'] == 'San José']
            with col1:
                st.markdown("Matriz de la Brújula")
                st.markdown(df_municipios_sj.style
                    .hide(axis='index')  # Oculta el índice visualmente
                    .to_html(), unsafe_allow_html=True
                    )
            with col2:
                st.markdown("Gráfico de la Brújula")
                # Extraer los datos
                categorias = df_municipios_sj["VARIABLE"].tolist()
                valores = df_municipios_sj["DERECHOS"].tolist()

                # Cerrar el polígono del radar
                categorias += [categorias[0]]
                valores += [valores[0]]

                # Crear gráfico radar
                fig = go.Figure(
                    data=go.Scatterpolar(
                        r=valores,
                        theta=categorias,
                        fill='toself',
                        name='Derechos',
                        line=dict(color='royalblue')
                    )
                )

                # Ajustes de diseño
                fig.update_layout(
                    width=350,
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',   # Fondo general transparente
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

                # Mostrar en Streamlit
                st.plotly_chart(fig, use_container_width=True)

        # Obtener lista única de variables
        variables = gdf_municipios["VARIABLE"].unique()

        # Selector en Streamlit
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables)

        # Filtrar el GeoDataFrame según la variable seleccionada
        gdf_municipios_sj = gdf_municipios[gdf_municipios['MUNICIPIO'] == 'San José']
        filtered_gdf = gdf_municipios_sj[gdf_municipios_sj["VARIABLE"] == selected_variable]
        centro = gdf_municipios_sj.geometry.union_all().centroid

        # Crear el mapa base centrado
        m = folium.Map(location=[centro.y, centro.x], zoom_start=9, tiles=None)

        folium.TileLayer("CartoDB dark_matter", name="Fondo oscuro").add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            name='Fondo satelital',
            overlay=False,
            control=True
        ).add_to(m)

        # Función para mapear 'derechos' a color (degradé de blanco a azul)
        def color_map(valor):
            colores = ["#ffffff", "#cce5ff", "#99ccff", "#3399ff", "#004c99"]
            return colores[int(valor)] if valor in range(5) else "#ffffff"

        # Agregar capa filtrada
        folium.GeoJson(
            filtered_gdf.to_json(),
            name=selected_variable,
            tooltip=folium.GeoJsonTooltip(
                fields=["DEPARTAMENTO","MUNICIPIO", "DERECHOS"],
                aliases=["Departamento:","Municipio:", "Derechos:"]
            ),
            style_function=lambda feature: {
                "fillColor": color_map(feature["properties"]["DERECHOS"]),
                "color": "#013161",
                "weight": 2,
                "fillOpacity": 0.5,
            }
        ).add_to(m)

        # Agregar control de capas
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # MOSTRAR el mapa después de agregar todas las capas
        html(m._repr_html_(), height=600)

    if option_escala_viv_suelo == "Localidades del Departamento de Santa María":
        st.subheader("Localidades del Departamento de Santa María")

        # Obtener lista única de localidades
        variables_localidades_sm = gdf_localidades["LOCALIDAD"].unique()
        localidades_sm = st.selectbox("Seleccionar una localidad del Departamento de Santa María", options=variables_localidades_sm)

        st.subheader(f"Resultados de la Brújula según cumplimiento de derechos de la localidad de {localidades_sm}")
        container = st.container(border=True)
        with st.container():
            col1, col2 = st.columns(2)
            df_localidades = gdf_localidades.drop(["geometry"], axis=1)
            df_localidades = df_localidades[["LOCALIDAD","VARIABLE", "DERECHOS"]]
            df_localidades = df_localidades[df_localidades['LOCALIDAD'] == localidades_sm]
            with col1:
                st.markdown("Matriz de la Brújula")
                st.markdown(df_localidades.style
                    .hide(axis='index')  # Oculta el índice visualmente
                    .to_html(), unsafe_allow_html=True
                    )
            with col2:
                st.markdown("Gráfico de la Brújula")
                # Extraer los datos
                categorias = df_localidades["VARIABLE"].tolist()
                valores = df_localidades["DERECHOS"].tolist()

                # Cerrar el polígono del radar
                categorias += [categorias[0]]
                valores += [valores[0]]

                # Crear gráfico radar
                fig = go.Figure(
                    data=go.Scatterpolar(
                        r=valores,
                        theta=categorias,
                        fill='toself',
                        name='Derechos',
                        line=dict(color='royalblue')
                    )
                )

                # Ajustes de diseño
                fig.update_layout(
                    width=350,
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',   # Fondo general transparente
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

                # Mostrar en Streamlit
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Territorialización de los indicadores de la Brújula")

        # Obtener lista única de variables
        variables = gdf_localidades["VARIABLE"].unique()

        # Selector en Streamlit
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables)

        # Filtrar el GeoDataFrame según la variable seleccionada
        gdf_localidades = gdf_localidades[gdf_localidades['LOCALIDAD'] == localidades_sm]
        filtered_gdf = gdf_localidades[gdf_localidades["VARIABLE"] == selected_variable]
        centro = filtered_gdf.geometry.union_all().centroid


        # Crear el mapa base centrado
        m = folium.Map(location=[centro.y, centro.x], zoom_start=14, tiles=None)

        folium.TileLayer("CartoDB dark_matter", name="Fondo oscuro").add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            name='Fondo satelital',
            overlay=False,
            control=True
        ).add_to(m)

        # Función para mapear 'derechos' a color (degradé de blanco a azul)
        def color_map(valor):
            colores = ["#ffffff", "#cce5ff", "#99ccff", "#3399ff", "#004c99"]
            return colores[int(valor)] if valor in range(5) else "#ffffff"

        # Agregar capa filtrada
        folium.GeoJson(
            filtered_gdf.to_json(),
            name=selected_variable,
            tooltip=folium.GeoJsonTooltip(
                fields=["DEPARTAMENTO","MUNICIPIO","LOCALIDAD", "DERECHOS"],
                aliases=["Departamento:","Municipio:","Localidad:", "Derechos:"]
            ),
            style_function=lambda feature: {
                "fillColor": color_map(feature["properties"]["DERECHOS"]),
                "color": "#013161",
                "weight": 2,
                "fillOpacity": 0.5,
            }
        ).add_to(m)

        # Agregar control de capas
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # MOSTRAR el mapa después de agregar todas las capas
        html(m._repr_html_(), height=600)

    if option_escala_viv_suelo == "Manzanas del Departamento de Santa María":
        st.subheader("Manzanas del Departamento de Santa María")

        # Obtener lista única de localidades
        variables_manzanero = gdf_manzanero["MUNICIPIO"].unique()
        manzanero_municipio = st.selectbox("Seleccionar un Municipio del Departamento de Santa María", options=variables_manzanero)

        st.subheader(f"Territorialización de los indicadores de la Brújula por manzana del Municipio de {manzanero_municipio}")

        # Obtener lista única de variables
        variables = gdf_manzanero["VARIABLE"].unique()

        # Selector en Streamlit
        selected_variable = st.selectbox("Seleccionar una variable para su visualización", options=variables)

        # Filtrar el GeoDataFrame según la variable seleccionada
        gdf_manzanero = gdf_manzanero[gdf_manzanero['MUNICIPIO'] == manzanero_municipio]
        filtered_gdf = gdf_manzanero[gdf_manzanero["VARIABLE"] == selected_variable]
        centro = filtered_gdf.geometry.union_all().centroid


        # Crear el mapa base centrado
        m = folium.Map(location=[centro.y, centro.x], zoom_start=12, tiles=None)

        folium.TileLayer("CartoDB dark_matter", name="Fondo oscuro").add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            name='Fondo satelital',
            overlay=False,
            control=True
        ).add_to(m)

        # Función para mapear 'derechos' a color (degradé de blanco a azul)
        def color_map(valor):
            colores = ["#ffffff", "#cce5ff", "#99ccff", "#3399ff", "#004c99"]
            return colores[int(valor)] if valor in range(5) else "#ffffff"

        # Agregar capa filtrada
        folium.GeoJson(
            filtered_gdf.to_json(),
            name=selected_variable,
            tooltip=folium.GeoJsonTooltip(
                fields=["MUNICIPIO","LOCALIDAD", "DERECHOS"],
                aliases=["Municipio:","Localidad", "Derechos:"]
            ),
            style_function=lambda feature: {
                "fillColor": color_map(feature["properties"]["DERECHOS"]),
                "color": "#013161",
                "weight": 2,
                "fillOpacity": 0.5,
            }
        ).add_to(m)

        # Agregar control de capas
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # MOSTRAR el mapa después de agregar todas las capas
        html(m._repr_html_(), height=600)