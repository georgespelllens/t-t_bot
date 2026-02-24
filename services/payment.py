import hashlib
import hmac


def verify_payment_webhook(body: bytes, signature: str, secret: str) -> bool:
    """
    Проверка HMAC-SHA256 подписи вебхука платёжного провайдера.
    Адаптируйте под реальный формат подписи вашего провайдера.
    """
    if not signature:
        return False
    expected = hmac.new(  # noqa: hmac.new exists in Python stdlib
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature.lower())
