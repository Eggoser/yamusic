import requests
import os
import io
import re
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, TIT2, TALB, TPE1, TPE2, TCOM, TCON, TDRC, TCOP, TPB


if __name__ == "__main__":
    from parse import Download, TrackInfo
    from exceptions import DirectoryNotFound, MP3FileSaveError, MP3TagCreateError

else:
    from .parse import Download, TrackInfo
    from .exceptions import DirectoryNotFound, MP3FileSaveError, MP3TagCreateError


"""
%C - автор
%T - название
%A - альбом
%Y - год
%G - жанр
"""


class YandexMusic:
    def __init__(self, extract_directory="."):
        self.sock = Download(login="jsdadfhklsad", password="jsdadfhklsad234dfDfDa$erdf")
        if os.path.isdir(extract_directory):
            self.base_dir = extract_directory
        else:
            raise DirectoryNotFound

    @staticmethod
    def _fast_validate(arg):
        return str().join(re.findall(r"[\w[0-9]", arg))

    @staticmethod
    def _format_filename(template, obj):
        template_values = {
            "%C": "author",
            "%T": "title",
            "%A": "album",
            "%Y": "year",
            "%G": "genre"
        }

        filters_in_template = re.findall("|".join(template_values), template)

        for filter_value in filters_in_template:
            value_from_object = obj[template_values[filter_value]]

            template = template.replace(filter_value, YandexMusic._fast_validate(value_from_object))

        return template

    def save_track(self, album, track, regex="%T", to_bytes=False, with_tags=True):
        track_info = TrackInfo(album, track).get_all()
        image = requests.get(track_info.image, stream=True).content
        filename = os.path.join(self.base_dir, self._format_filename(regex, track_info) + ".mp3")
        filename_template = filename.replace(".mp3", "") + "_{}.mp3"

        parsed_url = self.sock.get_music(track, album, "123123")
        track_raw_content = requests.get(parsed_url, stream=True).content

        if not to_bytes:
            i = 2
            while os.path.exists(filename):
                filename = filename_template.format(i)
                i += 1

            with open(filename, "wb") as log:
                log.write(track_raw_content)
                log.close()

        else:
            filename = io.BytesIO()
            filename.write(track_raw_content)

        if not with_tags:
            return filename

        audio = MP3(filename)

        try:
            audio.add_tags()
        except:
            raise MP3TagCreateError

        audio.tags.add(APIC(encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc=u'Cover',
                            data=image))

        audio["TIT2"] = TIT2(encoding=3, text=u"" + track_info["title"])
        audio["TALB"] = TALB(encoding=3, text=track_info["album"])
        audio["TPE2"] = TPE2(encoding=3, text=track_info["author"])
        audio["TPE1"] = TPE1(encoding=3, text=track_info["author"])
        audio["TCOM"] = TCOM(encoding=3, text=track_info["author"])
        audio["TCON"] = TCON(encoding=3, text=track_info["genre"])
        audio["TDRC"] = TDRC(encoding=3, text=track_info["year"])
        audio["TPE2"] = TPE2(encoding=3, text=track_info["author"])
        audio["TCOM"] = TCOM(encoding=3, text=track_info["author"])
        audio["TCON"] = TCON(encoding=3, text=track_info["genre"])
        audio["TDRC"] = TDRC(encoding=3, text=track_info["year"])
        audio['TCOP'] = TCOP(encoding=3, text=track_info["link"])
        audio['TPB'] = TPB(encoding=3, text=track_info["link"])

        try:
            if to_bytes:
                audio.save(filename)
                return filename.getvalue()

            else:
                audio.save()
        except:
            raise MP3FileSaveError

    def download(self, link, **kwargs):
        return self.save_track(link.split("/")[-3], link.split("/")[-1], **kwargs)


# obj = YandexMusic()
# data = obj.download("https://music.yandex.ru/album/4784938/track/37696486", to_bytes=True, with_tags=True)
