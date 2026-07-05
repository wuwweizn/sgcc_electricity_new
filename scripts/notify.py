import typing as typ
import os
import logging
import requests
import io

class PushplusNotify(typ.NamedTuple):

    def __call__(self, user_id, balance):
        BALANCE = float(os.getenv("BALANCE", 10.0))
        logging.info(f"检查电费余额。当余额低于 {BALANCE} 元时，将发送通知")
        if balance < BALANCE :
            PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN").split(",")
            for token in PUSHPLUS_TOKEN:
                title = "电费余额不足提醒"
                content = (f"您用户号{user_id}的当前电费余额为：{balance}元，请及时充值。" )
                url = ("http://www.pushplus.plus/send?token="+ token+ "&title="+ title+ "&content="+ content)
                resp = requests.get(url)
                logging.info(
                    f"用户 {user_id} 当前余额 {balance} 元低于 {BALANCE} 元，已发送通知，请注意查收并及时充值。"
                )
                return resp.status_code == 200
        return False

class UrlPushNotify(typ.NamedTuple):

    def __call__(self, user_id, balance):
        BALANCE = float(os.getenv("BALANCE", 10.0))
        logging.info(f"检查电费余额。当余额低于 {BALANCE} 元时，将发送通知")
        if balance < BALANCE :
            url = os.getenv("PUSH_URL")
            full_url = f"{url}"
            resp = requests.post(full_url, json={"user_id": user_id, "balance": balance})
            logging.info(
                f"用户 {user_id} 当前余额 {balance} 元低于 {BALANCE} 元，已发送通知，请注意查收并及时充值。"
            )
            return resp.status_code == 200
        return False

class UrlLoginQrCodeNotify(typ.NamedTuple):

    def __call__(self, qrcode, reason: str) -> bool:
        sent = False

        # 方式1：自定义 URL 推送
        url = os.getenv("PUSH_QRCODE_URL")
        if url:
            try:
                files = {'file': ("qrcode.png", io.BytesIO(qrcode), 'image/png')}
                resp = requests.post(url, files=files, data={"reason": reason})
                logging.info(f"推送二维码到自定义URL，状态码: {resp.status_code}")
                sent = resp.status_code == 200
            except Exception as e:
                logging.warning(f"自定义URL推送失败: {e}")

        # 方式2：PushPlus 推送（支持 HTML 图片内嵌）
        pushplus_token = os.getenv("PUSHPLUS_TOKEN", "")
        for token in [t.strip() for t in pushplus_token.split(",") if t.strip() and t.strip() != "xxxx"]:
            try:
                import base64
                b64 = base64.b64encode(qrcode).decode()
                content = (
                    f"<p>原因：{reason}</p>"
                    f"<p>请用国家电网 App 扫描下方二维码登录：</p>"
                    f"<img src='data:image/png;base64,{b64}'/>"
                )
                resp = requests.post(
                    "http://www.pushplus.plus/send",
                    json={"token": token, "title": "国网登录二维码", "content": content, "template": "html"},
                    timeout=15,
                )
                result = resp.json()
                if result.get("code") == 200:
                    logging.info("已通过 PushPlus 推送登录二维码")
                    sent = True
                else:
                    logging.warning(f"PushPlus 推送失败: {result.get('msg')}")
            except Exception as e:
                logging.warning(f"PushPlus 推送异常: {e}")

        if not sent:
            logging.warning("二维码推送失败：未配置 PUSH_QRCODE_URL 或 PUSHPLUS_TOKEN，二维码已保存到 /data/login_qr_code.png")
        return sent
