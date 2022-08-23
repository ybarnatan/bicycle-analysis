

import os
import pandas as pd
import datetime 
import time
import easygui as eg
import numpy as np
from geopy.distance import geodesic  
np.set_printoptions(precision=15) #Setea la presicion con la que se trabajan los nros en numpy


#%% DATA WRANGLING
 
def fecha_hora(df):
    ''' Splitea la columna en dos: fecha y hora que en todos los df estan juntas como str'''
    fecha_hora = df['Fecha de inicio'].str.split(' ', expand=True)
    # Se almacena en un nuevo df
    fecha_hora.columns = ['Fecha','Hora']
    
    return fecha_hora


def obtener_dia_semana(fecha):
    '''Obtiene de la fecha el dia de la semana'''
    return datetime.datetime.strptime(fecha,'%Y-%m-%d').weekday()


def nombre_dia(df):
    '''Obtiene el nombre del dia en base al numero de dia de la semana.'''
    dia = df.replace({0:'lunes', 1:'martes', 2:'miercoles', 3:'jueves', 4:'viernes', 5:'sabado', 6:'domingo'})
    return dia


def momento_dia_fc(x):
    '''Momento del dia en terminos coloquiales'''
    if (x['hora_dia']>= '06:00:00') & (x['hora_dia']<= '12:00:00'):
        return '1.Mañana'
    
    if (x['hora_dia']>='12:00:00') & (x['hora_dia'] <= '14:00:00'):
        return '2.Mediodia'
    
    if (x['hora_dia']>='14:00:00') & (x['hora_dia'] <= '19:00:00'):
        return '3.Tarde'

    if (x['hora_dia']>'19:00:00') & (x['hora_dia'] <= '24:00:00'):
        return '4.Noche'
    
    if (x['hora_dia']>'00:00:00') & (x['hora_dia'] < '06:00:00'):
        return '5.Madrugada'

def eliminarStringsVacios(df):
    #Remove, if any, rows with empty strings.
    df = df.loc[df['long_llegada'] != '']
    df = df.loc[df['long_salida'] != '']
    df = df.loc[df['lat_llegada'] != '']
    df = df.loc[df['lat_salida'] != '']
    return df



#Select folder with required data and directories or type wd manually.
dirBase = eg.diropenbox(msg="Abrir directorio base", title="Control: diropenbox")

#Load the data bases, available at Gobierno de la Ciudad de Buenos Aires webpage.
datos2021 = pd.read_csv(os.path.join(dirBase, 'data', 'recorridos-realizados-2021.csv' ))
estaciones = pd.read_csv(os.path.join(dirBase, 'data', 'nuevas-estaciones-bicicletas-publicas.csv'))

#Drop unused columns
datos2021 = datos2021.drop(["Estado cerrado", "Modelo de bicicleta", "Tipo de ciclista", "Origen de viaje"], axis=1) 

#Check & treat NaNs, null values or empty cells (string, '').
datos2021.isna().sum().sum() # 6 NaNs
datos2021 = datos2021.dropna() 
datos2021.isnull().values.any() #No null values

# New variables with date and hour of day and then they may be added to the original data frame
tiempo2021 = fecha_hora(datos2021)
dia2021 = tiempo2021.Fecha.map(obtener_dia_semana)
datos2021['dia_semana'] = nombre_dia(dia2021)
datos2021['hora_dia'] = tiempo2021.Hora
momento_dia = datos2021.apply(lambda x: momento_dia_fc(x),1)
datos2021['momento_dia'] = momento_dia

#Rename column names for clarity
datos2021.columns = ['ID', 'duracion_segs', 'id_estacion_inicio', 'fecha_de_inicio',
                     'nombre_estacion_inicio', 'fecha_de_fin', 'id_estacion_fin',
                    'nombre_estacion_fin', "ID_ciclista", "dia_semana", "hora_dia",'momento_dia']
estaciones.columns = ['WKT', 'id_estacion', "codigo", 'nombre_estacion','ubicacion', 'tipo', 'horario', 'anclajes' ]


#Assign long, lat for arrivals and departures.
def getCoord(df):
    #Takes the coordinates columns of a data frame [df], which cells are strings, 
    #and splits it into two columns: lat and long.
    columna = df['WKT'].str.split(' ', expand=True)
    columna.columns=['Nada', 'long', 'lat']
    df['long'] = columna['long'].str.replace("(", "").astype(float)
    df['lat'] = columna['lat'].str.replace(")", "").astype(float)
    return df


estaciones = getCoord(estaciones)
distancias = datos2021.copy(deep=True)
distancias['long_salida'] = ''
distancias['lat_salida'] = ''
distancias['long_llegada'] = ''
distancias['lat_llegada'] = ''
for i in range(len(estaciones)):
    estacion = estaciones['nombre_estacion'].iloc[i]
    distancias.loc[distancias['nombre_estacion_inicio'] == estacion , 'long_salida'] = float(estaciones['long'].iloc[i])
    distancias.loc[distancias['nombre_estacion_inicio'] == estacion , 'lat_salida'] = float(estaciones['lat'].iloc[i])
    distancias.loc[distancias['nombre_estacion_fin'] == estacion, 'long_llegada'] = float(estaciones['long'].iloc[i])
    distancias.loc[distancias['nombre_estacion_fin'] == estacion, 'lat_llegada'] = float(estaciones['lat'].iloc[i])


distancias = eliminarStringsVacios(distancias)



def haversine_vectorize(df, Rearth=6367):
    '''Calculates the geodesic distance between two points using the haversine formulation.
    Returns the distance in km by default; else, must set a fifth parameter'''
    

    lon_1 = df['long_salida'].to_numpy().astype(float)
    lat_1 = df['lat_salida'].to_numpy().astype(float)
    lon_2 = df['long_llegada'].to_numpy().astype(float)
    lat_2 = df['lat_llegada'].to_numpy().astype(float)

    lon1, lat1, lon2, lat2 = map(np.radians, [lon_1, lat_1, lon_2, lat_2]) #np.deg2rad(180) = np.radians


    newlon = lon2 - lon1
    newlat = lat2 - lat1

    haver_formula = np.sin(newlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(newlon/2.0)**2

    dist = 2 * np.arcsin(np.sqrt(haver_formula))
    km = Rearth * dist #6367 for distance in KM; for miles use 3958
    return km

#Calculate distances.
distancias['dist_km'] =  haversine_vectorize(distancias)

#Discard instances where the station of departure and arrival were the same.
distancias =  distancias[distancias['dist_km'] > 0]
distancias['dist_km'] = distancias['dist_km'].astype(float) 

#Calculate duration of trip based on date of departure and arrival.
distancias['fecha_de_inicio'] = pd.to_datetime(distancias['fecha_de_inicio'], format='%Y-%m-%d %H:%M:%S')
distancias['fecha_de_fin'] = pd.to_datetime(distancias['fecha_de_fin'], format='%Y-%m-%d %H:%M:%S')
distancias['duracion_min'] = ( distancias['fecha_de_fin']- distancias['fecha_de_inicio']).dt.total_seconds()/60


 
#Prepare the final data frame to export for visualization.
variables_medias = distancias.groupby('nombre_estacion_inicio')[['duracion_min', 'dist_km']].mean().reset_index(drop=False)
n_usos = distancias.groupby('nombre_estacion_inicio').size().reset_index(drop=False).rename(columns={'nombre_estacion_inicio':'nombre', 0:'nro_usos'})
my_data  = pd.concat([variables_medias, n_usos], axis=1) 
my_data.columns = ['nombre_estacion_inicio', 'duracion_media_min', 'dist_media_km', 'nombre', 'n_usos']
my_data = my_data.drop(["nombre"], axis=1)  #Dropeo una col que esta repetida

#Add to the dataframe the location of the station, but not all of them are both arrival
# and departure ones. Erase those who are not.
len(my_data['nombre_estacion_inicio'].unique()) == len(estaciones['nombre_estacion'].unique())
estacionesDatos = set(my_data['nombre_estacion_inicio'].unique()) #set de estaciones en mi data frame
estacionesEstaciones = set(estaciones['nombre_estacion'].unique()) #set de estaciones en el csv "estaciones"
estacionesDeMas = list(set(estacionesDatos) - set(estacionesEstaciones))
my_data =  my_data[~my_data['nombre_estacion_inicio'].isin(estacionesDeMas)]
my_data['coordenadas'] = '' 

for i in range(len(estaciones)):
    for k in range(len(my_data)):
        if my_data['nombre_estacion_inicio'].iloc[k] == estaciones['nombre_estacion'].iloc[i]:
           my_data['coordenadas'].iloc[k] = estaciones["WKT"].iloc[i]

my_data['long'] = ''
my_data['lat'] = ''
for k in range(len(my_data)):
    punto =  my_data['coordenadas'].iloc[k].split(" ")
    my_data['long'].iloc[k] = float(punto[1].replace("(", ""))
    my_data['lat'].iloc[k] =  float(punto[2].replace(")", ""))


#Export .csv
my_data.to_csv(os.path.join(dirBase, 'data', 'dataForClusteringAnalysis.csv'), index=False)
distancias.to_csv(os.path.join(dirBase, 'data','dataForEDA.csv'), index=False)




