import configparser
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

# Read configuration
config = configparser.RawConfigParser()
config.read('config.ini')
ip = config.get('server', 'ip')
start_port = config.getint('server', 'start_port')
num_ports = config.getint('server', 'num_ports')
password_consistent = config.getboolean('server', 'password_consistent')
default_password = config.get('server', 'password', fallback=None)
balanceThreshold = config.getint('server', 'balanceThreshold', fallback=5)
collectAddress = config.get('server', 'collectAddress', fallback=None)

# Define headers
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Pragma': 'no-cache',
    'Proxy-Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}


# Function to make a GET request and extract CSRF token and cookies
def make_request(ip, port):
    url = f'http://{ip}:{port}/'
    print(f'Making GET request to {url}')
    response = requests.get(url, headers=headers, verify=False, allow_redirects=False)

    if response.status_code == 302:
        redirect_url = response.headers['Location']
        print(f'Received 302 redirect to {redirect_url}')
        parsed_url = urlparse(redirect_url)
        next_param = parse_qs(parsed_url.query).get('next', [None])[0]
        if next_param:
            print(f'Unlocking with next parameter: {next_param}')
            csrf_token, cookies = unlock_request(ip, port, next_param)
            return csrf_token, cookies
    elif response.status_code == 200:
        if response.content:
            # Parse the HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token_tag = soup.find('input', {'id': 'csrf_token'})
            if csrf_token_tag:
                csrf_token = csrf_token_tag['value']
            else:
                raise ValueError('CSRF token not found in the response')
            cookies = response.cookies.get_dict()

            print(f'Extracted CSRF Token: {csrf_token}')
            print(f'Extracted Cookies: {cookies}')

            return csrf_token, cookies
        else:
            raise ValueError('Empty response content')
    else:
        raise ValueError(f'Unexpected status code: {response.status_code}')


# Function to make an unlock request
def unlock_request(ip, port, next_param):
    unlock_url = f'http://{ip}:{port}/unlock'
    password = config.get('passwords', str(port), fallback=default_password)
    unlock_data = {
        'passphrase': password,
        'next': next_param,
        'unlock': 'Submit'
    }
    unlock_headers = headers.copy()
    unlock_headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'http://{ip}:{port}',
        'Referer': f'http://{ip}:{port}/unlock?next={next_param}'
    })
    print(f'Making unlock request to {unlock_url} with next parameter: {next_param}')
    response = requests.post(f'{unlock_url}?next={next_param}', headers=unlock_headers, data=unlock_data, verify=False)
    print('Unlock request completed')

    if response.status_code == 200:
        # redirect_url = response.headers['Location']
        # print(f'Received 302 redirect to {redirect_url}')
        # response = requests.get(redirect_url, headers=headers, verify=False)
        if response.content:
            # Parse the HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token_tag = soup.find('input', {'id': 'csrf_token'})
            if csrf_token_tag:
                csrf_token = csrf_token_tag['value']
            else:
                raise ValueError('CSRF token not found in the response')
            cookies = response.cookies.get_dict()

            print(f'Extracted CSRF Token after unlock: {csrf_token}')
            print(f'Extracted Cookies after unlock: {cookies}')

            return csrf_token, cookies
        else:
            raise ValueError('Empty response content after unlock')
    elif response.status_code == 200:
        if response.content:
            # Parse the HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token_tag = soup.find('input', {'id': 'csrf_token'})
            if csrf_token_tag:
                csrf_token = csrf_token_tag['value']
            else:
                raise ValueError('CSRF token not found in the response')
            cookies = response.cookies.get_dict()

            print(f'Extracted CSRF Token after unlock: {csrf_token}')
            print(f'Extracted Cookies after unlock: {cookies}')

            return csrf_token, cookies
        else:
            raise ValueError('Empty response content after unlock')
    else:
        raise ValueError(f'Unexpected status code after unlock: {response.status_code}')


# Function to make a POST request to the /vault endpoint
def post_to_vault(ip, port, csrf_token, cookies, password):
    url = f'http://{ip}:{port}/vault'
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': f'session={cookies["session"]}',
        'Origin': f'http://{ip}:{port}',
        'Referer': f'http://{ip}:{port}/vault'
    })
    data = {
        'csrf_token': csrf_token,
        'password': password,
        'submit': 'Create Vault'
    }
    print(f'Making POST request to {url}')
    response = requests.post(url, headers=headers, data=data, verify=False)
    print('POST request completed')
    return response.content


# Function to make a POST request to the /vault endpoint
def post_to_dashboard(ip, port, csrf_token, cookies, password):
    url = f'http://{ip}:{port}/dashboard'
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': f'session={cookies["session"]}',
        'Origin': f'http://{ip}:{port}',
        'Referer': f'http://{ip}:{port}/dashboard'
    })

    print(f'Making POST request to {url}')
    response = requests.get(url, headers=headers, verify=False)
    print('POST request completed')
    return response.content


def post_to_wallet(ip, port, csrf_token, cookies, password):
    url = f'http://{ip}:{port}/wallet/main'
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': f'session={cookies["session"]}',
        'Origin': f'http://{ip}:{port}',
        'Referer': f'http://{ip}:{port}/wallet/main'
    })

    print(f'Making POST request to {url}')
    response = requests.get(url, headers=headers, verify=False)
    print('POST request completed')
    return response.content


# Function to extract balance from the HTML response
def extract_balance(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    balance = None
    for h4 in soup.find_all('h4', {'class': 'mb-0'}):
        try:
            balance_value = float(h4.text.strip())
            balance = balance_value
            break
        except ValueError:
            continue
    return balance


def send_to_collect_from_wallet(ip, port, csrf_token, cookies, password):
    url = f'http://{ip}:{port}/send_satori_transaction_from_wallet/main'
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': f'session={cookies["session"]}',
        'Origin': f'http://{ip}:{port}',
        'Referer': f'http://{ip}:{port}/wallet/main'
    })
    data = {
        'csrf_token': csrf_token,
        'address': collectAddress,
        'amount': 0.00000000,
        'sweep': 'y',
        'submit': 'Send'
    }
    print(f'Making POST request to {url} to send balance to collection address')
    response = requests.post(url, headers=headers, data=data, verify=False)
    print('POST request to send balance completed')
    return response.content


def send_to_collect_from_vault(ip, port, csrf_token, cookies, password):
    url = f'http://{ip}:{port}/send_satori_transaction_from_vault/main'
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': f'session={cookies["session"]}',
        'Origin': f'http://{ip}:{port}',
        'Referer': f'http://{ip}:{port}/vault'
    })
    data = {
        'csrf_token': csrf_token,
        'csrf_token': csrf_token,
        'address': collectAddress,
        'amount': 0.00000000,
        'sweep': 'y',
        'submit': 'Send'
    }
    print(f'Making POST request to {url} to send balance to collection address')
    response = requests.post(url, headers=headers, data=data, verify=False)
    print('POST request to send balance completed')
    return response.content


def collect_balance(ip, port, csrf_token, cookies, password):
    wallet_content = post_to_wallet(ip, port, csrf_token, cookies, password)
    wallet_balance = extract_balance(wallet_content)
    if wallet_balance is not None and wallet_balance > 0:
        print(f'【Wallet Balance from {ip}:{port}: {wallet_balance}】 - 从钱包归集余额')
        send_to_collect_from_wallet(ip, port, csrf_token, cookies, password)
        return port, wallet_balance, True
    else:
        print(f'【Wallet Balance from {ip}:{port}: {wallet_balance}】 - 钱包中无余额')

    vault_content = post_to_vault(ip, port, csrf_token, cookies, password)
    vault_balance = extract_balance(vault_content)
    if vault_balance is not None and vault_balance > 0:
        print(f'【Vault Balance from {ip}:{port}: {vault_balance}】 - 从保险库归集余额')
        send_to_collect_from_vault(ip, port, csrf_token, cookies, password)
        return port, vault_balance, True
    else:
        print(f'【Vault Balance from {ip}:{port}: {vault_balance}】 - 保险库中无余额')


# Worker function to process a single port
def process_port(port):
    try:
        if password_consistent:
            password = default_password
        else:
            password = config.get('passwords', str(port), fallback=default_password)
        print(f'Processing {ip}:{port} with password: {password}')
        csrf_token, cookies = make_request(ip, port)
        html_content = post_to_dashboard(ip, port, csrf_token, cookies, password)
        balance = extract_balance(html_content)
        if balance is not None and balance > 0:
            if balance >= balanceThreshold:
                print(f'【Balance from {ip}:{port}: {balance}】 - 不归集')
                return port, balance, False
            else:
                print(f'【Balance from {ip}:{port}: {balance}】 - 归集')
                collect_balance(ip, port, csrf_token, cookies, password)
                return port, balance, True
    except Exception as e:
        print(f'Error processing {ip}:{port} - {e}')
    return port, 0, False


# Main script to use threading for processing ports
total_balance = 0
balances = []
print('Starting balance extraction process...')
if collectAddress is None or collectAddress == '':
    print(f'归集地址未设置，不进行归集')
else:
    print(f'归集地址为{collectAddress}')
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_port, start_port + i) for i in range(num_ports)]
        for future in futures:
            port, balance, isCollect = future.result()
            balances.append((port, balance, isCollect))
            total_balance += balance

print('===============================')
print('Balances from each port:')
for port, balance, isCollect in balances:
    print(f'Port {port}: Balance {balance} - 是否归集 {isCollect}')

print(f'Total Balance: {total_balance}')
