import json
import os
import re
import smtplib
import ssl
import sys


from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request


load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "SneakMax")
MAIL_ADMIN = os.getenv("MAIL_ADMIN", SMTP_USER)

with open("products.json", "r", encoding="utf-8") as file:
    product_list = json.load(file)
with open("quiz.json", "r", encoding="utf-8") as file:
    quiz_list = json.load(file)
with open("team.json", "r", encoding="utf-8") as file:
    team_list = json.load(file)

app = Flask(__name__)
app.json.ensure_ascii = False

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
SIZE_RANGES = {
    "менее 36": (0, 35),
    "36-38": (36, 38),
    "39-41": (39, 41),
    "42-44": (42, 44),
    "45 и больше": (45, 99),
}
MAX_PICKED = 6


@app.route('/')
def main():
    return render_template('index.html', products=product_list, quiz=quiz_list, team=team_list)


def send_mail(to, subject, body, reply_to=None):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
        app.logger.error("SMTP не настроен: заполните SMTP_HOST, SMTP_USER и SMTP_PASSWORD в .env")
        return False
    message = EmailMessage()
    message["From"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    message["To"] = to
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=20) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(message)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(message)
    except (smtplib.SMTPException, OSError) as error:
        app.logger.error("Письмо на %s не отправлено. %s: %s", to, type(error).__name__, error)
        return False
    return True


def clean_choices(raw, allowed):
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    result = []
    for value in raw:
        value = str(value).strip()
        if value in allowed and value not in result:
            result.append(value)
    return result


def pick_products(sizes):
    bounds = [SIZE_RANGES[size] for size in sizes]
    if not bounds:
        return product_list[:MAX_PICKED]
    picked = []
    for product in product_list:
        for size in product.get("sizes", []):
            if any(low <= size <= high for low, high in bounds):
                picked.append(product)
                break
    if not picked:
        picked = product_list
    return picked[:MAX_PICKED]


def build_customer_letter(name, types, sizes, picked):
    lines = [
        f"{name}, здравствуйте!",
        "",
        "Мы подобрали для вас модели по ответам из квиза.",
    ]
    if types:
        lines.append("Тип обуви: " + ", ".join(types))
    if sizes:
        lines.append("Размер: " + ", ".join(sizes))
    lines.append("")
    for product in picked:
        product_sizes = ", ".join(str(size) for size in product.get("sizes", []))
        lines.append(f"- {product['name'].capitalize()}, {product['price']} руб., размеры: {product_sizes}")
    lines += ["", "С уважением, команда SneakMax"]
    return "\n".join(lines)


def build_admin_letter(name, email, types, sizes):
    lines = [
        "Новая заявка с квиза на сайте SneakMax.",
        "",
        f"Имя: {name}",
        f"E-mail: {email}",
        "Тип обуви: " + (", ".join(types) if types else "не выбрано"),
        "Размер: " + (", ".join(sizes) if sizes else "не выбрано"),
    ]
    return "\n".join(lines)


@app.post('/quiz/send')
def quiz_send():
    data = request.get_json(silent=True)
    if data is None:
        data = {key: request.form.getlist(key) for key in request.form}
        data = {key: value if len(value) > 1 else value[0] for key, value in data.items()}
    name = str(data.get("user_name", "")).strip()
    email = str(data.get("user_email", "")).strip()
    if len(name) < 2:
        return jsonify(ok=False, message="Укажите имя"), 400
    if not EMAIL_PATTERN.match(email):
        return jsonify(ok=False, message="Укажите корректный e-mail"), 400
    allowed_types = {item["model"] for item in quiz_list}
    types = clean_choices(data.get("types"), allowed_types)
    sizes = clean_choices(data.get("sizes"), SIZE_RANGES.keys())
    picked = pick_products(sizes)
    sent = send_mail(
        to=email,
        subject="Ваша подборка кроссовок SneakMax",
        body=build_customer_letter(name, types, sizes, picked),
    )
    if not sent:
        return jsonify(ok=False, message="Не удалось отправить письмо, попробуйте позже"), 502
    if MAIL_ADMIN:
        send_mail(
            to=MAIL_ADMIN,
            subject=f"Заявка с квиза: {name}",
            body=build_admin_letter(name, email, types, sizes),
            reply_to=email,
        )
    return jsonify(ok=True, message=f"Готово! Подборка отправлена на {email}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    app.run(debug=True)