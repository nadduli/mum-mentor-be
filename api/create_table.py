import uuid

from api.db.database import engine
from api.db.database import Base

from api.v1.models.user.user import User, UserAuthSession, UserActivityLog

# print("Creating tables...")
# Base.metadata.create_all(bind=engine)
# print("Done.")


print(str(uuid.uuid4()))