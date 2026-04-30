import argparse
import hashlib
from time import sleep

import requests
from bs4 import BeautifulSoup


class AutoSign:
    BASE_URL = "https://www.jkju.cc/"
    LOGIN_PAGE = BASE_URL + "member.php"
    LOGIN_URL = BASE_URL + "member.php"
    SIGN_PAGE_URL = BASE_URL + "plugin.php?id=zqlj_sign"

    LOGIN_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
        ),
        "Origin": BASE_URL,
        "Referer": LOGIN_PAGE + "?mod=logging&action=login",
    }

    SIGN_HEADERS = {
        "User-Agent": LOGIN_HEADERS["User-Agent"],
        "Referer": SIGN_PAGE_URL,
    }

    LOGIN_FORM_TEMPLATE = {
        "referer": BASE_URL + "index.php",
        "questionid": 0,
        "answer": "",
    }

    LOGIN_PARAMS_TEMPLATE = {
        "mod": "logging",
        "action": "login",
        "loginsubmit": "yes",
        "inajax": 1,
    }

    def __init__(self, username: str, password: str, is_email: bool = False):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.password_md5 = hashlib.md5(password.encode()).hexdigest()
        self.login_field = "email" if is_email else "username"

        self.login_form_data = self.LOGIN_FORM_TEMPLATE.copy()
        self.login_form_data.update(
            {"username": username, "password": password, "loginfield": self.login_field}
        )

        self.sign_url: str | None = None
        self.sign_page_html: str | None = None
        self.messages: list[str] = [f"签到任务: 镜客居\n登录账号: {username}"]

    # -------------------------
    # HTTP 请求封装
    # -------------------------
    def _get(self, url: str, **kwargs) -> requests.Response:
        resp = self.session.get(url, **kwargs)
        if resp.status_code == 403:
            self.session.cookies.clear_expired_cookies()
            resp = self.session.get(url, **kwargs)
        return resp

    def _post(self, url: str, data=None, params=None, headers=None) -> requests.Response:
        resp = self.session.post(url, data=data, params=params, headers=headers)
        if resp.status_code == 403:
            self.session.cookies.clear_expired_cookies()
            resp = self.session.post(url, data=data, params=params, headers=headers)
        return resp

    # -------------------------
    # 登录相关
    # -------------------------
    def _load_login_page(self) -> str:
        for _ in range(3):
            resp = self._get(self.LOGIN_PAGE, params={"mod": "logging", "action": "login"})
            if "document.location.reload" not in resp.text:
                return resp.text
            sleep(1)
        raise RuntimeError("登录页面加载失败或一直刷新")

    def _parse_login_form(self, html: str) -> tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        form_tag = soup.find("form", {"name": "login"})
        formhash = form_tag.find("input", {"name": "formhash", "type": "hidden"}).get("value")
        loginhash = form_tag.get("action").split("&")[-1].split("=")[-1]
        return formhash, loginhash

    def _get_login_hash(self) -> tuple[str, str]:
        html = self._load_login_page()
        return self._parse_login_form(html)

    def login(self) -> int:
        formhash, loginhash = self._get_login_hash()
        self.login_form_data["formhash"] = formhash
        login_params = self.LOGIN_PARAMS_TEMPLATE.copy()
        login_params["loginhash"] = loginhash

        resp = self._post(self.LOGIN_URL, data=self.login_form_data, params=login_params, headers=self.LOGIN_HEADERS)
        if "请输入验证码继续登录" in resp.text:
            return 0
        if "欢迎您回来" in resp.text:
            return 1
        return -1

    # -------------------------
    # 签到相关
    # -------------------------
    def _init_sign_page(self):
        resp = self._get(self.SIGN_PAGE_URL)
        self.sign_page_html = resp.text

    def _parse_sign_button(self) -> tuple[str, bool]:
        soup = BeautifulSoup(self.sign_page_html, "html.parser")
        sign_btn = soup.find("div", class_="bm signbtn cl").find("a")
        self.sign_url = self.BASE_URL + sign_btn.get("href")
        return self.sign_url, "今日已打卡" in sign_btn.text

    def _get_sign_trend(self) -> str:
        soup = BeautifulSoup(self.sign_page_html, "lxml")
        trend_lis = soup.select(
            '#wp > div.ct2.cl > div.sd > div:nth-of-type(3) > div.bm_c > ul > li'
        )
        return "\n".join(li.text for li in trend_lis)

    def sign(self) -> int:
        resp = self._get(self.sign_url, headers=self.SIGN_HEADERS)
        if "恭喜您，打卡成功！" in resp.text:
            return 1
        if "您今天已经打过卡了，请勿重复操作！" in resp.text:
            return 0
        return -1

    # -------------------------
    # 执行入口
    # -------------------------
    def start(self):
        status = self.login()
        if status == 0:
            self.messages.append("登录状态: 频繁登录，需要验证码")
        elif status == -1:
            self.messages.append("登录状态: 登录失败")
            print("\n".join(self.messages))
            return

        self._init_sign_page()
        _, already_signed = self._parse_sign_button()
        if already_signed:
            self.messages.append("执行结果: 今日已签到")
        else:
            sign_status = self.sign()
            self.messages.append(f"执行结果: {'签到成功' if sign_status == 1 else '今日已签到'}")

        self._init_sign_page()
        self.messages.append(self._get_sign_trend())
        print("\n".join(self.messages))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", required=True, help="用户名")
    parser.add_argument("-p", "--password", required=True, help="密码")
    parser.add_argument("-m", "--mode", help="模式: username | email")
    args = parser.parse_args()

    is_email = args.mode and args.mode.strip().lower() == "email"
    signer = AutoSign(args.user, args.password, is_email)
    signer.start()