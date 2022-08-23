# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 20:56:56 2021

@author: User
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import easygui as eg
import os


#Select folder with required data and directories or type wd manually.
#Then, load the data.
dirBase = eg.diropenbox(msg="Abrir directorio base", title="Control: diropenbox")
datos2021 = pd.read_csv(os.path.join( dirBase, 'data', 'dataForEDA.csv'))
estaciones = pd.read_csv(os.path.join( dirBase, 'data', 'nuevas-estaciones-bicicletas-publicas.csv'))
my_data = pd.read_csv(os.path.join( dirBase, 'data', 'dataForClusteringAnalysis.csv'))
dirSalida = os.path.join(dirBase, 'plots')

#Let's rename for clarity
datos2021['momento_dia'] = datos2021['momento_dia'].astype('category').cat.rename_categories(
    {'1.Mañana': 'Morning', 
     '2.Mediodia': 'Mid-day',
     '3.Tarde' : 'Afternoon',
     '4.Noche' : 'Night',
     '5.Madrugada' : 'Early morning'
    })

datos2021['dia_semana'] = datos2021['dia_semana'].astype('category').cat.rename_categories(
    {'lunes': 'Mon', 
     'martes': 'Tue',
     'miercoles' : 'Wed',
     'jueves' : 'Thu',
     'viernes' : 'Fri',
     'sabado' : 'Sat',
     'domingo' : 'Sun'
    })


#%% 1) Basic quantitative EDA

# Total departure/arrival stations
nInicio = "n = " + str(len(datos2021['id_estacion_inicio'].unique()))
nFin = "n = " + str(len(datos2021['id_estacion_fin'].unique()))
nEstaciones = pd.DataFrame({"nEstacionesUsadas" : [len(datos2021['id_estacion_inicio'].unique()), 
                              len(datos2021['id_estacion_fin'].unique())],'Tipo' : ["Inicio", "Fin"]})
nEstaciones['Tipo'] = nEstaciones['Tipo'].astype('category').cat.rename_categories({'Inicio': 'Departure', 'Fin': 'Arrival'})

inicio = set(datos2021['nombre_estacion_inicio'])
fin = set(datos2021['nombre_estacion_fin'])
sinUsar = str((fin-inicio)).replace("{'", "").replace("'}" , "")


plt.figure(figsize=(8,5))
ax = sns.barplot(x="Tipo", y="nEstacionesUsadas", data=nEstaciones, 
                 order = nEstaciones.sort_values('nEstacionesUsadas').Tipo, palette = 'GnBu')
ax.set_facecolor("white")
ax.text(-0.1, 200, nInicio, fontsize=14, size =20) #add text
ax.text(0.9, 200, nFin, fontsize=14, size =20) #add text
plt.title('Number of stations used for departure/arrival', y=1.05, size =20)
plt.ylabel('# Stations', size = 20)
plt.xlabel('')
plt.savefig(os.path.join(dirSalida, 'n_stations_arrival_departure.png'), dpi=300)



# Top 10 stations used as check in / out
top_outs =  datos2021['nombre_estacion_inicio'].value_counts()[:10].reset_index()
top_outs.rename(columns = {'index':'station', 'nombre_estacion_inicio':'count_station'}, inplace=True)
top_ins =  datos2021['nombre_estacion_fin'].value_counts()[:10].reset_index()
top_ins.rename(columns = {'index':'station', 'nombre_estacion_fin':'count_station'}, inplace=True)        


fig, axes = plt.subplots(1,2, figsize=(10,6), squeeze=False)
fig.suptitle('Most popular stations - top 10', size=16)                
sns.barplot(ax = axes[0,0], x=top_outs.count_station, y=top_outs.station,  orient="h", palette = ("rocket") ) 
sns.barplot(ax = axes[0,1], x=top_ins.count_station, y=top_ins.station,  orient="h", palette = ("rocket") ) 
plt.tight_layout(pad=2)
axes[0,0].set(xlabel='Count',  ylabel='Station name (out)')
axes[0,1].set(xlabel='Count',  ylabel='Station name (in)')
plt.savefig(os.path.join(dirSalida, 'most_used_stations.png'), dpi=300)



# Number of trips made as function of daytime
nViajes = datos2021.groupby(['momento_dia'])["ID"].count().reset_index()
nViajes = nViajes.rename({"ID" : "nro_de_viajes"}, axis = 1)


plt.figure(figsize=(12,5))
ax = sns.barplot(x="momento_dia", y="nro_de_viajes", data=nViajes, palette = 'GnBu')
ax.set_facecolor("white")
plt.title('Number of users per daytime period', y=1.05)
plt.xlabel('Daytime period')
plt.ylabel('# Trips')
plt.xlabel('')
plt.savefig(os.path.join(dirSalida, 'n_trips_per_daytime.png'), dpi=300)


# Time travel distributions
def plot_time_travel_distrib(df, ubicacion, varX, labelX, labelY, titulo, bineo, paletaColor, unColor, xmin, xmax, ymin, ymax):
    '''Function to plot distribution for each time period'''
    sns.histplot(ax=axes[ubicacion], data=df ,x=varX, binwidth=bineo, color=paletaColor[unColor]) 
    axes[ubicacion].set(xlabel=labelX, ylabel=labelY)
    axes[ubicacion].set(xlim = (xmin, xmax), ylim = (ymin, ymax))
    axes[ubicacion].set_title(titulo,fontsize=16)
    axes[ubicacion].axvline(x=df[varX].mean(), color='red', ls='--')
    axes[ubicacion].text(50, 0, f'mean={round(df[varX].mean(), 2)}', horizontalalignment='center', fontweight=8)
    

fig, axes = plt.subplots(2,3, figsize=(10,10), squeeze=False)
plt.rcParams['font.size'] = '12'
plt.tight_layout(pad=5)
paletaColor = sns.color_palette("Set2")
bineo = 5 #mins
var_x = 'duracion_min'
x_label = 'Time travel (min)'
y_label = 'Frequency'
yMax = 100000
xMax = 100

plot_time_travel_distrib(datos2021[datos2021['momento_dia'] == 'Morning'], (0,0), 
                         var_x, x_label, y_label, 'Morning', bineo, paletaColor, 0, 0, xMax, 0, yMax)
plot_time_travel_distrib(datos2021[datos2021['momento_dia'] == 'Mid-day'], (0,1), 
                         var_x, x_label, y_label, 'Mid-day', bineo, paletaColor, 1, 0, xMax, 0, yMax)
plot_time_travel_distrib(datos2021[datos2021['momento_dia'] == 'Afternoon'], (0,2), 
                         var_x, x_label, y_label, 'Afternoon', bineo, paletaColor, 2, 0, xMax, 0, yMax)
plot_time_travel_distrib(datos2021[datos2021['momento_dia'] == 'Night'], (1,0), 
                         var_x, x_label, y_label, 'Night', bineo, paletaColor, 3, 0, xMax, 0, yMax)
plot_time_travel_distrib(datos2021[datos2021['momento_dia'] == 'Early morning'], (1,1), 
                         var_x, x_label, y_label, 'Early morning', bineo, paletaColor, 4, 0, xMax, 0, yMax)
fig.delaxes(axes[1,2]) #Delete last unused grid location
plt.savefig(os.path.join(dirSalida, 'time_travel_distrib.png'), dpi=300)



# Time travel per day of week or daytime
conteos_dia_semana = datos2021.groupby(['dia_semana'])['duracion_min'].describe()[['count', 'mean']].reset_index()
conteos_momento_dia= datos2021.groupby(['momento_dia'])['duracion_min'].describe()[['count', 'mean']].reset_index()
semana = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

fig, axes = plt.subplots(1,2, figsize=(10,5), squeeze=False)
fig.suptitle('Number of trips and mean time travel per weekday', size=14)
plt.tight_layout(pad=4)
sns.barplot(ax = axes[0,0], data = conteos_dia_semana, x='dia_semana', y = 'count', order = semana, palette = 'crest')
sns.barplot(ax = axes[0,1], data = conteos_dia_semana, x='dia_semana', y = 'mean', order = semana, palette = 'viridis')
axes[0,0].set(xlabel='',  ylabel='# Trips')
axes[0,1].set(xlabel='',  ylabel='Mean time travel (min)')
plt.savefig(os.path.join(dirSalida, 'time_travel_number_travel_per_weekday.png'), dpi=300)


#Total users per check-out time.
pivot1 = pd.pivot_table(datos2021, values="momento_dia",
                        index=pd.to_datetime(datos2021['fecha_de_inicio']).dt.weekday, 
               columns=pd.to_datetime(datos2021['fecha_de_inicio']).dt.hour, aggfunc = 'count',fill_value=0)

pivot2 = pd.pivot_table(datos2021, values="momento_dia",
                        index=pd.to_datetime(datos2021['fecha_de_inicio']).dt.hour, 
               columns=["dia_semana"], aggfunc = 'count',fill_value=0)


plt.figure(figsize=(15,10))
ax = sns.heatmap(pivot1, square=True, cmap='Spectral_r', linewidths=.1,cbar_kws={"shrink": .4})
plt.setp(ax.xaxis.get_majorticklabels(), rotation=360 )
ax.set_title("Number of check outs by hour and weekday")
ax.set_xlabel("Day hour", labelpad = 12)
ax.set_ylabel("Weekday")
labels = [item.get_text()+''+'h' for item in ax.get_xticklabels()]
ax.set_xticklabels(labels)
ax.set_yticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], rotation = 15)
plt.tight_layout(pad=2)
plt.savefig(os.path.join(dirSalida, 'heatmap_checkout.png'), dpi=300)




#%% 2) Spatial EDA


def plot_over_map(mapa, datosLongLat, variable, colorElegido, radioCirculo):
    ''' Function to plot variables over map'''
    for k in range(len(my_data)):
        marker = folium.CircleMarker(location=[datosLongLat['lat'].iloc[k], datosLongLat['long'].iloc[k]],
                                     radius= datosLongLat[variable].iloc[k] / radioCirculo,
                                     popup = datosLongLat['nombre_estacion_inicio'].iloc[k],
                                     color = colorElegido)
        marker.add_to(mapa)
     
    
 

# # Checkouts
mapa_folium = folium.Map(location=[-34.6083,  -58.3712], zoom_start = 10)# Loads the Buenos Aires' map with Folium.
plot_over_map(mapa_folium, my_data, 'n_usos', 'black', 2000)
mapa_folium.save(os.path.join(dirSalida, "map_mean_uses.html"))

# Trip duration
mapa_folium_duracion = folium.Map(location=[-34.6083,  -58.3712], zoom_start= 10)
plot_over_map(mapa_folium_duracion, my_data, 'duracion_media_min', 'blue', 5)
mapa_folium_duracion.save(os.path.join(dirSalida, "map_mean_duration.html"))


mapa_folium_distancia = folium.Map(location=[-34.6083,  -58.3712], zoom_start= 10)
plot_over_map(mapa_folium_distancia, my_data, 'dist_media_km', 'red', 0.5)
mapa_folium_distancia.save(os.path.join(dirSalida, "map_mean_distance.html"))


#Top 10 trips: joint in/out
topViajes = datos2021[['nombre_estacion_inicio', 'nombre_estacion_fin', 'long_salida', 'lat_salida', 'long_llegada', 'lat_llegada']].value_counts()[:10].reset_index()
mapa_folium_viajes = folium.Map(location=[-34.6083,  -58.3712], zoom_start= 10)

for i in range(len(topViajes)):
    point = [[topViajes['lat_llegada'].iloc[i], topViajes['long_llegada'].iloc[i]],
               [topViajes['lat_salida'].iloc[i], topViajes['long_salida'].iloc[i]] 
               ] 
    folium.PolyLine(point, color='blue', weight=5, opacity=0.8).add_to(mapa_folium_viajes)
    folium.Marker([topViajes['lat_llegada'].iloc[i], topViajes['long_llegada'].iloc[i]], popup="End", icon=folium.Icon(color="red",icon="fa-flag-checkered", prefix="fa"),opacity=0.5).add_to(mapa_folium_viajes)    
    folium.Marker([topViajes['lat_salida'].iloc[i], topViajes['long_salida'].iloc[i]], popup="Start", icon=folium.Icon(color="green",icon="fa-star", prefix="fa"),opacity=0.5).add_to(mapa_folium_viajes)    
mapa_folium_viajes.save(os.path.join(dirSalida, "map_top_trips.html"))




