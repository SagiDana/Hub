#!/usr/bin/env python

from flask import Flask, request, Response, jsonify, send_file
from threading import Thread
import json

app = Flask(__name__)

# This is the scope where all the context will be saved.
global_scope = {
        "modules": {
            }
        }

def execute(code):
    """
    This method will execute whatever code given to it in the current
    interperted session.
    """
    output = None
    try:
        import sys
        from io import StringIO

        codeOut = StringIO()
        codeErr = StringIO()

        sys.stdout = codeOut
        sys.stderr = codeErr

        exec(code, global_scope)

        # restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # codeErr.getvalue()
        output = codeOut.getvalue()

        codeOut.close()
        codeErr.close()
    except Exception as e:
        output = e

    return output


def import_module(module_path, module_name):
    try:
        from importlib import import_module
        import sys

        # adding the path of the module 
        sys.path.insert(1, module_path)

        global_scope[module_name] = import_module(module_name)

        # deleting the path of the module 
        del sys.path[1]

        # keep track on all the loaded module & their paths.
        global_scope["modules"][module_name] = module_path

        return True
    except Exception as e:
        print("Exception: {}".format(e))
        return False


@app.route("/", methods=['GET', 'POST'])
def root_handler():
    return Response(status=200)

@app.route("/execute", methods=['POST'])
def execute_handler():
    if not request.is_json:
        return Response("missing parameter or malformed request", status=500)

    if "nvim_buffer" not in request.json:
        return Response("missing parameter or malformed request", status=500)

    code_to_execute = request.json['nvim_buffer']
    result = execute(code_to_execute)

    return result


@app.route("/applications", methods=['GET'])
def applications_handler():
    return jsonify(global_scope["modules"])


class HttpServer:
    """
    Hub HTTP Server to handle clients.
    """
    def __init__(self, port=1337):
        self.port = port
        self.flask_process = None

    def start(self):
        self.flask_thread = Thread(target=app.run, kwargs={
            'host': '127.0.0.1',
            'port': self.port,
        })
        self.flask_thread.setDaemon(True)
        self.flask_thread.start()

def init():
    config_path = "config.json"
    config = None
    try:
        with open(config_path) as config_file:
            config = json.loads(config_file.read())
    except:
        pass
    if not config:
        exit(1)
    
    for app_path in config["applications"]:
        if not import_module(app_path, config["applications"][app_path]):
            print("was unable to load: {}".format(config["applications"][app_path]))
            exit(1)

def main():
    init()

    http_server = HttpServer()
    http_server.start()

    while True:
        try:
            _ = input()
        except KeyboardInterrupt as e:
            break
        except:
            continue


if __name__=='__main__':
    main()
