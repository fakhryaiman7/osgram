"""Mock Instagram provider for offline testing and continuous integration.

Provides rich synthetic data conforming to the BaseInstagramProvider specification,
allowing full test suite execution without paid API keys, internet connectivity,
or risk of account bans.
"""
from typing import Any, Dict, List, Optional, Tuple

from src.providers.base import (
    BaseInstagramProvider,
    ProviderError,
    TargetNotFoundError,
)


class MockInstagramProvider(BaseInstagramProvider):
    """Synthetic provider containing comprehensive mock fixtures."""

    def __init__(self, target_prefix: str = ""):
        self.target_prefix = target_prefix
        self.call_history: List[str] = []

    @property
    def name(self) -> str:
        return "Mock Provider (Synthetic)"

    @property
    def is_free(self) -> bool:
        return True

    @property
    def request_delay(self) -> float:
        return 0.0

    def _record(self, method: str):
        self.call_history.append(method)

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        self._record("get_user_by_username")
        if username == "nonexistent_target_12345":
            return {"detail": "User not found"}

        is_private = username.startswith("private")
        pk = 12345678 if username != "privateuser" else 87654321

        return {
            "user": {
                "pk": pk,
                "id": str(pk),
                "username": username,
                "full_name": f"Mock {username.capitalize()}",
                "is_private": is_private,
                "is_verified": False,
                "biography": f"Official mock profile for {username}. OSINT testing account. 🔍 #security",
                "follower_count": 42,
                "following_count": 15,
                "media_count": 3,
                "is_business": True,
                "category": "Technology & Science",
                "public_email": f"{username}@example.com",
                "contact_phone_number": "+1234567890",
                "city_name": "San Francisco",
                "address_street": "100 Market St",
                "external_url": "https://example.com/target",
                "hd_profile_pic_url_info": {
                    "url": "https://example.com/static/mock_propic_hd.jpg"
                },
                "profile_pic_url": "https://example.com/static/mock_propic.jpg",
            }
        }

    def get_user_by_id(self, pk: Any) -> Dict[str, Any]:
        self._record("get_user_by_id")
        pk_int = int(pk)
        return {
            "user": {
                "pk": pk_int,
                "id": str(pk_int),
                "username": f"user_{pk_int}",
                "full_name": f"User {pk_int}",
                "is_private": False,
                "is_verified": False,
                "public_email": f"user_{pk_int}@testosint.org" if pk_int % 2 == 0 else None,
                "contact_phone_number": f"+1555000{pk_int % 1000:03d}" if pk_int % 3 == 0 else None,
            }
        }

    def get_user_medias(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("get_user_medias")
        items = [
            {
                "id": "mock_post_101",
                "code": "Cxyz101",
                "product_type": "feed",
                "media_type": 1,  # photo
                "comment_count": 3,
                "like_count": 120,
                "caption": {"text": "Sunset at the bay! #sunset #ocean #california with @friend_one"},
                "taken_at": 1696118400,  # 2023-10-01 00:00:00
                "accessibility_caption": "Photo of a sunset over the Pacific Ocean",
                "location": {
                    "pk": 1001,
                    "name": "Golden Gate Bridge",
                    "lat": 37.8199,
                    "lng": -122.4783,
                },
                "image_versions2": {
                    "candidates": [
                        {"url": "https://example.com/photos/101_high.jpg", "width": 1080, "height": 1080},
                        {"url": "https://example.com/photos/101_thumb.jpg", "width": 320, "height": 320},
                    ]
                },
                "usertags": [
                    {"user": {"pk": 9901, "username": "friend_one", "full_name": "Friend One"}}
                ],
            },
            {
                "id": "mock_post_102",
                "code": "Cxyz102",
                "product_type": "feed",
                "media_type": 2,  # video
                "comment_count": 5,
                "like_count": 85,
                "caption": {"text": "Testing our new python osint tools #osint #python #security"},
                "taken_at": 1696204800,  # 2023-10-02 00:00:00
                "accessibility_caption": "Video showing terminal console code scrolling",
                "location": {
                    "pk": 1002,
                    "name": "San Francisco Financial District",
                    "lat": 37.7946,
                    "lng": -122.3999,
                },
                "image_versions2": {
                    "candidates": [{"url": "https://example.com/photos/102_thumb.jpg"}]
                },
                "video_versions": [
                    {"url": "https://example.com/videos/102.mp4"}
                ],
                "usertags": [],
            },
            {
                "id": "mock_post_103",
                "code": "Cxyz103",
                "product_type": "carousel_container",
                "media_type": 8,  # carousel album
                "comment_count": 2,
                "like_count": 64,
                "caption": {"text": "Album photo set #travel #photography"},
                "taken_at": 1696291200,  # 2023-10-03 00:00:00
                "carousel_media": [
                    {
                        "id": "carousel_slide_1",
                        "media_type": 1,
                        "accessibility_caption": "First slide showing landscape",
                        "image_versions2": {"candidates": [{"url": "https://example.com/photos/103_1.jpg"}]},
                    },
                    {
                        "id": "carousel_slide_2",
                        "media_type": 1,
                        "accessibility_caption": "Second slide showing coffee shop",
                        "image_versions2": {"candidates": [{"url": "https://example.com/photos/103_2.jpg"}]},
                    },
                ],
                "image_versions2": {
                    "candidates": [{"url": "https://example.com/photos/103_1.jpg"}]
                },
                "usertags": [
                    {"user": {"pk": 9902, "username": "colleague_two", "full_name": "Colleague Two"}}
                ],
            },
        ]
        return items, None

    def get_media_comments(self, media_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("get_media_comments")
        comments = [
            {
                "user_id": 9901,
                "user": {"pk": 9901, "username": "friend_one", "full_name": "Friend One"},
                "text": "Great capture! 📸",
            },
            {
                "user_id": 9902,
                "user": {"pk": 9902, "username": "colleague_two", "full_name": "Colleague Two"},
                "text": "Love this spot, let us visit again soon.",
            },
            {
                "user_id": 9903,
                "user": {"pk": 9903, "username": "commenter_three", "full_name": "Random Commenter"},
                "text": "Awesome view!",
            },
        ]
        return comments, None

    def get_user_followers(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("get_user_followers")
        users = [
            {
                "pk": 9901,
                "username": "friend_one",
                "full_name": "Friend One",
                "profile_pic_url": "https://example.com/p/1.jpg",
                "is_private": False,
                "is_verified": False,
            },
            {
                "pk": 9902,
                "username": "colleague_two",
                "full_name": "Colleague Two",
                "profile_pic_url": "https://example.com/p/2.jpg",
                "is_private": True,
                "is_verified": False,
            },
            {
                "pk": 9904,
                "username": "follower_four",
                "full_name": "Follower Four",
                "profile_pic_url": "https://example.com/p/4.jpg",
                "is_private": False,
                "is_verified": True,
            },
        ]
        return users, None

    def get_user_following(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("get_user_following")
        users = [
            {
                "pk": 9901,
                "username": "friend_one",
                "full_name": "Friend One",
                "profile_pic_url": "https://example.com/p/1.jpg",
                "is_private": False,
                "is_verified": False,
            },
            {
                "pk": 9905,
                "username": "following_five",
                "full_name": "Following Five",
                "profile_pic_url": "https://example.com/p/5.jpg",
                "is_private": False,
                "is_verified": False,
            },
        ]
        return users, None

    def get_user_tag_medias(self, user_id: Any, next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("get_user_tag_medias")
        items = [
            {
                "id": "tag_post_201",
                "code": "Ctag201",
                "product_type": "feed",
                "media_type": 1,
                "user": {"pk": 9901, "username": "friend_one", "full_name": "Friend One"},
                "caption": {"text": "Team hackathon with @testuser"},
                "taken_at": 1696000000,
                "image_versions2": {"candidates": [{"url": "https://example.com/tag1.jpg"}]},
            }
        ]
        return items, None

    def get_user_stories(self, user_id: Any) -> List[Dict[str, Any]]:
        self._record("get_user_stories")
        return [
            {
                "id": "story_301",
                "media_type": 1,
                "image_versions2": {"candidates": [{"url": "https://example.com/story1.jpg"}]},
            }
        ]

    def get_user_highlights(self, user_id: Any) -> List[Dict[str, Any]]:
        self._record("get_user_highlights")
        return [
            {
                "id": "highlight:401",
                "title": "Summer 2023",
                "media_count": 8,
                "cover_media": {
                    "cropped_image_version": {"url": "https://example.com/hcover1.jpg"}
                },
                "created_at": 1690000000,
                "latest_reel_media": 1691000000,
            }
        ]

    def search_hashtag_medias(self, hashtag: str, sort: str = "top", next_page_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("search_hashtag_medias")
        items = [
            {
                "id": f"ht_{hashtag}_1",
                "caption": {"text": f"Exploring #{hashtag} today!"},
                "user": {"pk": 9901, "username": "friend_one"},
                "like_count": 250,
                "comment_count": 15,
                "media_type": 1,
            }
        ]
        return items, None

    def search_places(self, query: str) -> List[Dict[str, Any]]:
        self._record("search_places")
        return [
            {
                "location": {
                    "pk": 1001,
                    "name": "Golden Gate Bridge",
                    "address": "Golden Gate Bridge Highway",
                    "city": "San Francisco",
                    "lat": 37.8199,
                    "lng": -122.4783,
                }
            }
        ]

    def get_location_medias(self, location_pk: Any, max_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self._record("get_location_medias")
        items = [
            {
                "id": "loc_post_501",
                "caption": {"text": "Golden Gate visit!"},
                "user": {"pk": 9901, "username": "friend_one"},
                "like_count": 180,
                "comment_count": 8,
                "media_type": 1,
            }
        ]
        return items, None
