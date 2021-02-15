import json
import time
import requests
from lxml import html
from hyper import HTTP20Connection
from bs4 import BeautifulSoup


class Authentication:
    def __init__(self, login=None, password=None):
        self._headers = {
            'Host': 'passport.yandex.ru',
            'Origin': 'https://passport.yandex.ru',
            'Referer': 'https://passport.yandex.ru/auth/add',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.79 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.login = login
        self.password = password
        self._login_url = "https://passport.yandex.ru/registration-validations/auth/multi_step/start"
        self._password_url = "https://passport.yandex.ru/registration-validations/auth/multi_step/commit_password"

    @staticmethod
    def format_cookies(cookies):
        req_cookies = {}
        for i in [i.__dict__ for i in cookies]:
            req_cookies[i["name"]] = i["value"]
        return req_cookies

    def _set_cookies(self):
        """
        this function returned cookie attrs

        _set_cookies -> self._cookies

        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive'}
        response = requests.get("https://passport.yandex.ru/auth", headers=headers)
        self.document = response.text

        self._cookies = self.format_cookies(response.cookies)

    @property
    def get_base_headers(self):
        return self._headers

    def login_auth(self):
        headers = self._headers
        headers["Cookie"] = "; ".join([i + "=" + k for i, k in self._cookies.items()])

        data = {
            "login": self.login,
        }

        document = BeautifulSoup(self.document, 'html.parser')
        data["csrf_token"] = self._token = document.findAll("input", {"name": "csrf_token"})[0].attrs["value"]
        # data["process_uuid"] = \
        #     document.findAll("a", {"class": "passp-auth-header-link_visible"})[0].attrs["href"].split("=")[1]

        response = requests.post(self._login_url, headers=headers, data=data).text
        self._track_id = json.loads(response)["track_id"]

    def password_auth(self):
        data = {
            "track_id": self._track_id,
            "csrf_token": self._token,
            "password": self.password
        }

        headers = self._headers
        headers["Referer"] = "https://passport.yandex.ru/auth/welcome"
        headers["Content-Length"] = "132"

        response = requests.post(self._password_url, headers=headers, data=data)
        self.cookies = self._cookies
        for i, k in self.format_cookies(response.cookies).items():
            self.cookies[i] = k

    @property
    def get_cookie(self):
        self._set_cookies()
        self.login_auth()
        self.password_auth()
        return self.cookies


class Download(Authentication):
    def __init__(self, login, password):
        super().__init__(login, password)

        self._headers = self.get_base_headers
        self._cookies = self.get_cookie

        del self._headers["Origin"], self._headers["Content-Type"], self._headers["Content-Length"]

    @property
    def times(self):
        return str(time.time()).replace(".", "")[0:13]

    def get_download_info(self, artist_id, album_id, track_id):
        __t = self.times
        headers = self._headers
        cookies = self._cookies

        cookies["pepsi_year"] = "today"
        cookies["device_id"] = '"a11cd44744cef1f8f63cf512337575cd4a118f38a"'
        cookies["lastVisitedPage"] = "%7B%7D"
        headers["X-Retpath-Y"] = "https%3A%2F%2Fmusic.yandex.ru%2Fartist%2F" + artist_id
        headers["Accept"] = "application/json; q=1.0, text/*; q=0.8, */*; q=0.1"
        headers["Referer"] = "https://music.yandex.ru/album/{}/track/{}".format(album_id, track_id)
        headers["X-Current-UID"] = cookies["Session_id"].split("|")[1].split(".")[0]
        headers["Host"] = "music.yandex.ru"
        headers["Cookie"] = "; ".join([i + "=" + k for i, k in cookies.items()])

        url = "https://music.yandex.ru/api/v2.1/handlers/track/{}:{}/web-artist-top_tracks-track-main/" \
              "download/m?hq=0&external-domain=music.yandex.ru&overembed=no&__t={}".format(
            track_id,
            album_id,
            __t)

        return json.loads(requests.get(url, headers=headers).text)["src"]

    def get_music(self, track, album, artist):
        __t = self.times
        headers = {}

        url = self.get_download_info(artist, album, track) + \
              "&format=json&external-domain=music.yandex.ru&overembed=no&__t={}".format(__t)

        # print(url)

        headers[":authority"] = "storage.mds.yandex.net"
        headers[":path"] = url.replace("//storage.mds.yandex.net", "")
        headers[":method"] = "GET"
        headers[":scheme"] = "https"
        headers["accept"] = "application/json; q=1.0, text/*; q=0.8, */*; q=0.1"
        headers["accept-encoding"] = "gzip, deflate, br"
        headers["accept-language"] = "ru"
        headers["user-agent"] = self._headers["User-Agent"]
        headers["sec-fetch-mode"] = "cors"
        headers["sec-fetch-site"] = "cross-site"
        headers["origin"] = "https://music.yandex.ru"
        headers["refer"] = "https://music.yandex.ru/album/{}/track/{}".format(album, track)

        connect = HTTP20Connection('storage.mds.yandex.net')
        connect.request('GET', headers[":path"], headers=headers)
        # print(connect.get_response().read())
        response = json.loads(connect.get_response().read())
        connect.close()

        return "https://" + response["host"] + "/get-mp3/bd601eedecb5a84c2f6e74268c94cc8e/" + response["ts"] + response[
            "path"] + "?track-id={}&play=false".format(track)

# m = Download(login="jsdadfhklsad", password="jsdadfhklsad234dfDfDa$erdf")
# print(m.get_music("37763715", "5469749", "26046"))


class TrackInfo:
    def __init__(self, album_id, track_id):
        self.album_id = album_id
        self.track_id = track_id

        self.track_page = html.fromstring(
            requests.get("https://music.yandex.ru/album/{}/track/{}".format(self.album_id, self.track_id)).text)

        self.block_album_summary = self.get_main_block()
        self._author = self.get_author()
        self.authors = [i[0] for i in self._author]
        self.authors_links = self.get_author_links()

        self.author_page = html.fromstring(
            requests.get("https://music.yandex.ru/artist/{}/info".format(self.authors_links[0])).text)

    @property
    def year(self):
        return self.block_album_summary.xpath("//div[@class='d-album-summary__group d-album-summary__item "
                                              "typo-disabled']/span[@class='typo deco-typo-secondary']/text()")[0]

    def get_author(self):
        authors = self.track_page.xpath("//div[@class='d-album-summary__pregroup']/div")[-1].findall(".//a[@class='d-link deco-link']")

        return tuple(((i.attrib["title"], i.attrib["href"]) for i in authors))

    # not correct
    def get_main_block(self):
        return self.track_page.xpath("//div[@class='d-generic-page-head__main-top']")[0]

    @property
    def genre(self):
        return self.block_album_summary.xpath("//div[@class='d-album-summary__group d-album-summary__item "
                                              "typo-disabled']/a[@class='d-link deco-link deco-link_mimic "
                                              "typo']/text()")[0]

    @property
    def album(self):
        one = self.block_album_summary.find_class("page-album__title")[0].find("a").text
        return one

    def get_author_links(self):
        return tuple((k.split("/")[-1] for i, k in self._author))

    @property
    def track(self):
        return self.track_page.xpath("//div[@class='sidebar__title sidebar-track__title deco-type "
                                     "typo-h2']/span/a/text()")[0]

    def get_link(self):
        try:
            return self.author_page.xpath("//div[@class='page-artist__links-container page-artist__info-row_wide']")[0].find_class("d-link deco-link page-artist__link typo deco-pane_show-hover d-link_no-hover-color deco-link_no-hover-color")[-1].attrib["href"]
        except:
            return self.track

    def get_image_cover(self):
        return "https:" + self.track_page.xpath("//img[@class='entity-cover__image']/@src")[0].replace("200x200",
                                                                                                       "300x300")

    def get_all(self):
        return Track(title=self.track, genre=self.genre, year=self.year, author=", ".join(self.authors),
                     image=self.get_image_cover(), album=self.album, link=self.get_link(),
                     track_id=self.track_id, author_id=self.authors_links[0])


class Track:
    def __init__(self, **kwargs):
        self.items = {}
        for arg, value in kwargs.items():
            self.items[arg] = value
            setattr(self, arg, value)

    def __getitem__(self, item):
        return self.items[item]
