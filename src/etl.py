# Meta Token
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

