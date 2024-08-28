from lms import create_app
from dotenv import load_dotenv

load_dotenv()
app = create_app()


@app.route("/")
def home():
    return "Library Management System(TMS LIBRARY)"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
