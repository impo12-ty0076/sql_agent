# Import all models here for Alembic to detect them
from .base_model import BaseModel
from .models.user import User, UserPreference, UserDatabasePermission, UserSession, Role