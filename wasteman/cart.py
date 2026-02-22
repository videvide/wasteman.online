from .models import PosterVariation

class Cart:
    def __init__(self, session_cart=None):
        self.session_cart = session_cart if session_cart else {"items": {}, "total": 0}

    def clear(self, request):
        self.session_cart = {"items": {}, "total": 0}
        if bool(request.session.get("cart")):
            del request.session["cart"]

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

    def update_sum(self):
        self.session_cart["total"] = sum([quantity for quantity in self.session_cart["items"].values()])

    def update_from_formset(self, cleaned_data):
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
    def items(self):
        """Returns the session["items"].items()"""
        return self.session_cart["items"].items()