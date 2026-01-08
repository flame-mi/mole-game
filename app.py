from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    # 主页：渲染游戏页面
    return render_template("index.html")

if __name__ == "__main__":
    # 启动开发服务器，debug 方便新手调试
    app.run(debug=True)
