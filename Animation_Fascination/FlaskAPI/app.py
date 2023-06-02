import flask
from flask import Flask, jsonify, request
import json
from app_input_votescore import data_in
from app_input_gross import data_in
import numpy as np
import pickle

def load_models():
    file_name_g = "models/model_file_gross.p"
    with open(file_name_g, 'rb') as pickled:
        data = pickle.load(pickled)
        model = data['model']
    return model

app = Flask(__name__)
@app.route('/predict', methods=['GET'])
def predict():
    # parse input features from request
    request_json = request.get_json()
    x = request_json['input']
    print(x)
    x_in = np.array(x).reshape(1,-1)

    model = load_models()
    prediction = model.predict(x_in)[0]
    response = json.dumps({'response': str(prediction)})
    return response, 200

if __name__ == '__main__':
    application.run(debug=True)
