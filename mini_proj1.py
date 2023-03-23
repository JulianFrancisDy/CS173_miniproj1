import smartpy as sp
import sys 

class Lottery(sp.Contract):
    def __init__(self):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            n_tix_available = sp.nat(5),
            max_n_tix = sp.nat(5),
            admin = sp.test_account("admin").address
        )

    @sp.entry_point
    def buy_ticket(self, num_tickets = 1): # Added parameter "num_tickets", number of n_tix to be bought; default is 1
 
        sp.set_type(num_tickets, sp.TNat) # Convert num_tickets to TNat type

        # Sanity checks
        total_cost = sp.local("total_cost", sp.mul(self.data.ticket_cost, num_tickets))

        sp.verify(sp.amount >= sp.mul(self.data.ticket_cost, num_tickets)) # Transaction is greater than or equal to the cost of n_tix
        sp.verify(self.data.n_tix_available >= num_tickets, "NO n_tix AVAILABLE") # Check if there's enough available n_tix for the number of n_tix

        n_tix = sp.local("n_tix", num_tickets) # Create a local variable for n_tix

        # Update Storage
        sp.while n_tix.value > 0:
            self.data.players[sp.len(self.data.players)] = sp.sender
            self.data.n_tix_available = sp.as_nat(self.data.n_tix_available - 1)

            n_tix.value = sp.as_nat(n_tix.value-sp.nat(1)) # Decrement number of tix


        # Return extra tez balance to the sender
        extra_balance = sp.amount - sp.mul(self.data.ticket_cost, num_tickets) # Balance is now amount - total cost
        sp.if extra_balance > sp.tez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self):

        # Sanity checks
        sp.verify(self.data.n_tix_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = sp.as_nat(sp.now - sp.timestamp(0)) % self.data.max_n_tix
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.n_tix_available = self.data.max_n_tix

    @sp.entry_point
    def adjust_ticket(self, new_ticket_cost, new_max_n_tix): # New function that allows admin to change ticket cost and maximum n_tix
        
        # Sanity checks
        sp.verify(sp.sender == self.data.admin, message="MUST BE ADMIN TO CHANGE TICKET DETAILS") # Check if command was issued by admin
        sp.verify(self.data.n_tix_available == self.data.max_n_tix, message="GAME STARTED, CANNOT CHANGE n_tix") # Check if n_tix available match max n_tix

        # Modify n_tix
        self.data.ticket_cost = new_ticket_cost
        self.data.max_n_tix = new_max_n_tix
        self.data.n_tix_available = new_max_n_tix

@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")
    john = sp.test_account("john")

    # Contract instance
    lottery = Lottery()
    scenario += lottery

    # lottery.adjust_ticket(sp.tez(100), sp.nat(1000000))

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(2), sender = bob)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(3), sender = john)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = charles)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = mike, valid = False)


    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game().run(sender = admin, now = sp.timestamp(20))

    # Adjust Tickets Test
    lottery.adjust_ticket(new_ticket_cost = sp.tez(2), new_max_n_tix = sp.nat(6)).run(sender=alice, valid = False)
    lottery.adjust_ticket(new_ticket_cost = sp.tez(2), new_max_n_tix = sp.nat(6)).run(sender=admin)

    
