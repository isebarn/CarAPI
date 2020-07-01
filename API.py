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

@app.route('/makers')
def GetMakers():
    result = Operations.GetMakers()
    return jsonify(result)

@app.route('/models')
def GetModels():
    result = Operations.GetModels()
    return jsonify(result)

@app.route('/update')
def Update():
    result = Parser.parseAll()

    return jsonify({'new': str(result)})

@app.route('/CheckForSold')
def CheckForSold():
    result = Parser.checkSold()
    return jsonify({'sold': result})

@app.route('/GetAllSold')
def GetAllSold():
    result = Operations.GetAllSold()

    return jsonify(result)

@app.route('/GetUnsoldIDs')
def GetUnsoldIDs():
    result = Operations.GetUnsoldIDs()

    return jsonify(result)