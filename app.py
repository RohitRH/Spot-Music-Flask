from flask import Flask, render_template, url_for, request, session, redirect, make_response, session,flash,jsonify,make_response
import mysql.connector
import os
from werkzeug.utils import secure_filename
import datetime
from datetime import date

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'

# sess = Session()

#data = {}
#items = {}


USER='admin'
PASS='admin'

mydb = mysql.connector.connect(host="localhost", user="root", passwd="123456", database="spotify")
mycursor = mydb.cursor()

@app.route('/')
@app.route('/index')
def index():
    data,artist_data,l,artists=getData()
    return render_template('index.html',data=data,artist_data=artist_data,l=l,artists=artists)

def getData():
    sql1="select s.SongName,s.ReleaseDate,a.Name,s.ImagePath from songs s,artists a,artists_songs ss where s.SongId=ss.SongId and a.ArtistId=ss.ArtistId group by s.SongId order by s.Rating desc limit 10"
    mycursor.execute(sql1)
    data=mycursor.fetchall()
    #print(data)
    sql2="select a.Name,a.DOB from songs s,artists a,artists_songs ss where s.SongId=ss.SongId and a.ArtistId=ss.ArtistId group by a.ArtistId order by avg(s.Rating) desc limit 10"
    mycursor.execute(sql2)
    artist_data = mycursor.fetchall()
    songs,artists=getNames(artist_data,data)
    #print(l[4])
    #print(l[3])
    return data,artist_data,songs,artists


def getNames(artist_data,song_name):
    sql="select s.SongName,a.Name from songs s,artists a,artists_songs ss where s.SongId=ss.SongId and a.ArtistId=ss.ArtistId"
    mycursor.execute(sql)
    data=mycursor.fetchall()
    songs=[]
    #print(artist_data[0][0])
    #print(data)
    for i in range(len(artist_data)):
        songs_data=[]
        for j in range(len(data)):
            if(artist_data[i][0]==data[j][1]):
                songs_data.append(data[j][0])
        songs.append(songs_data)
    artists=[]
    #print(song_name)
    for i in range(len(song_name)):
        artists_names=[]
        for j in range(len(data)):
            if(song_name[i][0]==data[j][0]):
                artists_names.append(data[j][1])
        artists.append(artists_names)
    #print(songs)
    #print(artists)
    return songs,artists


@app.route('/addSong',methods=['GET','POST'])
def addSong():
    if(request.method=='GET'):
        if(session['login']):
            sql1="select Name from artists"
            mycursor.execute(sql1)
            artists_Names=mycursor.fetchall()
            return  render_template('add_song.html',artists_Names=artists_Names,loggedin=True)
        return render_template('login.html')
    if(request.method=='POST'):
        song = request.form['songName']
        ReleasedDate = request.form['ReleasedDate']

        artists = request.form.getlist('artist')
        #print(song,ReleasedDate,artists)
        image=request.files["file"]


        songId=storeData(song,ReleasedDate,image,artists)

        return redirect('/addSong')


def upload_image(image,songId):
    app.config["IMAGE_UPLOADS"] = "static/Song_images"
    if request.files:
        if image.filename == "":
            print("No filename")
            return redirect(request.url)

        if allowed_image(image.filename):
            ext = image.filename.rsplit(".", 1)[1]
            filename = secure_filename(str(songId)+"."+ext)

            image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))

            print("Image saved")
            return filename
        else:
            print("That file extension is not allowed")
            return redirect(request.url)



def storeData(song,ReleaseDate,image,artists):

    sql2="select s.SongId,s.SongName,a.ArtistId,a.Name from songs s,artists a,artists_songs ss where s.SongId=ss.SongId and a.ArtistId=ss.ArtistId"
    mycursor.execute(sql2)
    data=mycursor.fetchall()
    #print(data[0])
    #print(artists)
    s=list()
    si=set()
    for i in range(len(artists)):
        for j in range(len(data)):
            if(data[j][3]==artists[i]):
                s.append(data[j][2])
                break
    print(s)
    for i in range(len(data)):
        si.add(data[i][0])
    print(max(si)+1)
    ss=""
    artists_songs=[]
    songId=max(si)+1

    filename=upload_image(image, songId)
    imagePath="static/Song_images/"+filename
    print(filename)
    sql1 = "insert into songs(SongName,ReleaseDate,ImagePath,Rating) values(%s,%s,%s,%s)"
    val = [song, ReleaseDate, imagePath, 0]
    mycursor.execute(sql1, val)
    mydb.commit()

    for i in range(len(artists)):
        artists_songs.append([s[i],songId])
        if (i != len(artists) - 1):
            ss=ss+","
    print(artists_songs)
    artists_songs=str(artists_songs).replace('[',"",1)
    last_char_index = artists_songs.rfind("]")
    artists_songs = artists_songs[:last_char_index] + "" + artists_songs[last_char_index + 1:]
    artists_songs=artists_songs.replace("[","(").replace("]",")")
    sql3="insert into artists_songs values "+artists_songs
    print(sql3)
    mycursor.execute(sql3)
    mydb.commit()
    return songId

def allowed_image(filename):
    app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

@app.route('/addArtist',methods=['POST'])
def addArtist():
    req = request.get_json()

    print(req)
    sql1 = "insert into artists (Name,DOB,Bio) values(%s,%s,%s)"
    val = (req['name'], req['dob'], req['bio'])
    mycursor.execute(sql1, val)
    mydb.commit()

    res = make_response(jsonify(req), 200)

    return res

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pw']
        if (user == USER and pw == PASS):
            session['login']=True
            return redirect('index.html')
        session['login']=False
        return render_template('login.html',msg="Incorrect Username or Password")

@app.errorhandler(404)
def not_found(e):
    return redirect("/index")

@app.route('/logout')
def logout():
    session['login']=False
    return redirect('/index.html')

""""@app.route('/register', methods=['GET', 'POST'])
def register():
    if (request.method == 'GET'):
        return render_template('register.html')
    if (request.method == 'POST'):
        email = request.form['email']
        mobile = request.form['mobile']
        bid = request.form['bid']
        sname = request.form['sname']
        uname = request.form['uname']
        pw = request.form['password']
        a = db.users.find({'uname': uname})
        if (a.count() != 0):
            return render_template('register.html', msg="Username already exists try another")
        users = {"email": email, "mobile": mobile, "bid": bid, "sname": sname, "uname": uname, "pass": pw}
        db.users.insert(users)
        return redirect('/index')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html',alert=False)
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pw']
        a = db.users.find({'uname': user, 'pass': pw})
        # print(a.count())
        if (a.count() != 0):
            session['my_var'] = user
            lgin=session.get('login', None)
            lgin=True
            session['login'] = lgin
            det = db.users.find({'uname': user})
            # print(det[0]['sname'])
            #sname = det[0]['sname']
            bid = det[0]['bid']
            det1 = db.itm.find({'bid': bid})
            if(det1.count()!=0):
                return redirect(url_for('decide'))
            return redirect(url_for('store_data'))
        return render_template('login.html', msg="Incorrect Username or Password",alert=True)"""


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1')