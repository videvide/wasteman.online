from .models import PosterVariation

"""Cart names for total should be quantity..."""
class Cart:
    # This is not that good designed, but now it is working, should we dig into it now???
    # We are going to save now, and push to github before making drastic changes...
    def __init__(self, session_cart=None):
        # this is the problem with this design it is to unclear
        self.session_cart = session_cart if session_cart else {"items": {}, "total": 0}

    def clear(self, request):
        self.session_cart = {"items": {}, "total": 0}
        if bool(request.session.get("cart")):
            del request.session["cart"]

    def prepare_cart_items_for_poster_order(self):
        return {PosterVariation.objects.get(pk=key): value for key, value in self.items}

    def prepare_for_checkout(self):
        return {PosterVariation.objects.get(pk=key): value for key, value in self.items}
        
    def update(self, id, quantity, adding=False):
        if self.session_cart["items"].get(id):
            if adding:
                self.session_cart["items"][id] += quantity
            else:
                self.session_cart["items"][id] = quantity
        else:
            self.session_cart["items"][id] = quantity
        
        self.update_sum()

    """This should be called quantity, since it's the total amount of items...."""
    def update_sum(self):
        self.session_cart["total"] = sum([quantity for quantity in self.session_cart["items"].values()])

    def update_from_cart_page_formset(self, cleaned_data):
        """This is when we run from cart page before checkout..."""
        # Update with the formset.cleaned_data
        # [{'variation': 1, 'quantity': 20, 'remove': False}]
        for item in cleaned_data:
            if item["remove"]:
                self.remove(id=item["variation"])
            else:
                self.update(id=item["variation"], quantity=item["quantity"])

    def remove(self, id):
        if self.session_cart and bool(self.session_cart["items"].get(id)):
            self.session_cart["items"].pop(id)
            self.update_sum()

    @property
    def keys(self):
        """Returns the session["items"].keys()"""
        return self.session_cart["items"].keys()

    @property
    def items(self):
        """Returns the session["items"].items()"""
        return self.session_cart["items"].items()