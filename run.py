import app
import views


if __name__ == "__main__":
    app.web.run_app(app.app, host='127.0.0.1', port=8000)