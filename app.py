from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"
SECRET_KEY = 'SPARTA'

client = MongoClient('13.125.42.121', 27017, username="test", password="test")

db = client.gettravel

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        all_travels = list(db.travels.find({}, {'_id': False}))
        return render_template('index.html', user_info=user_info, travels=all_travels)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/search')
def search():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        search_name = request.args.get('name')
        print(search_name)
        all_travels = list(db.travels.find({'name':search_name}, {'_id': False}))
        return render_template('index.html', user_info=user_info, travels=all_travels)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/admin')
def admin():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('admin.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

#여행지 수정 페이지로 이동하기
@app.route('/admin-edit')
def admin_edit():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        travel_receive = request.args.get("travel_give")
        travel = db.travels.find_one({'name': travel_receive}, {'_id': False})
        print(travel)
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('edit.html', travel=travel, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/detail/<keyword>')
def detail(keyword):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        travel = db.travels.find_one({'name': keyword}, {'_id': False})
        return render_template('detail.html', travel=travel, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route("/get_travel", methods=['GET'])
def get_travel():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        travelname_receive = request.args.get("travelname_give")
        travel = db.travels.find_one({'name': travelname_receive}, {'_id': False})
        travel["count_heart"] = db.likes.count_documents({"travelname": travel["name"], "type": "heart"})
        travel["heart_by_me"] = bool(db.likes.find_one({"travelname": travel["name"], "type": "heart", "username": payload['id']}))
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "travel" : travel})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 누가 좋아요 눌렀느지는 토큰에서 아이디 꺼내면 바로 알 수 있음
        user_info = db.users.find_one({"username": payload["id"]})
        # 어떤 글인지
        travelname_receive = request.form["travelname_give"]
        # 어떤 종류의 반응인지
        type_receive = request.form["type_give"]
        action_receive = request.form["action_give"]
        doc = {
            "travelname": travelname_receive,
            "username": user_info["username"],
            "type": type_receive
        }
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        # 해당 글에 좋아요가 몇개인지
        count = db.likes.count_documents({"travelname": travelname_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/upload', methods=['POST'])
def upload():
    name_receive = request.form['name_give']
    address_receive = request.form['address_give']
    content_receive = request.form['content_give']

    # 파일 저장
    file = request.files["file_give"]

    # 확장자 가장마지막것
    extension = file.filename.split('.')[-1]

    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    filename = f'file-{mytime}'

    save_to = f'static/{filename}.{extension}'
    file.save(save_to)  # 경로와 이름

    # print(title_receive,content_receive )
    doc = {
        'name': name_receive,
        'address' : address_receive,
        'content': content_receive,
        'file': f'{filename}.{extension}'
    }

    db.travels.insert_one(doc);

    return jsonify({'msg': 'POST 요청 완료!'})

#여행지 수정된 정보 받아서 DB에 update하기
@app.route('/edit-travel', methods=['POST'])
def edit_travel():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        name_receive = request.form['name_give']
        oldname_receive = request.form['oldname_give']
        address_receive = request.form['address_give']
        content_receive = request.form['content_give']

        new_doc = {
            "name": name_receive,
            "address": address_receive,
            "content": content_receive
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            extension = file.filename.split('.')[-1]
            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
            filename = f'file-{mytime}'
            save_to = f'static/{filename}.{extension}'
            file.save(save_to)  # 경로와 이름
            new_doc["file"] = f'{filename}.{extension}'
        db.travels.update_one({'name': oldname_receive}, {'$set': new_doc})
        return jsonify({"result": "success", 'msg': '여행지를 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

#여행지 삭제하기
@app.route('/delete-travel', methods=['POST'])
def delete_travel():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        travel_receive = request.form['travelname_give']
        #travels 테이블에서 해당 여행지 정보 지워주기
        db.travels.delete_one({'name': travel_receive})
        #comments 테이블에서 해당 여행지 후기들 지워주기
        db.comments.delete_many({'travelname': travel_receive})
        #likes 테이블에서 해당 여행지 찜 지워주기
        db.likes.delete_many({'travelname': travel_receive})
        user_info = db.users.find_one({"username": payload["id"]})
        return jsonify({"result": "success", 'msg': '여행지를 삭제했습니다.'})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    # 회원가입
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    # 중복검사
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/comment/<keyword>')
def comment(keyword):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 유저정보 읽어옴
        user_info = db.users.find_one({"username": payload["id"]})
        travel = db.travels.find_one({'name': keyword}, {'_id': False})
        return render_template('comment.html', user_info=user_info, travel=travel)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/commenting', methods=['POST'])
def commenting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]
        travelname_receive = request.form["travelname_give"]
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            "profile_pic_real": user_info["profile_pic_real"],
            "comment": comment_receive,
            "date": date_receive,
            "travelname": travelname_receive
        }
        db.comments.insert_one(doc)
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/updatecomment', methods=['POST'])
def update_comment():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]
        travelname_receive = request.form["travelname_give"]
        new_doc = {
            "comment": comment_receive,
            "date": date_receive
        }
        db.comments.update_one({'username': user_info["username"], 'travelname': travelname_receive}, {'$set': new_doc})
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/deletecomment', methods=['POST'])
def delete_comment():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        writer_receive = request.form["writer_give"]
        travelname_receive = request.form["travelname_give"]
        db.comments.delete_one({'username': writer_receive, 'travelname': travelname_receive})
        return jsonify({"result": "success", 'msg': '삭제 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/get_comments", methods=['GET'])
def get_comments():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        travelname = request.args.get("travelname_give")
        comments = list(db.comments.find({"travelname": travelname}).sort("date", -1).limit(20))
        for comment in comments:
            print('코멘트 불러오기')
            print(comment)
            comment["_id"] = str(comment["_id"])
        return jsonify({"result": "success", "msg": "코멘트를 가져왔습니다.", "comments": comments, "travelname": travelname})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/mypage')
def mypage():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('mypage.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route("/get_mycomments", methods=['GET'])
def get_mycomments():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        username_receive = request.args.get("username_give")
        print('유저네임'+username_receive)
        comments = list(db.comments.find({"username": username_receive}).sort("date", -1).limit(20))
        for comment in comments:
            print('나의코멘트 불러오기')

            print(comment)
            comment["_id"] = str(comment["_id"])
        return jsonify({"result": "success", "msg": "코멘트를 가져왔습니다.", "comments": comments})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
@app.route("/mylike")
def mylikes():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        all_likes = list(db.likes.find({"username": payload["id"]}, {'_id': False}))
        print(all_likes)
        all_travel = []
        for like in all_likes:
            travel = db.travels.find_one({'name': like['travelname']}, {'_id': False})
            all_travel.append(travel)
        print(all_travel)
        return render_template('mylikes.html', user_info=user_info, travels=all_travel)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)