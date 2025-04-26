# Propósito del proyecto
- Necesitamos tener un reporte automático en el que ver los KPIs principales de las campañas y ver claramente los resultados de los tests que vamos haciendo.

# Proyecto ETL - reporting automatizado para campañas de Meta Ads
1. Extraer datos de coste e interacción con las campañas mediante la API de Meta 🧑🏼‍🔧
2. Extraer datos de ingresos y conversiones mediante la API del parnet de afiliados (Kissterra) 🧑🏼‍🔧
3. Plasmar datos en spreadsheet y csv 🧑🏼‍💻

_(hasta este punto lo hace el main.py, A PARTIR DE AQUÍ, TENDREMOS QUE VINCULAR LA SPREADSHEET CON LOOKER Y AUTOMATIZAR CON WINDOWS)_

4. Crear Dashboard mediante  Looker Studio 🧑🏼‍🎨 
5. Automatizar actualización de datos (recogida diaria de datos) 🧙🏼‍♂️

# Requisitos previos:

**(META):**

✅ Una cuenta de Meta Business Manager

✅ Acceso a una cuenta publicitaria con campañas activas

✅ Crear una app en Meta for Developers
(https://developers.facebook.com/tools/explorer/)

✅ Obtener:

- Access Token corto (1h de duración)

- Ad Account ID (act_XXXXXXXXX)

- (Opcional) App ID y App Secret


**(PARTNER DE AFILIADOS: KISSTERRA):**
(en tu caso, tendrás que adaptar la parte del código de la API del partner a la API de tu propio partner)

✅ Tener un acuerdo de partnership con Kissterra

✅ Un Affiliate ID 
_(proporcionado por el partner)_

✅ Una API Key de afiliado 
_(proporcionado por el partner)_


**(GOOGLE SHEETS):**

✅ Habilitamos la API de Google Sheets
- 1. Abrimos [Google Cloud Console](https://console.cloud.google.com/)
- 2. Habilitamos la Google Sheets API para tu proyecto.
- 3. Creamos credenciales tipo Cuenta de servicio.
- 4. Descargamos el archivo .json y lo guardamos como service_account.json
- 5. Compartimos la Google Sheet con: 'tu-cuenta-servicio'@'proyecto'.iam.gserviceaccount.com


# ▶️ Instrucciones para ejecutar el código
1. (**INSTALA REQUERIMIENTOS**) Ejecuta este código en tu terminal con tu **entorno conda** activado: 
conda env create -f environment.yml
2. (**AÑADE TUS IDS Y CREDENCIALES**) Añade tus tokens, credenciales, ids, etc. en el archivo ".env"
    (Meta) short_lived_token, app_id, app_secret, ad_account_ids 
    (Partner) api_key, network_id
    (Google Sheets) SPREADSHEET_ID, RANGE, SERVICE_ACCOUNT_FILE
3. (**EJECUTAR PYTHON**) Ejecuta el archivo main.py.


--> /gifs/main.py.gif

**IMPORTANTE: El código no funcionará si no añades los requisitos especificados anteriormente**


## Explicación paso a paso (instrucciones técnicas)
### 1. 🧑🏼‍🔧 Extraer datos mediante la API de Meta


🔍 Campos necesarios:

- Fecha ['date_start']
- Inversión ['spend']
- Impresiones ['impressions']
- Clics ['clicks']

#### Paso 1: Instalar el SDK de Meta en Python
    pip install facebook-business

#### Paso 2: Conectar con la API y Extrae Datos

    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights

    # Tus credenciales
    access_token = 'TU_ACCESS_TOKEN_CORTO'
    ad_account_id = 'act_XXXXXXXXXXXX'
    app_id = 'TU_APP_ID'
    app_secret = 'TU_APP_SECRET'

    # Inicializar API
    FacebookAdsApi.init(app_id, app_secret, access_token)

    # Define campos y nivel de agregación
    fields = [
        'campaign_name',
        'spend',
        'impressions',
        'clicks',
        'actions',
        'date_start',
        'date_stop'
    ]

    params = {
        'level': 'campaign',
        'date_preset': 'last_7d',
        'time_increment': 1
    }

    # Extraer datos
    ads = AdAccount(ad_account_id).get_insights(fields=fields, params=params)

    # Convertir a lista de diccionarios
    data = [ad.export_all_data() for ad in ads]

    # Mostrar un ejemplo
    import pandas as pd
    df = pd.DataFrame(data)
    print(df.head())

#### Paso 3: Intercambiar Access Token corto por uno de largo plazo

    import requests

    # ⚠️ Reemplaza con tus credenciales y el token corto obtenido
    app_id = 'TU_APP_ID'
    app_secret = 'TU_APP_SECRET'
    short_lived_token = 'ACCESS_TOKEN_CORTO'

    def get_long_lived_token(app_id, app_secret, short_token):
        url = 'https://graph.facebook.com/v19.0/oauth/access_token'
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': short_token
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data

    token_data = get_long_lived_token(app_id, app_secret, short_lived_token)

    print("🎟️ Access Token largo plazo:", token_data.get('access_token'))
    print("⌛ Expires in:", token_data.get('expires_in'), "seconds")

### 2. 🧑🏼‍🔧 Extraer datos mediante la API del partner de afiliados (Kissterra)
Requisitos previos:


🔍 Campos necesarios:

- Fecha ['start_date']
- Ingresos ['payout']
- Conversiones ['conversions']
- Clickout ['clickout']


#### Paso 1: Petición para obtener datos

    import requests
    import pandas as pd

    API_KEY = 'TU_API_KEY'  # proporcionado por Kissterra
    network_id = 'kissterra'  # o el que te hayan dado

    url = f'https://{network_id}.go2cloud.org/api/affiliate/stats.json'

    params = {
        'api_key': API_KEY,
        'start_date': '2024-03-01',
        'end_date': '2024-03-31',
        'group_by': 'date',
        'fields': 'date,revenue,clicks,conversions,payout',
        'limit': 1000
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Convertir a DataFrame
    df = pd.DataFrame(data['data']['stats'])
    print(df.head())




### 5. 🧙🏼‍♂️ Automatizar actualización de datos (recogida diaria de datos) 

#### Paso 1: Automatizar la extracción y transformación de datos

##### Usando el Programador de Tareas (Interfaz Gráfica)

1. Abrir el Programador de Tareas:

- Presiona Win+R, escribe taskschd.msc y pulsa Enter, o búscalo en el menú de inicio.

2. Crear una nueva tarea básica:

- En el panel derecho, selecciona Crear tarea básica….

- Dale un nombre (por ejemplo, "Ejecutar main.py") y, si lo deseas, una descripción.

3. Configurar el disparador (trigger):

- Elige la opción Diariamente.

- Establece la hora de inicio a las 9:00 a.m. y configura la recurrencia según necesites.

4. Definir la acción:

- Selecciona Iniciar un programa.

- En el campo Programa/script, debes indicar la ruta al ejecutable de Python. Por ejemplo:

    C:\Python312\python.exe
_(Asegúrate de poner la ruta correcta a tu instalación de Python.)_

En Agregar argumentos (opcional):, coloca la ruta completa de tu script. Por ejemplo:

swift
Copiar
"C:\Users\David\OneDrive\Escritorio\DATA SCIENCE - Evolve Academy\01. PROYECTO ETL\data_extraction.py"
En Iniciar en (opcional): puedes colocar el directorio donde se encuentra el script:

makefile
Copiar
C:\Users\David\OneDrive\Escritorio\DATA SCIENCE - Evolve Academy\01. PROYECTO ETL
Finalizar y probar:

Revisa la configuración y haz clic en Finalizar.

Para probar la tarea, selecciónala en el Programador de Tareas, haz clic derecho y elige Ejecutar. Comprueba que se ejecute correctamente.

#### Paso 2: Enviamos datos a una Spreadsheet de Google

Según la documentación oficial de Google Sheets API v4, vía la librería oficial (google-api-python-client), seguiremos los siguientes pasos:

2. Habilitamos la API de Google Sheets
- 1. Abrimos [Google Cloud Console](https://console.cloud.google.com/)
- 2. Habilitamo la Google Sheets API para tu proyecto.
- 3. Creamos credenciales tipo Cuenta de servicio.
- 4. Descargamos el archivo .json y lo guardamos como service_account.json
- 5. Compartimos la Google Sheet con: 'tu-cuenta-servicio'@'proyecto'.iam.gserviceaccount.com

3. Ya podemos proceder con el código (_tendremos que cambiar TU_SPREADSHEET_ID por el id de la spreadsheet, que la encontramos en la URL y revisar que el nombre de la "Hoja 1" aparezca tal cual, a veces puede ir todo junto "Hoja1" o aparecer en inglés):


####
    import pandas as pd
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    # === CONFIGURACIÓN ===
    SPREADSHEET_ID = 'TU_SPREADSHEET_ID'  # lo obtienes de la URL de la hoja
    RANGE = 'Hoja 1!A1'  # celda de inicio para escribir
    SERVICE_ACCOUNT_FILE = 'service_account.json'

    # === AUTENTICACIÓN ===
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # === INICIAR SERVICIO ===
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    # === CONVERTIR df a lista de listas ===
    values = [df.columns.tolist()] + df.values.tolist()

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





#### Paso 3: Recogemos datos desde Looker Studio (y dejamos reporte automatizado)
https://lookerstudio.google.com/reporting/39645a08-5ffa-4af4-a58a-e5701ff7c09b
