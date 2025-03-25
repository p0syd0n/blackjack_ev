from enum import Enum
import random
import builtins
import seaborn as sns
import matplotlib.pyplot as plt


# 4/6/8 decks, hit soft 17
DAS = False
DECKS = 8
ESTIMATE_TO = 2
ROUNDS = 200
DEBUG = False
BANK_START = 1000
bank = BANK_START
SHOE = 75 #percent
x = [0]
y = [bank]

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
        #dprint(len(decks))
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
    def __init__(self):
        pass
    def set_game(self, game):
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
    def __init__(self, main_character):
        self.main_character = main_character

        prep_decks = []
        for i in range(DECKS):
            new_deck = Deck()
            prep_decks.append(new_deck)

        self.main_deck = Deck(prep_decks)
        self.main_deck.shuffle()
        cards_to_cut = int(len(self.main_deck.content) * (SHOE / 100))
        self.main_deck.content = self.main_deck.content[:-cards_to_cut]
        self.dealer = Dealer()
        self.running_count = 0
        self.true_count = 0
        self.rounds_done = 0
        self.dealer_upcard = None


    def estimate_decks(self):
        if (ESTIMATE_TO <= 0):
            return len(self.main_deck.content) / 52
        return round((len(self.main_deck.content) / 52) * ESTIMATE_TO) / ESTIMATE_TO

    def update_true_count(self):
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
        self.update_true_count()
        bet = 2*(self.true_count)
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
        global bank
        
        while len(self.main_deck.content) > 15:  # buffer to make sure we have enough cards
            player_bet = self.make_bet()
            dprint("betting: " + str(player_bet))
            bank -= player_bet
            player_bet2 = None
            player_hand1 = []
            player_hand2 =  []
            dealer_hand = []
            self.draw_append_update(player_hand1)
            self.draw_append_update(player_hand1)

            self.draw_append_update(dealer_hand, True) #this is the upcard
            self.draw_append_update(dealer_hand)

            dprint(player_hand1)

            while self.total(player_hand1)[0] < 21:
                dprint("Starting feedback loop, the current total is: "+str(self.total(player_hand1)[0]))
                decision = main_character.decide(player_hand1, self.dealer_upcard)
                dprint("decision made: " + str(decision))
                match decision:
                    case DECISION.HIT:
                        dprint("Drawing card")
                        self.draw_append_update(player_hand1)
                    case DECISION.STAND:
                        dprint("Standing")
                        break
                    case DECISION.DOUBLE:
                        dprint("Doubling")
                        player_bet *= 2
                        self.draw_append_update(player_hand1)
                        break
                    case DECISION.SPLIT:
                        dprint("Splitting")
                        player_bet2 = player_bet
                        temp = player_hand1[1]
                        player_hand1 = [player_hand1[0]]
                        player_hand2 = [temp]
                        if player_hand1[0].value() == 11:
                            self.draw_append_update(player_hand1)
                            self.draw_append_update(player_hand2)
                            break
                        while self.total(player_hand1)[0] < 21:
                            dprint("Feedback Loop for Hand 1")
                            decision = main_character.decide(player_hand1, self.dealer_upcard, True)
                            dprint("Made decision for hand 2: " + str(decision))
                            match decision:
                                case DECISION.HIT:
                                    self.draw_append_update(player_hand1)
                                case DECISION.STAND:
                                    break
                                case DECISION.DOUBLE:
                                    player_bet *= 2
                                    self.draw_append_update(player_hand1)
                                    break
                        while self.total(player_hand2)[0] < 21:
                            dprint("Feedback Loop for Hand 2")
                            decision = main_character.decide(player_hand2, self.dealer_upcard, True)
                            dprint("Made decision for hand 2: " + str(decision))
                            match decision:
                                case DECISION.HIT:
                                    self.draw_append_update(player_hand2)
                                case DECISION.STAND:
                                    break
                                case DECISION.DOUBLE:
                                    player_bet *= 2
                                    self.draw_append_update(player_hand2)
                                    break
            dprint("Ended hand 1: " + str(self.total(player_hand1)[0]))
            dprint("Ended hand 2: "+ str(self.total(player_hand2)[0]))
            dprint("Starting Dealer algorithm")
            dealer_total = self.total(dealer_hand)
            while dealer_total[0] < 21:
                if dealer_total[0] < 17 or dealer_total[1] and dealer_total[0] == 17:
                    self.draw_append_update(dealer_hand)
                else:
                    break
                dealer_total =  self.total(dealer_hand)
            dprint("Dealer total: " +  str(dealer_total[0]))
            if dealer_total[0] > 21:
                dealer_total =  (0, False)

            difference1 = self.total(player_hand1)[0] - dealer_total[0]

            if difference1 > 0:
                if self.total(player_hand1)[0] > 21:
                    player_bet = 0 # This is just an easier way of checking for busts. If its a bust, set the bet to 0 which would make it all zero
                payout = 2 * player_bet
                if self.check_blackjack(player_hand1):
                    payout = 2.5 * player_bet
                bank += payout
                dprint("Win")
            elif difference1 == 0:
                bank += player_bet
                dprint("Push")

            if player_hand2 != []:
                difference2 = self.total(player_hand2)[0] - self.total(dealer_hand)[0]
                if difference2 > 0:
                    if self.total(player_hand1)[0] > 21:
                        player_bet = 0
                    payout = 2 * player_bet2
                    if self.check_blackjack(player_hand2):
                        payout = 2.5 * player_bet2
                    bank += payout
                elif difference2 == 0:
                    bank += player_bet2


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

main_character = Main_Character()

for i in range(ROUNDS):
    x.append(i)
    main_game = Game(main_character)
    main_character.set_game(main_game)
    main_game.gameloop()
    y.append(bank)
print(bank)
print(bank - BANK_START)

estimate_to_label = "perfect" if ESTIMATE_TO == -1 else f"1/{ESTIMATE_TO}"

# Construct the label string
label = f"DAS={DAS}, Decks={DECKS}, Estimation={estimate_to_label}, Rounds={ROUNDS}, Bank Start={BANK_START}, Shoe={SHOE}%"

# Create the plot
plt.figure(figsize=(10, 6))
sns.lineplot(x=x, y=y)

total_profit = y[-1] - BANK_START

# Add the total profit label inside the graph
plt.text(0.5, 0.85, f"Total Profit: ${total_profit:.2f}", ha="center", fontsize=12, color="green", weight="bold", transform=plt.gca().transAxes)

# Adding title and labels
plt.title("Bank Value per Round")
plt.xlabel("Round")
plt.ylabel("Bank Value")
plt.figtext(0.5, 0.01, label, ha="center", fontsize=10, wrap=True)  # Add label at the bottom
sns.regplot(x=x, y=y, scatter=False, order=2, line_kws={'color': 'red'})# Save the plot with a descriptive file name
filename = f"Bank_Chart_DAS_{DAS}_Decks_{DECKS}_Shoe_{SHOE}_Rounds_{ROUNDS}.png"
plt.savefig(filename)

# Show the plot
plt.show()



