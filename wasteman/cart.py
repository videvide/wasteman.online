from django.conf import settings

from .models import PosterVariation

class Cart:
    def __init__(self, session_cart=None):
        self.items = session_cart["items"] if session_cart else {}
        self.total = session_cart["total"] if session_cart else None


    def add_or_update_cart_item(self, request, id, quantity, adding=False):
        if adding and self.items.get(id):
            self.items[id] += quantity
        else:
            self.items[id] = quantity

        self.update_total_cart_quantity()
        self.populate_session_cart(request)
    

    def remove_cart_item(self, request, id):
        self.items.pop(id, None)
        self.update_total_cart_quantity()
        self.populate_session_cart(request)
    
    
    def update_total_cart_quantity(self):
        self.total = sum([x for x in self.items.values()])


    def populate_session_cart(self, request):
        request.session[settings.SESSION_CART_KEY] = {
            "items": self.items,
            "total": self.total
        }


    def clear_cart(self, request):
        self.items = {}
        self.total = None
        request.session.pop(settings.SESSION_CART_KEY, None)


    def update_from_formset(self, request, formset_data):
        """This is from cart page."""
        # Fix this with types or something cleaner...
        # [{'variation': 1, 'quantity': 20, 'remove': False}]
        for item in formset_data:
            if item["remove"]:
                self.remove_cart_item(request, id=item["variation"])
            else:
                self.add_or_update_cart_item(
                    request, 
                    id=item["variation"], 
                    quantity=item["quantity"]
                )


    def get_variations_list(self):
        return [PosterVariation.objects.get(pk=id) for id, _ in self.items.items()]


    def create_variations_and_formset_dict(self, formset):
        """This is for the cart page."""
        variations_and_forms = []
        for variation, form in zip(self.get_variations_list(), formset):
            variations_and_forms.append({variation: form})
        return variations_and_forms

  
    def get_items_for_checkout_session(self):
        return ((PosterVariation.objects.get(pk=id), quantity) for id, quantity in self.items.items())


    def get_items_for_poster_order(self):
        return ((PosterVariation.objects.get(pk=id), quantity) for id, quantity in self.items.items())
    

        
