from openai import OpenAI
import json
import re
from typing import Dict, Any
import argparse
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HOME_JSON_PATH = os.getenv("HOME_JSON_PATH")


def clean_json_response(response_text: str) -> str:
    response_text = re.sub(r'```json\s*', '', response_text)
    response_text = re.sub(r'```\s*$', '', response_text)
    # Fix curly quotes
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
        # Check if result has similar HTML structure
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

    return result  # Return last attempt if validation keeps failing

# ===== TRANSLATION FUNCTIONS =====

def process_translations(brand_name: str, product_title: str, language: str):
    """Process all translation placeholders"""

    # Hero Section
    translated = translate_text("Exclusive Holiday Bundles", language)
    replace_in_file(HOME_JSON_PATH, "NEW_HERO_CAPTION_TRANSLATED", translated)

    translated = translate_text("Save Up To 55%", language)
    replace_in_file(HOME_JSON_PATH, "NEW_HERO_BUTTON_TRANSLATED", translated)

    # Featured Section
    translated = translate_text("FEATURED IN", language)
    replace_in_file(HOME_JSON_PATH, "NEW_FEATURED_IN_TRANSLATED", translated)

    # Customer Reviews Section
    translated = translate_text("Look At How Others Are Loving Their Product!", language)
    replace_in_file(HOME_JSON_PATH, "NEW_CUSTOMER_LOVE_HEADING_TRANSLATED", translated)

    translated = translate_text("Real Reviews From Real People", language)
    replace_in_file(HOME_JSON_PATH, "NEW_REAL_REVIEWS_SUBHEADING_TRANSLATED", translated)

    translated = translate_text("CLAIM OFFER", language)
    replace_in_file(HOME_JSON_PATH, "NEW_CLAIM_OFFER_BUTTON_TRANSLATED", translated)

    # Lookbook Section
    translated = translate_text("Lookbook", language)
    replace_in_file(HOME_JSON_PATH, "NEW_LOOKBOOK_HEADING_TRANSLATED", translated)

    translated = translate_text("<p>Optional description for this section</p>", language)
    replace_in_file(HOME_JSON_PATH, "NEW_LOOKBOOK_DESCRIPTION_TRANSLATED", translated)

    translated = translate_text("Heading", language)
    replace_in_file(HOME_JSON_PATH, "NEW_LOOKBOOK_POINT_1_TITLE_TRANSLATED", translated)
    replace_in_file(HOME_JSON_PATH, "NEW_LOOKBOOK_POINT_2_TITLE_TRANSLATED", translated)

    translated = translate_text("Some optional description for this point", language)
    replace_in_file(HOME_JSON_PATH, "NEW_LOOKBOOK_POINT_1_DESC_TRANSLATED", translated)
    replace_in_file(HOME_JSON_PATH, "NEW_LOOKBOOK_POINT_2_DESC_TRANSLATED", translated)

    translated = translate_text("View product", language)
    replace_in_file(HOME_JSON_PATH, "NEW_VIEW_PRODUCT_BUTTON_TRANSLATED", translated)

    # Grid Section
    translated = translate_text("button", language)
    replace_in_file(HOME_JSON_PATH, "NEW_BUTTON_TEXT_TRANSLATED", translated)

    # Product Section
    translated = translate_text("Size Chart", language)
    replace_in_file(HOME_JSON_PATH, "NEW_SIZE_CHART_TRANSLATED", translated)

    translated = translate_text("1 Pack", language)
    replace_in_file(HOME_JSON_PATH, "NEW_PACK_1_LABEL_TRANSLATED", translated)

    translated = translate_text("3 Pack", language)
    replace_in_file(HOME_JSON_PATH, "NEW_PACK_3_LABEL_TRANSLATED", translated)

    translated = translate_text("4 Pack", language)
    replace_in_file(HOME_JSON_PATH, "NEW_PACK_4_LABEL_TRANSLATED", translated)

    translated = translate_text("5 Pack", language)
    replace_in_file(HOME_JSON_PATH, "NEW_PACK_5_LABEL_TRANSLATED", translated)

    translated = translate_text("Offer", language)
    replace_in_file(HOME_JSON_PATH, "NEW_OFFER_LABEL_TRANSLATED", translated)

    translated = translate_text("Most Popular", language)
    replace_in_file(HOME_JSON_PATH, "NEW_MOST_POPULAR_TRANSLATED", translated)

    translated = translate_text("Save (%)", language)
    replace_in_file(HOME_JSON_PATH, "NEW_SAVE_TEXT_TRANSLATED", translated)

    translated = translate_text("<p>Buy More Save More</p>", language)
    replace_in_file(HOME_JSON_PATH, "NEW_BUY_MORE_SAVE_MORE_TRANSLATED", translated)

    translated = translate_text("<p>Limited Time Offer</p>", language)
    replace_in_file(HOME_JSON_PATH, "NEW_LIMITED_TIME_OFFER_TRANSLATED", translated)

    # Philosophy Section
    translated = translate_text("OUR PRODUCT PHILOSOPHY", language)
    replace_in_file(HOME_JSON_PATH, "NEW_PRODUCT_PHILOSOPHY_CAPTION_TRANSLATED", translated)

    translated = translate_text("Learn More", language)
    replace_in_file(HOME_JSON_PATH, "NEW_LEARN_MORE_BUTTON_TRANSLATED", translated)

    # Testimonials
    translated = translate_text("What our customers say", language)
    replace_in_file(HOME_JSON_PATH, "NEW_CUSTOMER_TESTIMONIALS_HEADING_TRANSLATED", translated)

    # Final CTA
    translated = translate_text("Our Story", language)
    replace_in_file(HOME_JSON_PATH, "NEW_OUR_STORY_BUTTON_TRANSLATED", translated)

# ===== CONTENT GENERATION FUNCTIONS =====

def generate_hero_heading_prompt(brand_name: str, product_title: str,product_description:str, language: str) -> str:
    """Generate hero heading prompt"""
    return f"""
You are a marketing copywriter. Create a compelling hero heading in {language} for {brand_name}™'s {product_title} with the following description  : {product_description}.

Requirements:
- 2 lines maximum, use \\n for line break
- Emphasize confidence and transformation
- Include emotional appeal
- Keep it short and impactful
- Mention the holiday theme

Example format: "Rediscover Your Confidence\\nThis Holiday"

IMPORTANT: Return ONLY the heading text, no markdown, no code blocks, no explanations.
"""

def generate_hero_subheading_prompt(brand_name: str, product_title: str,product_description:str, language: str) -> str:
    """Generate hero subheading prompt"""
    return f"""
Create a compelling hero subheading in {language} for {brand_name}™'s {product_title} with the following description  : {product_description}.

Requirements:
- Include discount percentage (up to 55%)
- Use HTML format: Save up to 55% on <strong>Text Here</strong>
- Focus on exclusivity and limited time
- Keep it under 15 words

IMPORTANT: Return ONLY the subheading text, no markdown, no code blocks, no explanations.
"""

def generate_rating_text_prompt(brand_name: str, product_title: str,product_description:str, language: str) -> str:
    """Generate rating text prompt"""
    return f"""
Create a customer rating text in {language} for {brand_name}™.

Requirements:
- Format: "Rated X.X/5 by XXX+ Happy Customers"
- Use realistic numbers (4.7-4.9 rating, 800-2000 customers)
- Keep the word "Happy" or equivalent in {language}

IMPORTANT: Return ONLY the rating text, no markdown, no code blocks, no explanations.
"""


def generate_testimonials_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create 3 customer testimonials in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON with this EXACT format (no markdown, no explanations):

{{
  "testimonial_1": {{
    "caption": "Short benefit phrase",
    "text": "Customer quote about first experience",
    "author": "<p><strong>Benefit Title</strong><br/>— <em>Name, City, Region</em></p>"
  }},
  "testimonial_2": {{
    "caption": "Different benefit phrase", 
    "text": "Quote from long-term user perspective",
    "author": "<p><strong>Different Title</strong><br/>— <em>Name2, City2, Region2</em></p>"
  }},
  "testimonial_3": {{
    "caption": "Third benefit phrase",
    "text": "Quote from converted skeptic angle", 
    "author": "<p><strong>Third Title</strong><br/>— <em>Name3, City3, Region3</em></p>"
  }}
}}"""

def generate_customer_reviews_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create 3 customer reviews in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON (no markdown, no explanations):

{{
  "review_1": "<h1>Experience headline<br/></h1><p>Detailed review content.</p><h6><strong>Name - City</strong></h6>",
  "review_2": "<h1>Comparative headline with <em>{brand_name}™</em><br/></h1><p>Review comparing alternatives.</p><h6><strong>Name2 - City2</strong></h6>",
  "review_3": "<h1>Transformation headline about <em>{brand_name}™</em><br/></h1><p>Review about impact.</p><h6><strong>Name3 - City3</strong></h6>"
}}"""

def generate_benefits_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create 4 short product benefits in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "benefit_1": "Primary benefit with emphasis",
  "benefit_2": "Secondary benefit highlighting different angle",
  "benefit_3": "Third unique benefit",
  "benefit_4_heading": "Catchy heading",
  "benefit_4_text": "Supporting text with details"
}}

Requirements:
- All values must be raw text, no HTML tags (e.g., no <p>, <strong>)
- Keep benefits concise and compelling
- Ensure benefit_4_heading is catchy and benefit_4_text provides supporting details
- Match the product's context and brand tone

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""

def generate_scrolling_texts_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Generate 2 inspirational texts in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "text_1": "<p>First inspirational message</p>",
  "text_2": "<p>Second inspirational message with different emotional angle</p>"
}}"""


def generate_doctor_testimonial_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    """Generate expert testimonial with product-matched expertise"""
    return f"""
Create a short professional expert testimonial in {language} for {brand_name}™'s {product_title}.

PRODUCT CONTEXT: {product_description}

EXPERT MATCHING GUIDELINES:
- Analyze product type and match appropriate expert credentials
- Beauty/Skincare: Dermatologist, Aesthetician, Cosmetic Chemist
- Tech/Electronics: Engineer, Product Designer, Tech Analyst
- Fashion/Apparel: Fashion Designer, Stylist, Textile Expert
- Health/Wellness: Nutritionist, Trainer, Wellness Coach
- Home/Kitchen: Chef, Interior Designer, Home Expert
- Automotive: Mechanic, Racing Driver, Automotive Engineer
- Sports: Athlete, Coach, Sports Scientist
- Create realistic expert names and specific credentials

TESTIMONIAL STYLES TO VARY:
- Technical analysis: Focus on product engineering/quality
- Results-based: Highlight effectiveness and outcomes
- Comparative: Position against alternatives
- Professional recommendation: Why they recommend it
- Innovation focus: Breakthrough features or design

FORMAT REQUIREMENTS:
HTML format: "<p><strong>Compelling quote about product quality/results</strong></p><h6><strong>Expert Name, Specific Title/Credentials</strong></h6>"

IMPORTANT: Return ONLY the HTML testimonial, no markdown, no code blocks, no explanations.
Match the expert type precisely to the product category and create authentic, specific credentials.
Keep the content short and impactful.
"""


def generate_philosophy_heading_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    """Generate philosophy heading prompt"""
    return f"""
Create a philosophy heading in {language} for {brand_name}™'s {product_title}.

PRODUCT CONTEXT: {product_description}

Requirements:
- About crafting quality products
- Mention exceeding expectations
- Professional and inspiring tone
- 1-2 sentences maximum

IMPORTANT: Return ONLY the heading text, no markdown, no code blocks, no explanations.
"""


def generate_video_section_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    return f"""Create video section content in {language} for {brand_name}™'s {product_title}.

PRODUCT: {product_description}

Return ONLY valid JSON:

{{
  "heading": "Dynamic heading capturing product essence",
  "description": "<p><strong>Engaging</strong> 2-3 sentence description</p>",
  "feature_1": "<p><strong>First feature</strong> primary benefit</p>",
  "feature_2": "<p><strong>Second feature</strong> differentiation</p>", 
  "feature_3": "<p><strong>Third feature</strong> emotional benefit</p>",
  "percentage_text": "<p><strong>Performance metric</strong> specific claim</p>"
}}

Requirements:
- 'heading' must be raw text, no HTML tags
- 'description', 'feature_1', 'feature_2', 'feature_3', and 'percentage_text' must use HTML format: <p><strong>Key phrase</strong> remaining text</p>
- Ensure content is concise, compelling, and matches the product's context and brand tone
- 'description' should be 2-3 sentences, emphasizing product benefits
- 'feature_1', 'feature_2', 'feature_3' should highlight distinct benefits or features
- 'percentage_text' should include a specific, realistic performance claim (e.g., 90% customer satisfaction)

Example format for HTML fields:
- "<p><strong>Smoother</strong> facial wrinkles and fine lines</p>"
- "<p><strong>Hydrates</strong> skin for 24 hours</p>"

IMPORTANT: Return ONLY the JSON, no markdown, no code blocks, no explanations.
"""

def safe_json_parse(json_string: str, context: str, fallback_data: dict) -> dict:
    try:
        cleaned = clean_json_response(json_string)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"JSON parse failed for {context}, trying GPT fix...")
        try:
            fixed_json = fix_json_with_gpt(json_string, context)
            return json.loads(fixed_json)
        except:
            print(f"GPT fix failed for {context}, using fallback")
            return fallback_data

def generate_final_cta_heading_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    """Generate final CTA heading prompt with emotional variety"""
    return f"""
Create a powerful final call-to-action heading in {language} for {brand_name}™'s {product_title}.

PRODUCT CONTEXT: {product_description}

CREATIVE REQUIREMENTS:
- Generate unique, emotionally compelling messages that vary each time
- Adapt to different brand personalities and product types based on the product description
- Use diverse themes: transformation, discovery, excellence, journey, empowerment, lifestyle, achievement, etc.
- Create urgency or aspiration without being pushy
- Make it personally meaningful to potential customers

FORMAT: Use HTML tags for emphasis
- **bold text** for strong emphasis
- *italic text* for emotional highlights
- Mix and match for dynamic impact

INSPIRATION THEMES (choose and adapt):
- Personal transformation: "Transform Your *Daily Ritual*", "Elevate Your **Everyday**"
- Discovery: "Discover Your *True Potential*", "Uncover **Hidden Beauty**"
- Lifestyle: "Live **Boldly**", "Embrace *Authentic* Living"
- Achievement: "Achieve **Extraordinary** Results", "Reach Your *Peak Performance*"
- Experience: "Experience *Pure Luxury*", "Feel the **Difference**"
- Future: "Shape Your **Tomorrow**", "Begin Your *New Chapter*"

IMPORTANT: Return ONLY the heading text with HTML formatting, no markdown, no code blocks, no explanations.
Create something fresh and inspiring that matches the brand's essence.
"""

def generate_video_heading_prompt(brand_name: str, product_title: str, product_description: str, language: str) -> str:
    """Generate video heading prompt with dynamic variety"""
    return f"""
Create a captivating video section heading in {language} for {brand_name}™'s {product_title}.

PRODUCT CONTEXT: {product_description}

CREATIVE GUIDELINES:
- Analyze the product description and create specific, relevant headings
- Use powerful, action-oriented language
- Create emotional connection with target audience
- Vary between benefit-focused, feature-focused, and lifestyle-focused approaches
- Make it memorable and share-worthy

HEADING STYLES TO VARY BETWEEN:
- Benefit-driven: "**Transform** Your Experience", "**Unlock** Your Potential"
- Feature-focused: "**Innovation** That Inspires", "**Craftsmanship** Redefined"
- Lifestyle: "**Elevate** Your Daily Ritual", "**Embrace** Premium Living"
- Emotional: "**Feel** the Difference", "**Discover** True Quality"
- Action-oriented: "**Experience** Excellence", "**Achieve** More"

FORMAT REQUIREMENTS:
- Use **strong** tags for key emphasis words
- Keep it concise (2-6 words typically)
- Make it punchy and memorable
- Ensure it works with video content

IMPORTANT: Return ONLY the heading text with HTML formatting, no markdown, no code blocks, no explanations.
Make it specific to the product type and brand personality.
"""
# ===== MAIN PROCESSING FUNCTIONS =====

def clean_html_response(response_text: str) -> str:
    """Clean HTML response by removing markdown code blocks and extra formatting"""
    # Remove HTML markdown code blocks
    response_text = re.sub(r'```html\s*', '', response_text)
    response_text = re.sub(r'```\s*$', '', response_text)
    
    # Remove any leading/trailing whitespace
    response_text = response_text.strip()
    
    return response_text

def process_generated_content(brand_name: str, product_title: str, product_description: str, language: str):
    # Hero Heading
    prompt = generate_hero_heading_prompt(brand_name, product_title, product_description, language)
    hero_heading = prompt_gpt(prompt)
    replace_in_file(HOME_JSON_PATH, "NEW_HERO_HEADING_GENERATED", hero_heading)

    # Hero Subheading
    prompt = generate_hero_subheading_prompt(brand_name, product_title, product_description, language)
    hero_subheading = generate_with_format_validation(prompt, "Save up to 55% on <strong>Text Here</strong>")
    replace_in_file(HOME_JSON_PATH, "NEW_HERO_SUBHEADING_GENERATED", hero_subheading)

    # Rating Text
    prompt = generate_rating_text_prompt(brand_name, product_title, product_description, language)
    rating_text = prompt_gpt(prompt)
    replace_in_file(HOME_JSON_PATH, "NEW_RATING_TEXT_GENERATED", rating_text)

    # Testimonials
    prompt = generate_testimonials_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        testimonials = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "testimonials")
        testimonials = json.loads(fixed_result)
    
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_1_CAPTION_GENERATED", testimonials["testimonial_1"]["caption"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_1_TEXT_GENERATED", testimonials["testimonial_1"]["text"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_1_AUTHOR_GENERATED", testimonials["testimonial_1"]["author"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_2_CAPTION_GENERATED", testimonials["testimonial_2"]["caption"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_2_TEXT_GENERATED", testimonials["testimonial_2"]["text"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_2_AUTHOR_GENERATED", testimonials["testimonial_2"]["author"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_3_CAPTION_GENERATED", testimonials["testimonial_3"]["caption"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_3_TEXT_GENERATED", testimonials["testimonial_3"]["text"])
    replace_in_file(HOME_JSON_PATH, "NEW_TESTIMONIAL_3_AUTHOR_GENERATED", testimonials["testimonial_3"]["author"])

    # Customer Reviews
    prompt = generate_customer_reviews_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        reviews = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "reviews")
        reviews = json.loads(fixed_result)
    
    replace_in_file(HOME_JSON_PATH, "NEW_CUSTOMER_REVIEW_1_GENERATED", reviews["review_1"])
    replace_in_file(HOME_JSON_PATH, "NEW_CUSTOMER_REVIEW_2_GENERATED", reviews["review_2"])
    replace_in_file(HOME_JSON_PATH, "NEW_CUSTOMER_REVIEW_3_GENERATED", reviews["review_3"])

    # Benefits
    prompt = generate_benefits_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        benefits = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "benefits")
        benefits = json.loads(fixed_result)
    
    replace_in_file(HOME_JSON_PATH, "NEW_BENEFIT_1_TEXT_GENERATED", benefits["benefit_1"])
    replace_in_file(HOME_JSON_PATH, "NEW_BENEFIT_2_TEXT_GENERATED", benefits["benefit_2"])
    replace_in_file(HOME_JSON_PATH, "NEW_BENEFIT_3_HEADING_GENERATED", benefits["benefit_3"])
    replace_in_file(HOME_JSON_PATH, "NEW_BENEFIT_4_HEADING_GENERATED", benefits["benefit_4_heading"])
    replace_in_file(HOME_JSON_PATH, "NEW_BENEFIT_4_TEXT_GENERATED", benefits["benefit_4_text"])

    # Scrolling Texts
    prompt = generate_scrolling_texts_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        texts = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "scrolling_texts")
        texts = json.loads(fixed_result)
    
    replace_in_file(HOME_JSON_PATH, "NEW_SCROLLING_TEXT_1_GENERATED", texts["text_1"])
    replace_in_file(HOME_JSON_PATH, "NEW_SCROLLING_TEXT_2_GENERATED", texts["text_2"])

    # Video Content
    prompt = generate_video_section_prompt(brand_name, product_title, product_description, language)
    result = prompt_gpt(prompt)
    try:
        video_content = json.loads(clean_json_response(result))
    except:
        fixed_result = fix_json_with_gpt(result, "video_content")
        video_content = json.loads(fixed_result)
    
    replace_in_file(HOME_JSON_PATH, "NEW_BEAUTY_SERENITY_HEADING_GENERATED", video_content["heading"])
    replace_in_file(HOME_JSON_PATH, "NEW_VIDEO_SECTION_DESCRIPTION_GENERATED", video_content["description"])
    replace_in_file(HOME_JSON_PATH, "NEW_FEATURE_1_GENERATED", video_content["feature_1"])
    replace_in_file(HOME_JSON_PATH, "NEW_FEATURE_2_GENERATED", video_content["feature_2"])
    replace_in_file(HOME_JSON_PATH, "NEW_FEATURE_3_GENERATED", video_content["feature_3"])
    replace_in_file(HOME_JSON_PATH, "NEW_PERCENTAGE_TEXT_GENERATED", video_content["percentage_text"])

    # Video Heading
    prompt = generate_video_heading_prompt(brand_name, product_title, product_description, language)
    video_heading = generate_with_format_validation(prompt, "**Transform** Your Experience")
    replace_in_file(HOME_JSON_PATH, "NEW_VIDEO_HEADING_GENERATED", video_heading)

    # Philosophy Heading
    prompt = generate_philosophy_heading_prompt(brand_name, product_title, product_description, language)
    philosophy_heading = prompt_gpt(prompt)
    replace_in_file(HOME_JSON_PATH, "NEW_PHILOSOPHY_HEADING_GENERATED", philosophy_heading)

    # Doctor Testimonial
    prompt = generate_doctor_testimonial_prompt(brand_name, product_title, product_description, language)
    doctor_testimonial = generate_with_format_validation(prompt, "<p><strong>Compelling quote about product quality/results</strong></p><h6><strong>Expert Name, Specific Title/Credentials</strong></h6>")
    replace_in_file(HOME_JSON_PATH, "NEW_DOCTOR_TESTIMONIAL_GENERATED", doctor_testimonial)

    # Final CTA Heading
    prompt = generate_final_cta_heading_prompt(brand_name, product_title, product_description, language)
    result = generate_with_format_validation(prompt, "Love <strong>Your Skin</strong>, Let Your <em>Radiance</em> Begin")
    replace_in_file(HOME_JSON_PATH, "NEW_FINAL_CTA_HEADING_GENERATED", result)

def change_home_page_content(brand_name: str, product_title: str, product_description: str, language: str):
    """Main function to process all content"""
    print(f"Processing content for {brand_name}™ - {product_title} in {language}")

    # Process translations
    print("Processing translations...")
    process_translations(brand_name, product_title, language)

    # Process generated content
    print("Processing generated content...")
    process_generated_content(brand_name, product_title, product_description, language)

    print("Content processing completed!")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("brand_name")
    parser.add_argument("product_title")
    parser.add_argument("product_description")
    parser.add_argument("language")

    args = parser.parse_args()

    change_home_page_content(
        args.brand_name,
        args.product_title,
        args.product_description,
        args.language
    )