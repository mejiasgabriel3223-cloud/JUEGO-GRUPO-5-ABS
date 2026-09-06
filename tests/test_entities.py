import unittest

from entities import FlatChipsJoker, HandEvaluator, MultiplierJoker, Player, Rank, StandardDeckFactory, Suit
from entities.card import PlayingCard
from entities.base import ScoreContext


class EntityTests(unittest.TestCase):
    def test_standard_deck_has_52_cards(self):
        deck = StandardDeckFactory.create()
        self.assertEqual(len(deck), 52)

    def test_recursive_draw_many(self):
        deck = StandardDeckFactory.create()
        cards = deck.draw_many(8)
        self.assertEqual(len(cards), 8)
        self.assertEqual(len(deck), 44)

    def test_hand_pair(self):
        cards = [
            PlayingCard(Rank.ACE, Suit.CLUBS),
            PlayingCard(Rank.ACE, Suit.HEARTS),
            PlayingCard(Rank.SEVEN, Suit.CLUBS),
        ]
        name, context = HandEvaluator.evaluate(cards)
        self.assertEqual(name, "Pareja")
        self.assertGreater(context.score, 0)

    def test_polymorphic_jokers(self):
        base = ScoreContext(20, 2)
        jokers = [FlatChipsJoker(10), MultiplierJoker(2)]
        final = HandEvaluator.apply_jokers(base, jokers)
        self.assertEqual(final.chips, 30)
        self.assertEqual(final.multiplier, 4)
        self.assertEqual(final.score, 120)

    def test_player_serialization(self):
        player = Player("Gabriel")
        data = player.to_dict()
        self.assertEqual(data["name"], "Gabriel")
        self.assertIn("hand", data)
        self.assertIn("jokers", data)


if __name__ == "__main__":
    unittest.main()
