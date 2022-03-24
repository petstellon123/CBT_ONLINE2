from flask import Flask, request, jsonify, make_response
import pandas
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt

app = Flask(__name__, instance_relative_config=False)
app.config[ "SQLALCHEMY_DATABASE_URI" ] = "sqlite:///school.sqlite"
app.config[ "SQLALCHEMY_TRACK_MODIFICATIONS" ] = False

db = SQLAlchemy(app)

class ExamDetails(db.Model):
    __tablename__ = "examdetails"
    id = db.Column(db.Integer, primary_key=True)
    exam_title = db.Column(db.String, unique=False, nullable=False)
    exam_no = db.Column(db.String, unique=True, nullable=False)
    grading = db.Column(db.Integer, nullable=True)
    total_question = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    exam_date = db.Column(db.DateTime, unique=False, nullable=True)

    def __init__(self, exam_title, exam_no, grading, total_question, duration, exam_date):
        self.exam_title = exam_title
        self.exam_no = exam_no
        self.grading = grading
        self.total_question = total_question
        self.duration = duration
        self.exam_date = exam_date

    def __repr__(self):
        return "ExamDetails {}".format(self.exam_no)


class StudentLogin(db.Model):
    __tablename__ = "studentlogin"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    exam_no = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=True)
    total_question = db.Column(db.Integer, nullable=True)
    exam_code = db.Column(db.String, unique=False, nullable=False)
    done_exam = db.Column(db.Boolean, nullable=False)
    date = db.Column(db.DateTime, unique=False, nullable=False)

    def __init__(self, name, exam_no, email, score, total_question, exam_code, done_exam, date):
        self.name = name
        self.exam_no = exam_no
        self.email = email
        self.score = score
        self.total_question = total_question
        self.exam_code = exam_code
        self.done_exam = done_exam
        self.date = date

    def __repr__(self):
        return 'StudentLogin {}'.format(self.exam_no)


# commit = StudentLogin(name="Peter", exam_no="8999@pet", email="exampl@gmail.com", score=0, total_question=20,
#                       exam_code='MATH788767', done_exam=False, date=dt.now())
# db.session.add(commit)
# db.session.commit()
# std = StudentLogin.query.filter(StudentLogin.exam_no == "8999@pet").first()
# print(std.name)

#route to get exam details
@app.route("/exam_details/<exam_no>")
def exam_details_query(exam_no):
    data = ExamDetails.query.filter_by(exam_no=exam_no).first()
    std = StudentLogin.query.filter_by(exam_code=exam_no).all()
    print(std)
    exam_data = {
        'exam_title': data.exam_title,
        'exam_no': data.exam_no,
        'grading': data.grading,
        'duration': data.duration,
        'total_question': data.total_question,
        'exam_date': data.exam_date
    }
    return make_response(jsonify({
        "msg": "Successful",
        "exam details": exam_data,
    }))

# this route upload students logins and convert it to csv file
@app.route("/upload_std_logins", methods=[ "POST" ])
def upload_std_logins():
    datas = request.get_json()  # get json file from incoming request
    data = json.loads(datas)  # convert json file to dictionary
    print(data)
    # convert std_logins to csv file
    # std_data = pandas.DataFrame(data[ 'logins' ])
    # file_name = f"student_logins/{data[ 'exam_no' ]}_STUDENTLOGINS.csv"
    # std_data.to_csv(file_name)
    login = data['logins']
    try:
        n = 0
        while n < len(login['Names']):
            new_login = StudentLogin(name=login['Names'][n], exam_no=login['Password'][n], email=login['Email'][n],
                                     score=0, total_question=0, exam_code=data['exam_no'], done_exam=False, date=dt.now())
            db.session.add(new_login)
            n += 1
        db.session.commit()
    except:
        return jsonify({ "msg": "Dupplicate Entry." })
    else:
        return jsonify({ "msg": "Successful" })


@app.route("/upload_question", methods=[ "POST" ])
def upload_question():
    datas = request.get_json()  # get json file from incoming request
    data = json.loads(datas)  # convert json file to dictionary
    question = data[ 'question_db' ]  # extract question dictionary
    #print(question)
    # creating .csv file
    data_file = pandas.DataFrame(question)  # convert it to pandas dataframe
    file_name = f"questions_dir/{data[ 'exam_no' ]}.csv"  # create the csv file in the question folder
    data_file.to_csv(file_name)  # create csv file online

    #create exam details db
    new_details = ExamDetails(exam_title=data['exam_title'], exam_no=data['exam_no'], grading=2,
                              total_question=len(data['question_db']['questions']), duration=30, exam_date=dt.now())
    db.session.add(new_details)
    db.session.commit()
    return jsonify({ "success": "Sent successfully." })

#this route receive result of test
@app.route('/submit', methods=["GET", "POST"])
def submit_result():
    datas = request.get_json()  # get json file from incoming request
    data = json.loads(datas)  # convert json file to dictionary
    try:
        #update student result to database
        std_info = StudentLogin.query.filter_by(exam_no=data['exam_no']).first()
        std_info.score = int(data['result'])
        std_info.done_exam = True
        db.session.add(std_info)
        db.session.commit()
        #print(std_info.result)
    except:
        return jsonify({"msg": 'Denied'})
    else:
        return jsonify({"msg": "Successful"})





# this route is temporary just for testing sake
@app.route("/<exam_no>")
def all_std_log(exam_no):
    question_data = [ ]
    std_password = { }
    try:
        # check if the csv file exit
        data = pandas.read_csv(f"questions_dir/{exam_no}.csv")
        logins = StudentLogin.query.filter_by(exam_code=exam_no).all()
        exam_details = ExamDetails.query.filter_by(exam_no=exam_no).first()
    except FileNotFoundError:
        return make_response(jsonify({ "msg": "File not found" }))
    else:
        # create a loop to render the .csv file data to dictionary
        n = 0
        while n < len(data):
            question_data.append({ "question": data.questions[ n ],
                                   "incorrect_answers": [ data.option1[ n ], data.option2[ n ], data.option3[ n ] ],
                                   "correct_answer": data.correct[ n ] })
            n += 1
        # <---------------------------------------------->
        # read logins data to dictionary
        l = 0
        while l < (len(logins)):
            std_password[ logins[ l ].exam_no ] = { "password": logins[ l ].exam_no, "name": logins[ l ].name, 'result': logins[l].score,
                                                    "email": logins[ l ].email, "exam_title": exam_details.exam_title, 'done_exam': logins[l].done_exam,
                                                    'duration': exam_details.duration, 'grading': exam_details.grading,
                                                    'exam_no': exam_details.exam_no }
            l += 1
        # <----------------------------------------------->
        if std_password:
            return make_response(jsonify({
                "msg": "Successful",
                "std_info": std_password,
                # "question_bank": question_data,
            }))
        else:
            return make_response(jsonify({
                "msg": "Invalid password."
            }))


# this route will get login details and check if correct and return question and std info
@app.route("/get_question", methods=[ "POST" ])
def get_question():
    logins = request.get_json()
    credentials = json.loads(logins)
    question_data = [ ]
    std_password = { }
    try:
        # check if the csv file exit
        data = pandas.read_csv(f"questions_dir/{credentials[ 'exam_no' ]}.csv")
        #logins = pandas.read_csv(f"student_logins/{credentials[ 'exam_no' ]}_STUDENTLOGINS.csv")
        logins = StudentLogin.query.filter_by(exam_code=credentials[ 'exam_no' ]).all()
        exam_details = ExamDetails.query.filter_by(exam_no=credentials[ 'exam_no' ]).first()
    except FileNotFoundError:
        return jsonify({ "msg": "File not found" })
    else:
        # create a loop to render the .csv file data to dictionary
        n = 0
        while n < len(data):
            question_data.append({ "question": data.questions[ n ],
                                   "incorrect_answers": [ data.option1[ n ], data.option2[ n ], data.option3[ n ] ],
                                   "correct_answer": data.correct[ n ] })
            n += 1
        # <---------------------------------------------->
        # read logins data to dictionary
        l = 0
        while l < len(logins):
            std_password[ logins[ l ].exam_no ] = { "password": logins[ l ].exam_no, "name": logins[ l ].name,
                                                     "email": logins[ l ].email, "exam_title": exam_details.exam_title,
                                                    'duration': exam_details.duration, 'grading': exam_details.grading,
                                                    'exam_no': exam_details.exam_no}
            l += 1
        # <----------------------------------------------->
        if credentials[ 'password' ] in std_password:
            return jsonify({
                "msg": "Successful",
                "std_info": std_password[ credentials[ 'password' ] ],
                "question_bank": question_data,
            })
        else:
            return jsonify({
                "msg": "Invalid password."
            })


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
