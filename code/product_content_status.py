from openai import OpenAI
import json
import re
from typing import Dict, Any
import uuid
import os
import argparse

# Constants
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PRODUCT_JSON_PATH = os.getenv("PRODUCT_JSON_PATH")


def clean_json_response(response_text: str) -> str:
    response_text = re.sub(r"```json\s*", "", response_text)
    response_text = re.sub(r"```\s*$", "", response_text)
    response_text = response_text.replace('"', '"').replace('"', '"')
    response_text = re.sub(
        r"(?<!\\)'(?=([^']*'[^']*')*[^']*$)", "\\'", response_text
    )  # Escape single quotes
    response_text = response_text.replace(""", "'").replace(""", "'")
    return response_text.strip()


def fix_json_with_gpt(
    broken_json: str, context: str, expected_keys: list = None
) -> str:
    fix_prompt = f"""Fix this broken JSON and return ONLY valid JSON (no explanations, no markdown):

Context: {context}
Broken JSON: {broken_json}

Rules:
- All keys must have double quotes
- All string values must have double quotes
- For HTML attributes (e.g., href, title), use single quotes (e.g., href='/path')
- Escape quotes inside strings with backslashes
- Ensure proper string termination to avoid unterminated string errors
- No trailing commas
- Ensure ALL the following keys are included: {', '.join(expected_keys) if expected_keys else 'None specified'}
- If a key is missing, provide a default value relevant to the context:
  - For HTML fields, use '<p>Contenu par défaut</p>'
  - For raw text fields (e.g., head_text_lumin_hero_8jr4ii, text_264e37ac, text_74e17b96, text_popup_DVDmRD, stock-related texts, button texts), use 'Texte par défaut'
- Return only the fixed JSON"""

    try:
        print(
            f"Attempting to fix JSON for {context}. Input (first 500 chars): {broken_json[:500]}..."
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0.1,
            max_tokens=2000,
        )
        fixed_json = clean_json_response(response.choices[0].message.content.strip())
        print(f"Fixed JSON for {context} (first 500 chars): {fixed_json[:500]}...")
        return fixed_json
    except Exception as e:
        print(f"Error in fix_json_with_gpt for {context}: {e}")
        return broken_json


def prompt_gpt(prompt: str, max_retries: int = 3, max_tokens: int = 300) -> str:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            continue


def translate_text(text, target_language):
    prompt = f"Translate to {target_language}. Return only the translation, no explanations: {text}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip().replace('"', "")
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def replace_in_file(file_path: str, placeholder: str, content: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
        if placeholder in data:
            data = data.replace(placeholder, content)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(data)
            print(
                f"Replaced {placeholder} with content (first 100 chars): {content[:100]}..."
            )
        else:
            print(f"Warning: Placeholder {placeholder} not found in {file_path}")
    except Exception as e:
        print(f"Error replacing {placeholder} in {file_path}: {e}")


def validate_html_format(text: str, expected_format: str = None) -> bool:
    if expected_format and "<" in expected_format:
        original_tags = re.findall(r"<[^>]+>", expected_format)
        result_tags = re.findall(r"<[^>]+>", text)
        return len(original_tags) <= len(result_tags)
    return True


def generate_with_format_validation(
    prompt: str, expected_format: str = None, max_tokens: int = 300
) -> str:
    if expected_format and "<" in expected_format:
        prompt += f"\n\nIMPORTANT: Maintain the exact HTML structure from this example: {expected_format}"
    for attempt in range(3):
        result = prompt_gpt(prompt, max_tokens=max_tokens)
        if validate_html_format(result, expected_format):
            return result
        prompt += "\n\nPlease maintain the HTML tags structure exactly as shown in the example."
    return result


def process_product_translations(brand_name: str, product_title: str, language: str):
    translations = [
        (
            "Pairs well with",
            "NEW_BLOCK_HEADING_006E6C29_717A_4F58_8FEA_CABC7DA6316F_TRANSLATED",
        ),
        ("Shop Collection", "NEW_BUTTON_LABEL_BUTTON_MHN8PC_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_13A5819E_5698_472F_94EB_34D5A7AD9B21_TRANSLATED"),
        ("Jan 2024", "NEW_DATE_TEXT_30900101_E5C8_4C0E_B5BD_0FCF8EEA85CF_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_3C322C1A_1E3A_47E6_8D7B_720D506EB595_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_53A5B896_0517_4E05_80FE_B23DE703E79B_TRANSLATED"),
        ("Dec 2023", "NEW_DATE_TEXT_D032A47C_6F6E_4A8E_94B9_D1260A5D6B0D_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_E3288062_4139_4942_8A82_452BFEBBD63F_TRANSLATED"),
        ("Jan 2023", "NEW_DATE_TEXT_F57735F1_30A6_4538_8C95_BFE08674506B_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_REVIEW_ARWHQK_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_REVIEW_FWXHPQ_TRANSLATED"),
        ("July 2023", "NEW_DATE_TEXT_REVIEW_KAGTR4_TRANSLATED"),
        (
            "(x) People are looking at this",
            "NEW_FOMO_TEXT_BEFORE_4EC31670_952B_4ED4_8799_249844A8F39B_TRANSLATED",
        ),
        (
            "Rated the #1 drone technology in 2025.",
            "NEW_HEADER_TEXT_3475A8F9_021F_4ACD_8E57_163EF2A26740_TRANSLATED",
        ),
        (
            "100% Money <strong>Back</strong>!!",
            "NEW_HEADING_504C9E09_AAA7_49C4_8271_C6CA319D23F2_TRANSLATED",
        ),
        (
            "Shipping Information",
            "NEW_HEADING_9CCFFC8D_E4C7_404F_8007_8C5162F22285_TRANSLATED",
        ),
        ("FAQs", "NEW_HEADING_C0EF23CF_5481_4B47_9B78_3C28134C079A_TRANSLATED"),
        ("Is everything recyclable?", "NEW_HEADING_COLLAPSIBLE_ROW_BMHKAN_TRANSLATED"),
        ("How often should you use?", "NEW_HEADING_COLLAPSIBLE_ROW_GIDN9Z_TRANSLATED"),
        ("Does this really work?", "NEW_HEADING_COLLAPSIBLE_ROW_T3YHUA_TRANSLATED"),
        ("Ingredient list", "NEW_HEADING_COLLAPSIBLE_TAB_HK7DGX_TRANSLATED"),
        (
            "Returns & Refunds",
            "NEW_HEADING_F34AD5C4_50A9_4A95_A561_D8C51D1B76DD_TRANSLATED",
        ),
        (
            "<strong>Experience Stealth with AeroShadow X1</strong>",
            "NEW_HEADING_HEADING_8E7QYA_TRANSLATED",
        ),
        (
            "<strong>Precision Drone Technology</strong>",
            "NEW_HEADING_HEADING_AJMG6N_TRANSLATED",
        ),
        (
            "<strong>Fly Beyond Limits.</strong>",
            "NEW_HEADING_HEADING_JHTCQY_TRANSLATED",
        ),
        ("You may also like", "NEW_HEADING_RELATED-PRODUCTS_TRANSLATED"),
        (
            "What if it doesn’t work for me?",
            "NEW_HEADING_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_1_TRANSLATED",
        ),
        (
            "Guarantee?",
            "NEW_HEADING_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_2_TRANSLATED",
        ),
        (
            "Okay, but why have I never heard of this before?",
            "NEW_HEADING_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_3_TRANSLATED",
        ),
        (
            "Do you provide tracking information?",
            "NEW_HEADING_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_4_TRANSLATED",
        ),
        ("Johan D.", "NEW_NAME_TEXT_13A5819E_5698_472F_94EB_34D5A7AD9B21_TRANSLATED"),
        ("Sofia R.", "NEW_NAME_TEXT_30900101_E5C8_4C0E_B5BD_0FCF8EEA85CF_TRANSLATED"),
        ("Johan D.", "NEW_NAME_TEXT_3C322C1A_1E3A_47E6_8D7B_720D506EB595_TRANSLATED"),
        (
            "Amy Grady, B.",
            "NEW_NAME_TEXT_53A5B896_0517_4E05_80FE_B23DE703E79B_TRANSLATED",
        ),
        (
            "Anabella C.",
            "NEW_NAME_TEXT_D032A47C_6F6E_4A8E_94B9_D1260A5D6B0D_TRANSLATED",
        ),
        ("Johan D.", "NEW_NAME_TEXT_E3288062_4139_4942_8A82_452BFEBBD63F_TRANSLATED"),
        ("Vera R.", "NEW_NAME_TEXT_F57735F1_30A6_4538_8C95_BFE08674506B_TRANSLATED"),
        ("Johan D.", "NEW_NAME_TEXT_REVIEW_ARWHQK_TRANSLATED"),
        ("Johan D.", "NEW_NAME_TEXT_REVIEW_FWXHPQ_TRANSLATED"),
        ("Johan D.", "NEW_NAME_TEXT_REVIEW_KAGTR4_TRANSLATED"),
        ("Most Popular", "NEW_OPTION_1_BADGE_TEXT_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("1 Drone", "NEW_OPTION_1_LABEL_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        (
            "SPECIAL OFFER - Limited Time",
            "NEW_OPTION_2_BADGE_TEXT_QUANTITY_SELECTOR_Q9D74M_TRANSLATED",
        ),
        ("Buy 2, Get 1 FREE", "NEW_OPTION_2_LABEL_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        (
            "FLASH SALE — Grab It Before It's Gone",
            "NEW_OPTION_3_BADGE_TEXT_QUANTITY_SELECTOR_Q9D74M_TRANSLATED",
        ),
        ("Buy 3, Get 2 FREE", "NEW_OPTION_3_LABEL_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("Most Popular", "NEW_OPTION_4_BADGE_TEXT_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("4 Drones", "NEW_OPTION_4_LABEL_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("Most Popular", "NEW_OPTION_5_BADGE_TEXT_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("5 Drones", "NEW_OPTION_5_LABEL_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("Most Popular", "NEW_OPTION_6_BADGE_TEXT_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        ("6 Drones", "NEW_OPTION_6_LABEL_QUANTITY_SELECTOR_Q9D74M_TRANSLATED"),
        (
            "Nice Product",
            "NEW_REVIEW_HEAD_13A5819E_5698_472F_94EB_34D5A7AD9B21_TRANSLATED",
        ),
        (
            "Works well for advanced flights!",
            "NEW_REVIEW_HEAD_30900101_E5C8_4C0E_B5BD_0FCF8EEA85CF_TRANSLATED",
        ),
        (
            "Nice Product",
            "NEW_REVIEW_HEAD_3C322C1A_1E3A_47E6_8D7B_720D506EB595_TRANSLATED",
        ),
        (
            "The Only Drone That Has Worked For Me",
            "NEW_REVIEW_HEAD_53A5B896_0517_4E05_80FE_B23DE703E79B_TRANSLATED",
        ),
        (
            "Holy Unexpected!!",
            "NEW_REVIEW_HEAD_D032A47C_6F6E_4A8E_94B9_D1260A5D6B0D_TRANSLATED",
        ),
        (
            "Nice Product",
            "NEW_REVIEW_HEAD_E3288062_4139_4942_8A82_452BFEBBD63F_TRANSLATED",
        ),
        (
            "BEST PURCHASE BEST FIND",
            "NEW_REVIEW_HEAD_F57735F1_30A6_4538_8C95_BFE08674506B_TRANSLATED",
        ),
        ("Nice Product", "NEW_REVIEW_HEAD_REVIEW_ARWHQK_TRANSLATED"),
        ("Nice Product", "NEW_REVIEW_HEAD_REVIEW_FWXHPQ_TRANSLATED"),
        ("Nice Product", "NEW_REVIEW_HEAD_REVIEW_KAGTR4_TRANSLATED"),
        (
            "✨ <strong>Obsessed with the Results</strong>",
            "NEW_TITLE_COLUMN_7ZMKCE_TRANSLATED",
        ),
        (
            "⚡ <strong>Visible Results, Fast</strong>",
            "NEW_TITLE_COLUMN_9PFUYJ_TRANSLATED",
        ),
        ("💖 <strong>Worth Every Penny</strong>", "NEW_TITLE_COLUMN_HTTYFJ_TRANSLATED"),
        (
            "🌿 <strong>Advanced Drone Technology</strong>",
            "NEW_TITLE_COLUMN_XLTNH7_TRANSLATED",
        ),
        (
            "What makes AeroShadow right for you?",
            "NEW_TITLE_COMPARISON_TABLE_9J8NNQ_TRANSLATED",
        ),
        (
            "Why AeroShadow is <strong>Better</strong>",
            "NEW_TITLE_LUMIN_HERO_8JR4II_TRANSLATED",
        ),
        (
            "Drone Tech for the Best Flights Yet",
            "NEW_TITLE_MULTICOLUMN_XDHHWC_TRANSLATED",
        ),
        (
            "Was this helpful?",
            "NEW_LIKE_TEXT_3475A8F9_021F_4ACD_8E57_163EF2A26740_TRANSLATED",
        ),
        ("Load More", "NEW_LOAD_TEXT_3475A8F9_021F_4ACD_8E57_163EF2A26740_TRANSLATED"),
        (
            "Verified Buyer",
            "NEW_VERIFY_TEXT_3475A8F9_021F_4ACD_8E57_163EF2A26740_TRANSLATED",
        ),
        ("SkyForge Tech", "NEW_HEAD_TEXT_J7DFT4_GENERATED"),
    ]

    for original, placeholder in translations:
        translated = translate_text(original, language)
        replace_in_file(PRODUCT_JSON_PATH, placeholder, translated)


def generate_announcements_prompt(
    brand_name: str, product_title: str, product_description: str, language: str
) -> str:
    return f"""Create announcement contents in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with ALL specified keys:

{{
  "announcement_91817b81": "<h1>Announcement text</h1>",
  "announcement_gAyVVz": "<p>Announcement text</p>",
  "announcement_XGt7RJ": "<p>Announcement text</p>",
  "announcement_dd77f8e0": "<h1>Announcement text</h1>",
  "announcement_template_1": "<p>Announcement text</p>",
  "announcement_template_2": "<p>Announcement text</p>"
}}

Requirements:
- Maintain exact HTML tags: <h1> for announcement_91817b81 and announcement_dd77f8e0, <p> for others
- Keep texts short (3-8 words), impactful, and product-relevant
- Focus on promotions, eco-friendly aspects, or product benefits
- Match brand tone and product context
- Ensure ALL keys above are included with valid values

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""


def generate_button_texts_prompt(
    brand_name: str, product_title: str, product_description: str, language: str
) -> str:
    return f"""Create button text contents in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with ALL specified keys:

{{
  "image_4GCwJt": "Button text",
  "image_6kyG4n": "Button text",
  "image_8WUeHF": "Button text",
  "image_g6WCgH": "Button text",
  "image_mczRTQ": "Button text",
  "image_mWKfnL": "Button text",
  "image_XDdFEp": "Button text",
  "image_YQMGF7": "Button text",
  "image_template_1": "Button text",
  "text_j7Dft4": "Button text"
}}

Requirements:
- All values must be raw text, no HTML tags
- Keep texts short (2-5 words), action-oriented (e.g., "Shop Now", "Discover More")
- Match brand tone and product context
- For text_j7Dft4, include a hashtag (e.g., "#BrandName")
- Ensure ALL keys above are included with valid values

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""


def generate_content_prompt(
    brand_name: str, product_title: str, product_description: str, language: str
) -> str:
    return f"""Create content sections in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with ALL specified keys:

{{
  "content_9ccffc8d": "<p>Shipping details</p><p><a href='/collections/all' title='All products'>Link text</a></p><p>Sale policy</p>",
  "content_f34ad5c4": "<p>Shipping details</p><p><a href='/collections/all' title='All products'>Link text</a></p><p>Sale policy</p>",
  "content_promo_krqbTU": "<p>Promo text</p>",
  "content_promo_QC7Vbj": "<p>Promo text</p>",
  "content_collapsible_tab_HK7dGX": "<ul><li>Ingredient</li><li>Ingredient</li><li>Ingredient</li></ul>",
  "row_content_BMHKaN": "<p>FAQ response</p>",
  "row_content_GiDN9z": "<p>FAQ response</p>",
  "row_content_t3yhUa": "<p>FAQ response</p>",
  "row_content_template_1": "<p>FAQ response</p>",
  "row_content_template_2": "<p>FAQ response</p>",
  "row_content_template_3": "<p>FAQ response</p>",
  "row_content_template_4": "<p>FAQ response</p>",
  "tab_content_DgkJ3j": "<p>Tab description</p>",
  "tab_content_2_DgkJ3j": "<p>Tab description</p>",
  "tab_content_3_DgkJ3j": "<p>Tab description</p>"
}}

Requirements:
- Maintain exact HTML structure as shown (e.g., <p>, <a>, <ul><li>)
- Use single quotes for HTML attributes (e.g., href='/collections/all')
- Keep texts concise, relevant to product (e.g., shipping, returns, ingredients, FAQs)
- For content_9ccffc8d and content_f34ad5c4, include 3 paragraphs with a link in the second
- For content_collapsible_tab_HK7dGX, list 3-5 ingredients in <ul><li> format
- Match brand tone and product context
- Ensure ALL keys above are included with valid values

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""


def generate_review_content_prompt(
    brand_name: str, product_title: str, product_description: str, language: str
) -> str:
    return f"""Create review content in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with ALL specified keys:

{{
  "review_text_13a5819e": "<p>Review text</p>",
  "review_text_30900101": "<p>Review text</p>",
  "review_text_3c322c1a": "<p>Review text</p>",
  "review_text_53a5b896": "<p>Review text</p>",
  "review_text_d032a47c": "<p>Review text</p>",
  "review_text_e3288062": "<p>Review text</p>",
  "review_text_f57735f1": "<p>Review text</p>",
  "review_text_ArWHqK": "<p>Review text</p>",
  "review_text_fwxHPq": "<p>Review text</p>",
  "review_text_kAgTR4": "<p>Review text</p>",
  "rating_count_3475a8f9": "<strong>Number</strong> Real reviews, real results from <strong>people just like you.</strong>",
  "lrw_text_7f391028": "Rating | Reviews"
}}

Requirements:
- Review texts must use <p> tags, 1-3 sentences, positive and product-specific
- rating_count_3475a8f9 must use <strong> tags for number and phrase
- lrw_text_7f391028 must be raw text, format: "X.Y | Z Reviews"
- Match brand tone and product context
- Ensure ALL keys above are included with valid values

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""


def generate_quantity_selector_prompt(
    brand_name: str, product_title: str, product_description: str, language: str
) -> str:
    return f"""Create quantity selector content in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with ALL specified keys:

{{
  "option_1_save_text": "Save text",
  "option_1_unit_label": "Unit label",
  "option_2_save_text": "Save text",
  "option_2_unit_label": "Unit label",
  "option_3_promo": "<strong>Duration</strong> Months Supply | <strong>FREE Shipping</strong>",
  "option_3_save_text": "Save text",
  "option_3_unit_label": "Unit label",
  "option_4_save_text": "Save text",
  "option_4_unit_label": "Unit label",
  "option_5_save_text": "Save text",
  "option_5_unit_label": "Unit label",
  "option_6_save_text": "Save text",
  "option_6_unit_label": "Unit label",
  "quantity_title_text": "<h3>Bundle text</h3>"
}}

Requirements:
- Save texts and unit labels are raw text, concise (e.g., "Save 10%", "2 Months Supply")
- option_3_promo uses <strong> tags as shown
- quantity_title_text uses <h3> tags
- Match product context (e.g., drone accessories or bundles)
- Reflect escalating bundle benefits (e.g., more savings for larger packs)
- Ensure ALL keys above are included with valid values

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""


def generate_text_sections_prompt(
    brand_name: str, product_title: str, product_description: str, language: str
) -> str:
    return f"""Create text section content in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with ALL specified keys:

{{
  "head_text_lumin_hero_8jr4ii": "Hero headline text",
  "subtitle_text_j7Dft4": "<p><strong>Number FOLLOWERS</strong></p>",
  "text_1_hero_Wjwazn": "Descriptive text",
  "text_2_hero_Wjwazn": "Descriptive text",
  "text_3_hero_Wjwazn": "Descriptive text",
  "text_4_hero_Wjwazn": "Descriptive text",
  "text_5_hero_Wjwazn": "Descriptive text",
  "text_6_hero_Wjwazn": "Descriptive text",
  "text_264e37ac": "Order by timer for fast delivery",
  "text_504c9e09": "<p>Review text</p><h6>Policy</h6>",
  "text_74e17b96": "Vendor text",
  "text_promo_slide_YiPa48_1": "<p>Promo text</p>",
  "text_promo_slide_YiPa48_2": "<p>Promo text</p>",
  "text_promo_slide_YiPa48_3": "<p>Promo text</p>",
  "text_column_7zMkCE": "<p>Testimonial text – <strong>Name</strong></p>",
  "text_column_9PFUYj": "<p><em>Testimonial text</em> – <strong>Name</strong></p>",
  "text_column_htTYfJ": "<p><em>Testimonial text</em> – <strong>Name</strong></p>",
  "text_column_xLTnh7": "<p><em>Testimonial text</em> – <strong>Name</strong></p>",
  "text_column_afLRa6": "<h1><strong>Percentage</strong></h1><p>Benefit description</p>",
  "text_column_FpEWjD": "<h1><strong>Percentage</strong></h1><p>Benefit description</p>",
  "text_column_kcUK3B": "<h1><strong>Percentage</strong></h1><p>Benefit description</p>",
  "text_column_nMFyQP": "<h1><strong>Percentage</strong></h1><p>Benefit description</p>",
  "text_comparison_table_9j8NnQ": "<p>Comparison text</p>",
  "text_feature_6cxT6B": "<p>Feature with <strong>highlight</strong></p>",
  "text_feature_aYFzam": "<p>Feature with <strong>highlight</strong></p>",
  "text_feature_HCBWrx": "<p>Feature with <strong>highlight</strong></p>",
  "text_feature_Kgr9Aj": "<p>Feature with <strong>highlight</strong></p>",
  "text_feature_teRTgW": "<p>Feature with <strong>highlight</strong></p>",
  "text_text_T999BU": "<p>✔️ <strong>Benefit</strong> – Description<br/><br/>✔️ <strong>Benefit</strong> – Description</p>",
  "text_text_VYmMN6": "<p>Tagline</p>",
  "text_text_wFDAYF": "<p>Descriptive text</p>",
  "text_popup_DVDmRD": "Link text",
  "text_low_many_xPXzfP": "Stock alert",
  "text_low_one_xPXzfP": "Stock alert",
  "text_normal_xPXzfP": "Stock status",
  "text_soldout_xPXzfP": "Sold out notice",
  "text_untracked_xPXzfP": "Stock status"
}}

Requirements:
- Use raw text (no HTML) for head_text_lumin_hero_8jr4ii, text_1_hero_Wjwazn to text_6_hero_Wjwazn, text_264e37ac, text_74e17b96, text_popup_DVDmRD, stock-related texts
- Maintain exact HTML structure where specified
- Texts should be concise, product-relevant (e.g., benefits, testimonials, stock alerts)
- For columns (7zMkCE, 9PFUYj, htTYfJ, xLTnh7), include customer name in <strong>
- For columns (afLRa6, FpEWjD, kcUK3B, nMFyQP), use percentage (60-95%) and benefit
- Match brand tone and product context
- Ensure ALL keys above are included with valid values

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""


def process_product_generated_content(
    brand_name: str, product_title: str, product_description: str, language: str
):
    # Announcements
    prompt = generate_announcements_prompt(
        brand_name, product_title, product_description, language
    )
    result = generate_with_format_validation(prompt, "<h1>Text</h1>", max_tokens=500)
    try:
        announcements = json.loads(clean_json_response(result))
        print(
            f"Announcements JSON parsed successfully (first 500 chars): {json.dumps(announcements)[:500]}..."
        )
    except Exception as e:
        print(
            f"Failed to parse announcements JSON (first 500 chars): {result[:500]}..."
        )
        try:
            fixed_result = fix_json_with_gpt(
                result,
                "announcements",
                [
                    "announcement_91817b81",
                    "announcement_gAyVVz",
                    "announcement_XGt7RJ",
                    "announcement_dd77f8e0",
                    "announcement_template_1",
                    "announcement_template_2",
                ],
            )
            announcements = json.loads(fixed_result)
            print(f"First fix attempt succeeded for announcements.")
        except Exception as e:
            print(f"First fix attempt failed for announcements: {e}")
            try:
                fixed_result = fix_json_with_gpt(
                    result,
                    "announcements_retry",
                    [
                        "announcement_91817b81",
                        "announcement_gAyVVz",
                        "announcement_XGt7RJ",
                        "announcement_dd77f8e0",
                        "announcement_template_1",
                        "announcement_template_2",
                    ],
                )
                announcements = json.loads(fixed_result)
                print(f"Second fix attempt succeeded for announcements.")
            except Exception as e:
                print(f"Second fix attempt failed for announcements: {e}")
                raise Exception(
                    "Failed to generate valid announcements JSON after retries."
                )

    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ANNOUNCEMENT_91817B81_C148_4C6C_8A35_09D6BA380CA5_GENERATED",
        announcements["announcement_91817b81"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ANNOUNCEMENT_ANNOUNCEMENT_GAYVVZ_GENERATED",
        announcements["announcement_gAyVVz"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ANNOUNCEMENT_ANNOUNCEMENT_XGT7RJ_GENERATED",
        announcements["announcement_XGt7RJ"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ANNOUNCEMENT_DD77F8E0_9A10_41D6_A2A8_69B2326223A3_GENERATED",
        announcements["announcement_dd77f8e0"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ANNOUNCEMENT_TEMPLATE__15124688076883__05F459A6_0335_4BAB_8D23_AC347077EFCC_ANNOUNCEMENT_1_GENERATED",
        announcements["announcement_template_1"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ANNOUNCEMENT_TEMPLATE__15124688076883__05F459A6_0335_4BAB_8D23_AC347077EFCC_ANNOUNCEMENT_2_GENERATED",
        announcements["announcement_template_2"],
    )

    # Button Texts
    prompt = generate_button_texts_prompt(
        brand_name, product_title, product_description, language
    )
    result = prompt_gpt(prompt, max_tokens=300)
    try:
        button_texts = json.loads(clean_json_response(result))
        print(
            f"Button texts JSON parsed successfully (first 500 chars): {json.dumps(button_texts)[:500]}..."
        )
    except Exception as e:
        print(f"Failed to parse button texts JSON (first 500 chars): {result[:500]}...")
        try:
            fixed_result = fix_json_with_gpt(
                result,
                "button_texts",
                [
                    "image_4GCwJt",
                    "image_6kyG4n",
                    "image_8WUeHF",
                    "image_g6WCgH",
                    "image_mczRTQ",
                    "image_mWKfnL",
                    "image_XDdFEp",
                    "image_YQMGF7",
                    "image_template_1",
                    "text_j7Dft4",
                ],
            )
            button_texts = json.loads(fixed_result)
            print(f"First fix attempt succeeded for button texts.")
        except Exception as e:
            print(f"First fix attempt failed for button texts: {e}")
            try:
                fixed_result = fix_json_with_gpt(
                    result,
                    "button_texts_retry",
                    [
                        "image_4GCwJt",
                        "image_6kyG4n",
                        "image_8WUeHF",
                        "image_g6WCgH",
                        "image_mczRTQ",
                        "image_mWKfnL",
                        "image_XDdFEp",
                        "image_YQMGF7",
                        "image_template_1",
                        "text_j7Dft4",
                    ],
                )
                button_texts = json.loads(fixed_result)
                print(f"Second fix attempt succeeded for button texts.")
            except Exception as e:
                print(f"Second fix attempt failed for button texts: {e}")
                raise Exception(
                    "Failed to generate valid button texts JSON after retries."
                )

    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_4GCWJT_GENERATED",
        button_texts["image_4GCwJt"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_6KYG4N_GENERATED",
        button_texts["image_6kyG4n"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_8WUEHF_GENERATED",
        button_texts["image_8WUeHF"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_G6WCGH_GENERATED",
        button_texts["image_g6WCgH"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_MCZRTQ_GENERATED",
        button_texts["image_mczRTQ"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_MWKFNL_GENERATED",
        button_texts["image_mWKfnL"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_XDDFEP_GENERATED",
        button_texts["image_XDdFEp"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_IMAGE_YQMGF7_GENERATED",
        button_texts["image_YQMGF7"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_TEMPLATE__17146523746516__530954A1_091E_46FD_B6F9_AAAACA76CEB6_IMAGE_1_GENERATED",
        button_texts["image_template_1"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_BUTTON-TEXT_TEXT_J7DFT4_GENERATED",
        button_texts["text_j7Dft4"],
    )

    # Content Sections
    content_keys = [
        "content_9ccffc8d",
        "content_f34ad5c4",
        "content_promo_krqbTU",
        "content_promo_QC7Vbj",
        "content_collapsible_tab_HK7dGX",
        "row_content_BMHKaN",
        "row_content_GiDN9z",
        "row_content_t3yhUa",
        "row_content_template_1",
        "row_content_template_2",
        "row_content_template_3",
        "row_content_template_4",
        "tab_content_DgkJ3j",
        "tab_content_2_DgkJ3j",
        "tab_content_3_DgkJ3j",
    ]
    prompt = generate_content_prompt(
        brand_name, product_title, product_description, language
    )
    result = generate_with_format_validation(prompt, "<p>Text</p>", max_tokens=1000)
    try:
        content = json.loads(clean_json_response(result))
        print(
            f"Content sections JSON parsed successfully (first 500 chars): {json.dumps(content)[:500]}..."
        )
    except Exception as e:
        print(
            f"Failed to parse content sections JSON (first 500 chars): {result[:500]}..."
        )
        try:
            fixed_result = fix_json_with_gpt(result, "content_sections", content_keys)
            content = json.loads(fixed_result)
            print(f"First fix attempt succeeded for content sections.")
        except Exception as e:
            print(f"First fix attempt failed for content sections: {e}")
            try:
                fixed_result = fix_json_with_gpt(
                    result, "content_sections_retry", content_keys
                )
                content = json.loads(fixed_result)
                print(f"Second fix attempt succeeded for content sections.")
            except Exception as e:
                print(f"Second fix attempt failed for content sections: {e}")
                raise Exception(
                    "Failed to generate valid content sections JSON after retries."
                )

    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_CONTENT_9CCFFC8D_E4C7_404F_8007_8C5162F22285_GENERATED",
        content["content_9ccffc8d"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_CONTENT_F34AD5C4_50A9_4A95_A561_D8C51D1B76DD_GENERATED",
        content["content_f34ad5c4"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_CONTENT_PROMO_KRQBTU_GENERATED",
        content["content_promo_krqbTU"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_CONTENT_PROMO_QC7VBJ_GENERATED",
        content["content_promo_QC7Vbj"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_CONTENT_COLLAPSIBLE_TAB_HK7DGX_GENERATED",
        content["content_collapsible_tab_HK7dGX"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_COLLAPSIBLE_ROW_BMHKAN_GENERATED",
        content["row_content_BMHKaN"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_COLLAPSIBLE_ROW_GIDN9Z_GENERATED",
        content["row_content_GiDN9z"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_COLLAPSIBLE_ROW_T3YHUA_GENERATED",
        content["row_content_t3yhUa"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_1_GENERATED",
        content["row_content_template_1"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_2_GENERATED",
        content["row_content_template_2"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_3_GENERATED",
        content["row_content_template_3"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_ROW_CONTENT_TEMPLATE__15124688076883__C0EF23CF_5481_4B47_9B78_3C28134C079A_COLLAPSIBLE_ROW_4_GENERATED",
        content["row_content_template_4"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TAB_CONTENT_TABS_DGKJ3J_GENERATED",
        content["tab_content_DgkJ3j"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TAB_CONTENT_2_TABS_DGKJ3J_GENERATED",
        content["tab_content_2_DgkJ3j"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TAB_CONTENT_3_TABS_DGKJ3J_GENERATED",
        content["tab_content_3_DgkJ3j"],
    )

    # Review Content
    prompt = generate_review_content_prompt(
        brand_name, product_title, product_description, language
    )
    result = generate_with_format_validation(prompt, "<p>Text</p>", max_tokens=600)
    try:
        reviews = json.loads(clean_json_response(result))
        print(
            f"Review content JSON parsed successfully (first 500 chars): {json.dumps(reviews)[:500]}..."
        )
    except Exception as e:
        print(
            f"Failed to parse review content JSON (first 500 chars): {result[:500]}..."
        )
        try:
            fixed_result = fix_json_with_gpt(
                result,
                "review_content",
                [
                    "review_text_13a5819e",
                    "review_text_30900101",
                    "review_text_3c322c1a",
                    "review_text_53a5b896",
                    "review_text_d032a47c",
                    "review_text_e3288062",
                    "review_text_f57735f1",
                    "review_text_ArWHqK",
                    "review_text_fwxHPq",
                    "review_text_kAgTR4",
                    "rating_count_3475a8f9",
                    "lrw_text_7f391028",
                ],
            )
            reviews = json.loads(fixed_result)
            print(f"First fix attempt succeeded for review content.")
        except Exception as e:
            print(f"First fix attempt failed for review content: {e}")
            try:
                fixed_result = fix_json_with_gpt(
                    result,
                    "review_content_retry",
                    [
                        "review_text_13a5819e",
                        "review_text_30900101",
                        "review_text_3c322c1a",
                        "review_text_53a5b896",
                        "review_text_d032a47c",
                        "review_text_e3288062",
                        "review_text_f57735f1",
                        "review_text_ArWHqK",
                        "review_text_fwxHPq",
                        "review_text_kAgTR4",
                        "rating_count_3475a8f9",
                        "lrw_text_7f391028",
                    ],
                )
                reviews = json.loads(fixed_result)
                print(f"Second fix attempt succeeded for review content.")
            except Exception as e:
                print(f"Second fix attempt failed for review content: {e}")
                raise Exception(
                    "Failed to generate valid review content JSON after retries."
                )

    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_13A5819E_5698_472F_94EB_34D5A7AD9B21_GENERATED",
        reviews["review_text_13a5819e"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_30900101_E5C8_4C0E_B5BD_0FCF8EEA85CF_GENERATED",
        reviews["review_text_30900101"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_3C322C1A_1E3A_47E6_8D7B_720D506EB595_GENERATED",
        reviews["review_text_3c322c1a"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_53A5B896_0517_4E05_80FE_B23DE703E79B_GENERATED",
        reviews["review_text_53a5b896"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_D032A47C_6F6E_4A8E_94B9_D1260A5D6B0D_GENERATED",
        reviews["review_text_d032a47c"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_E3288062_4139_4942_8A82_452BFEBBD63F_GENERATED",
        reviews["review_text_e3288062"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_F57735F1_30A6_4538_8C95_BFE08674506B_GENERATED",
        reviews["review_text_f57735f1"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_REVIEW_ARWHQK_GENERATED",
        reviews["review_text_ArWHqK"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_REVIEW_FWXHPQ_GENERATED",
        reviews["review_text_fwxHPq"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_REVIEW_TEXT_REVIEW_KAGTR4_GENERATED",
        reviews["review_text_kAgTR4"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_RATING_COUNT_3475A8F9_021F_4ACD_8E57_163EF2A26740_GENERATED",
        reviews["rating_count_3475a8f9"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_LRW_TEXT_7F391028_A103_4E66_BB50_BD71D4672AF4_GENERATED",
        reviews["lrw_text_7f391028"],
    )

    # Quantity Selector
    prompt = generate_quantity_selector_prompt(
        brand_name, product_title, product_description, language
    )
    result = generate_with_format_validation(prompt, "<h3>Text</h3>", max_tokens=400)
    try:
        quantity = json.loads(clean_json_response(result))
        print(
            f"Quantity selector JSON parsed successfully (first 500 chars): {json.dumps(quantity)[:500]}..."
        )
    except Exception as e:
        print(
            f"Failed to parse quantity selector JSON (first 500 chars): {result[:500]}..."
        )
        try:
            fixed_result = fix_json_with_gpt(
                result,
                "quantity_selector",
                [
                    "option_1_save_text",
                    "option_1_unit_label",
                    "option_2_save_text",
                    "option_2_unit_label",
                    "option_3_promo",
                    "option_3_save_text",
                    "option_3_unit_label",
                    "option_4_save_text",
                    "option_4_unit_label",
                    "option_5_save_text",
                    "option_5_unit_label",
                    "option_6_save_text",
                    "option_6_unit_label",
                    "quantity_title_text",
                ],
            )
            quantity = json.loads(fixed_result)
            print(f"First fix attempt succeeded for quantity selector.")
        except Exception as e:
            print(f"First fix attempt failed for quantity selector: {e}")
            try:
                fixed_result = fix_json_with_gpt(
                    result,
                    "quantity_selector_retry",
                    [
                        "option_1_save_text",
                        "option_1_unit_label",
                        "option_2_save_text",
                        "option_2_unit_label",
                        "option_3_promo",
                        "option_3_save_text",
                        "option_3_unit_label",
                        "option_4_save_text",
                        "option_4_unit_label",
                        "option_5_save_text",
                        "option_5_unit_label",
                        "option_6_save_text",
                        "option_6_unit_label",
                        "quantity_title_text",
                    ],
                )
                quantity = json.loads(fixed_result)
                print(f"Second fix attempt succeeded for quantity selector.")
            except Exception as e:
                print(f"Second fix attempt failed for quantity selector: {e}")
                raise Exception(
                    "Failed to generate valid quantity selector JSON after retries."
                )

    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_1_SAVE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_1_save_text"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_1_UNIT_LABEL_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_1_unit_label"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_2_SAVE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_2_save_text"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_2_UNIT_LABEL_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_2_unit_label"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_3_PROMO_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_3_promo"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_3_SAVE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_3_save_text"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_3_UNIT_LABEL_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_3_unit_label"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_4_SAVE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_4_save_text"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_4_UNIT_LABEL_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_4_unit_label"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_5_SAVE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_5_save_text"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_5_UNIT_LABEL_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_5_unit_label"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_6_SAVE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_6_save_text"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_OPTION_6_UNIT_LABEL_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["option_6_unit_label"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_QUANTITY_TITLE_TEXT_QUANTITY_SELECTOR_Q9D74M_GENERATED",
        quantity["quantity_title_text"],
    )

    # Text Sections
    text_keys = [
        "head_text_lumin_hero_8jr4ii",
        "subtitle_text_j7Dft4",
        "text_1_hero_Wjwazn",
        "text_2_hero_Wjwazn",
        "text_3_hero_Wjwazn",
        "text_4_hero_Wjwazn",
        "text_5_hero_Wjwazn",
        "text_6_hero_Wjwazn",
        "text_264e37ac",
        "text_504c9e09",
        "text_74e17b96",
        "text_promo_slide_YiPa48_1",
        "text_promo_slide_YiPa48_2",
        "text_promo_slide_YiPa48_3",
        "text_column_7zMkCE",
        "text_column_9PFUYj",
        "text_column_htTYfJ",
        "text_column_xLTnh7",
        "text_column_afLRa6",
        "text_column_FpEWjD",
        "text_column_kcUK3B",
        "text_column_nMFyQP",
        "text_comparison_table_9j8NnQ",
        "text_feature_6cxT6B",
        "text_feature_aYFzam",
        "text_feature_HCBWrx",
        "text_feature_Kgr9Aj",
        "text_feature_teRTgW",
        "text_text_T999BU",
        "text_text_VYmMN6",
        "text_text_wFDAYF",
        "text_popup_DVDmRD",
        "text_low_many_xPXzfP",
        "text_low_one_xPXzfP",
        "text_normal_xPXzfP",
        "text_soldout_xPXzfP",
        "text_untracked_xPXzfP",
    ]
    prompt = generate_text_sections_prompt(
        brand_name, product_title, product_description, language
    )
    result = generate_with_format_validation(prompt, "<p>Text</p>", max_tokens=1500)
    try:
        texts = json.loads(clean_json_response(result))
        print(
            f"Text sections JSON parsed successfully (first 500 chars): {json.dumps(texts)[:500]}..."
        )
    except Exception as e:
        print(
            f"Failed to parse text sections JSON (first 500 chars): {result[:500]}..."
        )
        try:
            fixed_result = fix_json_with_gpt(result, "text_sections", text_keys)
            texts = json.loads(fixed_result)
            print(f"First fix attempt succeeded for text sections.")
        except Exception as e:
            print(f"First fix attempt failed for text sections: {e}")
            try:
                fixed_result = fix_json_with_gpt(
                    result, "text_sections_retry", text_keys
                )
                texts = json.loads(fixed_result)
                print(f"Second fix attempt succeeded for text sections.")
            except Exception as e:
                print(f"Second fix attempt failed for text sections: {e}")
                raise Exception(
                    "Failed to generate valid text sections JSON after retries."
                )

    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_HEAD_TEXT_LUMIN_HERO_8JR4II_GENERATED",
        texts["head_text_lumin_hero_8jr4ii"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_SUBTITLE_TEXT_J7DFT4_GENERATED",
        texts["subtitle_text_j7Dft4"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_1_HERO_WJWAZN_GENERATED",
        texts["text_1_hero_Wjwazn"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_2_HERO_WJWAZN_GENERATED",
        texts["text_2_hero_Wjwazn"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_3_HERO_WJWAZN_GENERATED",
        texts["text_3_hero_Wjwazn"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_4_HERO_WJWAZN_GENERATED",
        texts["text_4_hero_Wjwazn"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_5_HERO_WJWAZN_GENERATED",
        texts["text_5_hero_Wjwazn"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_6_HERO_WJWAZN_GENERATED",
        texts["text_6_hero_Wjwazn"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_264E37AC_8AC8_475C_9F10_973D46BB217D_GENERATED",
        texts["text_264e37ac"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_504C9E09_AAA7_49C4_8271_C6CA319D23F2_GENERATED",
        texts["text_504c9e09"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_74E17B96_75E8_4EC7_AE08_2DF77F4249CB_GENERATED",
        texts["text_74e17b96"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_1_PROMO_SLIDE_YIPA48_GENERATED",
        texts["text_promo_slide_YiPa48_1"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_2_PROMO_SLIDE_YIPA48_GENERATED",
        texts["text_promo_slide_YiPa48_2"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_3_PROMO_SLIDE_YIPA48_GENERATED",
        texts["text_promo_slide_YiPa48_3"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_7ZMKCE_GENERATED",
        texts["text_column_7zMkCE"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_9PFUYJ_GENERATED",
        texts["text_column_9PFUYj"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_HTTYFJ_GENERATED",
        texts["text_column_htTYfJ"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_XLTNH7_GENERATED",
        texts["text_column_xLTnh7"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_AFLRA6_GENERATED",
        texts["text_column_afLRa6"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_FPEWJD_GENERATED",
        texts["text_column_FpEWjD"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_KCUK3B_GENERATED",
        texts["text_column_kcUK3B"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COLUMN_NMFYQP_GENERATED",
        texts["text_column_nMFyQP"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_COMPARISON_TABLE_9J8NNQ_GENERATED",
        texts["text_comparison_table_9j8NnQ"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_FEATURE_6CXT6B_GENERATED",
        texts["text_feature_6cxT6B"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_FEATURE_AYFZAM_GENERATED",
        texts["text_feature_aYFzam"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_FEATURE_HCBWRX_GENERATED",
        texts["text_feature_HCBWrx"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_FEATURE_KGR9AJ_GENERATED",
        texts["text_feature_Kgr9Aj"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_FEATURE_TERTGW_GENERATED",
        texts["text_feature_teRTgW"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH, "NEW_TEXT_TEXT_T999BU_GENERATED", texts["text_text_T999BU"]
    )
    replace_in_file(
        PRODUCT_JSON_PATH, "NEW_TEXT_TEXT_VYMMN6_GENERATED", texts["text_text_VYmMN6"]
    )
    replace_in_file(
        PRODUCT_JSON_PATH, "NEW_TEXT_TEXT_WFDAYF_GENERATED", texts["text_text_wFDAYF"]
    )
    replace_in_file(
        PRODUCT_JSON_PATH, "NEW_TEXT_POPUP_DVDMRD_GENERATED", texts["text_popup_DVDmRD"]
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_LOW_MANY_INVENTORY_XPXZFP_GENERATED",
        texts["text_low_many_xPXzfP"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_LOW_ONE_INVENTORY_XPXZFP_GENERATED",
        texts["text_low_one_xPXzfP"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_NORMAL_INVENTORY_XPXZFP_GENERATED",
        texts["text_normal_xPXzfP"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_SOLDOUT_INVENTORY_XPXZFP_GENERATED",
        texts["text_soldout_xPXzfP"],
    )
    replace_in_file(
        PRODUCT_JSON_PATH,
        "NEW_TEXT_UNTRACKED_INVENTORY_XPXZFP_GENERATED",
        texts["text_untracked_xPXzfP"],
    )


def change_product_content(
    brand_name: str, product_title: str, product_description: str, language: str
):
    print(
        f"Processing product content for {brand_name}™ - {product_title} in {language}"
    )
    print("Processing product translations...")
    process_product_translations(brand_name, product_title, language)
    print("Processing product generated content...")
    process_product_generated_content(
        brand_name, product_title, product_description, language
    )
    print("Product content processing completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("brand_name")
    parser.add_argument("product_title")
    parser.add_argument("product_description")
    parser.add_argument("language")
    args = parser.parse_args()
    change_product_content(
        args.brand_name, args.product_title, args.product_description, args.language
    )
