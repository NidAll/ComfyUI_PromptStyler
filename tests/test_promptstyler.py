from __future__ import annotations

import unittest

import nodes
import style_library


class FakeTextEncoder:
    def __init__(self):
        self.last_text = None
        self.last_tokens = None

    def tokenize(self, text):
        self.last_text = text
        self.last_tokens = {"text": text}
        return self.last_tokens

    def encode_from_tokens_scheduled(self, tokens):
        return [[tokens, {"source": tokens["text"]}]]


class PromptStylerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = style_library.get_cached_style_library(load_policy=style_library.LOAD_POLICY_STRICT)
        cls.stable_node = nodes.PromptStylerConditioning()
        cls.primary_choice = next(choice for choice in cls.library.choices if choice.endswith("| cinematic_anamorphic"))
        cls.secondary_choice = next(choice for choice in cls.library.choices if choice.endswith("| cin_film_noir"))

    def test_apply_style_false_returns_raw_prompt(self):
        encoder = FakeTextEncoder()
        conditioning, styled_prompt = self.stable_node.encode(
            prompt="red fox",
            apply_style=False,
            style=self.primary_choice,
            template_variant="default",
            style_id_override="",
            text_encoder=encoder,
        )
        self.assertEqual("red fox", styled_prompt)
        self.assertEqual("red fox", encoder.last_text)
        self.assertEqual(1, len(conditioning))

    def test_style_id_override_takes_precedence(self):
        encoder = FakeTextEncoder()
        conditioning, styled_prompt = self.stable_node.encode(
            prompt="portrait",
            apply_style=True,
            style=self.secondary_choice,
            template_variant="default",
            style_id_override="cinematic_anamorphic",
            text_encoder=encoder,
        )
        expected_style = style_library.resolve_style_legacy(
            self.library,
            choice=self.primary_choice,
            style_id_override="cinematic_anamorphic",
        )
        expected_prompt, _details = style_library.compose_prompt_legacy(
            "portrait",
            expected_style,
            template_variant="default",
        )
        self.assertEqual(expected_prompt, styled_prompt)
        self.assertEqual(expected_prompt, encoder.last_text)
        self.assertEqual(1, len(conditioning))

    def test_legacy_default_variant_matches_expected_fixture(self):
        encoder = FakeTextEncoder()
        conditioning, styled_prompt = self.stable_node.encode(
            prompt="cinematic film still, robot detective",
            apply_style=True,
            style=self.primary_choice,
            template_variant="default",
            style_id_override="",
            text_encoder=encoder,
        )
        expected = (
            "cinematic film still, professional cinematography, cinematic framing, carefully composed shot, "
            "atmospheric depth, realistic lighting, cinematic, anamorphic look, shallow depth of field, "
            "dramatic lighting, robot detective, film grain, subtle halation, rich contrast, color graded, "
            "filmic color science, smooth highlight rolloff, deep blacks, subtle film grain, soft halation, "
            "high dynamic range"
        )
        self.assertEqual(expected, styled_prompt)
        self.assertEqual(expected, encoder.last_text)
        self.assertEqual(1, len(conditioning))

    def test_flux_variant_uses_variant_text_when_present(self):
        encoder = FakeTextEncoder()
        conditioning, styled_prompt = self.stable_node.encode(
            prompt="robot detective",
            apply_style=True,
            style=self.primary_choice,
            template_variant="flux_2_klein",
            style_id_override="",
            text_encoder=encoder,
        )
        expected_style = self.library.by_id["cinematic_anamorphic"]
        expected_prompt, _details = style_library.compose_prompt_legacy(
            "robot detective",
            expected_style,
            template_variant="flux_2_klein",
        )
        self.assertEqual(expected_prompt, styled_prompt)
        self.assertEqual(expected_prompt, encoder.last_text)
        self.assertEqual(1, len(conditioning))

    def test_missing_variant_falls_back_to_default(self):
        style = self.library.by_id["cinematic_anamorphic"]
        default_prompt, _default_details = style_library.compose_prompt_legacy(
            "robot detective",
            style,
            template_variant="default",
        )
        fallback_prompt, details = style_library.compose_prompt_legacy(
            "robot detective",
            style,
            template_variant="missing_variant",
        )
        self.assertEqual(default_prompt, fallback_prompt)
        self.assertEqual(style_library.DEFAULT_VARIANT, details["variant"])

    def test_missing_text_encoder_raises_explicit_error(self):
        with self.assertRaisesRegex(RuntimeError, "text_encoder input is invalid"):
            self.stable_node.encode(
                prompt="robot detective",
                apply_style=True,
                style=self.primary_choice,
                template_variant="default",
                style_id_override="",
                text_encoder=None,
            )

    def test_unknown_style_id_override_raises_error(self):
        encoder = FakeTextEncoder()
        with self.assertRaisesRegex(ValueError, "Unknown style_id_override"):
            self.stable_node.encode(
                prompt="robot detective",
                apply_style=True,
                style=self.primary_choice,
                template_variant="default",
                style_id_override="does_not_exist",
                text_encoder=encoder,
            )


if __name__ == "__main__":
    unittest.main()
