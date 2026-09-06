import unittest
from pathlib import Path

import pygame

from entities import (
    CardEntity,
    CardFactory,
    EntityCollection,
    FlatChipsJoker,
    GameRules,
    MultiplierJoker,
)


class EntityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_collection_accepts_duplicates_and_resizes(self):
        collection = EntityCollection()

        card_one = CardEntity("A", "S")
        card_two = CardEntity("A", "S")

        collection.add(card_one)
        collection.add(card_two)

        # La colección permite duplicados.
        self.assertEqual(len(collection), 2)
        self.assertIs(collection[0], card_one)
        self.assertIs(collection[1], card_two)

        # remove_at() reduce dinámicamente el tamaño.
        removed = collection.remove_at(1)

        self.assertIs(removed, card_two)
        self.assertEqual(len(collection), 1)

    def test_factory_creates_rect_and_asset_reference(self):
        factory = CardFactory(asset_root=Path("."))

        card = factory.create_card(
            rank="A",
            suit="S",
            x=100,
            y=200,
        )

        self.assertIsInstance(card, CardEntity)
        self.assertIsInstance(card.rect, pygame.Rect)

        self.assertEqual(card.rect.x, 100)
        self.assertEqual(card.rect.y, 200)

        # En los assets reales del repositorio,
        # S (Spades / Picas) utiliza P en el nombre del archivo.
        self.assertTrue(card.asset_path.endswith("A-P.png"))

        # También verificamos que el asset exista realmente.
        self.assertTrue(Path(card.asset_path).exists())

    def test_generic_collection_is_iterable(self):
        collection = EntityCollection()

        first = CardEntity("A", "S")
        second = CardEntity("K", "H")

        collection.add(first)
        collection.add(second)

        cards = list(collection)

        self.assertEqual(cards, [first, second])

    def test_jokers_modify_each_card(self):
        cards = EntityCollection()

        first = CardEntity("A", "S")
        second = CardEntity("K", "H")

        cards.add(first)
        cards.add(second)

        flat_joker = FlatChipsJoker(
            amount=20,
            probability=1.0,
        )

        multiplier_joker = MultiplierJoker(
            amount=2.0,
            probability=1.0,
        )

        # Como la probabilidad es 1.0, ambos Jokers deben activarse.
        self.assertTrue(flat_joker.activate(cards))
        self.assertTrue(multiplier_joker.activate(cards))

        # Los Jokers modifican el estado de cada carta.
        self.assertEqual(first.score, 20)
        self.assertEqual(second.score, 20)

        self.assertEqual(first.multiplier, 3.0)
        self.assertEqual(second.multiplier, 3.0)

    def test_rules_use_global_values_and_recursive_card_score(self):
        cards = EntityCollection()

        first = CardEntity(
            rank="A",
            suit="S",
            score=10,
            multiplier=2.0,
        )

        second = CardEntity(
            rank="K",
            suit="H",
            score=5,
            multiplier=2.0,
        )

        cards.add(first)
        cards.add(second)

        rules = GameRules(
            score=0,
            multiplier=3.0,
        )

        # A + K no forman pareja:
        # la jugada es High Card.
        result = rules.evaluate(cards)

        # High Card = 5 puntos base.
        # Las cartas aportan 10 + 5 = 15.
        # Score final = 0 + 5 + 15 = 20.
        self.assertEqual(result.name, "High Card")
        self.assertEqual(result.score, 20)

        # Multiplier global = 3.
        # Cada carta aporta +1 sobre el multiplicador base 1.
        # Por tanto:
        # 3 + 1 + 1 = 5.
        self.assertEqual(result.multiplier, 5.0)

        # Total = score * multiplier = 20 * 5 = 100.
        self.assertEqual(result.total, 100)


if __name__ == "__main__":
    unittest.main()