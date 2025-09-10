from app.db.session import engine
from app import models

if __name__ == '__main__':
    print("Creating database tables...")
    models.SQLModel.metadata.create_all(bind=engine)
    print("Done.")
