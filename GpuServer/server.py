from flask import Flask,jsonify,render_template,redirect
from flask import request
from flask_cors import CORS
#pip install flask-bcrypt
from flask_bcrypt import Bcrypt

# pip install gevent
from gevent.pywsgi import WSGIServer

from utils import encode_auth_token, decode_auth_token, plantData

import os
import base64
from datetime import datetime

import json
import sqlite3


app = Flask(__name__, static_url_path='/static')
flask_bcrypt = Bcrypt(app)
CORS(app)

extra_files = []

#dateToday = datetime.today().strftime('%Y-%m-%d')

@app.route("/")
def hello():
    message = "Hello, World"
    #return app.send_static_file('myfig.png')
    #return redirect("http://192.168.42.169:5000/static/images/myfig.png", code=302)
    # return render_template('index.html', message=message)
    return "It's Working"

## Incase a reset db is needed. A default admin user has to be created for login username:adminUser password: adminPassword
@app.route('/setup', methods = ['GET'])
def dbSetup():
    with sqlite3.connect('plant.db') as conn:
        c= conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
        username text,
        password text,
        isAdmin boolean,
        registeredOn text                
        ) """)
        passHash = flask_bcrypt.generate_password_hash("adminPassword").decode('utf-8')
        #c.execute("DELETE FROM users where username='adminUser'")
        c.execute("INSERT INTO users VALUES (:username,:password,:admin, :date)",
                  {'username':"adminUser", 'password':passHash, 'admin':True, 'date':datetime.now()})
        conn.commit()
        c.execute("""CREATE TABLE IF NOT EXISTS plants (
            plantId text,
            noLeaf text,
            regions text,
            maskArea integer,
            totalArea integer,
            greenPercentage real,
            inputUrl text,
            outputUrl text,
            date text
            ) """)
        conn.commit()
        c.execute("""CREATE TABLE IF NOT EXISTS plantDataTable (
                plantId text,
                plantType text,
                plantedOn text,
                remarks text
                ) """)
        return "DB Created"

#Register a new user
@app.route('/register', methods = ['POST'])
def userReg():
    if(request.is_json):
        content = request.get_json()
        print(content)
        userName = content['username']
        password = content['password']
        admin = content['admin']
        token = request.headers['Authorization']
        status, message, isAdmin = decode_auth_token(token)
        if(status):
            with sqlite3.connect('plant.db') as conn:
                    c= conn.cursor()
                    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    username text,
                    password text,
                    isAdmin boolean,
                    registeredOn text                
                    ) """)
                    
                    if(isAdmin!="False"):
                        c.execute("SELECT * FROM users where username=:userId", {'userId':userName})
                        tempdata = c.fetchall()
                        if len(tempdata) == 0:
                            print("User not found")
                            passHash = flask_bcrypt.generate_password_hash(password).decode('utf-8')
                            c.execute("INSERT INTO users VALUES (:username,:password,:admin, :date)", 
                                      {'username':userName, 'password':passHash, 'date':datetime.now(), 'admin':admin})
                            return jsonify(status=True,
                                           result="User Added Succesfully")
                        else:
                            return jsonify(status=False,
                                           result="User Already Exists")
                    else:
                        return jsonify(status=False,
                                           result="Permission Issue, Only Admins can add users")
        else:
            print(message)
            return jsonify(status=False, result=message)
    else:
        return jsonify(status=False,
                       result="Incorrect format")

#Delete a user
@app.route('/unregister', methods = ['POST'])
def userUnReg():
    if(request.is_json):
        content = request.get_json()
        userName = content['username']
        token = request.headers['Authorization']
        status, message, isAdmin = decode_auth_token(token)
        if(status):
            with sqlite3.connect('plant.db') as conn:
                if(isAdmin!="False"):
                    c= conn.cursor()
                    c.execute("DELETE FROM users where username=:userId", {'userId':userName})
                    return jsonify(status=True, result="Deleted Successfully")
                else:
                    return jsonify(status=False, result="Permission Issue, Only Admins can Remove Users")
        else:
            return jsonify(status=False, result=message)
    else:
        return jsonify(status=False, result="Incorrect Format")                        

#Authenticate a user, a token will be given on auth success, use this token for further calls
@app.route('/login', methods = ['POST'])
def userAuth():
    if(request.is_json):
        content = request.get_json()
        print(content)
        userName = content['username']
        password = content['password']
        with sqlite3.connect('plant.db') as conn:
                c= conn.cursor()
                c.execute("""CREATE TABLE IF NOT EXISTS users (
                username text,
                password text,
                isAdmin boolean,
                registeredOn text
                ) """)
                c.execute("SELECT * FROM users where username=:userId", {'userId':userName})
                tempdata = c.fetchall()
                if len(tempdata) == 0:
                    print("User not found")
                    return jsonify(username=userName,
                                       isAuth=False,
                                       authToken="",
                                       isAdmin=False)
                else:
                    passHash = tempdata[0][1]
                    valid = flask_bcrypt.check_password_hash(passHash, password)
                    if(valid):
                        print("User Authenticated: "+ tempdata[0][0])
                        admin = True if tempdata[0][2]==1 else False
                        return jsonify(username=userName,
                                       isAuth=True,
                                       authToken=encode_auth_token(tempdata[0][0], admin),
                                       isAdmin=admin)
                    else:
                        print("Incorrect Password, User Authentication Failed")
                        return jsonify(username=userName,
                                       isAuth=False,
                                       authToken="",
                                       isAdmin=False)
    else:
        print("unsupported request")
        return "method not allowed"               

#Test Method, to verify the token in GET and POST requests
@app.route('/verify', methods = ['GET','POST'])
def verifyToken():
    if request.method == 'POST':
        if(request.is_json):
            content = request.get_json()
            print(content)
            token = content['authToken']
            status, message, isAdmin = decode_auth_token(token)
            if(status):
                return jsonify(status = status,
                               message="Username: "+message,
                               isAdmin=isAdmin)
            else:
                print(message)
                return jsonify(status = status, message= message)
    else:
        token = request.headers['Authorization']
        status, message, isAdmin = decode_auth_token(token)
        if(status):
            return jsonify(status = status, 
                           message="Username: "+message,
                           isAdmin=isAdmin)
        else:
            print(message)
            return jsonify(status = status,
                           message= message)
        
#Add a new plant
@app.route('/addPlant', methods = ['POST'])
def set_plantData():
    #print(request.headers)
    token = request.headers['Authorization']
    print("Token",token)
    status, message, isAdmin = decode_auth_token(token)
    if(status):
        if(request.is_json):
            content = request.get_json()
            print(content)
            plantId = content['plantId']
            plantType = content['plantType']
            plantedOn = content['plantedOn']
            remarks = content['remarks']
            if(isAdmin!="False"):
                with sqlite3.connect('plant.db') as conn:
                    c= conn.cursor()
                    c.execute("""CREATE TABLE IF NOT EXISTS plantDataTable (
                    plantId text,
                    plantType text,
                    plantedOn text,
                    remarks text
                    ) """)
                    c.execute("SELECT * FROM plantDataTable where plantId=:plantId", {'plantId':plantId})
                    result = c.fetchall()
                    if len(result)>0:                    
                        return jsonify(status=False, data = "PlantId Already exists")
                    else:
                        c.execute("""INSERT INTO plantDataTable VALUES (
                    :plantId, :plantType, :date, :remarks) """, {'plantId':plantId, 'plantType':plantType, 'date':plantedOn, 'remarks':remarks})
                        return jsonify(status=True, data = "Plant Added Successfully")
            else:
                return jsonify(status=False, data="Permission Issue, Requires Admin Access")   
        else:
            return jsonify(status=False,
                               data = "Unsupported Format")
    else:
        print(message)
        return jsonify(status= status,
                       data = message)   

#Remove a plant
@app.route('/removePlant', methods = ['GET'])
def remove_plantData():
    #print(request.headers)
    token = request.headers['Authorization']
    print("Token",token)
    status, message, isAdmin = decode_auth_token(token)
    if(status):
        plantId = request.args.get('plantId')
        deleteMethod = request.args.get('deleteMethod')
        if(isAdmin!="False"):
            with sqlite3.connect('plant.db') as conn:
                c= conn.cursor()
                if(deleteMethod=="plantData"):
                    c.execute("DELETE FROM plantDataTable where plantId=:plantId", {'plantId':plantId})
                    return jsonify(status=True,
                                   data = "Deleted only Plant Data")
                elif(deleteMethod=="allData"):
                    c.execute("DELETE FROM plantDataTable where plantId=:plantId", {'plantId':plantId})
                    c.execute("DELETE FROM plants where plantId=:plantId", {'plantId':plantId})
                    return jsonify(status=True,
                                   data = "Deleted All Data")

                else:
                    return jsonify(status=False,
                                   data = "Unknown Delete Method")
        else:
            return jsonify(status=False, data="Permission Issue, Requires Admin Access")        
    else:
        print(message)
        return jsonify(status= status, data = message)
    
#List all plants that have atleast 1 data and optionally data in plantdatatable
@app.route('/listPlants', methods = ['GET'])
def get_plantData():
    #print(request.headers)
    token = request.headers['Authorization']
    print("Token",token)
    status, message, isAdmin = decode_auth_token(token)
    if(status):
        with sqlite3.connect('plant.db') as conn:
            c= conn.cursor()
            c.execute("SELECT DISTINCT plants.plantId, plantType, plantedOn, remarks FROM plants LEFT JOIN plantDataTable on plants.plantId = plantDataTable.plantId ")
            return jsonify(status=status,
                           data = c.fetchall())
    else:
        print(message)
        return jsonify(status= status,
                       data = message)

#Fetch plantId, GreenPercentage, Dates for all plants in Order
@app.route('/getPlantGrowth', methods = ['GET'])
def get_plantGrowthRate():
    token = request.headers['Authorization']
    status, message, isAdmin = decode_auth_token(token)
    if(status):
        with sqlite3.connect('plant.db') as conn:
                c= conn.cursor()
                c.execute("SELECT plantId, greenPercentage, date FROM plants ORDER BY plantId DESC, date ASC")
                result = c.fetchall()
                return jsonify(status= status, data = result)
    else:
        print(message)
        return jsonify(status= status, data = message)
    
#Fetch Data of a plant on a given date    
@app.route('/getData', methods = ['GET'])
def get_plantGrowthDataByDate():
    token = request.headers['Authorization']
    status, message, isAdmin = decode_auth_token(token)
    if(status):
        plantId = request.args.get('plantId')
        date = request.args.get('date')
        with sqlite3.connect('plant.db') as conn:
                c= conn.cursor()
                c.execute("SELECT * FROM plants where plantId=:plantId AND date=:date", {'plantId':plantId, 'date':date})
                result = c.fetchone()
                print("INFO: Fetched data of {} on {}".format(plantId,date))
                print(result)
                regions = json.loads(result[2])
                plant = plantData(str(result[0]), str(result[1]), regions, str(result[3]), str(result[4]), str(result[5]), str(result[6]), str(result[7]), str(result[8]))
                # response = json.dumps(plant.__dict__).replace('"',"'")
                response = json.dumps(plant.__dict__)
                return jsonify(status= status, data = response)
    else:
        print(message)
        return jsonify(status= status, data = message)

#Get all data of a given plant
@app.route('/getAllData', methods = ['GET'])
def get_plantAllData():
    token = request.headers['Authorization']
    status, message, isAdmin = decode_auth_token(token)
    if(status):
        plantId = request.args.get('plantId')
        with sqlite3.connect('plant.db') as conn:
                c= conn.cursor()
                c.execute("SELECT * FROM plants where plantId=:plantId", {'plantId':plantId})
                results = c.fetchall()
                print("INFO: Fetched data of {}".format(results[0][0]))
                plants=[]
                for result in results:
                    regions = json.loads(result[2])
                    plant = plantData(str(result[0]), str(result[1]), regions, str(result[3]), str(result[4]), str(result[5]), str(result[6]), str(result[7]), str(result[8]))
                    plants.append(plant.__dict__)
                #return jsonify(json.dumps(plant.__dict__))
                #response = json.dumps(plants)
                return jsonify(status=status, data=plants)
    else:
        print(message)
        return jsonify(status= status, data = message)

#Images are send to this method for analytics
@app.route('/postjson', methods = ['POST'])
def postJsonHandler():
    if(request.is_json):
        content = request.get_json()
        #print(content)
        img_name = content['filename']
        img_string = content['image']
        imgdata = base64.decodebytes(img_string.encode())
        
        save_dir = os.path.join(os.getcwd(), "static", datetime.today().strftime('%Y-%m-%d'))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        with open(os.path.join(save_dir,img_name),'wb') as f:
            f.write(imgdata)
            
        import detect as det
        results=det.analysePlant(os.path.join(save_dir,img_name), img_name)
        plant = plantData(results['plantId'], results["numLeaves"], results["regions"], str(results["totalMaskArea"]), results["totalPixels"], results["greenPercentage"], results["maskInput"], results["maskOutput"], datetime.today().strftime('%Y-%m-%d'))
        with sqlite3.connect('plant.db') as conn:
            c= conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS plants (
            plantId text,
            noLeaf text,
            regions text,
            maskArea integer,
            totalArea integer,
            greenPercentage real,
            inputUrl text,
            outputUrl text,
            date text
            ) """)
            c.execute("SELECT * FROM plants where plantId=:plantId AND date=:date", {'plantId':plant.plantId, 'date':datetime.today().strftime('%Y-%m-%d')})
            tempdata = c.fetchall()
            if len(tempdata) == 0:
                print("Insert to Database")
                c.execute("INSERT INTO plants VALUES (:plantId,:noLeaf,:regions,:maskArea,:totalArea,:greenPerc,:inputUrl,:outputUrl,:date)", {'plantId':plant.plantId, 'noLeaf':plant.noLeaf, 'regions':plant.regions, 'maskArea': plant.maskArea, 'totalArea':plant.totalArea,'greenPerc':plant.greenPercentage, 'inputUrl':plant.inputUrl, 'outputUrl':plant.outputUrl, 'date':plant.date})
            else:
                print("Update to Database")
                c.execute("""UPDATE plants SET noLeaf = :noLeaf, regions = :regions, maskArea = :maskArea,
        totalArea = :totalArea,greenPercentage = :greenPerc, inputUrl = :inputUrl, outputUrl = :outputUrl 
        WHERE plantId = :plantId AND date = :date""", {'plantId':plant.plantId, 'noLeaf':plant.noLeaf, 'regions':plant.regions, 'maskArea': plant.maskArea, 'totalArea':plant.totalArea,'greenPerc':plant.greenPercentage, 'inputUrl':plant.inputUrl, 'outputUrl':plant.outputUrl, 'date':plant.date})           
            conn.commit()          

        return jsonify(json.dumps(str(results)))
    else:
        print("unsupported request format")
        return "method not allowed"

if __name__ == '__main__':
    
    # app.config['TEMPLATE_AUTO_RELOAD'] = True
    # app.run(host='0.0.0.0',port=5000,debug = False)
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
   
