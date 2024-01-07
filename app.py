# app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    SelectField,
    DateField,
    RadioField,
    IntegerField,
)
from sqlalchemy import or_
from wtforms.validators import DataRequired, Email
from sqlalchemy.exc import SQLAlchemyError
from models import db, Course, User
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///courses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key"

db.init_app(app)
bootstrap = Bootstrap(app)


# class Form control
class CourseForm(FlaskForm):
    name = StringField("Nama Lengkap", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone_number = IntegerField("Nomor HP", validators=[DataRequired()])
    registration_date = DateField("Tanggal Masuk")
    gender = RadioField(
        "Jenis Kelamin",
        choices=[("Laki - Laki", "Laki - Laki"), ("Perempuan", "Perempuan")],
        validators=[DataRequired()],
    )
    subject = SelectField(
        "Mata Pelajaran",
        choices=[
            ("Matematika", "Matematika"),
            ("Biologi", "Biologi"),
            ("Kimia", "Kimia"),
            ("Fisika", "Fisika"),
            ("Ekonomi", "Ekonomi"),
            ("Geografi", "Geografi"),
            ("Sosiologi", "Sosiologi"),
            ("Sejarah", "Sejarah"),
            ("Bahasa Inggris", "Bahasa Inggris"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Simpan")


# Routes
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and password == user.password:
            login_user(user)
            flash("Anda berhasil login!", "success")
            return redirect(url_for("menu"))
        else:
            flash("Username atau password salah.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username sudah digunakan.", "danger")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Anda berhasil registrasi! Silahkan masuk.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda berhasil keluar!", "danger")
    return redirect(url_for("index"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/menu")
@login_required
def menu():
    return render_template("menu.html")


@app.route("/course_list")
@login_required
def course_list():
    courses = Course.query.all()
    return render_template("course_list.html", courses=courses)


@app.route("/course_card")
@login_required
def course_card():
    courses = Course.query.all()
    return render_template("course_card.html", courses=courses)


@app.route("/course/new", methods=["GET", "POST"])
@login_required
def course_new():
    form = CourseForm()
    if form.validate_on_submit():
        try:
            new_course = Course(
                name=form.name.data,
                email=form.email.data,
                phone_number=form.phone_number.data,
                registration_date=form.registration_date.data,
                gender=form.gender.data,
                subject=form.subject.data,
            )
            db.session.add(new_course)
            db.session.commit()
            flash("Data berhasil ditambahkan!", "success")
            return redirect(url_for("course_list"))
        except SQLAlchemyError as e:
            flash(f"Error:  {str(e)}", "danger")
            db.session.rollback()

    return render_template("course_form.html", form=form, action="Tambah")


@app.route("/course/edit/<int:id>", methods=["GET", "POST"])
@login_required
def course_edit(id):
    course = Course.query.get(id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.name = form.name.data
        course.email = form.email.data
        course.phone_number = form.phone_number.data
        course.registration_date = form.registration_date.data
        course.gender = form.gender.data
        course.subject = form.subject.data
        db.session.commit()
        flash("Data berhasil diedit!", "success")
        return redirect(url_for("course_list"))
    return render_template("course_form.html", form=form, action="Edit")


@app.route("/course/delete/<int:id>", methods=["GET", "POST"])
@login_required
def course_delete(id):
    course = Course.query.get(id)
    if request.method == "POST":
        db.session.delete(course)
        db.session.commit()
        flash("Data berhasil dihapus!", "success")
        return redirect(url_for("course_list"))
    return render_template("delete_confirm.html", course=course)


@app.route("/course/detail/<int:id>")
@login_required
def course_detail(id):
    course = Course.query.get(id)
    if course:
        return render_template("course_detail.html", course=course)
    else:
        flash("Tidak ada hasil yang ditemukan.", "info")
        return redirect(url_for("search_member"))


@app.route("/search_member", methods=["GET", "POST"])
@login_required
def search_member():
    if request.method == "POST":
        search_term = request.form.get("search_term", "")
        courses = Course.query.filter(or_(Course.name.ilike(f"%{search_term}%"))).all()

        if len(courses) == 1:
            return redirect(url_for("course_detail", id=courses[0].id))

        flash("Tidak ada hasil yang ditemukan.", "danger")
        return render_template("search_member.html", courses=courses)

    return render_template("search_member.html", courses=[])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
