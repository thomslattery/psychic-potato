from asyncio import exceptions
import requests, json
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv('OKTA_TOKEN')
BASE_URL = os.getenv('OKTA_TENANT')
limit = 25
DOMAIN = os.getenv('DOMAIN_TO_DELETE')

url = f'https://{BASE_URL}/api/v1/users?limit={limit}'
search = 'profile.login ew "dynanest.com"'

payload={}
headers = {
  'Accept': 'application/json',
  'Content-Type': 'application/json',
  'Authorization': f'SSWS {API_TOKEN}'
}

response = requests.request("GET", url, headers=headers, data=payload)
users = []


def get_okta_user(user_id):
    url_user = f'https://{BASE_URL}/api/v1/users/{user_id}'
    resp = requests.request("GET", url_user, headers=headers, data=payload)
    # Raise an error 
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f'Error: {str(err)}')
        return None
    resp_json = resp.json()
    return resp_json

    
def delete_okta_user(user_id):
    user_profile = get_okta_user(user_id)
    if user_profile:
        user_name = f"{user_profile['profile']['firstName']} {user_profile['profile']['lastName']}"
        login_name = user_profile['profile']['login']
        print(f'Attempting to delete {user_name} ({login_name})')
        status = user_profile['status']
        if status != "DEPROVISIONED":
            url_deactivate = f'https://{BASE_URL}/api/v1/users/{user_id}/lifecycle/deactivate'
            resp_deact = requests.request("POST", url_deactivate, headers=headers, data=payload)
            try:
                resp_deact.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(f'Error: {str(err)}')
                return None
        url_delete = f'https://{BASE_URL}/api/v1/users/{user_id}'
        resp_delete = requests.request('DELETE', url_delete, headers=headers, data=payload)
        try:
            resp_delete.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f'Error: {str(err)}')
            return None
        print(f'Successfully deleted {user_name} ({login_name})')
        return

def users_to_list(api_response, user_list):
    users_json = api_response.json()
    for user in users_json:
        user_list.append({
            'id': user['id'],
            'login': user['profile']['login'],
            'firstName': user['profile']['firstName'],
            'lastName': user['profile']['lastName']
        })


while 'next' in response.links:
    url = response.links['next']['url']
    response = requests.request("GET", url, headers=headers, data=payload)
    users_to_list(response, users)

users_to_delete = []
for user in users:
    user_domain = user['login'].split('@')[1]
    if user_domain == DOMAIN:
        users_to_delete.append(user)

for user_to_delete in users_to_delete:
    user_id = user_to_delete['id']
    delete_okta_user(user_id)
