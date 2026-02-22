from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .my_stripe import stripe

class ImageBase(models.Model):
    image = models.ImageField()
    alt_text = models.CharField(max_length=255, blank=True, null=True)


class NewsletterEmail(models.Model):
    """Model to store emails to send newsletters."""
    email = models.EmailField()
    consent = models.BooleanField(default=True)


class Address(models.Model):
    """Address for customers who signup."""
    line_1 = models.CharField(max_length=255)
    line_2 = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(verbose_name="State/Province/Region", max_length=255)
    zip = models.CharField(verbose_name="Zip code", max_length=255)
    country = models.CharField(max_length=255)


class UserInformation(models.Model):
    class Meta:
        abstract = True

    terms = models.BooleanField("Agreed to terms of service.")


class Wasteman(UserInformation):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class WastemanImage(ImageBase):
    wasteman = models.ForeignKey(Wasteman, on_delete=models.CASCADE)


class Customer(UserInformation):
    user = models.OneToOneField(User, verbose_name="Optional User object", on_delete=models.CASCADE, blank=True, null=True)
    address = models.OneToOneField(Address, on_delete=models.CASCADE)

    @property
    def is_guest(self):
        """When customer does not have login."""
        return self.user.DoesNotExist() == True


class Artwork(models.Model):
    """Base class with generic information."""
    wasteman = models.ForeignKey(Wasteman, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    year = models.CharField(max_length=4, blank=True, null=True)


class ArtworkImage(ImageBase):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)


class Details(models.Model):
    class Meta:
        abstract = True

    height = models.CharField(verbose_name="Height in cm", max_length=255)
    width = models.CharField(verbose_name="Width in cm", max_length=255)
    listed = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)


class Painting(Artwork, Details):
    """Contact to purchase."""
    ...


class PosterRatio(models.TextChoices):
    SQUARE = "square", "Square"
    RECTANGLE = "rectangle", "Rectangle"


# Predefined measurements with prices (width, height, price):
# Should be set with environment variables instead of github.
# Where to set this?
SQUARE_SIZES_AND_PIRCES = [(30,30,150), (50,50,300), (70,70,500)]
RECTANGULAR_SIZES_AND_PRICES = [(30,40,300), (50,70,500), (70,100,700)]


class Poster(Artwork):
    ratio = models.CharField(max_length=10, choices=PosterRatio)

    def save(self):
        """Automatically create variations with predefined sizes and prices."""
        super().save()
        if self.variations.count() <= 0:
            """We only run this the first save."""
            if self.ratio == PosterRatio.SQUARE:
                sizes_prices = SQUARE_SIZES_AND_PIRCES
            elif self.ratio == PosterRatio.RECTANGLE:
                sizes_prices = RECTANGULAR_SIZES_AND_PRICES
            for sp in sizes_prices:
                PosterVariation.objects.create(
                    poster=self,
                    width=sp[0],
                    height=sp[1],
                    price=sp[2]
                )
        return
    
    def __str__(self):
        return self.name


class PosterVariation(Details):
    """This class have variation specific info and is what we add to cart/order."""
    poster = models.ForeignKey(Poster, related_name="variations", on_delete=models.CASCADE)
    price = models.DecimalField(verbose_name="Price in SEK", max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, help_text="Dynamically added when instance is created.")
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True, help_text="Dynamically added when instance is created.")

    @property
    def stripe_price_format(self):
        """Returns the price in cents. Used with Stripe API."""
        return int(self.price * 100)

    def save(
        self,
        *,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        """Add product information to Stripe."""
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        if not self.stripe_product_id:
            stripe_product = stripe.Product.create(name=self.poster.name)
            self.stripe_product_id = stripe_product.id
            stripe_price = stripe.Price.create(
                currency="sek",
                unit_amount=self.stripe_price_format,
                product=self.stripe_product_id
            )
            self.stripe_price_id = stripe_price.id
            self.save()


# Can be imported from elsewhere
class PosterOrderStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PAID = "paid", "Paid"
    CANCELED = "canceled", "Canceled"


class PosterOrder(models.Model):
    """Order for posters."""
    wasteman = models.ForeignKey(Wasteman, related_name="sales", on_delete=models.CASCADE)
    # can be guest
    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)
    variations = models.ManyToManyField(PosterVariation)
    status = models.CharField(max_length=100, choices=PosterOrderStatus, default=PosterOrderStatus.UNPAID)
    created_at = models.DateTimeField(default=timezone.now)
    # Stripe stuff...
    stripe_checkout_session_id = models.CharField(max_length=255)
    
