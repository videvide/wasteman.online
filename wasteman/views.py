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
from django.http import HttpResponse, JsonResponse

from .forms import AddressForm, RegisterForm, LoginForm, AddToCartForm, UpdateCartForm
from .models import Address, PosterVariation, Wasteman, Poster, Painting, PosterOrder, PosterOrderStatus, PosterOrderVariation
from .cart import Cart

from .mail import send_producer_email, send_customer_receipt_email
from .my_stripe import stripe


def home(request):
    return render(request, "home.html", {"title": "Home Page"})


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
    return render(request, "artworks.html", {"paintings": Painting.objects.all()})


def painting(request, id):
    painting = get_object_or_404(Painting, pk=id)
    return render(request, "artwork.html", {"painting": painting})


def posters(request):
    return render(request, "artworks.html", {"posters": Poster.objects.all()})


def prepare_variation_choices(poster):
    """Prepares the variation choices for the form select input."""
    return [
        (
            variation.id,
            f"{variation.height}cm x {variation.width}cm: {variation.price} kr",
        )
        for variation in poster.variations.all()
    ]


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
            cart.update(form.cleaned_data["variation"], form.cleaned_data["quantity"], True)

            request.session[settings.SESSION_CART_KEY] = cart.session_cart
            messages.add_message(request, messages.SUCCESS, "Successfully added item to cart!")
    else:
        form = AddToCartForm(initial={"quantity": 1}, variation_choices=prepare_variation_choices(poster))

    return render(request, "artwork.html", {"poster": poster, "form": form})
        

def cart(request):
    """Handles cart updates from the cart page."""
    # Is this correct ?
    # Should be constant 
    cart = Cart(session_cart=request.session.get(settings.SESSION_CART_KEY))

    UpdateCartFormSet = formset_factory(UpdateCartForm, extra=0)
    
    if request.method == "POST":
        formset = UpdateCartFormSet(request.POST)
        if formset.is_valid():
            # look into cart functions 
            cart.update_from_cart_page_formset(formset.cleaned_data)
            request.session[settings.SESSION_CART_KEY] = cart.session_cart
            messages.add_message(request, messages.SUCCESS, "Successfully updated the cart!")
            return redirect("cart")
    
    else:
        # Fetch all cart_items from cart to render
        formset = UpdateCartFormSet(
            initial=[
                {
                    "variation": key,
                    "quantity": value,
                }
                # This is buggy af
                for key, value in cart.items
            ]
        )
        # Don't like!!!
        # Fetch all variations that are also cart_items
        # look into this...
        variations = [PosterVariation.objects.get(pk=x) for x, _ in cart.items]
        forms_and_variations = [] 
        for variation, form in zip(variations, formset):
            forms_and_variations.append({variation: form})

    return render(
        request, 
        "cart.html", 
        {
            # This is for formset management
            "formset": formset,
            "forms_and_variations": forms_and_variations, 
        }
    )


def address(request):
    """Take address from user and save to database and session."""
    if not request.session.has_key(settings.SESSION_CART_KEY):
        messages.add_message(request, messages.ERROR, "Invalid cart session.")
        return redirect("cart")
    
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = Address.objects.create(
                first_name = form.cleaned_data["first_name"],
                last_name = form.cleaned_data["last_name"],
                line_1 = form.cleaned_data["line_1"],
                line_2 = form.cleaned_data["line_2"],
                city = form.cleaned_data["city"],
                state = form.cleaned_data["state"],
                zip = form.cleaned_data["zip"],
                country = form.cleaned_data["country"],
                email = form.cleaned_data["email"],
            )
            request.session[settings.SESSION_ADDRESS_KEY] = address.id
            return redirect("checkout")
    else:
        form = AddressForm()

    return render(request, "address.html", {"form": form})


def checkout(request):
    """
        This is the view to save checkout information to database and create a Stripe checkout session.
    """
    if not request.session.has_key(settings.SESSION_ADDRESS_KEY):
        messages.add_message(request, messages.ERROR, "Invalid checkout session.")
        return redirect("cart")
    
    cart = Cart(session_cart=request.session.get(settings.SESSION_CART_KEY))
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": variant.stripe_price_id,
                    "quantity": quantity,
                } for variant, quantity in cart.prepare_for_checkout().items() # What???
            ],
            mode="payment",
            success_url=settings.STRIPE_CHECKOUT_SUCCESS_URL
        )

    # This is big wtf...
    except Exception as e:
        """We could check for ValueError and the like for the data processing of cart items."""
        """Django thinks this is a response object, but it is a freaking string..."""
        print(e)
        """Should return something else..."""
        messages.add_message(request, messages.INFO, "Sorry, something went wrong! Please try again or contact support.")
        return redirect("cart")
    
    address = Address.objects.get(pk=request.session[settings.SESSION_ADDRESS_KEY])
    poster_order = PosterOrder.objects.create(
        address=address, 
        stripe_checkout_session_id=checkout_session.id
    )
    # Wtf on the prepare stuff... needs tests!!! MF!!!!!!!! TEST!!!!!!
    # This feels off...
    # This could as well be add_cart_items_to_poster_order(poster_order)
    for variation, quantity in cart.prepare_cart_items_for_poster_order().items():
        poster_order_variation = PosterOrderVariation.objects.create(
            poster_order=poster_order,
            variation=variation,
            quantity=quantity,
            unit_price=variation.price
        )
        poster_order.variations.add(poster_order_variation)

    # Empty cart and del poster_order_id from session before checkout. TODO: Improve.
    cart.clear(request)
    del request.session[settings.SESSION_ADDRESS_KEY]
    
    return redirect(checkout_session.url)
    

# Change this to fetch from environment variable.
endpoint_secret = "whsec_0b292f3cc9bfa5317d9dd21c24059860cf3ea3f922947fb81be27c3776fbd1fd"
"""We want to listen for webhooks of finished payments and mark order as paid and start delivery."""
@csrf_exempt
def webhook(request):
    """
        This view handles Stripe webhooks that they send on events.
    """
    # Raw request body containing json string.
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    
    """We should probably always verify..."""
    """Could be to allow stripe listen."""
    if endpoint_secret:
        # Only verify the event if you've defined an endpoint secret
        # Otherwise, use the basic event deserialized with JSON
        sig_header = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return JsonResponse({"success": False})

    if event.type == "checkout.session.completed":
        poster_order = PosterOrder.objects.get(
            stripe_checkout_session_id=event["data"]["object"]["id"]
        )
        poster_order.stripe_payment_intent_id = event["data"]["object"]["payment_intent"]
        poster_order.status = PosterOrderStatus.PAID
        poster_order.save()

        # This is current stage...
        send_producer_email(poster_order)
        send_customer_receipt_email(poster_order)

    else:
        # Drop? 
        return HttpResponse(200)

    return HttpResponse()