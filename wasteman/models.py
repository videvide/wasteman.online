from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from .my_stripe import stripe

class ImageBase(models.Model):
    image = models.ImageField()
    alt_text = models.CharField(max_length=255, blank=True, null=True)


class NewsletterEmail(models.Model):
    """Model to store emails to send newsletters."""
    email = models.EmailField()
    consent = models.BooleanField(default=True)


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
    """We could improve this model to add customers to database."""
    user = models.OneToOneField(User, verbose_name="Optional User object", on_delete=models.CASCADE, blank=True, null=True)
    address = models.OneToOneField("Address", on_delete=models.CASCADE)

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


class Poster(Artwork):
    ratio = models.CharField(max_length=10, choices=PosterRatio)

    def save(self):
        """Automatically create variations with predefined sizes and prices."""
        super().save()
        if self.variations.count() <= 0:
            """We only run this the first save."""
            if self.ratio == PosterRatio.SQUARE:
                sizes_prices = settings.SQUARE_SIZES_AND_PIRCES
            elif self.ratio == PosterRatio.RECTANGLE:
                sizes_prices = settings.RECTANGULAR_SIZES_AND_PRICES
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
    def display_measurements(self):
        return f"{self.width} x {self.height}" 

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


class Address(models.Model):
    """Shipping address for those who purchase posters."""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    line_1 = models.CharField(max_length=255)
    line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(verbose_name="State/Province/Region", max_length=255, blank=True, null=True)
    zip = models.CharField(verbose_name="Zip code", max_length=255)
    country = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)

    @property
    def text_output(self):
        return f"""
            Name: {self.first_name} {self.last_name}
            Line 1: {self.line_1}
            Line 2: {self.line_2}
            City: {self.city}
            State: {self.state}
            Zip: {self.zip}
            Country: {self.country}
            Email: {self.email}
        """


class PosterOrderStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PAID = "paid", "Paid"
    CANCELED = "canceled", "Canceled"


class PosterOrder(models.Model):
    """Order for posters."""
    address = models.ForeignKey(Address, related_name="order", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=100, choices=PosterOrderStatus, default=PosterOrderStatus.UNPAID)
    created_at = models.DateTimeField(default=timezone.now)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)

    @property
    def print_line_items(self):
        """Return all line_items (variations) as text."""
        output = "poster_id, width, height, quantity\n"
        for ov in self.variations.all():
            output += f"{ov.variation.poster.id}, \
                        {ov.variation.width}, \
                        {ov.variation.height} \
                        {ov.variation.quantity}"
        return output
    

class PosterOrderVariation(models.Model):
    poster_order = models.ForeignKey(PosterOrder, related_name="variations", on_delete=models.CASCADE)
    variation = models.ForeignKey(PosterVariation, related_name="order_variations", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    """This is for when prices change..."""
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)