import argparse
import hashlib
import requests
from bs4 import BeautifulSoup


class AutoSign:
    LOGIN_PAGE = "https://www.jkju.cc/member.php"
    LOGIN_URL = "https://www.jkju.cc/member.php"
    SIGN_URL = "https://www.jkju.cc/plugin.php"
    SIGN_PAGE_URL = "https://www.jkju.cc/plugin.php?id=zqlj_sign"

    LOGIN_FORM_DATA = {
        "referer": "https://www.jkju.cc/",
        "questionid": 0,
        "answer": "",
        "cookietime": "2592000",
    }

    LOGIN_PARAMS = {
        "mod": "logging",
        "action": "login",
        "loginsubmit": "yes",
        "inajax": 1,
    }

    LOGIN_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        "Origin": "https://www.jkju.cc",
        "Referer": "https://www.jkju.cc/member.php?mod=logging&action=login",
    }

    SIGN_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        "Referer": "https://www.jkju.cc/",
    }

    def __init__(self, username: str, password: str, is_email: bool = False) -> None:
        self.session = requests.Session()
        self.username = username
        self.password_md5 = hashlib.md5(password.encode()).hexdigest()

        self.login_form_data = self.LOGIN_FORM_DATA.copy()
        self.login_form_data["username"] = username
        self.login_form_data["password"] = password
        self.login_form_data["loginfield"] = "email" if is_email else "username"

        self.sign_page_html: str | None = None
        self.message = f"签到任务: 镜客居\n登录账号: {username}\n"

    def _get_login_hash(self) -> tuple[str, str]:
        # 第一次 (403)，但设置了临时 cookie
        self.session.get(
            self.LOGIN_PAGE, params={"mod": "logging", "action": "login"}
        )
        # 第二次 (200)，必须带上第一次的 cookie
        resp2 = self.session.get(
            self.LOGIN_PAGE, params={"mod": "logging", "action": "login"}
        )
        soup = BeautifulSoup(resp2.text, "html.parser")

        form_tag = soup.find("form", {"name": "login"})
        formhash = form_tag.find("input", {"name": "formhash", "type": "hidden"}).get("value")
        loginhash = form_tag.get("action").split("&")[-1].split("=")[-1]

        return formhash, loginhash

    def login(self) -> int:
        """执行两次请求完成登录。"""
        formhash, loginhash = self._get_login_hash()
        self.login_form_data["formhash"] = formhash
        self.LOGIN_PARAMS["loginhash"] = loginhash

        self.session.post(
            self.LOGIN_URL,
            params=self.LOGIN_PARAMS,
            data=self.login_form_data,
            headers=self.LOGIN_HEADERS,
        )

        # 登录前清理掉临时 cookie
        self.session.cookies.clear_expired_cookies()

        resp = self.session.post(
            self.LOGIN_URL,
            params=self.LOGIN_PARAMS,
            data=self.login_form_data,
            headers=self.LOGIN_HEADERS,
        )

        text = resp.text
        if "请输入验证码继续登录" in text:
            return 0
        if "欢迎您回来" in text:
            return 1
        return -1

    def _init_sign_page(self) -> None:
        self.sign_page_html = self.session.get(self.SIGN_PAGE_URL).text

    def _get_sign_hash(self) -> str:
        soup = BeautifulSoup(self.sign_page_html, "html.parser")
        form_tag = soup.find("form", {"id": "scbar_form"})
        return form_tag.find("input", {"name": "formhash", "type": "hidden"}).get("value")

    def _get_sign_trend(self) -> str:
        soup = BeautifulSoup(self.sign_page_html, "lxml")
        trend_lis = soup.select('#wp > div.ct2.cl > div.sd > div:nth-of-type(3) > div.bm_c > ul > li')
        return "\n".join(li.text for li in trend_lis)

    def _already_signed(self) -> bool:
        soup = BeautifulSoup(self.sign_page_html, "html.parser")
        sign_status_text = soup.find("div", class_="bm signbtn cl").find("a").text
        return "今日已打卡" in sign_status_text

    def sign(self) -> int:
        """执行签到操作。"""
        sign_hash = self._get_sign_hash()
        resp = self.session.get(
            self.SIGN_URL,
            headers=self.SIGN_HEADERS,
            params={"id": "zqlj_sign", "sign": sign_hash},
        ).text

        if "恭喜您，打卡成功！" in resp:
            return 1
        if "您今天已经打过卡了，请勿重复操作！" in resp:
            return 0
        return -1

    def start(self) -> None:
        login_status = self.login()

        if login_status == 0:
            self.message += "登录状态: 频繁登录，需要验证码\n"
        elif login_status == -1:
            self.message += "登录状态: 登录失败\n"
            print(self.message)
            return

        self._init_sign_page()
        if self._already_signed():
            self.message += "执行结果: 今日已签到\n"
            self.message += self._get_sign_trend()
        else:
            sign_status = self.sign()
            if sign_status == -1:
                self.message += "执行结果: 签到失败\n"
            else:
                self.message += f"执行结果: {'签到成功' if sign_status == 1 else '今日已签到'}\n"
                self._init_sign_page()
                self.message += self._get_sign_trend()
        print(self.message)

if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-u","--user", type=str, required=True, help="用户")
    args_parser.add_argument("-p","--password", type=str, required=True, help="密码")
    args_parser.add_argument("-m","--mode", type=str, help="模式: username | email ")
    arguments = args_parser.parse_args()
    if arguments.mode is None or arguments.mode.strip().lower() != "email":
        arguments.mode = "username"
    signer = AutoSign(arguments.user, arguments.password, arguments.mode.strip().lower() == 'email')
    signer.start()
