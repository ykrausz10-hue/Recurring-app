from wsgiref.simple_server import make_server

from .app import make_app


if __name__ == "__main__":
    app = make_app()
    with make_server("0.0.0.0", 8000, app) as httpd:
        print("Serving on http://0.0.0.0:8000")
        httpd.serve_forever()
