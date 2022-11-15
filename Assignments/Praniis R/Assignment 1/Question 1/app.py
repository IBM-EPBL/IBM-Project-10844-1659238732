from urllib import request
from flask import Flask
from flask import render_template,request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method=="POST":
        result=request.form
        return render_template("user.html",result=result)
    return render_template("registration.html")