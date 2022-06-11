from flask import Flask, render_template, redirect, request, url_for, json, session, flash, jsonify
from pymongo import MongoClient
from bson.json_util import ObjectId
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename

now = datetime.now()

app = Flask(__name__)
app.secret_key = 'secretkey'  # secret_key는 서버상에 동작하는 어플리케이션 구분하기 위해 사용하고 복잡하게 만들어야 합니다.
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60)  # 로그인 지속시간을 정합니다. 60분(1시간)
app.config['JSON_AS_ASCII'] = False  # JSON 한글 인코딩

with open('./static/client_secret.json') as f:
    json_data = json.load(f)


# json 시리얼 오류 처리용 인코더
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)


app.json_encoder = MyEncoder

# db 연동
conn = MongoClient('127.0.0.1')
# db 생성
db = conn.Test


@app.route('/join', methods=['GET', 'POST'])
def join():
    if 'userid' in session:  # 로그인 여부 확인
        if request.method == "POST":
            # collection 생성
            collect = db.mongoWaiting
            meeting_collect = db.mongoMeeting

            meet_name = request.form["meet_name"]
            result = list(meeting_collect.find({'meet_name': meet_name}))
            leader_name = result[0]['leader_name']
            leader_id = result[0]['leader_id']
            user_name = session['username']
            user_id = session['userid']
            user_profile = session['profile']

            # document 생성
            doc = {
                "meet_name": meet_name,
                "leader_name": leader_name,
                "leader_id": leader_id,
                "user_name": user_name,
                "user_id": user_id,
                "user_profile": user_profile,
                "accept": None
            }

            # document 삽입
            collect.insert_one(doc)

            msg = "신청이 완료 되었습니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect('/')
        else:
            return redirect(url_for('main'))
    else:
        return redirect('/login')


# GET API(모임 목록 조회)
@app.route('/meeting_read', methods=['GET'])
def meeting_read():
    read = db.meetings.find()
    meetList = list()
    for result in read:
        meetList.append(result)
    return jsonify(meetList)


@app.route('/mymeets')
def my_meets():
    if 'userid' in session:  # 로그인 여부 확인
        return render_template('mypage.html', mypage=1)
    else:
        return redirect('/login')


@app.route('/', methods=['GET'])
def main():
    # collection 생성
    collect = db.mongoUser
    meeting_collect = db.mongoMeeting
    if 'userid' in session:  # 로그인 여부 확인
        userid = session['userid']
        # 회원정보가 db에 있는지 검색
        result = list(collect.find({'userid': userid}))
        meet = result[0]['meeting']

        meetList = list()  # 로그인된 유저가 가입한 모임명들의 배열

        for i in meet:
            if i != "":
                meetList.append(i)

        # 유저가 가입한 모임을 제외한 모든 모임들의 정보
        meetInfo = list(meeting_collect.find({'meet_name': {'$nin': meetList}}))
        # select 쿼리값 results에 저장 (맵의 마커에 사용)
        results = meeting_collect.find()

        return render_template('main.html', data=results, meetInfo=meetInfo)
    else:
        meetInfo = list(meeting_collect.find())
        # select 쿼리값 results에 저장 (맵의 마커에 사용)
        results = meeting_collect.find()

        return render_template('main.html', data=results, meetInfo=meetInfo)


@app.route('/find_pw', methods=['GET', 'POST'])
def find_pw():
    if request.method == "POST":
        # collection 생성
        collect = db.mongoUser

        # form에서 가져온 데이터들
        userid = request.form["userid"]
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]

        # 회원정보가 db에 있는지 검색
        result = list(collect.find({'userid': userid, 'username': username, 'email': email, 'phone': phone}))

        if result:  # 회원 정보가 있을 때
            password = result[0]['password']
            msg = username + "님의 비밀번호는 " + password + "입니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect(url_for('login'))
        else:  # 회원정보가 없을 때
            msg = "회원정보와 일치하는 비밀번호가 없습니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect(url_for('find_pw'))
    # GET일 경우
    return render_template('find_pw.html')


@app.route('/find_id', methods=['GET', 'POST'])
def find_id():
    if request.method == "POST":
        # collection 생성
        collect = db.mongoUser

        # form에서 가져온 데이터들
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]

        # 회원정보가 db에 있는지 검색
        result = list(collect.find({'username': username, 'email': email, 'phone': phone}))

        if result:  # 회원 정보가 있을 때
            userid = result[0]['userid']
            msg = username + "님의 아이디는 " + userid + "입니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect(url_for('login'))
        else:  # 회원정보가 없을 때
            msg = "회원정보와 일치하는 아이디가 없습니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect(url_for('find_id'))
    # GET일 경우
    return render_template('find_id.html')


@app.route('/mypage')
def my_page():
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        collect = db.mongoUser
        meeting_collect = db.mongoMeeting

        userid = session['userid']
        # 회원정보가 db에 있는지 검색
        result = list(collect.find({'userid': userid}))
        meet = result[0]['meeting']

        meetList = list()
        meetInfo = list()

        for i in meet:
            if i != "":
                meetList.append(i)

        for i in meetList:
            meetInfo.append(meeting_collect.find({'meet_name': i}))

        return render_template('mypage.html', meetInfo=meetInfo, mypage=0)
    else:
        return redirect('/login')


@app.route('/makepage', methods=['GET', 'POST'])
def make_page():
    if 'userid' in session:  # 로그인 여부 확인
        if request.method == "POST":
            # collection 생성
            collect = db.mongoMeeting
            user_collect = db.mongoUser

            f = request.files["meet_profile"]
            meet_profile = f.filename
            meet_name = request.form["meet_name"]
            meet_title = request.form["meet_title"]
            location = request.form["location"]
            category = request.form["category"]
            headcount = request.form["headcount"]
            currentcount = 1
            address = request.form["address"]
            meetDetail = request.form["meetDetail"]
            tags = request.form["tags"]
            lat = request.form["lat"]
            lng = request.form["lng"]
            leader_id = session['userid']
            leader_name = session['username']
            done = False  # 모집중-(done: False), 모집완료-(done: True)

            tag_arr = tags.split('#')  # 태그들이 저장된 배열

            # document 생성
            doc = {
                "meet_name": meet_name,
                "leader_id": leader_id,
                "leader_name": leader_name,
                "meet_title": meet_title,
                "location": location,
                "category": category,
                "headcount": int(headcount),
                "currentcount": int(currentcount),
                "address": address,
                "meetDetail": meetDetail,
                "tags": tag_arr,
                "lat": lat,
                "lng": lng,
                "done": done
            }

            if meet_profile:  # form에서 넘어온 profile 값이 있다면
                f.save(
                    './static/meet_profile/' + secure_filename(
                        meet_profile))  # 모임 프로필 이미지 파일 저장 (경로: static/meet_profile/)
                doc.update({'meet_profile': meet_profile})
                session['meet_profile'] = './static/meet_profile/' + meet_profile

            # user테이블에서 모임장의 meeting에 새로 만든 모임 추가 (배열에 값을 추가할 때는 $push 사용)
            user_collect.update_one({'userid': session['userid']}, {'$push': {"meeting": meet_name}})
            # document 삽입
            collect.insert_one(doc)

            redirect(url_for('my_page'))
        # GET일 경우
        return render_template('makemeet.html')
    else:
        return redirect('/login')


@app.route('/pfedit', methods=['GET', 'POST'])
def profile_edit():
    if 'userid' in session:  # 로그인 여부 확인
        if request.method == "POST":
            # collection 생성
            collect = db.mongoUser
            meeting_collect = db.mongoMeeting

            # form에서 값이 넘어오면 변수에 값 할당
            # 넘어오지 않는다면 null값 할당
            f = request.files["profile"]
            profile = f.filename
            username = request.form["username"]
            introduce = request.form["introduce"]

            doc = {}

            if profile:  # form에서 넘어온 profile 값이 있다면
                f.save('./static/profile/' + secure_filename(profile))  # 프로필 이미지 파일 저장 (경로: static/profile/)
                doc.update({'profile': profile})
                session['profile'] = './static/profile/' + profile
            if username:  # form에서 넘어온 username 값이 있다면
                doc.update({'username': username})
                session['username'] = username
            if introduce:  # form에서 넘어온 introduce 값이 있다면
                doc.update({'introduce': introduce})

            # 변경된 값 db에 반영
            collect.update_one({'userid': session['userid']}, {'$set': doc})
            meeting_collect.update_one({'leader_id': session['userid']}, {'$set': {"leader_name": username}})
            redirect(url_for('my_page'))

        # GET일 경우
        return render_template('profileedit.html')
    else:
        return redirect('/login')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # request.method를 통해 GET & POST 인지 확인함.
        # collection 생성
        collect = db.mongoUser

        # 폼에서 ID/PW 가져오기
        userid = request.form['id']
        password = request.form['password']

        # 폼에서 입력받은 userid와 password값이 있는지 db에서 조회
        result = list(collect.find({'userid': userid, 'password': password}))

        # userid와 password값이 db에 있다면 세션에 값입력
        if result:
            username = result[0]['username']
            profile = 'static/profile/' + result[0]['profile']
            session['userid'] = userid
            session['password'] = password
            session['username'] = username
            session['profile'] = profile
            return redirect(url_for('main'))
        else:  # userid와 password값이 db에 없을 경우 (id 또는 pw가 틀렸을 경우)
            msg = "아이디와 비밀번호를 다시 확인해주세요"
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            redirect(url_for('login'))
    # GET일 경우
    return render_template('login.html')


@app.route('/logout')
def logout():
    # 세션에서 값 삭제
    session.pop('userid', None)
    return redirect(url_for('main'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        # collection 생성
        collect = db.mongoUser

        # form에서 가져온 데이터들
        username = request.form["username"]
        userid = request.form["userid"]
        password = request.form["password1"]
        gender = request.form["gender"]
        birth = request.form["birth"]
        email = request.form["email"]
        phone = request.form["phone"]

        # document 생성
        doc = {
            "profile": "user.png",
            "username": username,
            "userid": userid,
            "password": password,
            "gender": gender,
            "birth": birth,
            "email": email,
            "phone": phone,
            "introduce": "",
            "meeting": [],
        }
        # userid가 db에 있는지 검색
        result = list(collect.find({'userid': userid}))

        # userid가 db에 없으면(중복되지 않는다면) insert쿼리 실행
        if not result:
            # document 삽입
            collect.insert_one(doc)
            return redirect(url_for('main'))
        # userid가 중복될 경우 다시 signup페이지로 이동
        else:
            msg = "이미 존재하는 아이디입니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect(url_for('signup'))
    else:  # 메소드가 GET일 경우
        return render_template('signup.html')


@app.route('/meet/<id>')
def meet_page(id=None):
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        collect = db.mongoBoard
        meeting_collect = db.mongoMeeting

        # 모임 정보
        meetInfo = meeting_collect.find({'_id': ObjectId(id)})

        # select 쿼리값 results에 저장
        results = collect.find()
        return render_template('meetpage.html', data=results, meetInfo=meetInfo)
    else:
        return redirect('/login')


@app.route('/meetadmin/<id>', methods=['GET', 'POST'])
def meet_admin(id=None):
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        collect = db.mongoUser
        meeting_collect = db.mongoMeeting
        waiting_collect = db.mongoWaiting

        # 모임 정보
        meetInfo = meeting_collect.find({'_id': ObjectId(id)})

        if request.method == "POST":
            return redirect('/meet/' + str(meetInfo[0]['_id']))

        else:
            meet_list = list(meeting_collect.find({'_id': ObjectId(id)}))
            meet_name = meet_list[0]['meet_name']
            members = list(collect.find({'meeting': meet_name}))
            waiting = list(waiting_collect.find({'meet_name': meet_name}))
            return render_template('meetadmin.html', meetInfo=meetInfo, members=members, waiting=waiting)
    else:
        return redirect('/login')

@app.route('/accept', methods=['GET', 'POST'])
def accept_meet():
    if 'userid' in session:  # 로그인 여부 확인
        if request.method == "POST":
            # collection 생성
            collect = db.mongoUser
            meeting_collect = db.mongoMeeting
            waiting_collect = db.mongoWaiting

            userid = request.form["userid"]
            meet_name = request.form["meet_name"]
            meet = list(meeting_collect.find({'meet_name': meet_name}))
            if session['userid'] == meet[0]['leader_id']:
                currentcount = meet[0]['currentcount']
                currentcount += 1
                meeting_collect.update_one({'meet_name': meet_name}, {'$set': {"currentcount": currentcount}})

                collect.update_one({'userid': userid}, {'$push': {"meeting": meet_name}})
                waiting_collect.delete_one({'user_id': userid, 'meet_name': meet_name})
                return redirect('/meetadmin/'+ str(meet[0]['_id']))
            else:
                # 로그인한 사용자와 일치하지 않으면
                msg = "권한이 없습니다."
                flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
                return redirect('/meetadmin/' + str(meet[0]['_id']))
        else:
            return redirect(url_for('main'))
    else:
        return redirect('/login')


@app.route('/reject', methods=['GET', 'POST'])
def reject_meet():
    if 'userid' in session:  # 로그인 여부 확인
        if request.method == "POST":
            # collection 생성
            waiting_collect = db.mongoWaiting
            meeting_collect = db.mongoMeeting

            userid = request.form["userid"]
            meet_name = request.form["meet_name"]
            meet = list(meeting_collect.find({'meet_name': meet_name}))
            if session['userid'] == meet[0]['leader_id']:
                waiting_collect.delete_one({'user_id': userid, 'meet_name': meet_name})
                return redirect('/meetadmin/' + str(meet[0]['_id']))
            else:
                # 로그인한 사용자와 일치하지 않으면
                msg = "권한이 없습니다."
                flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
                return redirect('/meetadmin/' + str(meet[0]['_id']))
        else:
            return redirect(url_for('main'))
    else:
        return redirect('/login')


@app.route('/quit', methods=['GET', 'POST'])
def quit_meet():
    if 'userid' in session:  # 로그인 여부 확인
        if request.method == "POST":
            # collection 생성
            collect = db.mongoUser
            meeting_collect = db.mongoMeeting

            userid = request.form["userid"]
            meet_name = request.form["meet_name"]
            meet = list(meeting_collect.find({'meet_name': meet_name}))
            if userid == session['userid']:
                collect.update_one({'userid': userid}, {'$pull': {"meeting": meet_name}})

                currentcount = meet[0]['currentcount']
                currentcount -= 1
                meeting_collect.update_one({'meet_name': meet_name}, {'$set': {"currentcount":currentcount}})
                return redirect('/')
            else:
                # 로그인한 사용자와 일치하지 않으면
                msg = "탈퇴 권한이 없습니다."
                flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
                return redirect('/meetadmin/' + str(meet[0]['_id']))
        else:
            return redirect(url_for('main'))
    else:
        return redirect('/login')


@app.route('/write/<id>', methods=['GET', 'POST'])  # 게시판 or 공지사항 글쓰기 페이지
def write(id=None):
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        meeting_collect = db.mongoMeeting
        # 모임 정보
        meetInfo = meeting_collect.find({'_id': ObjectId(id)})
        if request.method == "POST":
            # collection 생성
            collect = db.mongoBoard

            # form에서 가져온 데이터들
            title = request.form["title"]
            contents = request.form["contents"]
            userid = session['userid']
            username = session['username']
            meet_name = meetInfo[0]['meet_name']

            # document 생성
            doc = {
                "title": title,
                "contents": contents,
                "userid": userid,
                "username": username,
                "create_time": str(now.date()),
                "meet_name": meet_name
            }
            collect.insert_one(doc)
            return redirect('/meet/' + str(meetInfo[0]['_id']))
        # GET일 경우
        return render_template('makenotice.html', meetInfo=meetInfo)
    else:  # 로그인 안되어 있을 경우
        return redirect('/login')


@app.route('/notice/<meet_id>/<id>')  # 게시판 or 공지사항에 작성된 글 읽기 페이지
def notice(meet_id=None, id=None):
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        collect = db.mongoBoard
        meeting_collect = db.mongoMeeting

        # 모임 정보
        meetInfo = meeting_collect.find({'_id': ObjectId(meet_id)})

        # db에서 id와 일치하는 글 검색
        result = list(collect.find({'_id': ObjectId(id)}))
        result = result[0]
        return render_template('read.html', data=result, meetInfo=meetInfo)
    else:  # 로그인 안되어 있을 경우
        return redirect('/login')


@app.route('/delete/<meet_id>/<id>')
def delete(meet_id=None, id=None):
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        collect = db.mongoBoard

        # db에서 id와 일치하는 글 검색
        result = list(collect.find({'_id': ObjectId(id)}))
        if result[0]['userid'] == session['userid']:  # 작성자와 로그인한 사용자가 일치하면
            collect.delete_one({'_id': ObjectId(id)})  # 해당 게시글 삭제
            return redirect('/meet/' + meet_id)
        else:  # 작성자와 로그인한 사용자가 일치하지 않으면
            msg = "삭제 권한이 없습니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect('/notice/' + meet_id + '/' + id)
    else:  # 로그인 안되어 있을 경우
        return redirect('/login')


@app.route('/edit/<meet_id>/<id>', methods=['GET', 'POST'])  # 게시판 or 공지사항에 작성된 글 읽기 페이지
def edit(meet_id=None, id=None):
    if 'userid' in session:  # 로그인 여부 확인
        # collection 생성
        collect = db.mongoBoard
        meeting_collect = db.mongoMeeting

        # 모임 정보
        meetInfo = meeting_collect.find({'_id': ObjectId(meet_id)})

        if request.method == "POST":
            # form에서 가져온 데이터들
            title = request.form["title"]
            contents = request.form["contents"]
            userid = session['userid']
            username = session['username']

            # document 생성
            doc = {
                "title": title,
                "contents": contents,
                "userid": userid,
                "username": username,
                "create_time": str(now.date())
            }
            collect.update_one({'_id': ObjectId(id)}, {'$set': doc})
            return redirect('/meet/' + meet_id)

        # GET일 경우
        # db에서 id와 일치하는 글 검색
        result = list(collect.find({'_id': ObjectId(id)}))
        if result[0]['userid'] == session['userid']:  # 작성자와 로그인한 사용자가 일치하면
            result = result[0]
            return render_template('edit.html', data=result, meetInfo=meetInfo)
        else:  # 작성자와 로그인한 사용자가 일치하지 않으면
            msg = "수정 권한이 없습니다."
            flash(msg)  # 리턴할 때 같이 넘겨줄 메시지
            return redirect('/notice/' + meet_id + '/' + id)

    else:  # 로그인 안되어 있을 경우
        return redirect('/login')


# POST API(모임 등록)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    db.meetings.insert_one(data)

    return jsonify(result="success", result2=data)

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
