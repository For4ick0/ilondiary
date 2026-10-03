# serve.py
import http.server
import socketserver

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Сервер запущен: http://localhost:{PORT}")
    print("Ctrl+C для остановки")
    httpd.serve_forever()
