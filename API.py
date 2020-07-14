from flask import Flask
from flask import jsonify


from ORM import Operations
from Parse import Parser
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"*": {"origins": os.environ.get('WEB')}})

@app.route('/')
def GetMakerModelYearCount():
    result = Operations.GetMakerModelYearCount()
    return jsonify(result)

@app.route('/<maker>/<type>/<year>')
def GetMakerModelYearByParameters(maker, type, year):
    result = Operations.GetMakerModelYearByParameters(maker, type, year)
    return jsonify(result)

@app.route('/update')
def Update():
    result = Parser.Update()

    return jsonify(result)

@app.route('/GetLogs')
def GetLogs():
    result = Operations.GetLogs()

    return jsonify(result)

