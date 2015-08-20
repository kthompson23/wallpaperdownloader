# Log into Reddit and download the highest rated wallpaper
import argparse
import hashlib
import os
import praw
import requests
from urllib.parse import urlparse
import shutil
import sys
import tempfile

# textfile containing md5 hashes of previously downloaded images  so we don't get duplicates
downloaded_images = os.path.join('resources', 'downloaded_images')
previous_downloads = {}

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
    parser.add_argument('-s', '--save', dest='save_location', action='store',
            help="Save location of the downloaded wallpaper. If no save location is provided then ~/Pictures/Wallpapers will be used")

    return parser.parse_args()

def validate_unique_image(image_path):
    """
    Verify that the image downloaded has been downloaded before or not.

    Param: image_path - relative or absolute path to the image
    Return: boolean - true if the image is unique
    """

    is_unique = None

    # get the md5 hash of the downloaded file
    m = hashlib.md5()

    try:
        with open(image_path, 'rb') as f:
            m.update(f.read())
            image_hash = m.hexdigest()

    except Exception as ex:
        raise SystemExit("Could not read image {0} - {1}".format(image_path, ex))

    if previous_downloads.get(image_hash, False):
        is_unique = False
    else:
        previous_downloads[image_hash] = True
        try:
            with open(downloaded_images, 'a') as f:
                f.write(image_hash + '\n')
        except OSError as ex:
            print("Could not updated list of downloaded images - {0}.".format(ex))

        is_unique = True

    return is_unique

def main():

    program_options = parse_args()

    os_name, desktop_env = get_system_info()

    if os_name == "linux":
        if desktop_env not in ["gnome", "unity"]:
            raise SystemExit("Only Gnome3 and Unity are currently supported.")

        # import gsettings
        from gi.repository import Gio
    elif os_name == "windows":
        # needed to run some win32.dlls
        import ctypes
    else:
        raise SystemExit("Only Linux with Gnome3 or Unity or Windows is currently supported.")

    # always save to the temporary directory first
    wallpaper_dir = None
    temp_dir = tempfile.gettempdir()
    if program_options.save_location is None:
        # user did not pass in a save location. Try their home directory
        try:
            wallpaper_dir = os.path.join(os.environ['HOME'], 'Pictures', 'Wallpapers')
        except KeyError:
            # If the user's home directory isn't set then exit because in the GNOME shell
            # the set desktop background won't persist through a restart
            raise SystemExit("Home directory is not set. Set an explicit save location.")
    else:
        wallpaper_dir = program_options.save_location

    # validate that this location exists and we can read/write to it
    if not os.access(temp_dir, os.R_OK | os.W_OK):
        raise SystemExit("Cannot write to {0}.".format(temp_dir))
    if wallpaper_dir is not None:
        if not os.access(wallpaper_dir, os.R_OK | os.W_OK):
            raise SystemExit("Cannot write to {0}.".format(wallpaper_dir))

    # build dictionary of md5 hashes of previously downloaded images
    try:
        with open(downloaded_images, 'r') as f:
            for image_hash in f:
                # get rid of any newlines
                previous_downloads[image_hash.rstrip()] = True
    except IOError as ex:
        print("Could not build list of previously downloaded images - {0}".format(ex))

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
                with open(os.path.join(temp_dir, file_name), 'wb') as f:
                    for chunk in req.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                unique_image =  validate_unique_image(os.path.join(temp_dir, file_name))
                if unique_image:
                    # this is the first time downloading the image
                    wp_downloaded = True
                    break
            except SystemExit:
                raise
            except PermissionError as ex:
                raise SystemExit("Could not save file to {0} - {1}".format(wallpaper_dir, ex))
            except Exception as ex:
                print("Error downloading - {0}... trying next image".format(ex))
                continue
            finally:
                # close the socket
                req.close()


    if wp_downloaded:
        # first attempt to copy the wallpaper to the user's chosen directory.
        try:
            shutil.copy2(os.path.join(temp_dir, file_name), os.path.join(wallpaper_dir, file_name))
        except OSError as ex:
            raise SystemExit("Could not save wallpaper to {0} - {1}".format(os.path.join(wallpaper_dir, file_name), ex))

        if os_name == "linux":
            if desktop_env in ["gnome", "unity"]:
                # Gnome3 only for now
                GNOME_SCHEMA = "org.gnome.desktop.background"
                GNOME_KEY = "picture-uri"
                gsettings = Gio.Settings.new(GNOME_SCHEMA)
                gsettings.set_string(GNOME_KEY, "file://{0}".format(os.path.join(wallpaper_dir, file_name)))
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
