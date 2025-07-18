from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Kaspi сервер работает!"

if __name__ == "__main__":
    app.run()
