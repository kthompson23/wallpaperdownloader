# Log into Reddit and download the highest rated wallpaper
import argparse
import os
import praw
import requests
from urllib.parse import urlparse
import sys
import tempfile

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

def parse_args():
    """
    Return command-line options passed in by the user

    Param: None
    Return: program_options - argparse object of options specified by the user
                            - as commandline arguments
    """
    parser = argparse.ArgumentParser(description="Wallpaper Downloader.",
            epilog="Downloads the most popular wallpaper of the day from /r/wallpapers")
    parser.add_argument('--save', dest='save_location', nargs='?', const='home',
            help="Save the downloaded wallpaper. If no save location is provided then ~/Pictures/Wallpapers will be used")

    return parser.parse_args()

def main():

    program_options = parse_args()

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

    if program_options.save_location is None:
        # user does not want to save the wallpaper
        wallpaper_dir = tempfile.gettempdir()
    elif program_options.save_location == 'home':
        try:
            wallpaper_dir = os.path.join(os.environ['HOME'], 'Pictures', 'Wallpapers')
        except KeyError:
            # if the user's home directory isn't set then fall back to tmp
            wallpaper_dir = tempfile.gettempdir()
    else:
        wallpaper_dir = program_options.save_location

    # validate that this location exists and we can read/write to it
    if not os.access(wallpaper_dir, os.R_OK | os.W_OK):
        raise SystemExit("Cannot write to {0}.".format(wallpaper_dir))

    # setup the useragent
    user_name = "openedground"
    user_agent = "{0}:wallpaper_downloader:v1 (by /u/{1})".format(os_name, user_name)
    subreddit_name = "wallpapers"

    r = praw.Reddit(user_agent = user_agent)
    print('Running')

    wp_downloaded = False
    subreddit = r.get_subreddit(subreddit_name)
    for submission in subreddit.get_hot(limit=10):
        if submission.is_self:
            # ignore self posts
            continue

        if submission.url is not None:
            # validate that this is a direct image link and not a link to webpage containing an image

            file_name = urlparse(submission.url).path
            if file_name[-1] == '/':
                continue

            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.png']:
                continue

            if file_name[0] == '/':
                file_name = file_name[1:]

            try:
                print("Downloading: " + submission.url)
                req = requests.get(submission.url, stream=True)
                with open(os.path.join(wallpaper_dir, file_name), 'wb') as f:
                    for chunk in req.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                wp_downloaded = True
                break
            except PermissionError as ex:
                raise SystemExit("Could not save file to {0} - {1}".format(wallpaper_dir, ex))
            except Exception as ex:
                print("Error downloading - {0}... trying next image".format(ex))
                continue
            finally:
                # close the socket
                req.close()


    if wp_downloaded:
        if os_name == "linux":
            os.system("gsettings set org.gnome.desktop.background picture-uri \
                    file://{0}".format(os.path.join(wallpaper_dir, file_name)))
        elif sys_type == "windows":
            print("Not implemented for Windows yet")
        else:
            print("Not implemented yet.")

        print("All Done")

    else:
        raise SystemExit("Could not download Wallpaper")

    return

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as error:
        print(error)
        sys.exit(1)
