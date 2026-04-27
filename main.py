import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from items_data import BARTER_ITEMS

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mrrobotkeynt'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barter.db'

UPLOAD_FOLDER = os.path.join('static', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(200), default='default_avatar.png')

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    tier = db.Column(db.Integer)
    category = db.Column(db.String(50))
    level = db.Column(db.String(100))
    rarity = db.Column(db.String(20))
    image = db.Column(db.String(200))
    price = db.Column(db.Integer)
    requirements = db.relationship('Requirement', backref='item', lazy=True)

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not Item.query.first():
        for data in BARTER_ITEMS:
            new_item = Item(
                name=data['name'],
                tier=data['tier'],
                category=data['category'],
                level=data['level'],
                rarity=data['rarity'],
                image=data['image'],
                price=data['price']
            )
            db.session.add(new_item)
            db.session.flush()
            for res_name, amount in data['resources'].items():
                req = Requirement(resource_name=res_name, amount=amount, item_id=new_item.id)
                db.session.add(req)
        db.session.commit()

@app.route('/')
def index():
    all_items = Item.query.all()
    items_dict = {item.name: item for item in all_items}
    branches = [
        {
            "title": "ЛИНИЯ АК / ВСС / АШ",
            "rows": [
                ["АКС-74У", "АКС-74", "АКС-74М", "АН-94 <Абакан>", "АН-94М <Абакан>", "АЕК-971", "А-545"],
                [None, None, None, "АКМ", "АК-103", "АК-203", "АК-15"],
                [None, None, None, None, None, "ОЦ-14 <Гроза>", "АШ-12"],
                [None, None, None, None, "АКМ <Тишина>", "АС <Вал>", "АМБ-17"],
                [None, None, None, None, None, "ВСС <Винторез>", None]
            ]
        },
        {
            "title": "ЛИНИЯ НАТО",
            "rows": [
                ["M16A1", "М16А2", "М16А3", "M4A1", "LWRC M6", "SIG 516", "KS-1"]
            ]
        }
    ]
    for branch in branches:
        new_rows = []
        for row in branch["rows"]:
            new_rows.append([items_dict.get(name) for name in row])
        branch["rows"] = new_rows
    return render_template('index.html', branches=branches)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        file = request.files.get('avatar')
        if User.query.filter_by(username=username).first():
            return "Пользователь уже существует"
        filename = 'default_avatar.png'
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"{username}.{ext}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw, avatar=filename)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        return "Неверный логин или пароль"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
