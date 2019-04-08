from flask import Flask
import json,cv2
import os
import pymysql
from flask import Flask,Response,make_response
from flask import request
from flask import redirect
from flask import jsonify
from datetime import datetime , timedelta
import time
import requests
app = Flask(__name__)


@app.route('/vms/facedetect', methods=['GET','POST'])
def response():

    a = request.get_data()
    dict1 = json.loads(a)
    print(dict1)
    return json.dumps(0)








if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug='True')
