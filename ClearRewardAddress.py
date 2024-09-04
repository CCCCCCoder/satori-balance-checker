import requests
import configparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor


# Read configuration
config = configparser.RawConfigParser()
config.read('config.ini')
ip = config.get('server', 'ip')
start_port = config.getint('server', 'start_port')
num_ports = config.getint('server', 'num_ports')
password_consistent = config.getboolean('server', 'password_consistent')
default_password = config.get('server', 'password', fallback=None)
reward_address = config.get('server', 'rewardAddress', fallback=None)

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
def post_to_vault(ip, port, csrf_token, cookies, password, reward_address):
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
    # Call the new function to mine to address

    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')
    reward_address_self = soup.find('div', {'id': 'walletAddress'}).text.strip()
    mine_to_address(ip, port, cookies, reward_address_self)
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

def mine_to_address(ip, port, cookies, reward_address):
    url = f'http://{ip}:{port}/mine/to/address/{reward_address}'
    mine_headers = headers.copy()
    mine_headers.update({
        'Accept': '*/*',
        'Referer': f'http://{ip}:{port}/vault',
        'Cookie': f'session={cookies["session"]}'
    })
    print(f'Making request to {url}')
    response = requests.get(url, headers=mine_headers, verify=False)
    print(f'[config reward address] port {port} result: {response.content}')
    return response.content

# Loop through a range of port numbers and make requests
def process_port(port):
    print(f'正在查询端口 {port}')
    try:
        if password_consistent:
            password = default_password
        else:
            password = config.get('passwords', str(port), fallback=default_password)
        print(f'Processing {ip}:{port} with password: {password}')
        csrf_token, cookies = make_request(ip, port)

        html_content = post_to_vault(ip, port, csrf_token, cookies, password, reward_address)
        # balance = extract_balance(html_content)
        # if balance is not None:
        #     print(f'【Balance from {ip}:{port}: {balance}】')
        #     total_balance += balance
        return port
    except Exception as e:
        print(f'Error processing {ip}:{port} - {e}')

print('Starting balance extraction process...')
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_port, start_port + i) for i in range(num_ports)]
    for future in futures:
        port = future.result()

print(f'批量修改奖励地址完成')