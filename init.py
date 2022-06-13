import random

import flask
from flask import request, render_template, redirect, session, url_for
from flask_socketio import SocketIO, emit, disconnect

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "r`9[M-AtuO"
socketio = SocketIO(app, async_mode=None)
ssl_certificate = "/etc/pki/tls/certs/cert.crt"
ssl_certificate_key = "/etc/pki/tls/private/cert.key"

DEBUG = 1


def __output(*message):
    if DEBUG:
        print(message)


@app.route('/', methods=['GET', 'POST'])
def website():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        user_id = request.form['ID']
        user_password = request.form['passwd']
        if user_id == "123456" and user_password == 'root':
            return redirect('/success')
        else:
            __output("login fail")
            return render_template("index.html", user_id=user_id)


@app.route('/success', methods=['GET'])
def tmp_page():
    return render_template("YangTest/index.html")


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8080, ssl_context=(ssl_certificate, ssl_certificate_key))
