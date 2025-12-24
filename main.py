from bughouse.web_server import app
import uvicorn
import os
import socket

def get_local_ip():
    """Получить локальный IP адрес сервера"""
    try:
        # Создаем временное подключение к публичному DNS
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "localhost"

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    local_ip = get_local_ip()
    
    print("=" * 50)
    print(f"Сервер запускается на порту: {port}")
    print(f"Локальный доступ:           http://localhost:{port}")
    print(f"Доступ в сети:              http://{local_ip}:{port}")
    print("=" * 50)
    print("Сервер запущен! Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=port)