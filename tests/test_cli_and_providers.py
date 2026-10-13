"""Unit tests for the provider abstraction layer and restored CLI interface."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.Osintgram import Osintgram
from src.providers import (
    BaseInstagramProvider,
    MockInstagramProvider,
    ProviderError,
    get_provider,
)


def test_mock_provider_conforms_to_interface():
    provider = MockInstagramProvider()
    assert isinstance(provider, BaseInstagramProvider)
    assert provider.is_free is True
    assert provider.name == "Mock Provider (Synthetic)"

    # Test user lookup
    user_data = provider.get_user_by_username("testuser")
    assert "user" in user_data
    u = user_data["user"]
    assert u["username"] == "testuser"
    assert u["pk"] == 12345678
    assert u["is_private"] is False
    assert u["follower_count"] == 42

    # Test media lookup
    medias, cursor = provider.get_user_medias(12345678)
    assert len(medias) == 3
    assert cursor is None
    assert medias[0]["id"] == "mock_post_101"
    assert medias[0]["media_type"] == 1

    # Test followers lookup
    followers, fcursor = provider.get_user_followers(12345678)
    assert len(followers) == 3
    assert followers[0]["username"] == "friend_one"


def test_provider_factory_rejects_hikerapi():
    with pytest.raises(ProviderError) as exc_info:
        get_provider("hikerapi")
    assert "paid service and has been removed" in str(exc_info.value)


def test_provider_factory_resolves_mock(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_PROVIDER", raising=False)
    monkeypatch.delenv("INSTAGRAM_BACKEND", raising=False)
    provider = get_provider("mock")
    assert isinstance(provider, MockInstagramProvider)


def test_cli_info_command(tmp_path):
    output_dir = str(tmp_path / "out")
    api = Osintgram("testuser", is_file=True, is_json=True, is_cli=True, output_dir=output_dir, provider="mock")
    api.get_user_info()

    json_file = Path(output_dir) / "testuser" / "testuser_info.json"
    assert json_file.exists()
    data = json.loads(json_file.read_text())
    assert data["id"] == 12345678
    assert data["email"] == "testuser@example.com"
    assert data["edge_followed_by"] == 42


def test_cli_followers_and_followings(tmp_path):
    output_dir = str(tmp_path / "out")
    api = Osintgram("testuser", is_file=True, is_json=True, is_cli=True, output_dir=output_dir, provider="mock")
    api.get_followers()
    api.get_followings()

    f_txt = Path(output_dir) / "testuser" / "testuser_followers.txt"
    f_json = Path(output_dir) / "testuser" / "testuser_followers.json"
    assert f_txt.exists()
    assert f_json.exists()
    f_data = json.loads(f_json.read_text())
    assert "followers" in f_data
    assert len(f_data["followers"]) == 3
    assert f_data["followers"][0]["username"] == "friend_one"

    fw_txt = Path(output_dir) / "testuser" / "testuser_followings.txt"
    fw_json = Path(output_dir) / "testuser" / "testuser_followings.json"
    assert fw_txt.exists()
    assert fw_json.exists()
    fw_data = json.loads(fw_json.read_text())
    assert "followings" in fw_data
    assert len(fw_data["followings"]) == 2


def test_cli_comments_and_likes(tmp_path):
    output_dir = str(tmp_path / "out")
    api = Osintgram("testuser", is_file=True, is_json=True, is_cli=True, output_dir=output_dir, provider="mock")
    api.get_total_comments()
    api.get_total_likes()
    api.get_comment_data()

    c_json = Path(output_dir) / "testuser" / "testuser_comments.json"
    assert c_json.exists()
    c_data = json.loads(c_json.read_text())
    assert c_data["comment_counter"] == 10
    assert c_data["posts"] == 3

    l_json = Path(output_dir) / "testuser" / "testuser_likes.json"
    assert l_json.exists()
    l_data = json.loads(l_json.read_text())
    assert l_data["like_counter"] == 269

    cd_json = Path(output_dir) / "testuser" / "testuser_comment_data.json"
    assert cd_json.exists()
    cd_data = json.loads(cd_json.read_text())
    assert "Comments" in cd_data
    assert len(cd_data["Comments"]) == 9


def test_cli_captions_and_hashtags(tmp_path):
    output_dir = str(tmp_path / "out")
    api = Osintgram("testuser", is_file=True, is_json=True, is_cli=True, output_dir=output_dir, provider="mock")
    api.get_captions()
    api.get_hashtags()

    cap_json = Path(output_dir) / "testuser" / "testuser_captions.json"
    assert cap_json.exists()
    cap_data = json.loads(cap_json.read_text())
    assert len(cap_data["captions"]) == 3

    ht_json = Path(output_dir) / "testuser" / "testuser_hashtags.json"
    assert ht_json.exists()
    ht_data = json.loads(ht_json.read_text())
    assert "#sunset" in ht_data["hashtags"]
    assert "#security" in ht_data["hashtags"]


def test_cli_mediatype_and_tags(tmp_path):
    output_dir = str(tmp_path / "out")
    api = Osintgram("testuser", is_file=True, is_json=True, is_cli=True, output_dir=output_dir, provider="mock")
    api.get_media_type()
    api.get_people_tagged_by_user()
    api.get_people_who_commented()
    api.get_people_who_tagged()

    mt_json = Path(output_dir) / "testuser" / "testuser_mediatype.json"
    assert mt_json.exists()
    mt_data = json.loads(mt_json.read_text())
    assert mt_data["photos"] == 1
    assert mt_data["videos"] == 1
    assert mt_data["carousels"] == 1

    tag_json = Path(output_dir) / "testuser" / "testuser_tagged.json"
    assert tag_json.exists()

    comm_json = Path(output_dir) / "testuser" / "testuser_users_who_commented.json"
    assert comm_json.exists()

    wtag_json = Path(output_dir) / "testuser" / "testuser_users_who_tagged.json"
    assert wtag_json.exists()


def test_cli_contact_info(tmp_path):
    output_dir = str(tmp_path / "out")
    api = Osintgram("testuser", is_file=True, is_json=True, is_cli=True, output_dir=output_dir, provider="mock")
    api.get_fwersemail()

    fe_json = Path(output_dir) / "testuser" / "testuser_fwersemail.json"
    assert fe_json.exists()
    fe_data = json.loads(fe_json.read_text())
    assert "fwersemail" in fe_data
    assert len(fe_data["fwersemail"]) == 2
    assert fe_data["fwersemail"][0]["email"] == "user_9902@testosint.org"


def test_main_cli_subprocess(tmp_path):
    cmd = [
        sys.executable,
        "main.py",
        "testuser",
        "-p", "mock",
        "-c", "info",
        "-o", str(tmp_path / "cli_out"),
        "-j",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    assert res.returncode == 0
    assert "[ID] 12345678" in res.stdout
    assert "Mock Testuser" in res.stdout
    info_file = tmp_path / "cli_out" / "testuser" / "testuser_info.json"
    assert info_file.exists()
