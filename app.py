from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecretkey")

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    user = User(username=data["username"], password=data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"], password=data["password"]).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(days=1))
    return jsonify({"token": token})

@app.route("/notes", methods=["POST"])
@jwt_required()
def create_note():
    user_id = get_jwt_identity()
    data = request.json
    note = Note(title=data["title"], content=data["content"], user_id=user_id)
    db.session.add(note)
    db.session.commit()
    return jsonify({"message": "Note created"}), 201

@app.route("/notes", methods=["GET"])
@jwt_required()
def get_notes():
    user_id = get_jwt_identity()
    notes = Note.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": note.id, "title": note.title, "content": note.content} for note in notes])

@app.route("/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    user_id = get_jwt_identity()
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"message": "Note not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)
