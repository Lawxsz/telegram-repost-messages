import requests
import json
from datetime import datetime, timedelta
from requests.exceptions import ConnectTimeout

TOKEN = ''
channel_id = -100  # group ID
message_counts = {}

users_id = []
admin_id = []

def load_users():
    with open('users.json', 'r') as file:
        data = json.load(file)
        users_id = data['users']
        admin_id = data['admin']
    return users_id, admin_id

def save_users(users_id, admin_id):
    users_data = {'users': users_id, 'admin': admin_id}
    with open('users.json', 'w') as file:
        json.dump(users_data, file)

def check_message_limit(user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    count = message_counts.get(today, {}).get(user_id, 0)
    return count < 2

def update_message_count(user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in message_counts:
        message_counts[today] = {}
    message_counts[today][user_id] = message_counts[today].get(user_id, 0) + 1

def process_message(message):
    user_id = message['from']['id']
    chat_id = message['chat']['id']
    if chat_id == user_id:
        authorized_users = users_id + admin_id
        if user_id in authorized_users:
            if check_message_limit(user_id):
                forward_message_to_private_channel(channel_id, message, chat_id)
                update_message_count(user_id)
                send_message(chat_id, 'Your message has been sent to the channel.')
            else:
                send_message(chat_id, 'Hey, you have exceeded the daily post limit. Please try again later')
        else:
            send_message(chat_id, '? You are not authorized to send messages to the bot.')
    else:
        process_group_message(message)

def process_group_message(message):
    pass

def process_command(command, message):
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    if command == '/add':
        if user_id in admin_id:
            if 'text' in message:
                command_parts = message['text'].split()
                if len(command_parts) >= 2:
                    add_user_id = command_parts[1]
                    if add_user_id.isdigit() and int(add_user_id) not in users_id:
                        users_id.append(int(add_user_id))
                        save_users(users_id, admin_id)
                        send_message(chat_id, f'? User ID {add_user_id} has been added to the list.')
                    else:
                        send_message(chat_id, '? Invalid user ID.')
                else:
                    send_message(chat_id, '? Invalid command format.')
            else:
                send_message(chat_id, '? Invalid command format.')
        else:
            send_message(chat_id, '? You are not authorized to use this command.')

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    try:
        response = requests.post(url, json=params, timeout=10)
        return response.json()
    except Exception as e:
        print('Timeout error while sending the message:', str(e))

def forward_message_to_private_channel(channel_id, message, chat_id):
    url = f'https://api.telegram.org/bot{TOKEN}/forwardMessage'
    from_chat_id = message['chat']['id']
    message_id = message['message_id']
    params = {'chat_id': channel_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
    try:
        response = requests.post(url, json=params, timeout=10)
        if response.status_code == 200:
            send_message(chat_id, 'Thanks for trusting us to bring you customers :)!')
        else:
            send_message(chat_id, '? Failed to forward the message to the private channel.')
        return response.json()
    except Exception as e:
        print('Timeout error while forwarding the message to the private channel:', str(e))

def get_updates(offset=None):
    url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    params = {'offset': offset}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print('Timeout error while getting updates:', str(e))

def process_updates(updates):
    if 'result' in updates:
        for update in updates['result']:
            if 'message' in update:
                message = update['message']
                process_message(message)
            update_id = update['update_id']
            offset = update_id + 1
            get_updates(offset)

users_id, admin_id = load_users()

initial_updates = get_updates()
process_updates(initial_updates)

while True:
    updates = get_updates()
    process_updates(updates)
