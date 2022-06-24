#Efendi Kisnoto     19090057
#Abbror Sholakhudin 190900141

import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense,Conv2D,MaxPool2D,Dropout,BatchNormalization,Flatten,Activation
from keras.preprocessing import image 
from keras.preprocessing.image import ImageDataGenerator
import datetime 
from datetime import date
import pickle
from flask import Flask, jsonify,request,flash,redirect,render_template, session,url_for
from itsdangerous import json
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
from flask_restful import Resource, Api
import pymongo
import re
from flask_ngrok import run_with_ngrok
import pyngrok
from PIL import Image
import datetime
import random
import string


app = Flask(__name__)
run_with_ngrok(app)
UPLOAD_FOLDER = 'foto_burung'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = "bigtuing"
MONGO_ADDR = 'mongodb://localhost:27017'
MONGO_DB = "db_mibird"

conn = pymongo.MongoClient(MONGO_ADDR)
db = conn[MONGO_DB]

api = Api(app)


from tensorflow.keras.models import load_model
MODEL_PATH = 'model12lokal.h5'
model = load_model(MODEL_PATH,compile=False)

pickle_inn = open('num_12class_bird.pkl','rb')
num_classes_bird = pickle.load(pickle_inn)


def allowed_file(filename):     
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
  
@app.route('/api/v1/predict', methods=['POST'])

def predict():
    
    if 'image' not in request.files:
      flash('No file part')
      return jsonify({
            "pesan":"tidak ada form image"
          })
    file = request.files['image']
    if file.filename == '':
      return jsonify({
            "pesan":"tidak ada file image yang dipilih"
          })
    if file and allowed_file(file.filename):
      
      letters = string.ascii_lowercase
      result_str = ''.join(random.choice(letters) for i in range(5))
      
      filename = secure_filename(file.filename+result_str+".jpg")
      print(filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      path=("foto_burung/"+filename)
  
      
      today = date.today()
      db.riwayat.insert_one({'nama_file': filename, 'path': path, 'prediksi':'No predict', 'akurasi':0, 'tanggal':today.strftime("%d/%m/%Y")})

      img=image.load_img(path,target_size=(224,224))
      img1=image.img_to_array(img)
      img1=img1/255
      img1=np.expand_dims(img1,[0])
      predict=model.predict(img1)
      classes=np.argmax(predict,axis=1)
      for key,values in num_classes_bird.items():
          if classes==values:
            accuracy = float(round(np.max(model.predict(img1))*100,2))
            info = db['data_burung'].find_one({'nama': str(key)})
            db.riwayat.update_one({'nama_file': filename}, 
              {"$set": {
                'prediksi': str(key), 
                'akurasi':accuracy
              }
              })
            print("The predicted image of the bird is: "+str(key)+" with a probability of "+str(accuracy)+"%")            
           
            return jsonify({
            "Nama_Burung":str(key),
            "Accuracy":str(accuracy)+"%",
            "Nama_Ilmiah": info['nama_ilmiah'],
            "Spesies" : info['spesies'],
            "Makanan" : info['makanan'],
            "Status" :  info['status']         
                
            })       
    else:
      return jsonify({
        "Message":"bukan file image"
      })

@app.route('/admin')
def admin():
    return render_template("login.html")
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db['admin'].find_one({'username': str(username)})
        print(user)

        if user is not None and len(user) > 0:
            if password == user['password']:
                
                session['username'] = user['username']
                
                return redirect(url_for('dataBurung'))
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))
    else:
        return render_template('login.html')
    
    return render_template('dashboard.html')

@app.route('/dataBurung')
def dataBurung():
    data = db['data_burung'].find({})
    print(data)
    return render_template('dataBurung.html',dataBurung  = data)


@app.route('/tambahData')
def tambahData():

    return render_template('tambahData.html')

@app.route('/daftarBurung', methods=["POST"])
def daftarBurung():
    if request.method == "POST":
        nm_burung = request.form['nm_burung']
        nm_ilm = request.form['nm_ilmiah']
        spesies = request.form['spesies']
        makanan = request.form['makanan']
        status = request.form['status']
        if not re.match(r'[A-Za-z]+', nm_burung):
            flash("Nama harus pakai huruf Dong!")
        
        else:
            db.data_burung.insert_one({'nama': nm_burung, 'nama_ilmiah': nm_ilm, 'spesies':spesies, 'makanan':makanan, 'status':status})
            flash('Data Burung berhasil ditambah')
            return redirect(url_for('dataBurung'))

    return render_template("tambahData.html")

@app.route('/editBurung/<nama>', methods = ['POST', 'GET'])
def editBurung(nama):
  
    data = db['data_burung'].find_one({'nama': nama})
    print(data)
    return render_template('editBurung.html', editBurung = data)

@app.route('/updateBurung/<nama>', methods=['POST'])
def updatBurung(nama):
    if request.method == 'POST':
        
        nm_ilm = request.form['nm_ilmiah']
        spesies = request.form['spesies']
        makanan = request.form['makanan']
        status = request.form['status']
        if not re.match(r'[A-Za-z]+', nama):
            flash("Nama harus pakai huruf Dong!")
        else:
          db.data_burung.update_one({'nama': nama}, 
          {"$set": {
             
            'nama_ilmiah': nm_ilm, 
            'spesies':spesies, 
            'makanan':makanan, 
            'status':status
            }
            })

          flash('Data Burung berhasil diupdate')
          return render_template("popUpEdit.html")

    return render_template("dataBurung.html")

@app.route('/riwayat')
def riwayat():
    dataRiwayat = db['riwayat'].find({})
    print(dataRiwayat)
    return render_template('riwayat.html',riwayat  = dataRiwayat)
    
@app.route('/hapusRiwayat/<nama_file>', methods = ['POST','GET'])
def hapusRiwayat(nama_file):
  
    db.riwayat.delete_one({'nama_file': nama_file})
    flash('Riwayat Berhasil Dihapus!')
    return redirect(url_for('riwayat'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
  

  app.run()
