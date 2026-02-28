from django.conf import settings
from django.core.mail import send_mail

def send_producer_email(poster_order):
    """Send order request to print-on-demand service."""
    send_mail(
            subject="Print-on-demand poster order from wasteman.online",
            message=f"""
                Hi, we want to make an order for the following posters :)\n
                {poster_order.print_line_items}\n
                And we want it sent to this address:\n
                {poster_order.address.text_output}\n
                Thank you! 
            """,
            from_email=settings.FROM_EMAIL_SENDER,
            recipient_list=[settings.EMAIL_PRODUCER],
            fail_silently=False
        )
    # log successfully sent email...



def send_customer_receipt_email(poster_order):
    send_mail(
        subject=f"Receipt for poster order: {poster_order.id} - wasteman.online",
        message=f"""
            Thank you for ordering from us!\n
            Order nr: {poster_order.id}\n
            Your items:\n
            {poster_order.print_line_items}\n
            Your shipping address:\n
            {poster_order.address.text_output}\n
            Have a good one! :)
        """,
        from_email=settings.FROM_EMAIL_SENDER,
        recipient_list=[poster_order.address.email],
        fail_silently=False
    )
    # log successfully sent email...