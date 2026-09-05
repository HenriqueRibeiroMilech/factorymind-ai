from app import create_app
from app.modules.incidents.storage import init_db

if __name__ == "__main__":
    with create_app().app_context():
        init_db()
    print("Banco SQLite pronto. Registros existentes foram preservados.")
