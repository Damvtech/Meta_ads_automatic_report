import pandas as pd

import requests
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from datetime import date
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import time
import os
from dotenv import load_dotenv

import src.etl as etl
import src.eda as eda


# 1. Carga el .env situado en el mismo directorio donde se ejecuta main.py
load_dotenv() 

# DATA FROM META

# ⚠️ Reemplaza con tus credenciales y el token corto obtenido
short_lived_token = os.getenv('meta_short_lived_token')  # token a corto plazo
app_id = os.getenv('meta_app_id')  # ID de la aplicación
app_secret = os.getenv('meta_app_secret')  # solo si usarás token a largo plazo

token_data = etl.get_long_lived_token(app_id, app_secret, short_lived_token)
access_token = token_data.get('access_token')

print("🎟️ Access Token largo plazo:", access_token)
print("⌛ Expires in:", access_token, "seconds")

# Inicializar API
FacebookAdsApi.init(app_id, app_secret, access_token)

# Lista de cuentas publicitarias
ad_account_ids = os.getenv('meta_ad_account_ids')

# Campos e insights a consultar
fields = [
    'spend',
    'impressions',
    'clicks',
    'date_start'
]

# Fechas
start_date = '2025-02-13'
end_date = date.today().strftime('%Y-%m-%d')

# Parámetros
params = {
    'level': 'campaign',
    'time_increment': 1,
    'time_range': {
        'since': start_date,
        'until': end_date
    }
}

# Acumular resultados de todas las cuentas
all_data = []

for ad_account_id in ad_account_ids:
    print(f"📊 Consultando cuenta: {ad_account_id}")
    ads = AdAccount(ad_account_id).get_insights(fields=fields, params=params)
    data = [ad.export_all_data() for ad in ads]
    for entry in data:
        entry['ad_account_id'] = ad_account_id  # Agrega columna identificadora
    all_data.extend(data)

# Convertir todo a DataFrame
df_meta = pd.DataFrame(all_data)

path_csv_meta_raw = 'data/raw/meta_report.csv'
print(f'💾... Downloading raw Meta dataset to {path_csv_meta_raw}')
df_meta.to_csv(path_csv_meta_raw)

# LIMPIEZA Y TRANSFORMACIÓN

# Ordenamos por fecha
df_meta.sort_values(by='date_start', ascending=True, inplace=True)
# Renombramos columnas y eliminamos duplicada
df_meta.rename(columns={'date_start':'date'}, inplace = True)
# Adaptamos los tipos de dato
df_meta['spend'] = df_meta['spend'].astype(float).round(2)
df_meta['impressions'] = df_meta['impressions'].astype(int)
df_meta['clicks'] = df_meta['clicks'].astype(int)
# Reorganizamos las columnas
df_meta = df_meta[['date','spend','impressions','clicks']]
# reemplaza NaN por cadenas vacías
df_meta = df_meta.fillna("")
# Agrupamos por fecha (una fila por día)
df_meta = df_meta.groupby('date')[['spend','impressions','clicks']].sum()#.reset_index(inplace=True)

# Descargar el dataset
path_csv_meta_processed = 'data/processed/meta_daily_report.csv'
print(f'💾... Downloading processed Meta dataset to {path_csv_meta_processed}')
df_meta.to_csv(path_csv_meta_processed)

# EDA
eda.descriptive_info(df_meta)



# DATA FROM THE AFFILIATE PARTNER (KISSTERRA)

api_key = os.getenv('partner_api_key')
network_id = os.getenv('partner_network_id')
url_dia = f'https://{network_id}.api.hasoffers.com/Apiv3/json?api_key={api_key}&Target=Affiliate_Report&Method=getConversions&fields[]=Stat.sale_amount&fields[]=Stat.count_approved&fields[]=Stat.date&fields[]=Stat.currency&fields[]=Stat.approved_payout&filters[Stat.date][conditional]=GREATER_THAN_OR_EQUAL_TO&filters[Stat.date][values]=2025-02-13&sort[Stat.date]=asc&limit=1000000&totals=0&count=1'
url_hora = f'https://{network_id}.api.hasoffers.com/Apiv3/json?api_key={api_key}&Target=Affiliate_Report&Method=getConversions&fields[]=Stat.date&fields[]=Stat.hour&fields[]=Stat.sale_amount&fields[]=Stat.count_approved&fields[]=Stat.currency&fields[]=Stat.approved_payout&filters[Stat.date][conditional]=GREATER_THAN_OR_EQUAL_TO&filters[Stat.date][values]=2025-02-13&sort[Stat.date]=asc&limit=1000000&totals=0&count=1'
url_clics_dia = f'https://{network_id}.api.hasoffers.com/Apiv3/json?api_key={api_key}&Target=Affiliate_Report&Method=getStats&fields[]=Stat.date&fields[]=Stat.clicks&filters[Stat.date][conditional]=GREATER_THAN_OR_EQUAL_TO&filters[Stat.date][values]=2025-02-13'


# Hacemos la request a la API Rest
res_dia = requests.get(url_dia) # request por día
res_clics_dia = requests.get(url_clics_dia) # request por día
res_hora = requests.get(url_hora) # request por hora


if res_dia.status_code == 200:
    # Pasamos la request a formato json y desanidamos hasta llegar a coger el diccionario desde el que podremos desgranar las columnas y sus valores
    data = res_dia.json()['response']['data']['data']
    # Creamos una lista de diccionarios con los pares columna:valor
    dataset = []
    for i in data:
        # Accedemos correctamente a las claves del diccionario anidado
        dataset.append(i['Stat'])
    
    # Pasar dataset a formato datafram
    df = pd.DataFrame(dataset)

    # Descargar el dataset
    path_csv_convs_raw= 'data/raw/partner_convs_report.csv'
    print(f'💾... Downloading raw conversions dataset to {path_csv_convs_raw}')
    df.to_csv(path_csv_convs_raw)
    
    # LIMPIEZA Y PROCESAMIENTO DE DATOS
    # Ordemanos datos
    df.sort_values(by='date', ascending=False)
    # Renombramos columnas y eliminamos duplicada
    df.rename(columns={'count_approved':'conversions'}, inplace = True)
    df.rename(columns={'approved_payout':'revenue'}, inplace = True)
    df.drop(columns='approved_payout@USD', inplace=True)
    # Adaptamos los tipos de dato
    df['revenue'] = df['revenue'].astype(float).round(2).astype(int)
    df['conversions'] = df['conversions'].astype(int)
    # Reorganizamos las columnas
    df_performance = df[['date','conversions','revenue','currency']]
    

else:
    print("❌ Error: ", response.status_code, response.text)


if res_clics_dia.status_code == 200:
    # Pasamos la request a formato json y desanidamos hasta llegar a coger el diccionario desde el que podremos desgranar las columnas y sus valores
    data = res_clics_dia.json()['response']['data']['data']
    # Creamos una lista de diccionarios con los pares columna:valor
    dataset = []
    for i in data:
        # Accedemos correctamente a las claves del diccionario anidado
        dataset.append(i['Stat'])
    
    # Pasar dataset a formato datafram
    df_clicks = pd.DataFrame(dataset)

    # Descargar el dataset
    path_csv_clicks_raw= 'data/raw/partner_clics_report.csv'
    print(f'💾... Downloading raw conversions dataset to {path_csv_clicks_raw}')
    df.to_csv(path_csv_clicks_raw)

    # LIMPIEZA Y PROCESAMIENTO DE DATOS
    # Renombramos columna clicks
    df_clicks.rename(columns={'clicks':'clickouts'}, inplace = True)
    # Adaptamos tipo de dato
    df_clicks['clickouts'] = df_clicks['clickouts'].astype(int)
    # Ordemanos datos
    df_clicks.sort_values(by='date', ascending=False, inplace = True)
    

else:
    print("❌ Error: ", response.status_code, response.text)


# Añadimos a la tabla de performance, la tabla de clics
df_partner = df_performance.merge(df_clicks, on='date', how='left')

# Descargar el dataset
path_csv_partner= 'data/processed/partner_report.csv'
print(f'💾... Downloading processed partner dataset to {path_csv_partner}')
df_partner.to_csv(path_csv_partner)

# EDA
eda.descriptive_info(df_partner)



# JOIN BOTH TABLES

# Juntamos los datasets de meta y de nuestro partner
df_report = df_meta.merge(df_partner,on='date',how='left')

# Descargar el dataset
path_csv_daily_report= 'data/processed/daily_report.csv'
print(f'💾... Downloading processed report dataset to {path_csv_daily_report}')
df_report.to_csv(path_csv_daily_report)

# EDA
eda.descriptive_info(df_report)



# LOAD DATA TO A GOOGLE SPREADSHEET ONLINE

# === CONFIGURACIÓN ===
SPREADSHEET_ID = os.getenv('google_SPREADSHEET_ID')  # lo obtienes de la URL de la hoja
RANGE = os.getenv('google_range')  # celda de inicio para escribir
SERVICE_ACCOUNT_FILE = os.getenv('google_service_account_json')

# === AUTENTICACIÓN ===
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# === INICIAR SERVICIO ===
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# === CONVERTIR df_report a lista de listas ===
values = [df_report.columns.tolist()] + df_report.values.tolist()

# === ESCRIBIR LOS DATOS ===
request_body = {
    'values': values
}

response = sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE,
    valueInputOption='RAW',
    body=request_body
).execute()

print(f"✅ {response.get('updatedCells')} celdas actualizadas en Google Sheets.")