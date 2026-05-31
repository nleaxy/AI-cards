from app import app
from models import db, User

def promote_user(username):
    with app.app_context():
        # Find user by username
        user = User.query.filter_by(username=username).first()
        if user:
            # Change role to admin
            user.role = 'admin'
            db.session.commit()
            print(f"Успешно! Пользователь '{username}' теперь администратор.")
        else:
            print(f"Ошибка: Пользователь '{username}' не найден.")

if __name__ == "__main__":
    username = input("Введите имя пользователя (username), которого хотите сделать админом: ")
    promote_user(username)
