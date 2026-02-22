from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as logout_function
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as login_function
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import formset_factory
from django.conf import settings
from django.http import HttpResponse

from .forms import RegisterForm, LoginForm, AddToCartForm, UpdateCartForm
from .models import PosterVariation, Wasteman, Poster, Painting
from .cart import Cart

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
    # edit template to handle painting.
    return render(request, "artwork.html", {"painting": painting})


def posters(request):
    return render(request, "artworks.html", {"posters": Poster.objects.all()})


def poster(request, id):
    poster = Poster.objects.get(pk=id)
    variation_choices = [
        (v.id, f"{v.height}cm x {v.width}cm")
        for v in poster.variations.all()
    ]
    if request.method == "POST":
        form = AddToCartForm(request.POST, variation_choices=variation_choices)
        if form.is_valid():
            variation = form.cleaned_data["variation"]
            quantity = form.cleaned_data["quantity"]

            if request.session.has_key("cart"):
                cart = Cart(session_cart=request.session.get("cart"))
            else:
                cart = Cart()
            cart.update(variation, quantity, True)

            request.session["cart"] = cart.session_cart
            request.session.save()
            messages.add_message(request, messages.SUCCESS, "Successfully added item to cart!")

    else:
        form = AddToCartForm(initial={"quantity": 1}, variation_choices=variation_choices)

    return render(request, "artwork.html", {"poster": poster, "form": form})
        

def cart(request):
    cart = Cart(session_cart=request.session.get("cart"))
    UpdateCartFormSet = formset_factory(UpdateCartForm, extra=0)
    
    if request.method == "POST":
        formset = UpdateCartFormSet(request.POST)
        if formset.is_valid():
            cart.update_from_formset(formset.cleaned_data)
            request.session["cart"] = cart.session_cart
            request.session.save()
            messages.add_message(request, messages.SUCCESS, "Successfully updated the cart!")
            return redirect("cart")
    
    else:
        formset = UpdateCartFormSet(
            initial=[
                {
                    "variation": key,
                    "quantity": value,
                }
                for key, value in cart.items
            ]
        )
        variations = [PosterVariation.objects.get(pk=x) for x, _ in cart.items]
        forms_and_variations = [] 
        for variation, form in zip(variations, formset):
            forms_and_variations.append({variation: form})

    return render(
        request, 
        "cart.html", 
        {
            "forms_and_variations": forms_and_variations, 
            "formset": formset
        }
    )


"""Just make an anchor tag with redirect to this page..."""
def checkout(request):
    if request.method == "POST":
        cart = Cart(session_cart=request.session.get("cart"))
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        "price": variant.stripe_price_id,
                        "quantity": quantity,
                    } for variant, quantity in cart.prepare_for_checkout().items()
                ],
                mode="payment",
                success_url=settings.STRIPE_CHECKOUT_SUCCESS_URL
            )
        except Exception as e:
            """We could check for ValueError and the like for the data processing of cart items."""
            """Django thinks this is a response object, but it is a freaking string..."""
            print(e)
            """Should return something else..."""
            messages.add_message(request, messages.INFO, "Sorry, something went wrong! Please try again or contact support.")
            return redirect("cart")
        
        # Empty cart before redirecting to checkout, if checkout is canceled it is still cleared.
        cart.clear(request)
        # Create an order object and set status to unpaid and wait for webhook...
        return redirect(checkout_session.url)
    
    else:
        return redirect("cart")
    

def webhook(request):
    # should receive the Stripe webhook in json format...
    # https://docs.stripe.com/api/events/object?api-version=2026-01-28.preview&rds=1

    # Need endpoint secret 
    # Replace this endpoint secret with your unique endpoint secret key
    # If you're testing with the CLI, run 'stripe listen' to find the secret key
    # If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
    return HttpResponse("Coming soon...")