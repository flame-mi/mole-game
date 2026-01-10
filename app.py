
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# 用于 session/flash 的密钥，入门示例直接写死
app.config["SECRET_KEY"] = "mole-game-secret"
# SQLite 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 初始化数据库
db = SQLAlchemy(app)

# 用户模型：存用户名和密码哈希
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    score = db.relationship("Score", backref="user", uselist=False)

# 成绩模型：只存最高分
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    best_score = db.Column(db.Integer, default=0)

# 获取当前登录用户
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

# 获取排行榜前 10 名
def get_leaderboard():
    rows = (
        Score.query.join(User)
        .order_by(Score.best_score.desc(), User.username.asc())
        .limit(10)
        .all()
    )
    return [{"username": row.user.username, "score": row.best_score} for row in rows]

@app.route("/")
def index():
    user = get_current_user()
    leaderboard = get_leaderboard()
    return render_template(
        "index.html",
        is_logged_in=bool(user),
        username=user.username if user else "",
        leaderboard=leaderboard,
    )

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        flash("用户名和密码不能为空")
        return redirect(url_for("index"))

    if User.query.filter_by(username=username).first():
        flash("用户名已存在，请换一个")
        return redirect(url_for("index"))

    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    # 创建对应的分数记录
    score = Score(user_id=user.id, best_score=0)
    db.session.add(score)
    db.session.commit()

    session["user_id"] = user.id
    flash("注册成功，已自动登录！")
    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("用户名或密码错误")
        return redirect(url_for("index"))

    session["user_id"] = user.id
    flash("登录成功，开始游戏吧！")
    return redirect(url_for("index"))

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    flash("已退出登录")
    return redirect(url_for("index"))

@app.route("/submit_score", methods=["POST"])
def submit_score():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "请先登录"}), 401

    data = request.get_json(silent=True) or {}
    try:
        score_value = int(data.get("score", 0))
    except (TypeError, ValueError):
        score_value = 0

    # 更新最高分
    record = user.score
    if record is None:
        record = Score(user_id=user.id, best_score=0)
        db.session.add(record)

    is_new_record = score_value > record.best_score
    if is_new_record:
        record.best_score = score_value
        db.session.commit()

    leaderboard = get_leaderboard()
    return jsonify({
        "ok": True,
        "best": record.best_score,
        "new_record": is_new_record,
        "leaderboard": leaderboard,
    })
# 首次启动时创建数据库表
    with app.app_context():
        db.create_all()
if __name__ == "__main__":
    

    # 启动开发服务器，debug 方便新手调试
    app.run(debug=True)

