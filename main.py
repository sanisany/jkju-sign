import requests
from bs4 import BeautifulSoup
import hashlib
import argparse

class AutoSign:
    # 登录界面 (提取loginHash)
    _login_page = "https://www.jkju.cc/member.php"  # GET
    # 登录地址
    _login_url = "https://www.jkju.cc/member.php"  # POST
    # 签到地址
    _sign_url = "https://www.jkju.cc/plugin.php"  # GET
    # 签到页面
    _sign_page_url = "https://www.jkju.cc/plugin.php?id=zqlj_sign" # GET

    _login_form_data = {"referer": "https://www.jkju.cc/", "questionid": 0, "answer": "", "cookietime": "2592000"}

    _login_params = {"mod": "logging","action": "login","loginsubmit": "yes","inajax": 1}

    _login_header = {
        "user=agent": "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "origin": "https://www.jkju.cc",
        "referer": "https://www.jkju.cc/member.php?mod=logging&action=login",
    }

    _sign_header = {
        "user=agent": "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "refer": "https://www.jkju.cc/"
    }

    def __init__(self, username, password, is_email=False):
        self._session = requests.session()
        self._username = username
        self._password = hashlib.md5(password.encode()).hexdigest()
        self._login_form_data["username"] = username
        self._login_form_data["password"] = password
        self._sign_page_html = None
        if is_email:
            self._login_form_data["loginfield"] = "email"
        else:
            self._login_form_data["loginfield"] = "username"
        self.message = f"签到任务: 镜客居\n登录账号: {username}\n"

    def _get_login_hash(self):
        html = self._session.get(url=self._login_page, params={"mod": "logging", "action": "login"}).text
        soup = BeautifulSoup(html, 'html.parser')
        form_tag = soup.find("form", {"name": "login"})
        login_form_hash = form_tag.find("input", {"name": "formhash", "type": "hidden"}).get("value")
        login_hash_value = form_tag.get("action").split("&")[-1].split("=")[-1]
        return login_form_hash, login_hash_value

    def login(self):
        hashes = self._get_login_hash()
        self._login_form_data["formhash"] = hashes[0]
        self._login_params["loginhash"] = hashes[1]
        self._login_header["cookie"] = self._solve_cookie()
        login_response = self._session.post(self._login_url, params=self._login_params, data=self._login_form_data,
                                            headers=self._login_header).text
        if "请输入验证码继续登录" in login_response:
            return 0
        if "欢迎您回来" in login_response:
            return 1
        return -1

    def _get_sign_hash(self):
        soup = BeautifulSoup(self._sign_page_html, 'html.parser')
        form_tag = soup.find("form", {"id": "scbar_form"})
        sign_form_hash = form_tag.find("input", {"name": "formhash", "type": "hidden"}).get("value")
        return sign_form_hash

    def sign(self):
        sign_hash = self._get_sign_hash()
        self._sign_header["cookie"] = self._solve_cookie()
        response = self._session.get(url=self._sign_url, headers=self._sign_header,params={"id": "zqlj_sign", "sign": sign_hash}).text
        if response.find("恭喜您，打卡成功！") >= 0:
            return 1
        if response.find("您今天已经打过卡了，请勿重复操作！") >= 0:
            return 0
        return -1

    def _init_sign_page(self):
        self._sign_page_html = self._session.get(url=self._sign_page_url).text

    def _get_sign_trend(self):
        soup = BeautifulSoup(self._sign_page_html, 'lxml')
        trend_lis = soup.select('#wp > div.ct2.cl > div.sd > div:nth-of-type(3) > div.bm_c > ul > li')
        trend_message = ""
        for li in trend_lis:
            trend_message += f'{li.text}\n'
        return trend_message

    def _check_sign(self):
        bs = BeautifulSoup(self._sign_page_html, 'html.parser')
        sign_status_text = bs.find("div", attrs={"class": "bm signbtn cl"}).find("a").text
        if sign_status_text.find("今日已打卡") >= 0:
            return True
        return False

    def _solve_cookie(self):
        cookies = self._session.cookies.get_dict()
        cookies_str_list = [f"{k}={v}" for k, v in cookies.items()]
        cookies_str = "; ".join(cookies_str_list)
        return cookies_str

    def start(self):
        login_status = self.login()

        if login_status == 0:
            self.message += "登录状态: 频繁登录，需要验证码\n"
        if login_status == -1:
            self.message += "登录状态: 登录失败\n"
            print(self.message)
            return

        self._init_sign_page()
        has_sign = self._check_sign()
        if has_sign:
            self.message += f"执行结果: 今日已签到\n"
            self.message += self._get_sign_trend()
        else:
            sign_status = self.sign()
            if sign_status == -1:
                self.message += f'执行结果: 签到失败\n'
            else:
                self.message += f'执行结果: {"签到成功" if sign_status == 1 else "今日已签到"}\n'
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
