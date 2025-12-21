from bughouse.web_server import app
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Bughouse сервер запущен!")
    print(f"Открой в браузере: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
