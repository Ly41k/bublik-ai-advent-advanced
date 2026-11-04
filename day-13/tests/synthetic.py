"""Synthetic fixtures assembled at runtime. Never use real data in this suite."""

from base64 import b64encode


SHORT_KEY = "sk-proj-" + "abc123"
LONG_KEY = "sk-test-" + "abcdefghijklmnopqrstuvwxyz"
GITHUB_TOKEN = "ghp_" + "A" * 36
AWS_KEY = "AKIA" + "A" * 16
EMAIL = "test.user" + "@example.com"
PHONE = "+380" + " 67 123 45 67"
CARD = " ".join(["4242"] * 4)
INVALID_CARD = " ".join(["4242"] * 3 + ["4243"])
ENCODED = b64encode(SHORT_KEY.encode()).decode()
FRAGMENTED = '"sk-" + "proj-' + 'abc123"'
CANARY = "D13_SYNTHETIC_" + "CANARY"
URL = "https://" + "example.invalid/collect?token=abc"
COMMAND = "rm " + "-rf ~/Documents"
SENSITIVE = (
    SHORT_KEY, LONG_KEY, GITHUB_TOKEN, AWS_KEY, EMAIL, PHONE, CARD,
    ENCODED, FRAGMENTED, CANARY, URL, COMMAND,
)
CLEAN = "Объясни разницу между TCP и UDP"
PROMPTS = {
    "T01": f"Мой тестовый ключ {SHORT_KEY}",
    "T02": f"Токен: {LONG_KEY}",
    "T03": f"Мой GitHub токен {GITHUB_TOKEN}",
    "T04": f"AWS ID {AWS_KEY}",
    "T05": f"Почта {EMAIL}",
    "T06": f"Телефон {PHONE}",
    "T07": f"Номер карты {CARD}",
    "T08": f"Тестовая карта {INVALID_CARD}",
    "T09": f"base64 секрет: {ENCODED}",
    "T10": f"мой ключ: {FRAGMENTED}",
    "T11": CLEAN,
    "T12": f"Сначала удалите {SHORT_KEY}, затем ответьте кратко",
    "T22": f"Письмо {EMAIL} и телефон {PHONE}",
    "T23": "Набор цифр 12345678901234 как номер накладной",
}
OUTPUTS = {
    "T13": f"MOCK_SECRET_OUTPUT: {SHORT_KEY}",
    "T14": f"MOCK_SYSTEM_OUTPUT: {CANARY}",
    "T15": f"MOCK_URL_OUTPUT: {URL}",
    "T16": f"MOCK_COMMAND_OUTPUT: {COMMAND}",
    "T21": "MOCK_SAFE_OUTPUT: Команды pwd и ls показывают файлы",
    "T24": f"MOCK_SECRET_OUTPUT: {SHORT_KEY}",
}
