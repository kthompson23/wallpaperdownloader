# Log into Reddit and download the highest rated wallpaper
import os
import praw
import requests
from urllib.parse import urlparse
# gsettings set org.gnome.desktop.background picture-uri file:///home/kenny/Documents/python/wallpaper/src/MrBBaV7.jpg

user_agent = "Linux:wallpaper_downloader:v1 (by /u/openedground)"
subreddit_name = "wallpapers"

def main():
    # currently this only works on gnome3
    if os.environ['GDMSESSION'] != 'gnome':
        print("Currenly gnome3 only!")
        return

    wallpaper_dir = os.path.join(os.environ['HOME'], 'Pictures', 'Wallpapers')
    r = praw.Reddit(user_agent = user_agent)
    print('Running')

    subreddit = r.get_subreddit(subreddit_name)
    for submission in subreddit.get_hot(limit=10):
        if submission.url is not None:
            # todo - need to validate that this is actually an image link
            break

    print("Downloading: " + submission.url)
    file_name = urlparse(submission.url).path
    if file_name[0] == '/':
        file_name = file_name[1:]

    req = requests.get(submission.url, stream=True)
    with open(os.path.join(wallpaper_dir, file_name), 'wb') as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    os.system("gsettings set org.gnome.desktop.background picture-uri file://" + os.path.join(wallpaper_dir, \
        file_name))
    print("All Done")

if __name__ == "__main__":
    main()
