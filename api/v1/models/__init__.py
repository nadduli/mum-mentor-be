
from .albums import Album
from .memories import Memory
from .photos import Photos
# Import models in the correct order to avoid circular dependencies
from api.v1.models.milestones import Milestone
from api.v1.models.categories import Category

__all__ = ["Milestone", "Category"]

from .albums import Album  
from .memories import Memory  
from .photos import Photos  
from .user.user import User  
"""
Top-level package for models.

Import commonly-used model modules here so that importing
`api.v1.models` will also import all model classes. This ensures
SQLAlchemy sees every declarative model before it configures mappers
and prevents relationship lookups (like "Memory") from failing due
to import-order issues.
"""

# Import model classes so they are registered on package import
from .albums import Album  # noqa: F401
from .memories import Memory  # noqa: F401
from .photos import Photos  # noqa: F401
from .user.user import User  # noqa: F401
