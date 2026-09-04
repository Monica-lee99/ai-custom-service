import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import quote


ALGORITHM = "HMAC-SHA256"


def _hmac_sha256(key, message):
    if isinstance(key, str):
        key = key.encode()
    if isinstance(message, str):
        message = message.encode()
    return hmac.new(key, message, hashlib.sha256).digest()


def _canonical_query(params):
    parts = []
    for key in sorted(params):
        parts.append(f"{quote(str(key), safe='-_.~')}={quote(str(params[key]), safe='-_.~')}")
    return "&".join(parts)


def _normalize_header_value(value):
    return " ".join(str(value).strip().split())


def sign_headers(
    access_key_id,
    secret_key,
    method,
    canonical_uri,
    query_params,
    headers,
    payload,
    region="cn-north-1",
    service="rtc",
    now=None,
):
    now = now or datetime.now(timezone.utc)
    request_date = now.strftime("%Y%m%dT%H%M%SZ")
    short_date = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(payload).hexdigest()

    sign_headers_map = {key.lower(): value for key, value in headers.items()}
    sign_headers_map["x-date"] = request_date
    sign_headers_map["x-content-sha256"] = payload_hash

    signed_header_names = sorted(sign_headers_map)
    canonical_headers = "".join(
        f"{name}:{_normalize_header_value(sign_headers_map[name])}\n"
        for name in signed_header_names
    )
    signed_headers = ";".join(signed_header_names)
    canonical_request = "\n".join(
        [
            method.upper(),
            canonical_uri,
            _canonical_query(query_params),
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    credential_scope = f"{short_date}/{region}/{service}/request"
    string_to_sign = "\n".join(
        [
            ALGORITHM,
            request_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )

    date_key = _hmac_sha256(secret_key, short_date)
    region_key = _hmac_sha256(date_key, region)
    service_key = _hmac_sha256(region_key, service)
    signing_key = _hmac_sha256(service_key, "request")
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    authorization = (
        f"{ALGORITHM} Credential={access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    result = dict(headers)
    result["X-Date"] = request_date
    result["X-Content-Sha256"] = payload_hash
    result["Authorization"] = authorization
    return result
