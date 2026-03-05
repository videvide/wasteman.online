import os
from typing import Optional
from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse

def get_env_vars(key: str, default: Optional[str] = None) -> str:
    """Retrives an environment variable or raises error if not found."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"{key} is required but not set.")
    return value

def parse_sizes_and_prices(sizes_and_prices):
    """We parse this format: x,x,y;x,x,y == w,h,p;w,h,p"""
    return [item.split(",") for item in sizes_and_prices.split(";")]

def get_all_shipping_countries():
    return [
    "AC", "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ",
    "AR", "AT", "AU", "AW", "AX", "AZ", "BA", "BB", "BD", "BE",
    "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ",
    "BR", "BS", "BT", "BV", "BW", "BY", "BZ", "CA", "CD", "CF",
    "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO", "CR", "CV",
    "CW", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC",
    "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FO",
    "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL",
    "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY",
    "HK", "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN",
    "IO", "IQ", "IS", "IT", "JE", "JM", "JO", "JP", "KE", "KG",
    "KH", "KI", "KM", "KN", "KR", "KW", "KY", "KZ", "LA", "LB",
    "LC", "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA",
    "MC", "MD", "ME", "MF", "MG", "MK", "ML", "MM", "MN", "MO",
    "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ",
    "NA", "NC", "NE", "NG", "NI", "NL", "NO", "NP", "NR", "NU",
    "NZ", "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM",
    "PN", "PR", "PS", "PT", "PY", "QA", "RE", "RO", "RS", "RU",
    "RW", "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ",
    "SK", "SL", "SM", "SN", "SO", "SR", "SS", "ST", "SV", "SX",
    "SZ", "TA", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL",
    "TM", "TN", "TO", "TR", "TT", "TV", "TW", "TZ", "UA", "UG",
    "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VN", "VU", "WF",
    "WS", "XK", "YE", "YT", "ZA", "ZM", "ZW", "ZZ",
]

def create_signed_newsletter_email_token_link(email):
    signer = Signer()
    token = signer.sign(email)
    return f"{settings.SITE_ORIGIN}" + reverse("newsletter_confirmation", args=[token]) # strip() ???


def verify_signed_newsletter_email_token(token):
    signer = Signer()
    return signer.unsign(token)
        