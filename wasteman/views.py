import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as logout_function
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as login_function
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import formset_factory
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.core.signing import BadSignature
from django.views.decorators.http import require_http_methods

from wasteman.utils import get_all_shipping_countries, verify_signed_newsletter_email_token

from .forms import NewsletterForm, RegisterForm, LoginForm, AddToCartForm, UpdateCartForm
from .models import Address, NewsletterEmail, Wasteman, Poster, Painting, PosterOrder, PosterOrderStatus, PosterOrderVariation
from .cart import Cart

from .mail import send_producer_email, send_customer_receipt_email, send_newsletter_confirmation_email
from .my_stripe import stripe


def home(request):
    newsletter_form = NewsletterForm()
    return render(request, "home.html", {"title": "Home Page", "newsletter_form": newsletter_form})


@require_http_methods(["GET"])
def newsletter_confirmation(request, token):
    try: 
        email = verify_signed_newsletter_email_token(token)
        email = NewsletterEmail.objects.get(email=email)
    except BadSignature:
        return HttpResponseBadRequest("Invalid token.")
    except NewsletterEmail.DoesNotExist:
        # Log this since it should not happen...
        return HttpResponse(500)
    
    if not email.confirmed:
        email.confirmed = True
        email.save()

    messages.add_message(request, messages.SUCCESS, "You successfully confirmed your email!")
    return redirect("home")


@require_http_methods(["POST"])
def newsletter_signup(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        if not form.cleaned_data["consent"]:
            messages.add_message(request, messages.INFO, "You must give consent to signup for our newsletter.")
            return redirect("home")
        
        email = NewsletterEmail.objects.filter(email=form.cleaned_data["email"])
        if not email:
            email = NewsletterEmail.objects.create(email=form.cleaned_data["email"])
            send_newsletter_confirmation_email(form.cleaned_data["email"])

        messages.add_message(request, messages.SUCCESS, "You successfully signed up for our newsletter, check your inbox for confirmation email!")
        return redirect("home")
    

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                form.cleaned_data["username"],
                form.cleaned_data["email"],
                form.cleaned_data["password"]
            )
            wasteman = Wasteman.objects.create(
                user=user,
                terms=form.cleaned_data["terms"]
            )
            messages.add_message(request, messages.SUCCESS, f"Account '{wasteman.user.username}' successfully created!")
            return redirect("admin:index")
        
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"]
            )
            if user is not None:
                login_function(request, user)
                messages.add_message(request, messages.SUCCESS, "You successfully logged in!")
                return redirect("profile")
            else:
                messages.add_message(request, messages.ERROR, "Invalid credentials, try again!")
                return render(request, "login.html", {"form": LoginForm()}) 

    else:
        form = LoginForm()
    
    return render(request, "login.html", {"form": form})


@login_required
def profile(request):
    """Could show the orders made and favorites..."""
    if request.method == "POST":
        password_change_form = PasswordChangeForm(request.POST)
        if password_change_form.is_valid():
            # should also in fact change the password...
            messages.add_message(request, messages.SUCCESS, "Your password was successfully changed!")
            return redirect("profile")

    else:
        password_change_form = PasswordChangeForm(request)

    return render(request, "profile.html", {"password_change_form": password_change_form})


@login_required
def logout(request):
    logout_function(request)
    messages.add_message(request, messages.SUCCESS, "You have successfully logged out!")
    return redirect("home")


def paintings(request):
    return render(request, "artworks.html", {"paintings": Painting.objects.all(), "page": "Paintings"})


def painting(request, id):
    painting = get_object_or_404(Painting, pk=id)
    return render(request, "artwork.html", {"painting": painting})


def posters(request):
    return render(request, "artworks.html", {"posters": Poster.objects.all(), "page": "Posters"})


def prepare_variation_choices(poster):
    """Prepares the variation choices for the form select input."""
    return [
        (
            variation.id,
            f"{variation.height}cm x {variation.width}cm: {variation.price} kr",
        )
        for variation in poster.variations.all()
    ]


# Looks ok atm...
def poster(request, id):
    """Renders poster page and handles adding to cart."""
    poster = Poster.objects.get(pk=id)

    if request.method == "POST":
        form = AddToCartForm(request.POST, variation_choices=prepare_variation_choices(poster))
        if form.is_valid():
            if request.session.has_key(settings.SESSION_CART_KEY):
                cart = Cart(session_cart=request.session.get(settings.SESSION_CART_KEY))
            else:
                cart = Cart()
            cart.add_or_update_cart_item(
                request,
                id=form.cleaned_data["variation"], 
                quantity=form.cleaned_data["quantity"], 
                adding=True)
            messages.add_message(request, messages.SUCCESS, "Successfully added item to cart!")
    else:
        form = AddToCartForm(initial={"quantity": 1}, variation_choices=prepare_variation_choices(poster))

    return render(request, "artwork.html", {"poster": poster, "form": form})


def cart(request):
    cart = Cart(session_cart=request.session.get(settings.SESSION_CART_KEY))
    UpdateCartFormSet = formset_factory(UpdateCartForm, extra=0)

    if request.method == "POST":
        formset = UpdateCartFormSet(request.POST)
        if formset.is_valid():
            cart.update_from_formset(request, formset_data=formset.cleaned_data)
            messages.add_message(request, messages.SUCCESS, "Successfully updated the cart!")
            return redirect("cart")
    
    else:
        # We need this for formset management.
        formset = UpdateCartFormSet(
            initial=[
                {
                    "variation": key,
                    "quantity": value,
                }
                for key, value in cart.items.items()
            ]
        )
        
    return render(
        request, 
        "cart.html", 
        {
            "formset": formset,
            "forms_and_variations": cart.create_variations_and_formset_dict(formset),
            "total_poster_cost": cart.get_total_poster_cost(),
            "total_shipping_cost": cart.get_total_shipping_cost(),
            "total_cost": cart.get_total_cost(),
        }
    )


def create_poster_order(request, checkout_session_id, cart: Cart):
    try:
        poster_order = PosterOrder.objects.create(
            stripe_checkout_session_id=checkout_session_id
        )
        for variation, quantity in cart.get_items_for_poster_order():
            poster_order_variation = PosterOrderVariation.objects.create(
                poster_order=poster_order,
                variation=variation,
                quantity=quantity,
                unit_price=variation.price
            )
            poster_order.variations.add(poster_order_variation)
    except Exception as e:
        # Log this!
        raise Exception("Failed to create poster_order!")
    

def checkout(request):
    """
        This is the view to save checkout information to database and create a Stripe checkout session.
    """
    if not request.session.has_key(settings.SESSION_CART_KEY):
        messages.add_message(request, messages.ERROR, "Invalid cart session.")
        return redirect("cart")
    
    cart = Cart(session_cart=request.session.get(settings.SESSION_CART_KEY))
    try:
        checkout_session = stripe.checkout.Session.create(
            shipping_options=[
                {
                    # We need to create shipping rate manually since we do not know order quantity
                    "shipping_rate_data": {
                        "type": "fixed_amount",
                        "fixed_amount": {"amount": cart.get_total_shipping_cost_in_cents(), "currency": "sek"},
                        "display_name": "Shipping cost",
                        "delivery_estimate": {
                            "minimum": {"unit": "business_day", "value": 3},
                            "maximum": {"unit": "business_day", "value": 14},
                        },
                    },
                },
            ],
            shipping_address_collection={"allowed_countries": get_all_shipping_countries()},
            mode="payment",
            success_url=settings.STRIPE_CHECKOUT_SUCCESS_URL,
            line_items=[
                {
                    "price": variation.stripe_price_id,
                    "quantity": quantity,
                } for variation, quantity in cart.get_items_for_checkout_session()
            ],
        )
    # Fix this!
    except Exception as e:
        # Log this!
        messages.add_message(request, messages.INFO, "Sorry, something went wrong! Please try again or contact support.")
        return redirect("cart")
    
    create_poster_order(request, checkout_session.id, cart)
    cart.clear_cart(request)
    return redirect(checkout_session.url)
    

@csrf_exempt
def webhook(request):
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        return HttpResponse(status=400)
    
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        print('⚠️  Webhook signature verification failed.' + str(e))
        return JsonResponse({"success": False})

    if event.type == "checkout.session.completed":
        poster_order = PosterOrder.objects.get(
            stripe_checkout_session_id=event["data"]["object"]["id"]
        )
        event_customer_details = event["data"]["object"]["customer_details"]
        address = Address.objects.create(
            name = event_customer_details["name"],
            email = event_customer_details["email"],
            line1 = event_customer_details["address"]["line1"],
            line2 = event_customer_details["address"]["line2"],
            city = event_customer_details["address"]["city"],
            state = event_customer_details["address"]["state"],
            postal_code = event_customer_details["address"]["postal_code"],
            country = event_customer_details["address"]["country"],
        )
        poster_order.address = address
        poster_order.stripe_payment_intent_id = event["data"]["object"]["payment_intent"]
        poster_order.status = PosterOrderStatus.PAID
        poster_order.save()

        send_producer_email(poster_order)
        send_customer_receipt_email(poster_order)

    return HttpResponse(200)