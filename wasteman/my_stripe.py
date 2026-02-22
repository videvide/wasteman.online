from .utils import get_env_vars

import stripe
stripe.api_key = get_env_vars("STRIPE_SK_TEST")

"""On successful order we should send email to printer."""

