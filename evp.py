from enum import Enum
import random
import builtins
import seaborn as sns
import matplotlib.pyplot as plt
from time import sleep

# 4/6/8 decks, hit soft 17
TRACE= False
DAS = False
DECKS = 8

#graph profit for each round as a data point. Setting to False will 
# graph profit from each hand as a data point.
GRAPH_PER_ROUND = False 
ESTIMATE_TO = 2
ROUNDS = 20
DEBUG = False
BANK_START = 1000
bank = BANK_START
SHOE = 75 #percent
MIN_BET = 10


class DECISION(Enum):
    HIT = "H"
    STAND = "S"
    DOUBLE = "D"
    SPLIT = "P"
    DOUBLE_OR_STAND = "DS"
    DOUBLE_OR_HIT = "DH"
    SPLIT_IF_DAS = "SP"

class Card:
    SUITS = ['spade', 'heart', 'diamond', 'club']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.count_value = 1 if rank in ['2', '3', '4', '5', '6'] else (-1 if rank in ['10', 'J', 'Q', 'K', 'A'] else 0)    
    def __repr__(self):
        return f"Card('{self.rank}', '{self.suit}')"
    
    def __str__(self):
        return f"{self.rank} of {self.suit}s"
    
    def value(self):
        """Returns the blackjack value of the card"""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Soft value, can be 1 in some cases
        else:
            return int(self.rank)
    def get_count_value(self):
        return self.count_value

class Deck:
    def __init__(self, decks=[]):
        self.content = []
        if (decks == []):
            for suit in Card.SUITS:
                for rank in Card.RANKS:
                    self.content.append(Card(rank, suit))
        else:
            for deck in decks:
                for card in deck.content:
                    self.content.append(card)

    def __str__(self):
        return f"Deck of {len(self.content)/52} Decks"

    def shuffle(self):
        random.shuffle(self.content)


class Player:
    def __init__(self, game):
        self.game = game


class Dealer(Player):
    pass


class Main_Character(Player):
    def decide(self, hand, dealer_upcard, prev_was_split=False):
        dealer_upcard_index = dealer_upcard.value() - 2
        total = self.game.total(hand)
        decision =  None
        try:
            pairs_condition = hand[0].rank == hand[1].rank and len(hand) == 2 and not prev_was_split
        except:
            pairs_condition = False
        if total[1]:
            if total[0] < 13:
                decision = DECISION.HIT
            elif total[0] > 18:
                decision = DECISION.STAND
            else:
                decision = blackjack_strategy["soft"][total[0]][dealer_upcard_index]
        elif pairs_condition:
            key = None
            try:
                key = int(hand[0].rank)
            except:
                key = 10
            decision = blackjack_strategy["pairs"][key][dealer_upcard_index]
        else:
            if total[0] <= 8:
                decision = DECISION.HIT
            elif total[0] >= 17:
                decision = DECISION.STAND
            else:
                decision = blackjack_strategy["hard"][total[0]][dealer_upcard_index]
        return decision


class Game:
    def __init__(self, shoe, min_bet, estimate_to, das, decks, current_trial_bank, data):
        self.data = data
        self.bank = current_trial_bank
        self.main_character = Main_Character(self)
        self.shoe = shoe
        self.min_bet = min_bet
        self.estimate_to = estimate_to
        self.das = das
        self.decks = decks

        prep_decks = []
        for i in range(self.decks):
            new_deck = Deck()
            prep_decks.append(new_deck)

        self.main_deck = Deck(prep_decks)
        self.main_deck.shuffle()
        cards_to_cut = int(len(self.main_deck.content) * (1-(self.shoe / 100)))

        self.main_deck.content = self.main_deck.content[:-cards_to_cut]
        self.dealer = Dealer(self)
        self.running_count = 0
        self.true_count = 0
        self.rounds_done = 0
        self.edge = 0.005 * self.true_count
        self.dealer_upcard = None


    def estimate_decks(self):
        if (self.estimate_to <= 0):
            return len(self.main_deck.content) / 52
        return round((len(self.main_deck.content) / 52) * self.estimate_to) / self.estimate_to

    def update_true_count_and_edge(self):
        step(f"Estimating decks left to be {self.estimate_decks()}, and a rc of {self.running_count}, setting true count to {self.running_count / self.estimate_decks()}")
        self.true_count = self.running_count / self.estimate_decks()

    def total(self, list):
        total = 0
        soft = False
        for card in list:
            if card.rank == "A":
                soft = True
            total += card.value()
        if (total > 21 and soft):
            total -= 10
            soft = False
        return (total, soft)
    
    def make_bet(self):
        #return random.randint(10,int(bank))

        self.update_true_count_and_edge()
        #edges.append(self.edge)

        bet = self.edge * self.bank * 0.5 # half-kelly i think
        if bet > 150:
            bet = 150

        if bet < 10:
            bet = 10

        return bet
    
    def draw_append_update(self, hand, upcard=False):
        new_card = self.main_deck.content[len(self.main_deck.content)-1]
        self.main_deck.content.pop()
        hand.append(new_card)
        self.running_count += new_card.get_count_value()
        if upcard:
            self.dealer_upcard = new_card

    def check_blackjack(self, hand):
        return (hand[0].rank in ["K", "Q", "J"] and hand[1].rank == "A") or (hand[1].rank in ["K", "Q", "J"] and hand[0].rank == "A") if len(hand) >= 2 else False

    def gameloop(self):
        print("Starting a new game where the bank is "+str(self.bank))
        step("Started new gameloop (new game)")
        
        while len(self.main_deck.content) > 15:  # buffer to make sure we have enough cards
            bank_start_of_round = self.bank
            step("Making a new bet")
            player_bet = self.make_bet()
            step(f"the rc={self.running_count} and true count was: {self.true_count} which resulted in a bet of {player_bet}")
            self.bank -= player_bet
            player_bet2 = None
            player_hand1 = []
            player_hand2 =  []
            dealer_hand = []
            self.draw_append_update(player_hand1)
            self.draw_append_update(player_hand1)
            step(f"You have been dealt: {player_hand1} ({'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard})")

            self.draw_append_update(dealer_hand, True) #this is the upcard
            self.draw_append_update(dealer_hand)
            step(f"The dealer has been dealt: {dealer_hand} with an upcard of {self.dealer_upcard}")

            step(f"You begin making decisions. Your current total is {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard}")
            while self.total(player_hand1)[0] < 21:
                step("Feedback loop iteration. The current total is: "+str(self.total(player_hand1)[0]))
                decision = self.main_character.decide(player_hand1, self.dealer_upcard)
                step(f"You have made the decision to {decision} based off a {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard}")
                match decision:
                    case DECISION.HIT:
                        self.draw_append_update(player_hand1)
                        step(f"New hand: {player_hand1}\n{'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]}")
                    case DECISION.STAND:
                        step(f"Standing on a {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard.value()}")
                        break
                    case DECISION.DOUBLE:
                        step("Doubling")
                        player_bet *= 2
                        step(f"New bet: {player_bet}")
                        self.draw_append_update(player_hand1)
                        step(f"New hand: {player_hand1}\n{'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]}")
                        break
                    case DECISION.SPLIT:
                        step("Splitting")
                        player_bet2 = player_bet
                        temp = player_hand1[1]
                        player_hand1 = [player_hand1[0]]
                        player_hand2 = [temp]
                        if player_hand1[0].value() == 11:
                            step("Aces were split. Drawing 1 card per hand")
                            self.draw_append_update(player_hand1)
                            self.draw_append_update(player_hand2)
                            break
                        while self.total(player_hand1)[0] < 21:
                            step("New iteration for hand 1 feedback loop")
                            decision = self.main_character.decide(player_hand1, self.dealer_upcard, True)
                            step(f"You have made the decision to, on hand 1, {decision} based off a {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard}")
                            match decision:
                                case DECISION.HIT:
                                    self.draw_append_update(player_hand1)
                                    step(f"New hand: {player_hand1}\n{'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]}")
                                case DECISION.STAND:
                                    step(f"Standing on a {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard.value()}")
                                    break
                                case DECISION.DOUBLE:
                                    step("Doubling Hand 1")
                                    player_bet *= 2
                                    step(f"New bet hand 1: {player_bet}")
                                    self.draw_append_update(player_hand1)
                                    step(f"New hand 1: {player_hand1}\n{'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]}")
                                    break
                        while self.total(player_hand2)[0] < 21:
                            step("New iteration for hand 2 feedback loop")
                            decision = self.main_character.decide(player_hand2, self.dealer_upcard, True)
                            step(f"You have made the decision to, on hand 2, {decision} based off a {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]} vs a {self.dealer_upcard}")
                            match decision:
                                case DECISION.HIT:
                                    self.draw_append_update(player_hand2)
                                    step(f"New hand: {player_hand2}\n{'soft' if self.total(player_hand2)[1] else 'hard'} {self.total(player_hand2)[0]}")
                                case DECISION.STAND:
                                    step(f"Standing on a {'soft' if self.total(player_hand2)[1] else 'hard'} {self.total(player_hand2)[0]} vs a {self.dealer_upcard.value()}")
                                    break
                                case DECISION.DOUBLE:
                                    step("Doubling Hand 2")
                                    player_bet2 *= 2
                                    step(f"New bet hand 2: {player_bet2}")
                                    self.draw_append_update(player_hand2)
                                    step(f"New hand 2: {player_hand2}\n{'soft' if self.total(player_hand2)[1] else 'hard'} {self.total(player_hand2)[0]}")
                                    break

            step("Ended hand 1: " + str(self.total(player_hand1)[0]))
            step("Ended hand 2: "+ str(self.total(player_hand2)[0]))
            dealer_total = self.total(dealer_hand)
            step(f"Starting Dealer algorithm with total {'soft' if dealer_total[1] else 'hard'} {dealer_total[0]}")

            while dealer_total[0] < 21:
                if dealer_total[0] < 17 or dealer_total[1] and dealer_total[0] == 17:
                    step(f"Dealer hitting with total {'soft' if dealer_total[1] else 'hard'} {dealer_total[0]}")
                    self.draw_append_update(dealer_hand)
                else:
                    break
                dealer_total =  self.total(dealer_hand)
            step(f"Dealer stops. total: {'soft' if dealer_total[1] else 'hard'} {dealer_total[0]}")
            if dealer_total[0] > 21:
                dealer_total =  (0, False)
                step(f"The dealer busts. Setting dealer total to hard 0")

            difference1 = self.total(player_hand1)[0] - dealer_total[0]
            step(f"END OF ROUND\n    Player total: \n\tHand 1: {'soft' if self.total(player_hand1)[1] else 'hard'} {self.total(player_hand1)[0]}\n\tHand 2:  {'soft' if self.total(player_hand2)[1] else 'hard'} {self.total(player_hand2)[0]}")
            step(f"Score difference for hand 1 is: {difference1}")
            if difference1 > 0:
                step("Dif > 0")
                if self.total(player_hand1)[0] > 21:
                    step("Player busts. setting his bet to 0")
                    player_bet = 0 # This is just an easier way of checking for busts. If its a bust, set the bet to 0 which would make it all zero
                payout = 2 * player_bet
                if self.check_blackjack(player_hand1):
                    step("The player has blackjack. Payout 2.5 * bet (1 * bet + 1.5 * bet)")
                    payout = 2.5 * player_bet
                self.bank += payout
                step(f"Paid out the player with {payout - player_bet}")
            elif difference1 == 0:
                step("Player push")
                self.bank += player_bet
            else:
                step(f"Dif: {difference1}, money was lost")

            if player_hand2 != []:
                difference2 = self.total(player_hand2)[0] - self.total(dealer_hand)[0]
                step(f"A second hand exists. Its difference is {difference2}")
                if difference2 > 0:
                    if self.total(player_hand1)[0] > 21:
                        step("Hand 2 busted. bet = 0 making payout 0")
                        player_bet = 0
                    payout = 2 * player_bet2
                    if self.check_blackjack(player_hand2):
                        step("Hand 2 Blackjack")
                        payout = 2.5 * player_bet2
                    self.bank += payout
                    step(f"Payed {payout - player_bet} for hand 2.")
                elif difference2 == 0:
                    self.bank += player_bet2
                    step("Pushed hand 2.")
                else:
                    step("Lost hand 2.")
            if self.bank - bank_start_of_round > 0:
                prefix = "[+] "
            elif self.bank == bank_start_of_round:
                prefix = "[=] "
            else:
                prefix = "[-] "
            step(f"{prefix}{abs(self.bank-bank_start_of_round)}")
            print("The bank is now"+str(self.bank))
            if self.bank <= self.min_bet:
                
                self.main_deck.content =  [] # just a quick way to exit the current shoe loop. 
            self.data.append(0 if self.bank <= 0 else self.bank)



blackjack_strategy = {
    "hard": {
        8: [DECISION.HIT] * 10,  # All dealer upcards
        9: [DECISION.HIT, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE,
            DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        10: [DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE,
             DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.HIT, DECISION.HIT],
        11: [DECISION.DOUBLE] * 10,  # Always double
        12: [DECISION.HIT, DECISION.HIT, DECISION.STAND, DECISION.STAND, DECISION.STAND,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        13: [DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        14: [DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        15: [DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        16: [DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
    },
    "soft": {
        13: [DECISION.HIT, DECISION.HIT, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.HIT,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        14: [DECISION.HIT, DECISION.HIT, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.HIT,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        15: [DECISION.STAND, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        16: [DECISION.STAND, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE, DECISION.DOUBLE,
             DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        17: [DECISION.DOUBLE if DAS else DECISION.STAND, DECISION.DOUBLE if DAS else DECISION.STAND, DECISION.DOUBLE if DAS else DECISION.STAND, 
             DECISION.DOUBLE if DAS else DECISION.STAND, DECISION.DOUBLE if DAS else DECISION.STAND, DECISION.STAND, DECISION.STAND,
             DECISION.HIT, DECISION.HIT, DECISION.HIT],
        18: [DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.DOUBLE if DAS else DECISION.STAND,
             DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND, DECISION.STAND],
    },
    "pairs": {
        2: [DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT,
            DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        3: [DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT,
            DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        4: [DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.SPLIT if DAS else DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT], 
        5: [DECISION.DOUBLE] * 8 + [DECISION.HIT, DECISION.HIT],  # 2-9: Double, 10-A: Hit
        6: [DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT,
            DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        7: [DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT,
            DECISION.SPLIT, DECISION.HIT, DECISION.HIT, DECISION.HIT, DECISION.HIT],
        8: [DECISION.SPLIT] * 8 + [DECISION.HIT, DECISION.HIT],  # 2-9: Split, 10-A: Hit
        9: [DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT, DECISION.SPLIT,
            DECISION.STAND, DECISION.SPLIT, DECISION.SPLIT, DECISION.STAND, DECISION.STAND],
        10: [DECISION.STAND] * 10,  # Always stand
        'A': [DECISION.SPLIT] * 10,  # Always split
    }
}

def dprint(message):
    if DEBUG:
        print(message)

def step(message):
    if TRACE:
        input(message)


def run_game():
    pass

def run_sim(shoe, min_bet, estimate_to, das, decks, bank_start, rounds, filename=""):
    y = [bank]
    current_trial_bank = bank_start
    for i in range(rounds):
        # game: main_character, shoe, min_bet, estimate_to, das, decks
        main_game = Game(SHOE, MIN_BET, ESTIMATE_TO, DAS, DECKS, current_trial_bank, y)
        main_game.gameloop()
        current_trial_bank = main_game.bank

    print(current_trial_bank)
    print(current_trial_bank - bank_start)

    estimate_to_label = "perfect" if estimate_to == -1 else f"1/{estimate_to}"

    # Construct the label string
    label = f"DAS={das}, Decks={decks}, Estimation={estimate_to_label}, Rounds={rounds}, Bank Start={bank_start}, Shoe={shoe}%"

    # Create the plot
    plt.figure(figsize=(10, 6))
    x = []
    for i in range(len(y)):
        x.append(i)
    #print(x)
    sns.lineplot(x=x, y=y)

    total_profit = y[-1] - bank_start

    # Add the total profit label inside the graph
    plt.text(0.5, 0.85, f"Total Profit: ${total_profit:.2f}", ha="center", fontsize=12, color="green", weight="bold", transform=plt.gca().transAxes)

    # Adding title and labels
    plt.title(f"Bank Value per Hand")
    plt.xlabel(f"Hand")
    plt.ylabel("Bank Value")
    plt.figtext(0.5, 0.01, label, ha="center", fontsize=10, wrap=True)  # Add label at the bottom
    try:

        sns.regplot(x=x, y=y, scatter=False, order=2, line_kws={'color': 'red'})# Save the plot with a descriptive file name
    except Exception as e:
        print(F"Problems making the line of best fit: \n{e}")
    filename_gen = f"Bank_Chart_DAS_{das}_Decks_{decks}_Shoe_{shoe}_Rounds_{rounds}.png" if filename == "" else filename
    plt.savefig(filename_gen)

    # Show the plot
    plt.show()

run_sim(SHOE, MIN_BET, ESTIMATE_TO, DAS, DECKS, BANK_START, ROUNDS)

