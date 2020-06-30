from flask import Flask
from flask import jsonify


from ORM import Operations
from Parse import Parser

app = Flask(__name__)

@app.route('/')
def GetMakerModelYearCount():
    result = Operations.GetMakerModelYearCount()
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