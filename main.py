from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, login_user, logout_user, current_user, LoginManager, UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_wtf import FlaskForm
from wtforms.fields import StringField, URLField, SelectField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from sqlalchemy import Integer, String, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5
from functools import wraps
from flask_ckeditor import CKEditorField
from flask_ckeditor import CKEditor
from random import choice
import datetime as dt
app = Flask(__name__)


# Initialize the extension
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# Configure our Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Cafes.db"
# Define the secret Key for the app
app.config["SECRET_KEY"] = "you_secret_key_is_here"
# Initialize the app with extension
db.init_app(app)

# Initialize our loginManger
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize Bootstrap

bootstrap = Bootstrap5(app)

ckeditor = CKEditor(app)

logos = [
    "https://static.vecteezy.com/system/resources/thumbnails/005/076/592/small_2x/hacker-mascot-for-sports-and-esports-logo-free-vector.jpg",
    "https://cdn.shopify.com/shopifycloud/hatchful_web_two/bundles/4a14e7b2de7f6eaf5a6c98cb8c00b8de.png"]


# Define our table
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="cafes")
    has_sockets: Mapped[int] = mapped_column(Integer, nullable=False)
    has_toilet: Mapped[int] = mapped_column(Integer, nullable=False)
    has_wifi: Mapped[int] = mapped_column(Integer, nullable=False)
    can_take_calls: Mapped[int] = mapped_column(Integer, nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String, nullable=False)
    cafe_review = relationship("Review", back_populates="cafe")


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    cafes = relationship("Cafe", back_populates="user")
    password: Mapped[str] = mapped_column(String(400), nullable=False)
    reviews = relationship("Review", back_populates="user")


class Review(db.Model):
    review_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_content: Mapped[str] = mapped_column(String(500), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafe.id"))
    user = relationship("User", back_populates="reviews")
    cafe = relationship("Cafe", back_populates="cafe_review")


# create a form using wtforms
class AddingForm(FlaskForm):
    name = StringField(label="Cafe Name", validators=[DataRequired()])
    map_url = URLField(label='Map_Url Cafe', validators=[DataRequired(), URL(message="Url Invalid")])
    cafe_image_url = URLField(label='Image_Url Cafe', validators=[DataRequired(), URL(message="Url Invalid")])
    cafe_location = StringField(label="Location", validators=[DataRequired()])
    sockets = SelectField(label="hasSockets", validators=[DataRequired()], choices=("Select yes or no", "yes", "no"))
    Toilet = SelectField(label="hasToilet", validators=[DataRequired()], choices=("Select yes or no", "yes", "no"))
    wifi = SelectField(label="hasWifi", validators=[DataRequired()], choices=("Select yes or no", "yes", "no"))
    Calls = SelectField(label="CanTakeCalls", validators=[DataRequired()], choices=("Select yes or no", "yes", "no"))
    seats = StringField(label="number_Seats", validators=[DataRequired()])
    price = StringField(label="Coffee Price", validators=[DataRequired()])
    sb_button = SubmitField(label="Add")


class Comment(FlaskForm):
    body = CKEditorField("body", validators=[DataRequired()])
    send_bt = SubmitField("Send")


class LoginForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    login_bt = SubmitField(label="Login")


# create the table
with app.app_context():
    db.create_all()


# create the user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
def show_all_caffe():
    # query all the cafes from the database
    all_cafes = db.session.execute(db.Select(Cafe).order_by(Cafe.name)).scalars().all()
    return render_template("index.html", cafes=all_cafes, is_login=current_user.is_authenticated)


@app.route("/caffe", methods=["POST", "GET"])
def show_cafe():
    current_date = dt.datetime.now()

    commentForm = Comment()
    random_avatar = choice(logos)
    cafe_id = request.args.get("id", " ")
    request_cafe = db.get_or_404(Cafe, cafe_id)
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("OOPS.You are not allowed to put a comment.please login")
            return redirect(url_for("login"))

        else:
            new_review = Review(
                review_content=request.form.get("body"),
                user=current_user,
                cafe=request_cafe,
            )

            db.session.add(new_review)
            db.session.commit()

    return render_template("Caffe.html", cafe=request_cafe, avatar=random_avatar, comment=commentForm,
                           is_login=current_user.is_authenticated,
                           date_now=current_date,
                           )


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        user_password = request.form.get("password")
        password = generate_password_hash(password=user_password, method="pbkdf2:sha256:600000", salt_length=8)
        email = request.form.get("email")
        name = request.form.get("name")
        new_user = User(
            name=name,
            email=email,
            password=password,

        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("show_all_caffe"))
    return render_template('register.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST":
        user_email = request.form.get("email")
        user_password = request.form.get("password")
        get_user = db.session.execute(db.Select(User).where(User.email == user_email)).scalar()
        print(get_user)
        if get_user and check_password_hash(pwhash=get_user.password, password=user_password):
            login_user(get_user)
            return redirect(url_for("show_all_caffe"))
        elif get_user is None:
            flash(message="Email does not exit!please try again.")
            return redirect(url_for("login"))
        elif get_user and not check_password_hash(pwhash=get_user.password, password=user_password):
            flash(message="Password Incorrect!please try again")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("show_all_caffe"))


@app.route("/add_cafe", methods=["POST", "GET"])
@login_required
def add_cafe():
    addCafeForm = AddingForm()
    if addCafeForm.validate_on_submit():
        new_cafe = Cafe(
            name=addCafeForm.name.data,
            map_url=addCafeForm.map_url.data,
            user=current_user,
            img_url=addCafeForm.cafe_image_url.data,
            location=addCafeForm.cafe_location.data,
            has_sockets=addCafeForm.sockets.data,
            has_toilet=addCafeForm.Toilet.data,
            has_wifi=addCafeForm.wifi.data,
            can_take_calls=addCafeForm.Calls.data,
            seats=addCafeForm.seats.data,
            coffee_price=addCafeForm.price.data,

        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for("show_all_caffe"))
    return render_template("add_cafe.html", form=addCafeForm)


@app.route("/delete")
def delete():
    cafe_delete_id = request.args.get("id", " ")
    cafe_want_to_delete = db.get_or_404(Cafe, cafe_delete_id)
    db.session.delete(cafe_want_to_delete)
    db.session.commit()
    return redirect(url_for('show_all_caffe'))


if __name__ == "__main__":
    app.run(debug=True)
