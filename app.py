import json
import os
import re
import sys
import resend


from email.utils import formataddr
from dotenv import load_dotenv
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request


load_dotenv()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
MAIL_FROM = os.getenv("MAIL_FROM", "onboarding@resend.dev").strip()
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "SneakMax")
MAIL_ADMIN = os.getenv("MAIL_ADMIN", "g4728281919@gmail.com").strip()
resend.api_key = RESEND_API_KEY

with open("products.json", "r", encoding="utf-8") as file:
    product_list = json.load(file)
with open("quiz.json", "r", encoding="utf-8") as file:
    quiz_list = json.load(file)
with open("team.json", "r", encoding="utf-8") as file:
    team_list = json.load(file)
with open("faq.json", "r", encoding="utf-8") as file:
    faq_list = json.load(file)

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
    return render_template('index.html', products=product_list, quiz=quiz_list, team=team_list, faq=faq_list)


def send_mail(to, subject, body, reply_to=None):
    if not RESEND_API_KEY:
        app.logger.error("Resend не настроен: заполните RESEND_API_KEY в .env")
        return False
    params = {
        "from": formataddr((MAIL_FROM_NAME, MAIL_FROM)),
        "to": [to],
        "subject": subject,
        "text": body,
    }
    if reply_to:
        params["reply_to"] = [reply_to]
    try:
        result = resend.Emails.send(params)
    except resend.exceptions.ResendError as error:
        app.logger.error("Письмо на %s не отправлено. Resend %s: %s", to, error.code, error.message)
        return False
    except (ValueError, OSError) as error:
        app.logger.error("Письмо на %s не отправлено. %s: %s", to, type(error).__name__, error)
        return False
    app.logger.info("Письмо на %s отправлено, id %s", to, result.get("id"))
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


def build_contact_letter(name, phone):
    lines = [
        "Новая заявка на обратный звонок с сайта SneakMax.",
        "",
        f"Имя: {name}",
        f"Телефон: {phone}",
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


@app.post('/contact/send')
def contact_send():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    name = str(data.get("user_name", "")).strip()
    phone = str(data.get("tel", "")).strip()
    digits = re.sub(r"\D", "", phone)
    if len(name) < 2:
        return jsonify(ok=False, message="Укажите имя"), 400
    if not 10 <= len(digits) <= 15:
        return jsonify(ok=False, message="Укажите корректный номер телефона"), 400
    if not MAIL_ADMIN:
        app.logger.error("Заявка не отправлена: заполните MAIL_ADMIN в .env")
        return jsonify(ok=False, message="Не удалось отправить заявку, попробуйте позже"), 502
    sent = send_mail(
        to=MAIL_ADMIN,
        subject=f"Заявка на звонок: {name}",
        body=build_contact_letter(name, phone),
    )
    if not sent:
        return jsonify(ok=False, message="Не удалось отправить заявку, попробуйте позже"), 502
    return jsonify(ok=True, message="Спасибо! Менеджер свяжется с вами")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    app.run(debug=True)