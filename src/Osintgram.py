"""Osintgram CLI controller.

Implements the original interactive CLI commands and output formats,
connecting to backend providers through the provider abstraction without
requiring paid HikerAPI tokens.
"""
import datetime
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from prettytable import PrettyTable

from src import printcolors as pc
from src.osint_service import OsintgramService, OsintServiceError
from src.providers import (
    BaseInstagramProvider,
    ProviderError,
    TargetNotFoundError,
    UnsupportedCapabilityError,
    get_provider,
)


class Osintgram:
    """Core CLI engine for Osintgram, providing original shell commands."""

    def __init__(
        self,
        target: str,
        is_file: bool = False,
        is_json: bool = False,
        is_cli: bool = False,
        output_dir: Optional[str] = "output",
        clear_cookies: bool = False,
        provider: Optional[str] = None,
    ):
        self.output_root = output_dir or "output"
        self.output_dir = self.output_root
        self.cli_mode = is_cli
        self.writeFile = bool(is_file)
        self.jsonDump = bool(is_json)

        # Provider initialization
        try:
            self._provider = get_provider(provider)
        except Exception as e:
            pc.printout(f"Provider initialization error: {e}\n", pc.RED)
            sys.exit(1)

        self.service: Optional[OsintgramService] = None
        self.target = ""
        self.target_id = None
        self.is_private = False
        self.user = {}

        if target:
            self.setTarget(target)

    def setTarget(self, target: str):
        """Set or switch the analysis target."""
        clean_target = target.strip().lstrip("@")
        self.target = clean_target

        try:
            self.service = OsintgramService(clean_target, self._provider)
            self.user = self.service.user
            self.target_id = self.service.target_id
            self.is_private = self.service.is_private
        except Exception as e:
            pc.printout(f"Error resolving target @{clean_target}: {e}\n", pc.RED)
            if self.cli_mode:
                sys.exit(2)
            return

        self.output_dir = os.path.join(self.output_root, str(self.target))
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self.__printTargetBanner__()

    def __printTargetBanner__(self):
        pc.printout("Target: ", pc.GREEN)
        pc.printout(str(self.target), pc.CYAN)
        pc.printout(f" [{self.target_id}]")
        if self.is_private:
            pc.printout(" [PRIVATE PROFILE]", pc.BLUE)
        print("\n")

    def check_private_profile(self) -> bool:
        if self.is_private:
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return True
        return False

    def set_write_file(self, flag: bool):
        self.writeFile = flag
        status = "enabled" if flag else "disabled"
        color = pc.GREEN if flag else pc.RED
        pc.printout("Write to file: ")
        pc.printout(f"{status}\n", color)

    def set_json_dump(self, flag: bool):
        self.jsonDump = flag
        status = "enabled" if flag else "disabled"
        color = pc.GREEN if flag else pc.RED
        pc.printout("Export to JSON: ")
        pc.printout(f"{status}\n", color)

    def clear_cache(self):
        """Clear local request cache."""
        cache_path = Path("cache/requests.sqlite3")
        if cache_path.exists():
            try:
                cache_path.unlink()
                pc.printout("Request cache cleared successfully.\n", pc.GREEN)
            except Exception as e:
                pc.printout(f"Failed to clear cache: {e}\n", pc.RED)
        else:
            pc.printout("Cache is already empty.\n", pc.YELLOW)

    def change_target(self):
        pc.printout("Insert new target username: ", pc.YELLOW)
        new_target = input().strip()
        if new_target:
            self.setTarget(new_target)

    # ---- 1. info ----
    def get_user_info(self):
        if not self.user:
            pc.printout("Target not initialized.\n", pc.RED)
            return

        data = self.user
        pc.printout("[ID] ", pc.GREEN)
        pc.printout(f"{data.get('pk')}\n")
        pc.printout("[FULL NAME] ", pc.RED)
        pc.printout(f"{data.get('full_name')}\n")
        pc.printout("[BIOGRAPHY] ", pc.CYAN)
        pc.printout(f"{data.get('biography')}\n")
        pc.printout("[FOLLOWED] ", pc.BLUE)
        pc.printout(f"{data.get('follower_count')}\n")
        pc.printout("[FOLLOW] ", pc.GREEN)
        pc.printout(f"{data.get('following_count')}\n")
        pc.printout("[MEDIA] ", pc.CYAN)
        pc.printout(f"{data.get('media_count')}\n")
        pc.printout("[BUSINESS ACCOUNT] ", pc.RED)
        pc.printout(f"{data.get('is_business')}\n")
        if data.get("is_business") and data.get("category"):
            pc.printout("[BUSINESS CATEGORY] ")
            pc.printout(f"{data.get('category')}\n")
        pc.printout("[VERIFIED ACCOUNT] ", pc.CYAN)
        pc.printout(f"{data.get('is_verified')}\n")
        if data.get("public_email"):
            pc.printout("[EMAIL] ", pc.BLUE)
            pc.printout(f"{data.get('public_email')}\n")
        if data.get("hd_profile_pic_url_info", {}).get("url"):
            pc.printout("[HD PROFILE PIC] ", pc.GREEN)
            pc.printout(f"{data['hd_profile_pic_url_info']['url']}\n")
        if data.get("city_name"):
            pc.printout("[CITY] ", pc.YELLOW)
            pc.printout(f"{data.get('city_name')}\n")
        if data.get("address_street"):
            pc.printout("[ADDRESS STREET] ", pc.RED)
            pc.printout(f"{data.get('address_street')}\n")
        if data.get("contact_phone_number"):
            pc.printout("[CONTACT PHONE NUMBER] ", pc.CYAN)
            pc.printout(f"{data.get('contact_phone_number')}\n")

        if self.jsonDump:
            user_dump = {
                "id": data.get("pk"),
                "full_name": data.get("full_name"),
                "biography": data.get("biography"),
                "edge_followed_by": data.get("follower_count"),
                "edge_follow": data.get("following_count"),
                "is_business_account": data.get("is_business"),
                "is_verified": data.get("is_verified"),
                "profile_pic_url_hd": data.get("hd_profile_pic_url_info", {}).get("url"),
                "email": data.get("public_email"),
                "city_name": data.get("city_name"),
                "address_street": data.get("address_street"),
                "contact_phone_number": data.get("contact_phone_number"),
            }
            json_file = os.path.join(self.output_dir, f"{self.target}_info.json")
            with open(json_file, "w") as f:
                json.dump(user_dump, f, indent=2)

    # ---- 2. addrs ----
    def get_addrs(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target localizations...\n")
        try:
            res = self.service.get_addrs()
        except Exception as e:
            pc.printout(f"Error fetching addresses: {e}\n", pc.RED)
            return

        locations = res if isinstance(res, list) else res.get("locations", [])
        if not locations:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
            return

        t = PrettyTable(["Post", "Address", "Time"])
        t.align["Post"] = "l"
        t.align["Address"] = "l"
        t.align["Time"] = "l"

        pc.printout(f"\nWoohoo! We found {len(locations)} addresses\n", pc.GREEN)
        addrs_list = []
        for i, loc in enumerate(locations, 1):
            addr_str = loc.get("address") or f"Lat: {loc.get('lat')}, Lng: {loc.get('lng')}"
            time_str = loc.get("taken_at") or "Unknown"
            t.add_row([str(i), addr_str, time_str])
            if self.jsonDump:
                addrs_list.append({"address": addr_str, "time": time_str, "lat": loc.get("lat"), "lng": loc.get("lng")})

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_addrs.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_addrs.json"), "w") as f:
                json.dump({"address": addrs_list}, f, indent=2)

    # ---- 3. captions ----
    def get_captions(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target captions...\n")
        try:
            captions = self.service.get_captions()
        except Exception as e:
            pc.printout(f"Error fetching captions: {e}\n", pc.RED)
            return

        if not captions:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
            return

        pc.printout(f"\nWoohoo! We found {len(captions)} captions\n", pc.GREEN)
        for s in captions:
            print(f"{s}\n")

        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_captions.txt"), "w") as f:
                f.write("\n".join(captions))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_captions.json"), "w") as f:
                json.dump({"captions": captions}, f, indent=2)

    # ---- 4. comments ----
    def get_total_comments(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target total comments...\n")
        try:
            res = self.service.get_total_comments()
        except Exception as e:
            pc.printout(f"Error fetching total comments: {e}\n", pc.RED)
            return

        total = res.get("comment_counter", res.get("total", 0))
        posts = res.get("posts", 0)
        min_ = res.get("min", 0)
        max_ = res.get("max", 0)
        avg = res.get("avg", 0)

        result = f" comments in {posts} posts (min: {min_}, max: {max_}, avg: {avg})\n"
        pc.printout(str(total), pc.MAGENTA)
        pc.printout(result)

        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_comments.txt"), "w") as f:
                f.write(f"{total} comments in {posts} posts\n")
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_comments.json"), "w") as f:
                json.dump({"comment_counter": total, "posts": posts, "min": min_, "max": max_, "avg": avg}, f, indent=2)

    # ---- 5. commentdata ----
    def get_comment_data(self):
        if self.check_private_profile():
            return
        pc.printout("Retrieving all comments, this may take a moment...\n")
        try:
            data = self.service.get_comment_data()
        except Exception as e:
            pc.printout(f"Error fetching comments: {e}\n", pc.RED)
            return

        t = PrettyTable(["POST ID", "ID", "Username", "Comment"])
        t.align["POST ID"] = "l"
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Comment"] = "l"

        for c in data:
            comment_text = c.get("comment") or c.get("text")
            t.add_row([c.get("post_id"), c.get("user_id"), c.get("username"), comment_text])

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_comment_data.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_comment_data.json"), "w") as f:
                json.dump({"Comments": data}, f, indent=2)

    # ---- 6. followers ----
    def get_followers(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target followers...\n")
        try:
            followers = self.service.get_followers()
        except Exception as e:
            pc.printout(f"Error fetching followers: {e}\n", pc.RED)
            return

        t = PrettyTable(["ID", "Username", "Full Name"])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        for u in followers:
            t.add_row([str(u.get("id") or u.get("pk")), u.get("username"), u.get("full_name")])

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_followers.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_followers.json"), "w") as f:
                json.dump({"followers": followers}, f, indent=2)

    # ---- 7. followings ----
    def get_followings(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target followings...\n")
        try:
            followings = self.service.get_followings()
        except Exception as e:
            pc.printout(f"Error fetching followings: {e}\n", pc.RED)
            return

        t = PrettyTable(["ID", "Username", "Full Name"])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        for u in followings:
            t.add_row([str(u.get("id") or u.get("pk")), u.get("username"), u.get("full_name")])

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_followings.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_followings.json"), "w") as f:
                json.dump({"followings": followings}, f, indent=2)

    # ---- 8. hashtags ----
    def get_hashtags(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target hashtags...\n")
        try:
            res = self.service.get_hashtags()
        except Exception as e:
            pc.printout(f"Error fetching hashtags: {e}\n", pc.RED)
            return

        if not res:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
            return

        print()
        lines = []
        tags_list = []
        if isinstance(res, list):
            for item in res:
                tag = item.get("hashtag")
                count = item.get("count", 0)
                line = f"{count}. {tag}"
                print(line)
                lines.append(line)
                tags_list.append(tag)
        elif isinstance(res, dict):
            counts = res.get("counts", res)
            for tag, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                line = f"{count}. {tag}"
                print(line)
                lines.append(line)
                tags_list.append(tag)

        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_hashtags.txt"), "w") as f:
                f.write("\n".join(lines))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_hashtags.json"), "w") as f:
                json.dump({"hashtags": tags_list}, f, indent=2)

    # ---- 9. likes ----
    def get_total_likes(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target total likes...\n")
        try:
            res = self.service.get_total_likes()
        except Exception as e:
            pc.printout(f"Error fetching total likes: {e}\n", pc.RED)
            return

        total = res.get("like_counter", res.get("total", 0))
        posts = res.get("posts", 0)
        min_ = res.get("min", 0)
        max_ = res.get("max", 0)
        avg = res.get("avg", 0)
        result = f" likes in {posts} posts (min: {min_}, max: {max_}, avg: {avg})\n"

        pc.printout(f"\n{total}", pc.MAGENTA)
        pc.printout(result)

        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_likes.txt"), "w") as f:
                f.write(f"{total}{result}")
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_likes.json"), "w") as f:
                json.dump({"like_counter": total, "posts": posts, "min": min_, "max": max_, "avg": avg}, f, indent=2)

    # ---- 10. mediatype ----
    def get_media_type(self):
        if self.check_private_profile():
            return
        pc.printout("Analyzing target media types...\n")
        try:
            res = self.service.get_media_type()
        except Exception as e:
            pc.printout(f"Error analyzing media types: {e}\n", pc.RED)
            return

        photos = res.get("photos", 0)
        videos = res.get("videos", 0)
        carousels = res.get("carousels", 0)
        total = res.get("total", 0)

        pc.printout(f"\nWoohoo! We found {total} medias\n", pc.GREEN)
        print(f"Photos: {photos}")
        print(f"Videos: {videos}")
        print(f"Carousels: {carousels}")

        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_mediatype.txt"), "w") as f:
                f.write(f"Photos: {photos}\nVideos: {videos}\nCarousels: {carousels}\n")
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_mediatype.json"), "w") as f:
                json.dump({"photos": photos, "videos": videos, "carousels": carousels, "total": total}, f, indent=2)

    # ---- 11. photodes ----
    def get_photo_description(self):
        if self.check_private_profile():
            return
        try:
            res = self.service.get_photo_descriptions()
            found = res.get("found", [])
            if not found:
                pc.printout("No photo descriptions found.\n", pc.YELLOW)
                return
            for item in found:
                print(f"[{item.get('code')}]: {item.get('description')}\n")
            if self.writeFile:
                with open(os.path.join(self.output_dir, f"{self.target}_photodes.txt"), "w") as f:
                    f.write("\n".join(str(d) for d in found))
            if self.jsonDump:
                with open(os.path.join(self.output_dir, f"{self.target}_photodes.json"), "w") as f:
                    json.dump({"photo_descriptions": found}, f, indent=2)
        except Exception as e:
            pc.printout(f"Error: {e}\n", pc.RED)

    # ---- 12. photos ----
    def get_user_photo(self):
        if self.check_private_profile():
            return
        pc.printout("How many photos you want to download (default all): ", pc.YELLOW)
        user_input = input().strip()
        limit = None
        if user_input and user_input.lower() not in ("all", ""):
            try:
                limit = int(user_input)
            except ValueError:
                pc.printout("Wrong value entered\n", pc.RED)
                return

        pc.printout("Fetching photos list...\n")
        try:
            photos = self.service.get_user_photos(limit=limit)
        except Exception as e:
            pc.printout(f"Error fetching photos: {e}\n", pc.RED)
            return

        counter = 0
        for p in photos:
            url = p.get("url") or p.get("photo_url")
            pid = p.get("id")
            if url:
                try:
                    filepath = os.path.join(self.output_dir, f"{self.target}_{pid}.jpg")
                    urllib.request.urlretrieve(url, filepath)
                    counter += 1
                    sys.stdout.write(f"\rDownloaded {counter}")
                    sys.stdout.flush()
                except Exception as e:
                    pass

        pc.printout(f"\nWoohoo! We downloaded {counter} photos (saved in {self.output_dir} folder)\n", pc.GREEN)

    # ---- 13. propic ----
    def get_user_propic(self):
        data = self.user
        propic_res = {}
        try:
            if self.service:
                propic_res = self.service.get_user_propic()
        except Exception:
            pass
        url = propic_res.get("url") or data.get("hd_profile_pic_url_info", {}).get("url") or data.get("profile_pic_url")
        if url:
            try:
                dest = os.path.join(self.output_dir, f"{self.target}_propic.jpg")
                urllib.request.urlretrieve(url, dest)
                pc.printout("Target propic saved in output folder\n", pc.GREEN)
            except Exception as e:
                pc.printout(f"Failed to download profile pic: {e}\n", pc.RED)
        else:
            pc.printout("Sorry! No profile picture found :-(\n", pc.RED)

    # ---- 14. stories ----
    def get_user_stories(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for target stories...\n")
        try:
            stories = self.service.get_user_stories()
        except Exception as e:
            pc.printout(f"Error fetching stories: {e}\n", pc.RED)
            return

        counter = 0
        for item in stories:
            sid = item.get("id")
            url = item.get("url") or item.get("media_url")
            ext = ".mp4" if (item.get("media_type") == 2 or item.get("media_type") == "video") else ".jpg"
            if url:
                try:
                    dest = os.path.join(self.output_dir, f"{self.target}_{sid}{ext}")
                    urllib.request.urlretrieve(url, dest)
                    counter += 1
                except Exception:
                    pass

        if counter > 0:
            pc.printout(f"\n{counter} target stories saved in output folder\n", pc.GREEN)
        else:
            pc.printout("\nSorry! No active stories found :-(\n", pc.RED)

    # ---- 15. tagged ----
    def get_people_tagged_by_user(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for users tagged by target...\n")
        try:
            tagged = self.service.get_people_tagged_by_user()
        except Exception as e:
            pc.printout(f"Error fetching tagged users: {e}\n", pc.RED)
            return

        if not tagged:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
            return

        t = PrettyTable(["Posts", "Full Name", "Username", "ID"])
        t.align["Posts"] = "l"
        t.align["Full Name"] = "l"
        t.align["Username"] = "l"
        t.align["ID"] = "l"

        for u in tagged:
            posts_count = u.get("posts", u.get("posts_tagged", 1))
            uid = u.get("id") or u.get("pk")
            t.add_row([posts_count, u.get("full_name"), u.get("username"), str(uid)])

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_tagged.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_tagged.json"), "w") as f:
                json.dump({"tagged": tagged}, f, indent=2)

    # ---- 16. wcommented ----
    def get_people_who_commented(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for users who commented...\n")
        try:
            users = self.service.get_people_who_commented()
        except Exception as e:
            pc.printout(f"Error fetching commenters: {e}\n", pc.RED)
            return

        if not users:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
            return

        t = PrettyTable(["Comments", "ID", "Username", "Full Name"])
        t.align["Comments"] = "l"
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        for u in users:
            cnt = u.get("counter", u.get("comments_count", 1))
            uid = u.get("id") or u.get("pk")
            t.add_row([str(cnt), str(uid), u.get("username"), u.get("full_name")])

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_users_who_commented.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_users_who_commented.json"), "w") as f:
                json.dump({"users_who_commented": users}, f, indent=2)

    # ---- 17. wtagged ----
    def get_people_who_tagged(self):
        if self.check_private_profile():
            return
        pc.printout("Searching for users who tagged target...\n")
        try:
            users = self.service.get_people_who_tagged()
        except Exception as e:
            pc.printout(f"Error fetching users who tagged: {e}\n", pc.RED)
            return

        if not users:
            pc.printout("\nSorry! No results found :-(\n", pc.RED)
            return

        t = PrettyTable(["Medias", "ID", "Username", "Full Name"])
        t.align["Medias"] = "l"
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        for u in users:
            cnt = u.get("counter", u.get("posts_count", 1))
            uid = u.get("id") or u.get("pk")
            t.add_row([str(cnt), str(uid), u.get("username"), u.get("full_name")])

        print(t)
        if self.writeFile:
            with open(os.path.join(self.output_dir, f"{self.target}_users_who_tagged.txt"), "w") as f:
                f.write(str(t))
        if self.jsonDump:
            with open(os.path.join(self.output_dir, f"{self.target}_users_who_tagged.json"), "w") as f:
                json.dump({"users_who_tagged": users}, f, indent=2)

    # ---- 18. Contact Info (Emails & Numbers) ----
    def _run_contact_search(self, method, title, filename):
        if self.check_private_profile():
            return
        pc.printout(f"Searching for {title}... (only publicly listed info will be returned)\n")
        try:
            res = method(match_limit=20, max_checks=100)
            matches = res.get("matches", []) if isinstance(res, dict) else res
            if not matches:
                pc.printout(f"No public {title} found among scanned accounts.\n", pc.YELLOW)
                return

            t = PrettyTable(["Username", "Contact", "Full Name"])
            for m in matches:
                t.add_row([m.get("username"), m.get("email") or m.get("phone") or m.get("contact_phone_number"), m.get("full_name")])
            print(t)

            if self.writeFile:
                with open(os.path.join(self.output_dir, f"{self.target}_{filename}.txt"), "w") as f:
                    f.write(str(t))
            if self.jsonDump:
                with open(os.path.join(self.output_dir, f"{self.target}_{filename}.json"), "w") as f:
                    json.dump({filename: matches}, f, indent=2)
        except Exception as e:
            pc.printout(f"Error: {e}\n", pc.RED)

    def get_fwersemail(self):
        self._run_contact_search(self.service.get_followers_email, "follower emails", "fwersemail")

    def get_fwingsemail(self):
        self._run_contact_search(self.service.get_followings_email, "following emails", "fwingsemail")

    def get_fwersnumber(self):
        self._run_contact_search(self.service.get_followers_phone, "follower phone numbers", "fwersnumber")

    def get_fwingsnumber(self):
        self._run_contact_search(self.service.get_followings_phone, "following phone numbers", "fwingsnumber")

    # ---- 19. Enhanced v2 Commands in CLI ----
    def get_about(self):
        try:
            about = self.service.get_account_about()
            print(json.dumps(about, indent=2))
        except UnsupportedCapabilityError as e:
            pc.printout(f"Unavailable on active provider: {e}\n", pc.YELLOW)
        except Exception as e:
            pc.printout(f"Error: {e}\n", pc.RED)

    def get_highlights(self):
        try:
            highlights = self.service.get_highlights()
            print(json.dumps(highlights, indent=2))
        except Exception as e:
            pc.printout(f"Error: {e}\n", pc.RED)

    def get_posting_times(self):
        try:
            times = self.service.get_posting_times()
            print(json.dumps(times, indent=2))
        except Exception as e:
            pc.printout(f"Error: {e}\n", pc.RED)

    def get_suggested(self):
        try:
            suggested = self.service.get_suggested_profiles()
            print(json.dumps(suggested, indent=2))
        except UnsupportedCapabilityError as e:
            pc.printout(f"Unavailable on active provider: {e}\n", pc.YELLOW)
        except Exception as e:
            pc.printout(f"Error: {e}\n", pc.RED)
