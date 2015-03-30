# Log into Reddit and download the highest rated wallpaper
import os
import praw
import requests
from urllib.parse import urlparse
import sys

def get_system_info():
    """
    Return os and desktop information

    Param: None
    Return: os_name - name of the current operating system
                    - linux, windows, osx, unknown
            desktop_env - name of the desktop environment
                        - gnome, unity, aqua, Explorer, Unknown
    """

    sys_type= sys.platform.lower()
    if sys_type == "linux":
        os_name = sys_type
        desktop_env = os.environ.get("DESKTOP_SESSION", "unknown").lower()
    elif sys_type == "win32":
        os_name = 'windows'
        desktop_env = "explorer"
    elif sys_type == "darwin":
        os_name = "osx"
        desktop_env = "aqua"
    else:
        os_name = "unknown"
        desktop_env = "unknown"

    return os_name, desktop_env

def main():

    os_name, desktop_env = get_system_info()

    if os_name == "linux":
        if desktop_env not in ["gnome", "unity"]:
            raise SystemExit("Only Gnome3 and Unity are currently supported.")

        # import gconf
        # not sure if python3 bindings exist
    elif os_name == "windows":
        # needed to run some win32.dlls
        import ctypes
    else:
        raise SystemExit("Only Linux with Gnome3 or Unity or Windows is currently supported.")

    user_name = "openedground"
    user_agent = "{0}:wallpaper_downloader:v1 (by /u/{1})".format(os_name, user_name)
    subreddit_name = "wallpapers"

    r = praw.Reddit(user_agent = user_agent)
    print('Running')

    subreddit = r.get_subreddit(subreddit_name)
    for submission in subreddit.get_hot(limit=10):
        if submission.url is not None:
            # todo - need to validate that this is actually an image link
            break

    file_name = urlparse(submission.url).path
    if file_name[0] == '/':
        file_name = file_name[1:]

    wallpaper_dir = os.path.join(os.environ['HOME'], 'Pictures', 'Wallpapers')
    print("Downloading: " + submission.url)
    req = requests.get(submission.url, stream=True)
    with open(os.path.join(wallpaper_dir, file_name), 'wb') as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()

    if os_name == "linux":
        os.system("gsettings set org.gnome.desktop.background picture-uri \
                file://{0}".format(ms.path.join(wallpaper_dir, file_name)))
    elif sys_type == "windows":
        print("Not implemented for Windows yet")
    else:
        print("Not implemented yet.")

    print("All Done")

    return

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as error:
        print(error)
        sys.exit(1)
