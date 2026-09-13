import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from states.play_state import PlayState
from states.store_state import StoreState
from entities import CardEntity


class StorePlayLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    @staticmethod
    def _card(suit: str, rank: str) -> CardEntity:
        """Construye una carta mínima usando la firma esperada por el proyecto."""
        return CardEntity(rank=rank, suit=suit)

    def test_store_reward_is_saved_from_leftover_resources(self):
        context = {
            "round": 1,
            "money": 0,
            "jokers": [],
            "ante": 1,
            "blind_target": 100,
            "blind_name": "Ciega pequeña",
            "blind_is_boss": False,
        }
        state = PlayState(self.screen, context)
        state.hands_left = 2
        state.discards_left = 1
        state.round_score = 120
        state._prepare_store_transition()

        reward = context["round_reward"]
        self.assertEqual(reward["total"], reward["base"] + 2 + 1)
        self.assertEqual(context["money"], reward["total"])
        self.assertTrue(context["blind_won"])

    def test_store_returns_play_with_selected_blind(self):
        context = {"money": 20, "jokers": [], "ante": 1}
        store = StoreState(self.screen, context)
        store.enter()
        store.phase = StoreState.BLIND_SELECT
        result = store._continue_to_play()

        self.assertEqual(result, "PLAY")
        self.assertIn("blind_target", context)
        self.assertIn("blind_name", context)
        self.assertIn("blind_is_boss", context)

    def test_sort_by_suit_uses_real_card_symbols_and_descending_rank(self):
        context = {"money": 0, "jokers": [], "blind_target": 100}
        state = PlayState(self.screen, context)
        cards = [
            self._card("♠", "2"),
            self._card("♥", "K"),
            self._card("♣", "7"),
            self._card("♦", "A"),
            self._card("♣", "Q"),
            self._card("♥", "3"),
            self._card("♦", "10"),
            self._card("♠", "J"),
        ]
        state.cards.clear()
        state.cards.add_many(cards)
        state._sync_card_rects()
        state.sort_by_suit()

        actual = [(card.suit, card.rank) for card in state.cards]
        expected = [
            ("♣", "Q"),
            ("♣", "7"),
            ("♦", "A"),
            ("♦", "10"),
            ("♥", "K"),
            ("♥", "3"),
            ("♠", "J"),
            ("♠", "2"),
        ]
        self.assertEqual(actual, expected)

    def test_sort_by_rank_is_descending_and_uses_suit_as_tiebreaker(self):
        context = {"money": 0, "jokers": [], "blind_target": 100}
        state = PlayState(self.screen, context)
        cards = [
            self._card("♠", "10"),
            self._card("♣", "A"),
            self._card("♥", "10"),
            self._card("♦", "K"),
            self._card("♣", "10"),
            self._card("♠", "A"),
            self._card("♦", "3"),
            self._card("♥", "Q"),
        ]
        state.cards.clear()
        state.cards.add_many(cards)
        state._sync_card_rects()
        state.sort_by_rank()

        actual = [(card.rank, card.suit) for card in state.cards]
        expected = [
            ("A", "♣"),
            ("A", "♠"),
            ("K", "♦"),
            ("Q", "♥"),
            ("10", "♣"),
            ("10", "♥"),
            ("10", "♠"),
            ("3", "♦"),
        ]
        self.assertEqual(actual, expected)

    def test_buy_offer_deducts_money_and_persists_joker(self):
        context = {"money": 50, "jokers": [], "ante": 1}
        store = StoreState(self.screen, context)
        store.enter()
        offer = store.offers[0]
        starting_money = store.money
        price = offer.price
        joker_name = offer.joker.name

        store._buy_offer(0)

        self.assertEqual(store.money, starting_money - price)
        self.assertEqual(len(store.jokers), 1)
        self.assertEqual(store.jokers[0].name, joker_name)
        self.assertLess(len(store.offers), 2)

    def test_buy_offer_rejects_insufficient_money(self):
        context = {"money": 0, "jokers": [], "ante": 1}
        store = StoreState(self.screen, context)
        store.enter()
        price = store.offers[0].price

        store._buy_offer(0)

        self.assertEqual(store.money, 0)
        self.assertEqual(store.jokers, [])
        self.assertIn(str(price), store.message)

def test_sell_selected_returns_half_purchase_price(self):
    context = {"money": 100, "jokers": [], "ante": 1}
    store = StoreState(self.screen, context)
    store.enter()

    purchase_price = store.offers[0].price
    store._buy_offer(0)

    self.assertEqual(len(store.jokers), 1)
    self.assertEqual(store.money, 100 - purchase_price)

    store.selected_owned_index = 0
    store._sell_selected()

    sell_value = max(1, purchase_price // 2)

    self.assertEqual(store.money, 100 - purchase_price + sell_value)
    self.assertEqual(store.jokers, [])
    self.assertIsNone(store.selected_owned_index)

    def test_reroll_charges_exact_cost_and_replaces_offers(self):
        context = {"money": 20, "jokers": [], "ante": 1}
        store = StoreState(self.screen, context)
        store.enter()
        old_offer_objects = [id(offer.joker) for offer in store.offers]

        store._reroll()

        self.assertEqual(store.money, 15)
        self.assertEqual(len(store.offers), 2)
        self.assertNotEqual(old_offer_objects, [id(offer.joker) for offer in store.offers])

    def test_full_store_flow_preserves_purchased_joker_into_play_context(self):
        context = {"money": 50, "jokers": [], "ante": 1}
        store = StoreState(self.screen, context)
        store.enter()
        purchased = store.offers[0].joker
        store._buy_offer(0)
        store._continue_to_play()

        self.assertIn(purchased, context["jokers"])
        self.assertEqual(store.context["blind_name"], store.blind_options[0].name)
        self.assertEqual(store.context["blind_target"], store.blind_options[0].target)


if __name__ == "__main__":
    unittest.main()
