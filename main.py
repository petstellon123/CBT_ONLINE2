from flask import Flask, request, jsonify, make_response
import pandas
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt

app = Flask(__name__, instance_relative_config=False)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///school.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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

#this route upload students logins and convert it to csv file
@app.route("/upload_std_logins", methods=["POST"])
def upload_std_logins():
    datas = request.get_json()  # get json file from incoming request
    data = json.loads(datas)  # convert json file to dictionary
    #convert std_logins to csv file
    std_data = pandas.DataFrame(data['logins'])
    file_name = f"student_logins/{data['exam_no']}_STUDENTLOGINS.csv"
    std_data.to_csv(file_name)
    return jsonify({"msg": "Successful"})


@app.route("/upload_question", methods=["POST"])
def upload_question():
    datas = request.get_json() #get json file from incoming request
    data = json.loads(datas) #convert json file to dictionary
    question = data['question_db'] #extract question dictionary
    #creating .csv file
    data_file = pandas.DataFrame(question) #convert it to pandas dataframe
    file_name = f"questions_dir/{data['exam_no']}.csv" #create the csv file in the question folder
    data_file.to_csv(file_name) #create csv file online
    return jsonify({"success": "Sent successfully."})

#this route is temporary just for testing sake
@app.route("/<exam_no>")
def all_std_log(exam_no):
    question_data = [ ]
    std_password = { }
    try:
        # check if the csv file exit
        data = pandas.read_csv(f"questions_dir/{exam_no}.csv")
        logins = pandas.read_csv(f"student_logins/{exam_no}_STUDENTLOGINS.csv")
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
        while l < len(logins):
            std_password[ logins.Password[ l ] ] = { "password": logins.Password[ l ], "name": logins.Names[ l ],
                                                     "email": logins.Email[ l ] }
            l += 1
        # <----------------------------------------------->
        if std_password:
            return make_response(jsonify({
                "msg": "Successful",
                "std_info": std_password,
                #"question_bank": question_data,
            }))
        else:
            return make_response(jsonify({
                "msg": "Invalid password."
            }))

#this route will get login details and check if correct and return question and std info
@app.route("/get_question", methods=["POST"])
def get_question():
    logins = request.get_json()
    credentials = json.loads(logins)
    question_data = []
    std_password = {}
    try:
        #check if the csv file exit
        data = pandas.read_csv(f"questions_dir/{credentials['exam_no']}.csv")
        logins = pandas.read_csv(f"student_logins/{credentials['exam_no']}_STUDENTLOGINS.csv")
    except FileNotFoundError:
        return jsonify({"msg": "File not found"})
    else:
        #create a loop to render the .csv file data to dictionary
        n = 0
        while n < len(data):
            question_data.append({"question": data.questions[n],
                                   "incorrect_answers": [data.option1[n], data.option2[n], data.option3[n]],
                                   "correct_answer": data.correct[n]})
            n += 1
        #<---------------------------------------------->
        #read logins data to dictionary
        l = 0
        while l < len(logins):
            std_password[logins.Password[l]] = {"password": logins.Password[l], "name": logins.Names[l], "email": logins.Email[l]}
            l += 1
        #<----------------------------------------------->
        if credentials['password'] in std_password:
            return jsonify({
                "msg": "Successful",
                "std_info": std_password[credentials['password']],
                "question_bank" : question_data,
            })
        else:
            return jsonify({
                "msg": "Invalid password."
            })


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
