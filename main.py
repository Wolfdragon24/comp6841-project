import os
import json
import datetime
import base64

from flask import Flask, render_template, send_file, jsonify, request
import pytz

aus = pytz.timezone('Australia/Sydney')

challenges = {
    "osint": {
        "title": "Where was I taken?",
        "desc": "I spy with my little eye... a world far down below. Name from whence the lens nigh, then the flag you seek you know.\n\nThe flag is in all caps separated by underscores, e.g. DOM_CTF{CENTRAL_STATION}. https://ctf.wolfdragon.me/resources/osint.jpg",
        "answer": "MERITON_SUITE_WORLD_TOWER"
    },
    "bufferformat": {
        "title": "One won't bring you far enough...",
        "desc": "You've seen buffer overflows vulnerabilities, you've seen format strings vulnerabilities, but have you needed both?\n\nLocated at 'nc ctf.wolfdragon.me 62401' is the answer you seek, exploring the binary locally first from 'https://ctf.wolfdragon.me/resources/bufferformat' is highly recommended!",
        "answer": "TRAILBLAZED_THE_DOUBLE"
    },
    "stego": {
        "title": "Great views up here!",
        "desc": "Up in the air again in yet another challenge. This time, keep your eyes out for clues and you might just spot the keys you're looking for. Your key will be enclosed in two keys, though what you have now might not be what you must use now...\n\nhttps://ctf.wolfdragon.me/resources/stego.png",
        "answer": "HIDDEN_IN_PLANE_SIGHT"
    }
}

# Construct application
app = Flask(__name__)

# ROUTES

@app.route('/', methods=['GET'])
def main():
    return render_template('index.html')

@app.route('resources/<str:name>', methods=['GET'])
def fetch_resource(name):
    return send_file(f'resources/{name}')

@app.route('/user/<str:user_id>', methods=['GET'])
def locate_user(user_id):
    if request.method == "GET":
        if user_id in users:
            return jsonify({
                'valid': True,
                'cookie': users[user_id]['cookie']
            })

        return jsonify({
            'valid': False
        })

    return jsonify({
        'valid': False
    })

@app.route('/user', methods=['GET'])
def user_details():
    if request.method == "GET":
        cookie = request.headers.get('cookie', '')
        user = get_user_by_cookie(cookie)

        if not user:
            return jsonify({
                'valid': False
            })

        return jsonify({
            'valid': True,
            'points': user['points'],
            'username': user['username']
        })

    return jsonify({
        'valid': False
    })

@app.route('/challenge/<str:challenge_id>', methods=['GET', 'POST'])
def challenge_lookup(challenge_id):
    cookie = request.headers.get('cookie', '')
    user = get_user_by_cookie(cookie)

    if challenge_id in challenges:
        challenge = challenges[challenge_id]
    else:
        return jsonify({
            'valid': False
        })
    got_flag = challenge_id in user['challenges']

    if request.method == "GET":
        return jsonify({
            'valid': True,
            'title': challenge['title'],
            'desc': challenge['desc'],
            'gotFlag': got_flag
        })
    if request.method == "POST":
        data = request.get_json(force=True)
        if data['submission'] == f"DOM_CTF{{{challenge['answer']}}}":
            if got_flag:
                return jsonify({
                    'valid': False,
                    'correct': True
                })

            user['challenges'].append(challenge_id)

            update_db(users)

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

# HELPER FUNCTIONS

def make_cookie(username: str):
    return base64.b64encode(f'{username}-{datetime.datetime.now(aus)}'.encode('utf-8')).decode()

def get_user_by_cookie(cookie: str):
    user = [users[user] for user in users.items() if users[user]['cookie'] == cookie]
    return user[0] if user else None

def fetch_db():
    if os.path.exists('database.json'):
        with open('database.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    return {}

def update_db(data):
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)

# SETUP

users = fetch_db()
