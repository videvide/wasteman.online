from django.conf import settings
from django.core.mail import send_mail

def send_producer_email(poster_order):
    """Send order request to print-on-demand service."""
    try:
        send_mail(
                subject="Print-on-demand poster order from wasteman.online",
                message=f"""
                    Hi, we want to make an order for the following posters:\n
                    {poster_order.print_line_items}\n
                    And we want it sent to this address:\n
                    {poster_order.address.text_output}\n
                    Thank you! 
                """,
                from_email=settings.EMAIL_FROM_SENDER,
                recipient_list=[settings.EMAIL_PRODUCER],
                fail_silently=False
            )
    except Exception as e:
        print(f"Producer email failed with Exception: {e}")
        # Log failed email send...
    
    print("Producer email succesfully sent!")
    # Log successfully sent email...


def send_customer_receipt_email(poster_order):
    """Send customer receipt."""
    try:
        send_mail(
            subject=f"Receipt for poster order: {poster_order.id} - wasteman.online",
            message=f"""
                Thank you for your order!\n
                Order nr: {poster_order.id}\n
                Your items:\n
                {poster_order.print_line_items}\n
                Your shipping address:\n
                {poster_order.address.text_output_with_email}\n
                Please contact us if you have any questions!\n
                Thank you!
            """,
            from_email=settings.EMAIL_FROM_SENDER,
            recipient_list=[poster_order.address.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Customer receipt email failed with Exception: {e}")
        # Log failed email send...

    print("Customer receipt email successfully sent!")
    # Log successfully sent email...