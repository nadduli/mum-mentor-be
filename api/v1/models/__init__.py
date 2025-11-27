
from .albums import Album
from .memories import Memory
from .photos import Photos

from api.v1.models.milestones import Milestone
from api.v1.models.categories import Category

__all__ = ["Milestone", "Category"]

from .albums import Album  
from .memories import Memory  
from .photos import Photos  
from .user.user import User  


# Import model classes so they are registered on package import
from .albums import Album  # noqa: F401
from .memories import Memory  # noqa: F401
from .photos import Photos  # noqa: F401
from .user.user import User  # noqa: F401
from .community import Post, PostPhoto, PostLikes, PostComments  # noqa: F401
from .resource import Resource, ResourceMedia, ResourceLikes, ResourceComment, SavedForLater  # noqa: F401

from .journal.journal import Journal  # noqa: F401
from .journal.journal_photos import JournalPhoto  # noqa: F401
from .journal.journal_category import JournalCategory  # noqa: F401
from .journal.journal_likes import JournalLike  # noqa: F401
from .journal.journal_comments import JournalComment  # noqa:
