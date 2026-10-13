"""Free Instagrapi backend provider implementing BaseInstagramProvider.

Uses authenticated Instagram mobile session settings saved via
`scripts/instagrapi_login.py`. Zero paid API cost.
"""
import configparser
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.providers.base import (
    BaseInstagramProvider,
    ProviderError,
    TargetNotFoundError,
    UnsupportedCapabilityError,
)

DEFAULT_SESSION_PATH = "config/instagrapi_session.json"


class InstagrapiBackendError(ProviderError):
    """Raised when the instagrapi backend cannot authenticate or initialize."""


def resolve_instagrapi_credentials(
    credentials_path: str = "config/credentials.ini",
) -> tuple[Optional[str], Optional[str]]:
    """Resolve (username, password) from environment or credentials.ini."""
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    if username and password:
        return username, password
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(credentials_path)
        username = username or parser.get("Credentials", "username", fallback=None) or None
        password = password or parser.get("Credentials", "password", fallback=None) or None
    except Exception:
        pass
    return username, password


def session_exists(session_path: str = DEFAULT_SESSION_PATH) -> bool:
    return Path(session_path).exists()


class InstagrapiProvider(BaseInstagramProvider):
    """Instagram data provider powered by instagrapi."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_path: str = DEFAULT_SESSION_PATH,
    ):
        session_file = Path(session_path)
        if not session_file.exists():
            raise InstagrapiBackendError(
                f"No saved instagrapi session at {session_path}. Run "
                "`python scripts/instagrapi_login.py` once from a terminal to "
                "log in (and complete any challenge) before using this provider."
            )

        from instagrapi import Client

        self._cl = Client()
        self._cl.load_settings(session_file)

        u = username
        p = password
        if not u or not p:
            u, p = resolve_instagrapi_credentials()

        if u and p:
            try:
                self._cl.login(u, p)
            except Exception as e:
                raise InstagrapiBackendError(
                    f"instagrapi login failed using the saved session: {e}. "
                    "Re-run `python scripts/instagrapi_login.py` to refresh it."
                ) from e

    @property
    def name(self) -> str:
        return "instagrapi (Free Mobile Client)"

    @property
    def is_free(self) -> bool:
        return True

    @property
    def request_delay(self) -> float:
        return 1.0

    @staticmethod
    def _full_user_to_dict(user) -> dict:
        d = {
            "pk": user.pk,
            "username": user.username,
            "full_name": user.full_name,
            "is_private": user.is_private,
            "is_verified": user.is_verified,
            "biography": getattr(user, "biography", None),
            "follower_count": getattr(user, "follower_count", None),
            "following_count": getattr(user, "following_count", None),
            "media_count": getattr(user, "media_count", None),
            "is_business": getattr(user, "is_business", None),
            "public_email": getattr(user, "public_email", None),
            "contact_phone_number": getattr(user, "contact_phone_number", None),
            "city_name": getattr(user, "city_name", None),
            "address_street": getattr(user, "address_street", None),
            "category": getattr(user, "category", None),
        }
        for field in (
            "external_url",
            "account_type",
            "category_name",
            "business_category_name",
            "business_contact_method",
            "public_phone_country_code",
            "public_phone_number",
            "zip",
            "latitude",
            "longitude",
            "instagram_location_id",
        ):
            value = getattr(user, field, None)
            if value not in (None, ""):
                d[field] = str(value) if field == "external_url" else value
        pic_hd = getattr(user, "profile_pic_url_hd", None)
        if pic_hd:
            d["hd_profile_pic_url_info"] = {"url": str(pic_hd)}
        d["id"] = user.pk
        return d

    @staticmethod
    def _short_user_to_dict(user) -> dict:
        return {
            "pk": user.pk,
            "id": user.pk,
            "username": user.username,
            "full_name": user.full_name,
            "is_private": user.is_private,
            "is_verified": user.is_verified,
            "profile_pic_url": str(getattr(user, "profile_pic_url", "")) if getattr(user, "profile_pic_url", None) else None,
        }

    @staticmethod
    def _media_to_dict(media) -> dict:
        taken_at_val = getattr(media, "taken_at", None)
        if isinstance(taken_at_val, (int, float)):
            taken_at_ts = int(taken_at_val)
        elif hasattr(taken_at_val, "timestamp"):
            taken_at_ts = int(taken_at_val.timestamp())
        else:
            taken_at_ts = None

        d = {
            "id": getattr(media, "id", getattr(media, "pk", None)),
            "pk": getattr(media, "pk", getattr(media, "id", None)),
            "code": getattr(media, "code", None),
            "product_type": getattr(media, "product_type", "feed"),
            "comment_count": getattr(media, "comment_count", 0) or 0,
            "like_count": getattr(media, "like_count", 0) or 0,
            "media_type": getattr(media, "media_type", 1),
            "accessibility_caption": getattr(media, "accessibility_caption", None),
            "caption": {"text": media.caption_text} if getattr(media, "caption_text", None) else None,
            "taken_at": taken_at_ts,
            "user": InstagrapiProvider._short_user_to_dict(media.user) if getattr(media, "user", None) else {},
            "usertags": [
                {
                    "user": {
                        "pk": tag.user.pk,
                        "username": tag.user.username,
                        "full_name": tag.user.full_name,
                    }
                }
                for tag in (media.usertags or [])
                if tag.user
            ],
        }
        if media.location and media.location.lat is not None and media.location.lng is not None:
            d["location"] = {"lat": media.location.lat, "lng": media.location.lng}

        if media.media_type == 8 and media.resources:
            d["carousel_media"] = []
            for resource in media.resources:
                item = {
                    "id": resource.pk,
                    "media_type": resource.media_type,
                    "accessibility_caption": getattr(resource, "accessibility_caption", None),
                }
                if resource.thumbnail_url:
                    item["image_versions2"] = {"candidates": [{"url": str(resource.thumbnail_url)}]}
                if resource.media_type == 2 and resource.video_url:
                    item["video_versions"] = [{"url": str(resource.video_url)}]
                d["carousel_media"].append(item)
        else:
            candidates = []
            if media.image_versions2 and media.image_versions2.candidates:
                candidates = [{"url": str(c.url)} for c in media.image_versions2.candidates]
            elif media.thumbnail_url:
                candidates = [{"url": str(media.thumbnail_url)}]
            if candidates:
                d["image_versions2"] = {"candidates": candidates}
            if media.media_type == 2 and media.video_url:
                d["video_versions"] = [{"url": str(media.video_url)}]
        return d

    @staticmethod
    def _comment_to_dict(comment) -> dict:
        user = comment.user
        return {
            "user_id": user.pk if user else None,
            "user": {"pk": user.pk, "username": user.username, "full_name": user.full_name} if user else {},
            "text": comment.text,
        }

    @staticmethod
    def _story_to_dict(story) -> dict:
        d = {"id": story.id, "media_type": story.media_type}
        if story.thumbnail_url:
            d["image_versions2"] = {"candidates": [{"url": str(story.thumbnail_url)}]}
        if story.media_type == 2 and story.video_url:
            d["video_versions"] = [{"url": str(story.video_url)}]
        return d

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        try:
            user = self._cl.user_info_by_username_v1(username)
        except Exception as e:
            if "not found" in str(e).lower() or type(e).__name__ == "UserNotFound":
                return {"detail": str(e)}
            return {"error": str(e)}
        return {"user": self._full_user_to_dict(user)}

    def get_user_by_id(self, pk: Any) -> Dict[str, Any]:
        try:
            user = self._cl.user_info_v1(str(pk))
        except Exception as e:
            return {"error": str(e)}
        return {"user": self._full_user_to_dict(user)}

    def get_user_medias(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        medias, cursor = self._cl.user_medias_paginated_v1(str(user_id), amount=33, end_cursor=next_page_id or "")
        return [self._media_to_dict(m) for m in medias], cursor or None

    def get_media_comments(self, media_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        try:
            comments, cursor = self._cl.media_comments_chunk(str(media_id), max_amount=20, min_id=next_page_id or None)
        except Exception as e:
            if type(e).__name__ == "MediaNotFound":
                raise RuntimeError(f"Entries not found: {e}") from e
            raise
        return [self._comment_to_dict(c) for c in comments], cursor or None

    def get_user_followers(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        users, cursor = self._cl.user_followers_v1_chunk(str(user_id), max_amount=50, max_id=next_page_id or "")
        return [self._short_user_to_dict(u) for u in users], cursor or None

    def get_user_following(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        users, cursor = self._cl.user_following_v1_chunk(str(user_id), max_amount=50, max_id=next_page_id or "")
        return [self._short_user_to_dict(u) for u in users], cursor or None

    def get_user_tag_medias(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        medias, cursor = self._cl.usertag_medias_paginated_v1(str(user_id), amount=33, end_cursor=next_page_id or "")
        return [self._media_to_dict(m) for m in medias], cursor or None

    def get_user_stories(self, user_id: Any) -> List[Dict[str, Any]]:
        stories = self._cl.user_stories_v1(str(user_id))
        return [self._story_to_dict(s) for s in stories]

    def get_user_highlights(self, user_id: Any) -> List[Dict[str, Any]]:
        tray = []
        for h in self._cl.user_highlights(str(user_id)):
            cover = getattr(h, "cover_media", None)
            url = getattr(getattr(cover, "cropped_image_version", None), "url", None) if cover else None
            tray.append({
                "id": f"highlight:{h.pk}",
                "title": h.title,
                "media_count": h.media_count,
                "cover_media": {"cropped_image_version": {"url": str(url)} if url else {}},
                "created_at": None,
                "latest_reel_media": None,
            })
        return tray

    def search_hashtag_medias(self, hashtag: str, sort: str = "top", next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        chunked = getattr(self._cl, "hashtag_medias_v1_chunk", None)
        if chunked is not None:
            medias, cursor = chunked(hashtag, max_amount=30, tab_key=sort, max_id=next_page_id or None)
        else:
            one_shot = getattr(self._cl, f"hashtag_medias_{sort}_v1", None)
            medias = one_shot(hashtag, amount=30) if (one_shot and not next_page_id) else []
            cursor = None
        return [self._media_to_dict(m) for m in medias], cursor or None

    def search_places(self, query: str) -> List[Dict[str, Any]]:
        places = self._cl.fbsearch_places(query)
        return [{"location": {
            "pk": location.pk,
            "name": location.name,
            "address": location.address,
            "city": location.city,
            "lat": location.lat,
            "lng": location.lng,
        }} for location in places if location.pk]

    def get_location_medias(self, location_pk: Any, max_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        chunked = getattr(self._cl, "location_medias_v1_chunk", None)
        if chunked is not None:
            medias, cursor = chunked(int(location_pk), max_amount=30, tab_key="recent", max_id=max_id or None)
        else:
            medias = self._cl.location_medias_recent_v1(int(location_pk), amount=30) if not max_id else []
            cursor = None
        return [self._media_to_dict(m) for m in medias], cursor or None
