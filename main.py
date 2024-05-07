import datetime
import requests
from bs4 import BeautifulSoup
import hashlib


def get_now():
    return datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")


class AutoSign:
    # 登录界面 (提取loginHash)
    _login_page = "https://www.jkju.cc/member.php"  # GET
    # 登录地址
    _login_url = "https://www.jkju.cc/member.php"  # POST
    # 签到地址
    _sign_url = "https://www.jkju.cc/plugin.php"  # GET
    # 签到页面
    _sign_page_url = "https://www.jkju.cc/plugin.php?id=k_misign:sign" # GET

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
        self._rank = None
        self._session = requests.session()
        self._username = username
        self._password = hashlib.md5(password.encode()).hexdigest()
        self._login_form_data["username"] = username
        self._login_form_data["password"] = password
        if is_email:
            self._login_form_data["loginfield"] = "email"
        else:
            self._login_form_data["loginfield"] = "username"
        self.message = f"镜客居签到\n账号:{username}\n"

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
        if "欢迎您回来" in login_response:
            return True
        return False

    def _get_sign_hash(self):
        self._sign_header["cookie"] = self._solve_cookie()
        html = self._session.get(url=self._sign_url, params={"id": "k_misign:sign"}, headers=self._sign_header).text
        soup = BeautifulSoup(html, 'html.parser')
        form_tag = soup.find("form", {"id": "scbar_form"})
        sign_form_hash = form_tag.find("input", {"name": "formhash", "type": "hidden"}).get("value")
        return sign_form_hash

    def sign(self):
        sign_hash = self._get_sign_hash()
        self._sign_header["cookie"] = self._solve_cookie()
        response = self._session.get(url=self._sign_url, headers=self._sign_header,params={"id": "k_misign:sign", "operation": "qiandao", "format": "empty", "inajax": 1, "ajaxtarget": "JD_sign", "formhash": sign_hash}).text
        success = self.check_sign()
        if "<![CDATA[今日已签]]>" in response:
            return 0
        else:
            if success:
                return 1
            return -1

    def check_sign(self):
        page_html = self._session.get(url=self._sign_page_url).text
        bs = BeautifulSoup(page_html, 'html.parser')
        qd_rank = bs.find("input", attrs={"id": "qiandaobtnnum"}).get("value")
        if int(qd_rank) > 0:
            self._rank = qd_rank
            return True
        return False

    def _solve_cookie(self):
        cookies = self._session.cookies.get_dict()
        cookies_str_list = [f"{k}={v}" for k, v in cookies.items()]
        cookies_str = "; ".join(cookies_str_list)
        return cookies_str

    def start(self):
        login_status = self.login()
        if not login_status:
            self.message += f"{get_now()}\n状态:登录失败\n"
            print(self.message)
            return
        sign_status = self.sign()
        if sign_status == 0:
            self.message += f"{get_now()}\n状态:今日已经签到\n签到排名:{self._rank}\n"
        elif sign_status == 1:
            self.message += f"{get_now()}\n状态:签到成功\n签到排名:{self._rank}\n"
        else:
            self.message += f"{get_now()}\n状态:签到失败\n"
        print(self.message)


if __name__ == "__main__":
    # 任选一种方式进行
    AutoSign("用户名", "密码").start()
    AutoSign("邮箱", "密码", is_email=True).start()


