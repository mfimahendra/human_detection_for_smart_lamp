import io
import os
# import RPi.GPIO as GPIO

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, Response
from flask_cors import CORS, cross_origin

app = Flask(__name__)

# Configure Flask-CORS
cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["x-csrf-token"])

relay_pins = [17, 18, 27, 22]
#26, 20, 21

@app.route('/')
def index():        
    return jsonify({
        "url": "/lamp/<lamp_idx>/<lamp_state>",
        "relay_pins": relay_pins
    })
    

@app.route("/lamp/<lamp_idx>/<lamp_state>")
def lamp(lamp_idx, lamp_state):

    # 1 = 17, 2 = 18, 3 = 27, 4 = 22
    if int(lamp_idx) not in range(1, 5):
        return jsonify({
            "status": 400,
            "message": "Invalid lamp index. Use 1, 2, 3, or 4."
        })

    if lamp_state == "on":
        # GPIO.output(relay_pins[int(lamp_idx)], GPIO.HIGH) 
        print(f"relay_pins[int(lamp_idx)] = {relay_pins[int(lamp_idx)-1]}")
        print(f"Lamp {lamp_idx} on")
    elif lamp_state == "off":
        # GPIO.output(relay_pins[int(lamp_idx)], GPIO.LOW)
        print(f"relay_pins[int(lamp_idx)-1] = {relay_pins[int(lamp_idx)-1]}")
        print(f"Lamp {lamp_idx} off")
    else:
        return jsonify({
            "status": 400,
            "message": "Invalid lamp state. Use 'on' or 'off'."
        })

    responses = {
        "status": 200,
        "message": f"Lamp {lamp_idx} is turned {lamp_state}",
    }
    return jsonify(responses)


if __name__ == '__main__':            
    app.run(host="0.0.0.0",port=5021, debug=True)    
