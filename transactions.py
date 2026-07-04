from data import Data
from dotenv import load_dotenv
import os
import stripe
import threading

class Transactions:
    load_dotenv()
    s_client = stripe.StripeClient(os.getenv("STRIPE_K"))
    transaction_lock = threading.Lock()

    def complete_payment(session_id):
            
            #print("Fulfilling Checkout Session", session_id)
            # Lock for safety
            with Transactions.transaction_lock:

                # Retrieve the Checkout Session from the API with line_items expanded
                checkout_session = Transactions.s_client.v1.checkout.sessions.retrieve(
                    session_id,
                    params={'expand': ['line_items']},
                )

                # Is the fulfillment already, well, fulfilled?
                if "fulfilled" in checkout_session.metadata and checkout_session.metadata["fulfilled"]:
                    return

                # Check the Checkout Session's payment_status property
                # to determine if fulfillment should be performed
                if checkout_session.payment_status != 'unpaid':

                    team_id = checkout_session.metadata["team_id"]
                    user_id = checkout_session.metadata["user_id"]

                    for item in checkout_session.line_items.data:
                        product_id = item.price.product
                        qty = item.quantity # Should not be above 1!
                        amount_paid = item.amount_total
                        currency = item.currency

                        s = Data.create_transaction(team_id, user_id, product_id, qty, amount_paid, currency)
                        if not s:
                            return
                        
                        s = Data.set_team_payment_status(team_id, True)
                        if not s:
                            return
                        
                    # Fulfilled as long as both, no all, above succeeded
                    checkout_session.update({"metadata": {"fulfilled": True}})