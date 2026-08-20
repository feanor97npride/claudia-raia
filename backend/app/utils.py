from datetime import datetime

from flask import jsonify


def parse_date(value):
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def error(message, status=400):
    return jsonify({"error": message}), status


def paginate_none(items):
    return items
