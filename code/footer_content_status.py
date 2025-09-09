from openai import OpenAI
import json
import re
from typing import Dict, Any
import argparse
import os

# Constants (define these as needed)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
FOOTER_JSON_PATH = os.getenv("FOOTER_JSON_PATH")

def clean_json_response(response_text: str) -> str:
    response_text = re.sub(r'```json\s*', '', response_text)
    response_text = re.sub(r'```\s*$', '', response_text)
    response_text = response_text.replace('"', '"').replace('"', '"')
    response_text = response_text.replace(''', "'").replace(''', "'")
    return response_text.strip()

def fix_json_with_gpt(broken_json: str, context: str) -> str:
    fix_prompt = f"""Fix this broken JSON and return ONLY valid JSON (no explanations, no markdown):

Context: {context}
Broken JSON: {broken_json}

Rules:
- All keys must have double quotes
- All string values must have double quotes  
- No trailing commas
- Escape quotes inside strings with backslashes
- Return only the fixed JSON"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0.1,
            max_tokens=500
        )
        return clean_json_response(response.choices[0].message.content.strip())
    except:
        return broken_json

def prompt_gpt(prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            result = response.choices[0].message.content.strip()
            return result
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
        return response.choices[0].message.content.strip().replace('"','')
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def replace_in_file(file_path: str, placeholder: str, content: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
    data = data.replace(placeholder, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(data)

def validate_html_format(text: str, expected_format: str = None) -> bool:
    """Validate if generated text maintains HTML format"""
    if expected_format and "<" in expected_format:
        original_tags = re.findall(r'<[^>]+>', expected_format)
        result_tags = re.findall(r'<[^>]+>', text)
        return len(original_tags) <= len(result_tags)
    return True

def generate_with_format_validation(prompt: str, expected_format: str = None) -> str:
    """Generate content and validate HTML format"""
    if expected_format and "<" in expected_format:
        prompt += f"\n\nIMPORTANT: Maintain the exact HTML structure from this example: {expected_format}"

    for attempt in range(3):
        result = prompt_gpt(prompt)
        if validate_html_format(result, expected_format):
            return result
        prompt += "\n\nPlease maintain the HTML tags structure exactly as shown in the example."

    return result

# ===== FOOTER TRANSLATION FUNCTION =====

def process_footer_translations(brand_name: str, product_title: str, language: str):
    """Process footer translation placeholders"""
    translated = translate_text("* We Promise not to use your email for Spam! You can unsubscribe at any time.", language)
    replace_in_file(FOOTER_JSON_PATH, "NEW_NEWSLETTER_SMALL_TEXT_TRANSLATED", translated)

    translated = translate_text("Information", language)
    replace_in_file(FOOTER_JSON_PATH, "NEW_FOOTER_INFO_HEADING_TRANSLATED", translated)

    translated = translate_text("Shop", language)
    replace_in_file(FOOTER_JSON_PATH, "NEW_FOOTER_SHOP_HEADING_TRANSLATED", translated)

    translated = translate_text("Subscribe to our emails", language)
    replace_in_file(FOOTER_JSON_PATH, "NEW_FOOTER_NEWSLETTER_HEADING_TRANSLATED", translated)

# ===== FOOTER CONTENT GENERATION FUNCTIONS =====

def generate_trust_badges_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create 4 trust badge contents in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "badge_1": {{
    "title": "<strong>Badge title</strong>",
    "text": "<p>Badge description</p>"
  }},
  "badge_2": {{
    "title": "<strong>Badge title</strong>",
    "text": "<p>Badge description</p>"
  }},
  "badge_3": {{
    "title": "<strong>Badge title</strong>",
    "text": "<p>Badge description</p>"
  }},
  "badge_4": {{
    "title": "<strong>Badge title</strong>",
    "text": "<p>Badge description</p>"
  }}
}}

Requirements:
- 'title' must use HTML <strong> tags, e.g., <strong>Fast Shipping</strong>
- 'text' must use HTML <p> tags, e.g., <p>Doorstep delivery to most of the US.</p>
- Keep titles short (2-4 words) and texts concise (1 sentence)
- Focus on trust-building themes: shipping, quality, customer satisfaction, returns
- Match the product's context and brand tone

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""

def generate_scroll_footer_text_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create 3 scrolling footer texts in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "text_1": "<strong>Scrolling text</strong>",
  "outline_1": "Outline word",
  "text_2": "<strong>Scrolling text</strong>",
  "outline_2": "Outline word",
  "text_3": "<strong>Scrolling text</strong>",
  "outline_3": "Outline word"
}}

Requirements:
- 'text_1', 'text_2', 'text_3' must use HTML <strong> tags, e.g., <strong>Free Shipping</strong>
- 'outline_1', 'outline_2', 'outline_3' must be raw text, single word or short phrase
- Keep texts short (2-4 words) and impactful, focusing on benefits like shipping, support, or quality
- Outline words should be a key word from the corresponding text
- Match the product's context and brand tone

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""

def generate_newsletter_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create newsletter section content in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "heading": "Newsletter heading",
  "text": "<p>Newsletter description</p>"
}}

Requirements:
- 'heading' must be raw text, no HTML tags
- 'text' must use HTML <p> tags, e.g., <p>Be the first to know about new collections.</p>
- Heading should be short (5-8 words), encouraging subscription
- Text should be 1-2 sentences, highlighting benefits of subscribing
- Match the product's context and brand tone

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""

def generate_footer_contact_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create footer contact content in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "heading": "Contact heading",
  "subtext": "<p>Contact details</p>"
}}

Requirements:
- 'heading' must be raw text, no HTML tags
- 'subtext' must use HTML <p> tags, including at least email and phone with <strong> tags, e.g., <p><strong>hello@brand.com</strong></p><p>Call: <strong>+1 (123) 456-7890</strong></p>
- Heading should be short (3-6 words), inviting contact
- Subtext should include a generic email, phone, and optional support hours
- Match the product's context and brand tone

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""

# ===== MAIN FOOTER PROCESSING FUNCTION =====

def process_footer_generated_content(brand_name: str, product_title: str, product_description: str, language: str):
    """Process generated footer content"""
    # Trust Badges
    prompt = generate_trust_badges_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        trust_badges = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "trust_badges")
        trust_badges = json.loads(fixed_result)
    
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_1_TITLE_GENERATED", trust_badges["badge_1"]["title"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_1_TEXT_GENERATED", trust_badges["badge_1"]["text"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_2_TITLE_GENERATED", trust_badges["badge_2"]["title"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_2_TEXT_GENERATED", trust_badges["badge_2"]["text"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_3_TITLE_GENERATED", trust_badges["badge_3"]["title"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_3_TEXT_GENERATED", trust_badges["badge_3"]["text"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_4_TITLE_GENERATED", trust_badges["badge_4"]["title"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_TRUST_BADGE_4_TEXT_GENERATED", trust_badges["badge_4"]["text"])

    # Scroll Footer Text
    prompt = generate_scroll_footer_text_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        scroll_texts = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "scroll_footer_texts")
        scroll_texts = json.loads(fixed_result)
    
    replace_in_file(FOOTER_JSON_PATH, "NEW_SCROLL_FOOTER_TEXT_1_GENERATED", scroll_texts["text_1"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_SCROLL_FOOTER_OUTLINE_1_GENERATED", scroll_texts["outline_1"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_SCROLL_FOOTER_TEXT_2_GENERATED", scroll_texts["text_2"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_SCROLL_FOOTER_OUTLINE_2_GENERATED", scroll_texts["outline_2"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_SCROLL_FOOTER_TEXT_3_GENERATED", scroll_texts["text_3"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_SCROLL_FOOTER_OUTLINE_3_GENERATED", scroll_texts["outline_3"])

    # Newsletter
    prompt = generate_newsletter_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        newsletter = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "newsletter")
        newsletter = json.loads(fixed_result)
    
    replace_in_file(FOOTER_JSON_PATH, "NEW_NEWSLETTER_HEADING_GENERATED", newsletter["heading"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_NEWSLETTER_TEXT_GENERATED", newsletter["text"])

    # Footer Contact
    prompt = generate_footer_contact_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        footer_contact = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "footer_contact")
        footer_contact = json.loads(fixed_result)
    
    replace_in_file(FOOTER_JSON_PATH, "NEW_FOOTER_CONTACT_HEADING_GENERATED", footer_contact["heading"])
    replace_in_file(FOOTER_JSON_PATH, "NEW_FOOTER_CONTACT_SUBTEXT_GENERATED", footer_contact["subtext"])

def change_footer_content(brand_name: str, product_title: str, product_description: str, language: str):
    """Main function to process footer content"""
    print(f"Processing footer content for {brand_name}™ - {product_title} in {language}")

    # Process footer translations
    print("Processing footer translations...")
    process_footer_translations(brand_name, product_title, language)

    # Process footer generated content
    print("Processing footer generated content...")
    process_footer_generated_content(brand_name, product_title, product_description, language)

    print("Footer content processing completed!")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("brand_name")
    parser.add_argument("product_title")
    parser.add_argument("product_description")
    parser.add_argument("language")

    args = parser.parse_args()

    change_footer_content(
        args.brand_name,
        args.product_title,
        args.product_description,
        args.language
    )