import os
import json
import datetime
import base64
from multiprocessing import Lock
from multiprocessing.managers import AcquirerProxy, BaseManager, DictProxy

from flask import Flask, render_template, send_file, jsonify, request
import pytz

aus = pytz.timezone('Australia/Sydney')

challenges = {
    "osint": {
        "title": "Where was I taken?",
        "desc": "I spy with my little eye... a world far down below. Name from whence the lens nigh, then the flag you seek you know.\n\nThe flag is in all caps separated by underscores, e.g. DOM_CTF{CENTRAL_STATION}. <a href='http://ctf.wolfdragon.me:5000/resources/osint.jpg' download>Resources</a>",
        "answer": "MERITON_SUITE_WORLD_TOWER"
    },
    "bufferformat": {
        "title": "One won't bring you far enough...",
        "desc": "You've seen buffer overflows vulnerabilities, you've seen format strings vulnerabilities, but have you needed both?\n\nLocated at <code>nc ctf.wolfdragon.me 62401</code> is the answer you seek, exploring the binary locally first from <a href='http://ctf.wolfdragon.me:5000/resources/bufferformat' download>resources</a> is highly recommended!",
        "answer": "TRAILBLAZED_THE_DOUBLE"
    },
    "stego": {
        "title": "Great views up here!",
        "desc": "Up in the air again in yet another challenge. This time, keep your eyes out for clues and you might just spot the keys you're looking for. Seek for what is contained, and you might find another source. Your key will be enclosed in two keys, though what you have now might not be what you must use now...\n\n<a href='http://ctf.wolfdragon.me:5000/resources/stego.png' download>Resources</a>",
        "answer": "HIDDEN_IN_PLANE_SIGHT"
    },
    "thomas": {
        "title": "They're two, they're four, they're six, they're eight",
        "desc": "Thomas needs your help to decipher a hidden secret. Take a look through the <a href='http://ctf.wolfdragon.me:5000/resources/thomas.zip' download>resources</a> to find a page of clues, a scrap transcript, and an image which will aid your quest.",
        "answer": "APPARENTLY_TANK_ENGINES_CAN_BE_EATEN"
    }
}

HOST = "127.0.0.1"
PORT = 62400
KEY = b"secret"

def fetch_db():
    try:
        if os.path.exists('database.json'):
            with open('database.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except ValueError:
        pass

    return {}

def update_db(data):
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_shared_state(host, port, key):
    stored_dict = fetch_db()
    lock = Lock()
    manager = BaseManager((host, port), key)
    manager.register("get_dict", lambda: stored_dict, DictProxy)
    manager.register("get_lock", lambda: lock, AcquirerProxy)
    try:
        manager.get_server()
        manager.start()
    except OSError:  # Address already in use
        manager.connect()
    return manager.get_dict(), manager.get_lock()

users, shared_lock = get_shared_state(HOST, PORT, KEY)

# Construct application
app = Flask(__name__)

# ROUTES

@app.route('/', methods=['GET'])
def main():
    return render_template('index.html')

@app.route('/internal_resources/<string:name>', methods=['GET'])
def fetch_internal_res(name):
    return send_file(f'resources/{name}')

@app.route('/resources/<string:name>', methods=['GET'])
def fetch_resource(name):
    return send_file(f'resources/{name}', as_attachment=True)

@app.route('/user/<string:user_id>', methods=['GET', 'POST'])
def locate_user(user_id):
    if request.method == "GET":
        if user_id in users:
            return jsonify({
                'valid': True,
                'cookie': format_cookie(users[user_id]['cookie'])
            })

        return jsonify({
            'valid': False
        })
    if request.method == "POST":
        if user_id in users:
            return jsonify({
            'valid': False
        })

        user = make_user(user_id)
        with shared_lock:
            update_db(users.copy())

        return jsonify({
            'valid': True,
            'cookie': format_cookie(user['cookie'])
        })

    return jsonify({
        'valid': False
    })

@app.route('/user', methods=['GET'])
def user_details():
    if request.method == "GET":
        cookie = request.headers.get('user', '')
        user = get_user_by_cookie(cookie)

        if not user:
            return jsonify({
                'valid': False
            })

        return jsonify({
            'valid': True,
            'points': len(user["challenges"]),
            'username': user['username']
        })

    return jsonify({
        'valid': False
    })

@app.route('/challenge/<string:challenge_id>', methods=['GET', 'POST'])
def challenge_lookup(challenge_id):
    cookie = request.headers.get('user', '')
    user = get_user_by_cookie(cookie)
    user_id = user['username']

    if challenge_id in challenges:
        challenge = challenges[challenge_id]
    else:
        return jsonify({
            'valid': False
        })
    got_flag = challenge_id in user['challenges'] if user else False

    if request.method == "GET":
        return jsonify({
            'valid': True,
            'title': challenge['title'],
            'desc': challenge['desc'],
            'gotFlag': got_flag
        })
    if request.method == "POST":
        if not user:
            return jsonify({
                    'valid': False,
                    'correct': False
                })
        data = request.get_json(force=True)
        if data['submission'] == f"DOM_CTF{{{challenge['answer']}}}":
            if got_flag:
                return jsonify({
                    'valid': False,
                    'correct': True
                })

            user['challenges'].append(challenge_id)

            with shared_lock:
                users[user_id] = user
                update_db(users.copy())

            return jsonify({
                'valid': True,
                'correct': True
            })

        return jsonify({
            'valid': True,
            'correct': False
        })

    return jsonify({
        'valid': False
    })

# ADMIN ROUTES
@app.route("/admin/list_users")
def list_users():
    if request.args.get('password') == "ctfOverride":
        with shared_lock:
            return jsonify(users.copy())
    return ""

# HELPER FUNCTIONS

def make_cookie(username: str):
    return base64.b64encode(f'{username}-{datetime.datetime.now(aus)}'.encode('utf-8')).decode()

def get_user_by_cookie(cookie: str):
    with shared_lock:
        user = [users[user] for user in users.keys() if users[user]['cookie'] == cookie]
    return user[0] if user else None

def check_username_present(username: str):
    with shared_lock:
        return username in users

def format_cookie(cookie: str):
    return f"challengeCookie={cookie};max-age=max-age-in-seconds=60*60*24*14"

def make_user(username: str):
    new_user = {
        "username": username,
        "challenges": [],
        "cookie": make_cookie(username)
    }
    with shared_lock:
        users[username] = new_user

    return new_user
