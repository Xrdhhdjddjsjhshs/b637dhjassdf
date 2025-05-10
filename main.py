from telethon import TelegramClient
from quart import Quart, jsonify, request
from colorama import Fore, init
import json, os, asyncio, nest_asyncio

init()
nest_asyncio.apply()

sending = False
cooldown_send = 0
text_send = ''

# Check if config.txt exists, if not create it or prompt for credentials
config_file = 'config.txt'
if not os.path.exists(config_file):
    print(f'{Fore.LIGHTYELLOW_EX}Конфиг не найден. Давайте создадим новый config.txt{Fore.RESET}')
    api_id = input(f'{Fore.LIGHTCYAN_EX}Введите API_ID: {Fore.RESET}')
    api_hash = input(f'{Fore.LIGHTCYAN_EX}Введите API_HASH: {Fore.RESET}')
    
    config = {
        "API_ID": api_id,
        "API_HASH": api_hash
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    print(f'{Fore.LIGHTGREEN_EX}Config.txt создан успешно{Fore.RESET}')

# Read config
with open(config_file, 'r') as f: 
    content = f.read()
    try: 
        config = json.loads(content)
        print(f'{Fore.LIGHTGREEN_EX}Конфиг загружен.{Fore.RESET}')
        
        # Verify if API_ID and API_HASH are present and not empty
        if not config.get('API_ID') or not config.get('API_HASH'):
            print(f'{Fore.LIGHTRED_EX}Ошибка: API_ID или API_HASH пусты в config.txt{Fore.RESET}')
            api_id = input(f'{Fore.LIGHTCYAN_EX}Введите API_ID: {Fore.RESET}')
            api_hash = input(f'{Fore.LIGHTCYAN_EX}Введите API_HASH: {Fore.RESET}')
            
            config['API_ID'] = api_id
            config['API_HASH'] = api_hash
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f'{Fore.LIGHTGREEN_EX}Config.txt обновлен{Fore.RESET}')
            
    except Exception as e: 
        input(f'{Fore.LIGHTRED_EX}Ошибка: не удалось запарсить конфиг: {Fore.RESET}{e}')
        os._exit(0)

client = TelegramClient('shizwbot', config['API_ID'], config['API_HASH'], device_model="iPhone 16 Pro", system_version="IOS 18.1")

async def get_groups():
    groups = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            groups.append([dialog.title, dialog.id])
    return groups

async def send_messages_handler(data):
    global sending, cooldown_send, text_send
    text_send = data['text']
    sending = True
    cooldown_send = data['cooldown']
    print(data)
    for group in data['groups']: 
        if not sending: break
        try: 
            await client.send_message(int(group['id']), data['text'], parse_mode='HTML')
            print('Отправлено сообщение')
        except Exception as e: print(e)
        await asyncio.sleep(int(data['cooldown']))
    sending = False
    return {'success': True}

app = Quart(__name__)

@app.before_serving
async def startup():
    await client.start() 
    print(f'{Fore.LIGHTGREEN_EX}Успешный вход в сессию.{Fore.RESET}')

@app.after_serving
async def cleanup():
    await client.disconnect()
    
@app.route("/")
async def panel():
    with open('index.html', encoding='utf8') as f: return f.read()

@app.route("/stop_sending")
async def stop_sending():
    global sending
    sending = False
    return {'success': True}

@app.route("/get_info")
async def get_info():
    global sending, cooldown_send, text_send
    return jsonify({
        'cooldown': cooldown_send,
        'sending': sending,
        'text': text_send
    })

@app.route("/get_groups")
async def send_groups():
    groups = await get_groups()
    return jsonify(groups)

@app.route("/send_messages", methods=['POST'])
async def send_messages():
    data = json.loads(await request.get_data(as_text=True))
    r = await send_messages_handler(data)
    return r

async def main():
    print(f'{Fore.LIGHTGREEN_EX}Запускаем панель... Ссылка для входа: {Fore.LIGHTYELLOW_EX}http://127.0.0.1:1337{Fore.RESET}')
    await app.run(port=1337, debug=False)

asyncio.run(main())
