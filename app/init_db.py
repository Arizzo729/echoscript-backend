from app.db import Base, engine
from app.models import User

Base.metadata.create_all(bind=engine)
