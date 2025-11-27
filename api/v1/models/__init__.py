# Import model classes so they are registered on package import
from .albums import Album  # noqa: F401
from .memories import Memory  # noqa: F401
from .photos import Photos  # noqa: F401
from .user.user import User  # noqa: F401

# Community models
from .community import Post, PostPhoto, PostLikes, PostComments  # noqa: F401

# Resource models
from .resource import Resource, ResourceMedia, ResourceLikes, ResourceComment, SavedForLater  # noqa: F401

# Journal models
from .journal.journal import Journal  # noqa: F401
from .journal.journal_photos import JournalPhoto  # noqa: F401
from .journal.journal_category import JournalCategory  # noqa: F401
from .journal.journal_likes import JournalLike  # noqa: F401
from .journal.journal_comments import JournalComment  # noqa: F401

# Milestone and Category models
from .milestones import Milestone  # noqa: F401
from .categories import Category  # noqa: F401

__all__ = [
    "Album",
    "Memory",
    "Photos",
    "User",
    "Post",
    "PostPhoto",
    "PostLikes",
    "PostComments",
    "Resource",
    "ResourceMedia",
    "ResourceLikes",
    "ResourceComment",
    "SavedForLater",
    "Journal",
    "JournalPhoto",
    "JournalCategory",
    "JournalLike",
    "JournalComment",
    "Milestone",
    "Category",
]