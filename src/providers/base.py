"""Provider abstraction for Instagram data sources.

Enables swapping backend data providers (Instagrapi, Mock/Offline testing,
Meta Graph API) without modifying Osintgram's CLI or OSINT service layer.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class ProviderError(Exception):
    """Base error for Instagram data providers."""


class UnsupportedCapabilityError(ProviderError):
    """Raised when an operation is not supported by the active provider."""


class TargetNotFoundError(ProviderError):
    """Target user could not be found."""


class RateLimitExceededError(ProviderError):
    """Provider rate limit reached."""


class BaseInstagramProvider(ABC):
    """Abstract interface defining required capabilities for Instagram data access.
    
    Subclasses must implement the core methods. For backwards compatibility with
    OsintgramService, standard aliases matching the legacy service signatures are
    provided.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this provider."""
        raise NotImplementedError

    @property
    def is_free(self) -> bool:
        """Whether this provider operates without paid API credits."""
        return True

    @property
    def request_delay(self) -> float:
        """Recommended delay (in seconds) between requests to prevent rate limiting."""
        return 0.5

    # ---- Core Provider Interface ----

    @abstractmethod
    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Fetch profile information by username. Returns {"user": {...}} or raises."""
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, pk: Any) -> Dict[str, Any]:
        """Fetch user by numeric primary key / ID."""
        raise NotImplementedError

    @abstractmethod
    def get_user_medias(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch a page of posts by user ID. Returns (items, next_page_id)."""
        raise NotImplementedError

    @abstractmethod
    def get_media_comments(self, media_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch comments for a media post. Returns (comments, next_page_id)."""
        raise NotImplementedError

    @abstractmethod
    def get_user_followers(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch followers of a user. Returns (users, next_page_id)."""
        raise NotImplementedError

    @abstractmethod
    def get_user_following(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch accounts followed by user. Returns (users, next_page_id)."""
        raise NotImplementedError

    @abstractmethod
    def get_user_tag_medias(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch posts where user is tagged. Returns (items, next_page_id)."""
        raise NotImplementedError

    @abstractmethod
    def get_user_stories(self, user_id: Any) -> List[Dict[str, Any]]:
        """Fetch active stories for a user. Returns list of story item dicts."""
        raise NotImplementedError

    @abstractmethod
    def get_user_highlights(self, user_id: Any) -> List[Dict[str, Any]]:
        """Fetch story highlights for a user. Returns list of highlight tray dicts."""
        raise NotImplementedError

    def get_user_suggested_profiles(self, user_id: Any) -> List[Dict[str, Any]]:
        """Fetch suggested profiles for a user. Raises UnsupportedCapabilityError if not available."""
        raise UnsupportedCapabilityError(f"Suggested profiles are not supported by {self.name}.")

    def get_user_about(self, user_id: Any) -> Dict[str, Any]:
        """Fetch account history/about info. Raises UnsupportedCapabilityError if not available."""
        raise UnsupportedCapabilityError(f"'About this account' is not supported by {self.name}.")

    @abstractmethod
    def search_hashtag_medias(self, hashtag: str, sort: str = "top", next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Search medias by hashtag."""
        raise NotImplementedError

    @abstractmethod
    def search_places(self, query: str) -> List[Dict[str, Any]]:
        """Search places by text query."""
        raise NotImplementedError

    @abstractmethod
    def get_location_medias(self, location_pk: Any, max_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch recent medias for a place/location."""
        raise NotImplementedError

    # ---- Backwards-Compatible Legacy / Service Adapter Signatures ----
    # These adapt the provider directly into the shapes that OsintgramService expects.

    def user_by_username_v2(self, username: str) -> Dict[str, Any]:
        return self.get_user_by_username(username)

    def user_by_id_v2(self, pk: Any) -> Dict[str, Any]:
        return self.get_user_by_id(pk)

    def user_medias_g2(self, user_id: Any, next_page_id: Optional[str] = None) -> Dict[str, Any]:
        items, cursor = self.get_user_medias(user_id, next_page_id=next_page_id)
        return {"response": {"items": items}, "next_page_id": cursor or None}

    def media_comments_v2(self, media_id: Any, page_id: str = "") -> Dict[str, Any]:
        comments, cursor = self.get_media_comments(media_id, next_page_id=page_id or None)
        return {"response": {"comments": comments}, "next_page_id": cursor or None}

    def user_followers_g2(self, user_id: Any, page_id: Optional[str] = None) -> Dict[str, Any]:
        users, cursor = self.get_user_followers(user_id, next_page_id=page_id)
        return {"response": {"users": users}, "next_page_id": cursor or None}

    def user_following_g2(self, user_id: Any, page_id: Optional[str] = None) -> Dict[str, Any]:
        users, cursor = self.get_user_following(user_id, next_page_id=page_id)
        return {"response": {"users": users}, "next_page_id": cursor or None}

    def user_tag_medias_v2(self, user_id: Any, page_id: str = "") -> Dict[str, Any]:
        items, cursor = self.get_user_tag_medias(user_id, next_page_id=page_id or None)
        return {"response": {"items": items}, "next_page_id": cursor or None}

    def user_stories_v2(self, user_id: Any) -> Dict[str, Any]:
        items = self.get_user_stories(user_id)
        return {"reel": {"items": items}}

    def user_highlights_v2(self, user_id: Any, **kwargs) -> Dict[str, Any]:
        tray = self.get_user_highlights(user_id)
        return {"response": {"tray": tray}}

    def user_suggested_profiles_v2(self, user_id: Any, **kwargs) -> Dict[str, Any]:
        users = self.get_user_suggested_profiles(user_id)
        return {"response": {"users": users}}

    def user_about_gql(self, user_id: Any, **kwargs) -> Dict[str, Any]:
        data = self.get_user_about(user_id)
        return {"response": data}

    def hashtag_medias_top_v2(self, name: str, page_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        items, cursor = self.search_hashtag_medias(name, sort="top", next_page_id=page_id)
        return {"response": {"items": items}, "next_page_id": cursor or None}

    def hashtag_medias_recent_v2(self, name: str, page_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        items, cursor = self.search_hashtag_medias(name, sort="recent", next_page_id=page_id)
        return {"response": {"items": items}, "next_page_id": cursor or None}

    def fbsearch_places_v2(self, query: str, **kwargs) -> Dict[str, Any]:
        places = self.search_places(query)
        return {"items": places}

    def location_medias_recent_chunk_v1(self, location_pk: Any, max_id: Optional[str] = None, **kwargs) -> List[Any]:
        items, cursor = self.get_location_medias(location_pk, max_id=max_id)
        return [items, cursor or None]
