"""
Basecamp AI QC Bot v15.0 – Multi-Project Support
Handles multiple projects with project-specific brand contexts
"""

import re
import os
from datetime import datetime
import traceback
from dotenv import load_dotenv
from groq import Groq
import requests
from flask import Flask, request, jsonify
from PIL import Image
from huggingface_hub import InferenceClient
import threading
from queue import Queue
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

CONFIG = {
    "CLIENT_ID": os.getenv("CLIENT_ID", ""),
    "CLIENT_SECRET": os.getenv("CLIENT_SECRET", ""),
    "REFRESH_TOKEN": os.getenv("REFRESH_TOKEN", ""),
    "ACCOUNT_ID": os.getenv("ACCOUNT_ID", ""),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
}

# Project configurations with brand personality
PROJECTS = {
    37749144: {
        "name": "ABAD BUILDERS",
        "card_table_id": 7457620867,
        "brand_context": """Background: Founded in 1995 under the ABAD Group, Abad Builders is a Kochi-based premium real estate developer specializing in luxury apartments and villas, with 48+ completed projects and 3,000+ families housed, known for trust, transparency, and superior craftsmanship.

Tone: Formal, polished, professional, and premium at all times.

Audience: High-end, discerning homebuyers seeking exclusivity, long-term value, and refined living.

Content Focus: Always highlight project location, connectivity advantages, premium amenities, and clear unique selling points.

Communication Style: Direct, concise, confident, and impact-driven with no unnecessary fluff.

Visual Direction: Use high-quality, elegant, minimal visuals that reflect luxury, scale, and architectural finesse.

Trends: Instagram trends and viral formats are allowed only when adapted tastefully to match a premium real estate brand.

Language: Content may be in English, Malayalam, Manglish(English+Malayalam) ; English, Malayalam, Manglish(English+Malayalam) must be equally refined, accurate, and professional.

Goal: Drive qualified leads, encourage site visits, and build long-term brand trust."""
    },
    42909637: {
        "name": "ActivBase",
        "card_table_id": 8806504777,
        "brand_context": """Background: Activbase is a sports and orthopedic rehabilitation brand in India focused on holistic wellness, movement science, and empowering individuals across all demographics.

Tone: Polished, professional, credible, and performance-focused.

Communication Style: Direct and professional; minimal humor is allowed but must remain subtle, relevant, and never casual.

Trends: Use relevant sports, rehabilitation, and fitness trends only when they reinforce Activbase’s mission and expertise.

Audience: Athletes, sports enthusiasts, and individuals seeking high-quality orthopedic rehabilitation and fitness solutions.

Facilities & Locations: Highlight state-of-the-art rehabilitation facilities, modern equipment, and multi-location presence across India.

Language: English, Malayalam, Manglish(English+Malayalam)  content are both allowed; English, Malayalam, Manglish(English+Malayalam) must be equally refined in quality, clarity, and professionalism.

Goal: Enable optimal physical and mental performance while promoting a culture of excellence in health, movement, and recovery."""
    },
    32745257: {
        "name": "Angel Lungies",
        "card_table_id": 6147569340,
        "brand_context": """Background: Founded in 1988, Angel Lungies is a third-generation Indian textile brand known for high-quality lungies and premium Indian cotton bath towels, built on craftsmanship, quality, and customer trust.

Tone: Professional, simple, and easy to understand.

Communication Style: Direct and product-focused, clearly highlighting features, benefits, and everyday comfort.

Visual Direction: Products must be showcased clearly, properly, and prominently in all images.

Trends: Trends and popular formats are allowed when they support product clarity and value.

Audience: Everyday consumers seeking comfortable, durable, and high-quality lungies and towels.

Language: English, Malayalam, Manglish(English+Malayalam) content are allowed; both must be high-quality, accurate, and easy to understand.

Goal: Emphasize product quality, comfort, and value while building long-term customer trust and loyalty.

Benjies Rule: When referring to Benjies, never use the words activewear, boxers, innerwear, or underwear."""
    },
    43383165: {
        "name": "Bismi Connect",
        "card_table_id": 8929602065,
        "brand_context": """Background: Bismi Connect Kottayam, part of the Bismi Group, is a multi-category retail store in  Kerala, offering home appliances, electronics, mobiles, computers, and related services through a trusted statewide retail network.

Audience: Families and homemakers, tech-savvy customers, first-time buyers needing guidance, working professionals upgrading home or office appliances, and students purchasing mobiles, laptops, and accessories.

Tone: Friendly, professional, approachable, and customer-first.

Communication Style: Direct, simple, and easy to understand, clearly highlighting product features, benefits, pricing value, and practical usage.

Visual Direction: Products must be showcased clearly, prominently, and accurately in all images and videos.

Trends: Reels and viral formats are allowed when clean, relevant, and strictly product-focused.

Language:English, Malayalam, Manglish(English+Malayalam) content are both allowed and must be high-quality, professional, and consumer-friendly.

Goal: Emphasize product value, quality, and usefulness, build trust and loyalty, help customers make confident buying decisions, and position Bismi Connect as a reliable all-in-one electronics and appliance destination."""
    },
    30438693: {
        "name": "BluCampus",
        "card_table_id": 7086056821,
        "brand_context": """Background: BluCampus, established in 2023, is the education arm of Blusteak Media, delivering industry-driven digital marketing education powered by real agency experience and hands-on training.

Brand Essence: A practical, skill-first learning hub focused on real-world exposure, agency-level expertise, and job readiness.

Audience: Students seeking industry-relevant training, freshers aiming for job-ready skills, working professionals upskilling or switching careers, and entrepreneurs learning digital marketing.

Tone: Motivational, professional, positive, and trustworthy.

Communication Style: Direct, clear, and inspiring, emphasizing practical learning, mentorship strength, real agency environment, and career outcomes without overhype.

Visual Direction: Use real class sessions, agency-style training setups, student activities, and practical work environments.

Trends: Clean, relevant trends are allowed when they support education, authenticity, and learning outcomes.

Language: High-quality English, Malayalam, Manglish(English+Malayalam) content; both must be crisp, educational, and easy to understand.

Goal: Position BluCampus as Kerala’s most trusted practical digital marketing learning hub by driving admissions through proof of job readiness, mentorship, and real project exposure."""
    },
    36261272: {
        "name": "Brillar",
        "card_table_id": 7069783202,
        "brand_context": """Background: Brillar, from the ABAD Group and rooted in Kochi’s culinary culture, offers premium frozen foods that deliver authentic homestyle taste for modern, busy lifestyles.

Brand Essence: A balance of authenticity, convenience, and soulful flavour—preserving traditional cooking values in ready-to-use food solutions.

Audience: Working professionals, busy households, students living away from home, and families seeking quick yet authentic meals.

Product Categories: Ready-to-Fry, Ready-to-Cook, and Heat-&-Eat products, positioned as quick, easy, high-quality, and homestyle.

Tone: Warm, inviting, family-oriented, and trustworthy.

Communication Style: Direct, simple, and emotionally warm, highlighting taste, convenience, quality, and authenticity without exaggeration.

Visual Direction: Showcase food clearly, appetizingly, and realistically, focusing on freshness and homely appeal.

Trends: Instagram and Reel trends are allowed when clean, food-focused, and aligned with brand warmth.

Language: High-quality English, Malayalam, Manglish(English+Malayalam) content, maintaining emotional flavour, clarity, and consumer friendliness.

Goal: Position Brillar as a trusted frozen food brand delivering the true taste of home with modern convenience, driving purchase through flavour, ease, and reliability."""
    },
    
    24763032: {
        "name": "Blusteak",
        "card_table_id": 7036264515,
        "brand_context": """Background: Founded in 2017 by Telson Thomas and Jaison Thomas, Blusteak Media is a Kerala-based creative digital marketing agency with a 25+ member team, delivering result-oriented digital solutions to 75+ clients across four continents.

Brand Essence: A fusion of creativity, performance, and smart digital problem-solving, blending data, storytelling, and innovation to drive measurable business growth.

Audience: Ambitious brands seeking online growth, performance-driven campaigns, strong social media presence, and end-to-end digital strategy.

Tone: Confident, creative, modern, solution-oriented, and insight-led, never overhyped.

Communication Style: Clear, concise, and value-driven, focusing on results, strategy, creativity, and brand growth.

Visual Direction: Fresh, aesthetic, trend-aware, and consistently aligned with the brand’s creative identity.

Trends & Humor: All relevant trends and humorous formats are allowed, including reel-based and trend-led content, as long as they remain smart, strategic, and brand-relevant.

Language: High-quality English, Malayalam, and Manglish (English + Malayalam), maintaining clarity, professionalism, and creative expression.

Goal: Position Blusteak Media as Kerala’s top creative-performance digital agency by showcasing measurable results, strategic thinking, and standout creative execution."""
    },


    24763639: {
        "name": "Care N Cure",
        "card_table_id": 7036265363,
        "brand_context": """Background: Care n Cure Pharmacy is a trusted healthcare retail chain in Qatar, operating 63+ outlets across Doha, including multiple 24×7 pharmacies, offering professional pharmacist-led guidance and high-quality, internationally compliant healthcare products.

Brand Essence: Accessible, supportive, and reliable healthcare delivered with professionalism, accuracy, and care.

Audience: Residents of Doha and wider Qatar, including families, working professionals, parents, and elderly customers seeking convenient and trustworthy pharmacy services.

Tone: Professional, warm, friendly, empathetic, culturally respectful, and easy to understand.

Communication Style: Supportive and community-focused, highlighting accessibility, pharmacist expertise, safety, hygiene, and accurate dispensing without medical claims.

Content Focus: Emphasise 24×7 availability, convenient locations, friendly pharmacists, product authenticity, international standards, and reliable service.

Visual Direction: Clean, hygienic, lifestyle-oriented visuals with minimal text and clear product presentation.

Trends: Clean, relevant trends are allowed when they remain informative, respectful, and healthcare-appropriate.

Language: Clear, simple, and professional English (and Arabic/Malayalam only if approved), avoiding complex medical terminology.

Word Restrictions: Never use outcome-based or guarantee terms (e.g., guaranteed, complete cure, 100% results); use safe alternatives like expert guidance, supportive care, helps in managing, recommended options.

Do’s: Highlight 24×7 service, pharmacist support, accuracy, safety standards, and Qatar/Doha context.

Don’ts: Do not promise outcomes, give prescriptions, exaggerate effects, or imply guaranteed medical results.

Goal: Position Care n Cure Pharmacy as Qatar’s most dependable, accessible, and professional pharmacy chain built on trust, care, and convenience."""
    },
    42155802: {
        "name": "Chakolas",
        "card_table_id": 8610065428,
        "brand_context": """Background: Chakolas Pavilion is a distinguished event destination in Kalamassery, Ernakulam, known for refined architecture, calm ambience, and precisely orchestrated hospitality across banquets, dining, and guest services.

Brand Essence: Quiet elegance, disciplined execution, and thoughtfully curated experiences shaped by aesthetics, structure, and grace.

Experience & Offerings: World-class banquet halls, gourmet F&B and outdoor catering, professional event coordination, luxury guest accommodation, spacious parking, immaculate hygiene, and seamless event flow.

Audience: High-earning NRIs, corporate leaders, entrepreneurs, discerning families, and individuals who value subtle refinement over flamboyance.

Tone: Poetic, calm, sophisticated, culturally grounded, and emotionally layered.

Language Style: Refined vocabulary with rhythm and restraint, evoking harmony, serenity, craftsmanship, and timelessness without exaggeration.

Communication Style: Experience-led, evocative, and human, never sales-driven, generic, templated, or mechanical.

Visual Direction: Cinematic yet calm visuals highlighting space, light, structure, hospitality, and atmosphere.

Trends: Trend formats are allowed only when executed with elegance, restraint, and aesthetic alignment.

Tone Restrictions: Avoid words like lavish, majestic, unforgettable, memorable, grand clichés, overhype, slang, or robotic phrasing.

Writing Approach: Use subtle imagery, gentle symbolism, and cultural touchstones to convey refinement without loudness.

Operational Note: High-demand venue with peak-season bookings; early reservations are recommended.

Goal: Position Chakolas Pavilion as a venue of quiet distinction—where gatherings unfold with precision, beauty, and understated luxury."""
    },
    44872946: {
        "name": "Dito",
        "card_table_id": 9304562627,
        "brand_context": """Background: DIT’O is a modern beverage solutions brand combining India’s filter coffee heritage with precision engineering to deliver fast, hygienic, and consistent coffee at scale.

Brand Essence: Traditional taste, engineered for speed, hygiene, and zero manual effort.

Product Offering: Automated filter coffee machines designed for high-volume environments, delivering taste-accurate output with minimal human intervention.

Key Benefits: Fast dispensing, hygienic operation, consistent taste, high-volume capacity, operational reliability, and reduced manpower dependency.

Use Cases: Hotels, cafés, buffets, room service, offices, airports, hospitals, transit hubs, colleges, universities, and institutional facilities.

Audience: HoReCa owners, chefs, F&B managers, café operators, office administrators, HR and workplace managers, facility heads, and institutional decision-makers.

Tone: Direct, sharp, performance-driven, and conversion-focused.

Communication Style: Product-first and solution-oriented, using short sentences and clear functional benefits with no storytelling or filler.

Visual Direction: Machines in action, clean outputs, hygienic setups, and high-footfall usage scenarios.

Trends: Allowed only if they reinforce speed, efficiency, hygiene, and performance.

Language: Clear, concise English (and approved regional languages if required), written for Meta and Google Ads performance.

Goal: Position DIT’O as the most reliable high-performance beverage machine brand by highlighting speed, hygiene, consistency, zero manual effort, and measurable operational efficiency."""},
    33660253: {
        "name": "Geojit",
        "card_table_id": 6378073817,
        "brand_context": """Background: Geojit is a leading Indian investment services company with a strong presence across India and GCC countries, serving over a million clients with decades of trusted financial expertise.

Brand Essence: A transparent, compliant, and client-first financial partner enabling responsible investing across life stages.

Experience & Offerings: Mutual fund and insurance distribution, equities, derivatives, commodities, PMS, goal-based financial planning, and advanced digital investment platforms supported by branches, online portals, and customer care.

Audience: First-time investors seeking guided understanding, existing investors exploring broader services, professionals planning early retirement, retirees, and individuals seeking reliable investment support.

Tone: Educational, factual, empowering, friendly, and trustworthy—never fear-driven or salesy.

Communication Style: Education-first and product-supported, using simple explanations of investment concepts while maintaining accuracy, clarity, and regulatory discipline.

Content Focus: Transparency, compliance, expert guidance, diversified solutions, digital tools, and multi-channel accessibility.

Visual Direction: Clean, professional visuals showcasing real platforms, dashboards, tools, and practical investment use cases.

Trends: Light engagement formats allowed only if informative, compliant, and professional; no memes, clickbait, or urgency tactics.

Compliance Rules: Strict adherence to RBI, SEBI, and mutual fund advertising regulations; mandatory disclaimers where required; no guarantees, performance promises, or misleading claims.

Restrictions: Never guarantee returns, create fear-based narratives, exaggerate outcomes, or imply assured profits.

Language: Clear, professional English (and approved regional languages if applicable), with no slang or emotional manipulation.

Goal: Position Geojit as a safe, compliant, and trustworthy investment partner that builds confidence through education, clarity, and responsible financial communication."""
    },
    
    44358469: {
        "name": "Happy Hens",
        "card_table_id": 9169106524,
        "brand_context": """Background: Happy Hens is an ethics-driven, natural-farming egg brand founded by Manjunath M and Ashok Kannan, focused on nutritional integrity, biodiversity-friendly practices, and responsible production.

Audience: Fitness-focused consumers, high-income and quality-conscious buyers, and individuals addressing protein, Vitamin D, and Vitamin B12 nutritional needs.

Tone: Scientific, intelligent, premium, and ad-ready, with zero clichés, no poetic filler, and no exaggerated claims.

Communication Style: Fact-driven and product-first, using accurate nutrition science (bioavailability, amino acid profile, micronutrient density, HDL relevance) in clear, concise language.

Product Positioning: Happy Hens eggs deliver high protein digestibility, strong micronutrient density, and cleaner nutrition through ethical hen-raising, supporting strength training, recovery, and daily nutritional balance.

Content Rules: Every message must state a clear, verifiable nutritional benefit; generic terms like “healthy eggs” are not allowed.

Trends & Formats: Trends, memes, and high-conversion Meta/Google Ads are allowed only when facts remain accurate and compliant.

Restrictions: No medical claims, cures, emotional manipulation, vague adjectives, unrealistic promises, or non-scientific statements.

QC Standard: Reject any content that is generic, unverified, emotionally driven, or scientifically incorrect.

Goal: Position Happy Hens as a premium, nutrition-forward egg brand trusted by informed consumers for ethical sourcing and measurable nutritional value."""
    },
    40447220: {
        "name": "Incheon Kia",
        "card_table_id": 9221243664,
        "brand_context": """Background: Incheon Kia is a leading Kia dealership network in Kerala with multiple showrooms, advanced service workshops, and Certified Pre-Owned outlets, recognised for ISO-certified quality and environmental standards and award-winning dealership excellence.

Brand Essence: Trust-led automotive retail built on quality systems, service precision, and customer experience.

Experience & Offerings: Modern Kia showrooms, high-tech workshops with certified technicians, structured service processes, and a transparent Certified Pre-Owned program.

Audience: Premium car buyers in Kerala, urban professionals, families seeking dependable and feature-rich vehicles, and first-time or upgrade buyers who value trust and service quality.

Tone: Premium, clear, informative, professional, and customer-first.

Communication Style: Product- and service-focused with factual accuracy, clarity, and zero exaggeration.

Content Focus: Vehicle features, safety and technology highlights, service reliability, ISO standards, sustainability focus, and award credentials.

Visual Direction: Clean, premium visuals showcasing vehicles, showrooms, service quality, and customer experience.

Restrictions: Never use overclaims (e.g., best ever, guaranteed, zero maintenance), misleading performance or safety statements, false delivery/mileage promises, slang, memes, or casual humour.

Compliance: Ensure accurate feature representation and adherence to automotive communication norms at all times.

Goal: Position Incheon Kia as Kerala’s most trusted Kia dealership network by consistently reinforcing quality, reliability, service excellence, and transparent customer experience."""
    },
    
    43584998: {
        "name": "Me n Moms",
        "card_table_id": 8981389456,
        "brand_context": """Background: Founded in 1994 by Mr. Naresh Khatar, Me N Moms is a leading Indian babycare and parenting brand with 100+ stores nationwide, supporting parents through the baby’s foundation years (0–3 years).

Brand Essence: Safe, trusted, and science-backed babycare designed to make early parenting easier and more confident.

Product Portfolio: Babycare essentials across feeding, hygiene, travel, nursery, toys, fashion, and maternity, led by the in-house brand Mee Mee.

Proof Points: 100+ PAN-India stores, 10,000+ retail partners, products tested to ASTM, EN, and BIS standards, child-safe materials, and innovative designs.

Audience: New parents, expecting mothers, gift buyers, and middle-income to premium families seeking certified, safe, and affordable baby products.

Tone: Warm, empathetic, parent-first, trustworthy, and reassuring—never fear-driven.

Communication Style: Clear, product- and safety-focused, benefit-led, and easy to understand, optimized for high-conversion Meta and Google Ads.

Content Focus: Product safety, certifications, baby-friendly materials, practical benefits, and everyday parenting convenience.

Visual Direction: Products must be shown clearly and accurately, with clean, family-friendly visuals.

Trends: Allowed only when factual, safe, and appropriate for babycare categories.

Restrictions: No medical claims, fear-based messaging, overpromising, exaggerated language, or guarantees.

CTA Guidance: Always include clear CTAs such as Shop Now, Learn More, or Visit Store.

QC Standard: Every creative must show the product clearly, highlight benefits simply, mention safety/certifications when relevant, remain emotionally warm but practical, and follow Meta/Google ad best practices.

Goal: Position Me N Moms as India’s most trusted one-stop babycare brand by reinforcing safety, certification, convenience, and parental confidence."""
    },
    44319946: {
        "name": "Mother's Food",
        "card_table_id": 9159425873,
        "brand_context": """Background: Mother’s Foods is a 50-year heritage FMCG brand from Kerala, trusted for pure, home-style food products made with natural ingredients, honest processing, and modern hygiene standards.

Brand Essence: Tradition-led purity, family trust, and everyday food made with care.

Audience: Health-conscious families, homemakers, urban professionals, wellness-oriented consumers, culture-rooted buyers, and NRIs seeking authentic Kerala purity and clean-label foods.

Tone: Warm, trustworthy, family-oriented, and culturally rooted—never dramatic, fear-based, or medical.

Communication Style: Simple, clean, and honest, focusing on purity, natural ingredients, consistency, and home-style care.

Content Focus: Ingredient transparency, traditional values (used sparingly), hygiene standards, and everyday reliability.

Claims & Compliance: Use preservative-free or natural claims only when factually applicable; avoid exaggeration, miracle claims, medical statements, or false nutritional messaging.

Visual Direction: Clean, homely, fresh visuals that align with natural, honest, and hygienic food values.

Restrictions: No misleading health claims, no fear-based language, no over-commercial tone, and no inaccurate ingredient assertions.

QC Standard: Every creative must accurately reflect purity and ingredients, maintain a warm family tone, use heritage responsibly, and align visuals and words with freshness, hygiene, and honesty.

Goal: Position Mother’s Foods as a trusted Kerala heritage brand delivering pure, natural, and dependable everyday foods rooted in tradition and care."""
    },
    44944277: {
        "name": "Pulimoottil",
        "card_table_id": 9324174080,
        "brand_context": """Background: Pulimoottil Silks is a 100-year legacy apparel brand from Kerala with six large-format showrooms, offering premium-quality, tradition-rooted, and innovative clothing collections in an elegant, family-friendly shopping environment.

Brand Essence: Heritage, trust, uncompromising quality, and culturally rooted elegance in apparel.

Audience: Brides and wedding families, NRKs, fashion-conscious youth, homemakers, festive shoppers, and value-driven families seeking premium-quality, trusted heritage clothing.

Tone: Premium, warm, family-friendly, elegant, festive, and tradition-forward; never slangy or meme-like.

Communication Style: Clear, culturally sophisticated, and quality-focused, highlighting legacy, service, and authentic silk craftsmanship.

Content Focus: Pure silk / Silk Mark, bridal wear, family shopping, premium collections, showroom experience, and Kerala-rooted elegance.

Visual Direction: Grand, festive, premium, and culturally resonant; highlighting silk, bridal, and family collections in elegant store settings.

Restrictions: Avoid unrealistic offers, overclaims, low-price positioning, slang, memes, or cheap-sales tonality.

QC Standard: Verify accurate representation of legacy, quality, silk purity, collection relevance, store details, and premium, family-oriented tone.

Goal: Position Pulimoottil Silks as Kerala’s trusted century-old apparel brand delivering premium, culturally rooted, and family-focused shopping experiences."""
    },
    34803430: {
        "name": "Zeiq Consultants",
        "card_table_id": 6662918066,
        "brand_context": """Background: Zeiq is a premier German language training and abroad education consultancy in Kerala, delivering transparent guidance, personalized support, and high-quality language coaching, with 100+ completed batches and 1,000+ students placed globally.

Brand Essence: Trusted, student-focused, and results-oriented language and abroad education support.

Audience: Students aiming for Germany and other countries, young professionals, parents seeking reliable institutes, career-builders, and individuals pursuing certified language skills and authentic abroad guidance.

Tone: Friendly, motivating, educational, slightly humorous, direct, positive, and supportive.

Communication Style: Trend- and moment-friendly, student-centric, clear, and confident; emphasizes trust, affordability, experienced trainers, and tangible student outcomes.

Content Focus: Language coaching quality, abroad guidance, student support, Zeiq’s credibility, and the “Why choose Zeiq” value proposition.

Visual Direction: Neat, student-focused visuals with clear hierarchy and emphasis on learning outcomes.

Restrictions: Never belittle students or countries, never exaggerate or promise guaranteed visas/admissions, humor must be respectful and educational.

QC Standard: Verify respectful tone, accurate representation of training and abroad services, clear value messaging, and proper student-centric visual hierarchy.

Goal: Position Zeiq as Kerala’s most trusted German language and abroad education consultancy, highlighting credibility, quality, and student success."""
    },
        34803430: {
        "name": "Zeiq Consultants",
        "card_table_id": 9238571731,
        "brand_context": """Background: Zeiq is a premier German language training and abroad education consultancy in Kerala, offering transparent guidance, personalized support, and high-quality language coaching with 100+ completed batches and 1,000+ students placed globally.

Brand Essence: Trusted, student-focused, outcome-oriented language and abroad education.

Audience: Students aiming for Germany and other countries, young professionals, parents seeking reliable institutes, career-builders, and learners seeking certified language skills and authentic abroad guidance.

Tone: Friendly, motivating, educational, slightly humorous, direct, positive, and supportive.

Communication Style: Trend- and moment-friendly, student-centric, clear, concise, and confidence-inspiring; emphasizes trust, affordability, experienced trainers, and tangible outcomes.

Content Focus: Language training quality, German certifications (A1–C1), placement support, Zeiq’s credibility, and “Why choose Zeiq” as the USP.

High-Conversion Ad Guidelines: Short, sharp headlines (30–40 chars), clear USP, strong CTA (Enroll Now, Book Free Counselling, Join Today), outcomes-focused, no misleading visa or placement promises, professional and accurate messaging.

Visual Direction: Clean, student-focused visuals with clear hierarchy, trend integration allowed if relevant, respecting platform policies.

Restrictions: Never belittle students or countries; humor must be educative and respectful; no exaggerated or false claims; maintain trust, professionalism, and accuracy.

QC Standard: Verify instant headline hook, crisp conversion-focused messaging, visible USP, strong CTA, respectful tone, trend relevance, platform compliance, and clear Meta ad visual hierarchy.

Goal: Position Zeiq as Kerala’s most trusted German language and abroad education consultancy, driving enrollments through credibility, quality, affordability, and demonstrable student success."""
    },
}

@dataclass
class QCTask:
    """Represents a single QC task"""
    comment_id: int
    project_id: int
    card_id: int
    content: str
    urls: list
    brand_context: str
    full_context: str
    timestamp: float

# Global queue and processing state
qc_queue = Queue()
processing_lock = threading.Lock()
is_processing = False
current_task: Optional[QCTask] = None

# Lazy initialization of Groq client
def get_groq_client():
    """Initialize Groq client lazily to avoid errors if API key is missing"""
    if not hasattr(get_groq_client, 'client'):
        get_groq_client.client = Groq(api_key=CONFIG["GROQ_API_KEY"])
    return get_groq_client.client

# Queue system
access_token = None
processed_comments = set()
IMAGE_BASE_DIR = "qc_images"

# Create base image directory
os.makedirs(IMAGE_BASE_DIR, exist_ok=True)
def get_access_token():
    global access_token
    try:
        r = requests.post(
            "https://launchpad.37signals.com/authorization/token",
            data={
                "type": "refresh",
                "client_id": CONFIG["CLIENT_ID"],
                "client_secret": CONFIG["CLIENT_SECRET"],
                "refresh_token": CONFIG["REFRESH_TOKEN"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        if r.ok:
            access_token = r.json()["access_token"]
            print(f"✓ Token refreshed @ {datetime.now().strftime('%H:%M:%S')}")
            return access_token
        else:
            print(f"✗ Token refresh failed: {r.status_code}")
    except Exception as e:
        print(f"✗ Token error: {e}")
    return None

# ==================== PROJECT UTILITIES ====================
def get_project_config(project_id):
    """Get project configuration by ID"""
    return PROJECTS.get(project_id)

def get_project_image_path(project_id):
    """Get project-specific image path"""
    project_config = get_project_config(project_id)
    if not project_config:
        return os.path.join(IMAGE_BASE_DIR, f"project_{project_id}_temp.jpg")
    
    # Create project-specific folder
    project_name = project_config["name"].replace(" ", "_").lower()
    project_folder = os.path.join(IMAGE_BASE_DIR, project_name)
    os.makedirs(project_folder, exist_ok=True)
    
    return os.path.join(project_folder, "latest_qc_image.jpg")

# ==================== UTILITIES ====================
def strip_html(html):
    """Remove HTML tags and normalize whitespace"""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()

def extract_urls(text):
    """Extract URLs from text - PRESERVES CASE for Drive IDs"""
    return re.findall(r"https?://[^\s<>\"{}|\\^`\[\]]+", text)

# ==================== GOOGLE DRIVE DOWNLOAD ====================
def download_image_to_disk(url, save_path):
    """Downloads image from Google Drive with virus scan bypass"""
    try:
        if "drive.google.com" not in url:
            print("✗ Not a Google Drive URL")
            return None

        # Extract file ID - PRESERVE CASE!
        fid = None
        if "/d/" in url:
            fid = url.split("/d/")[1].split("/")[0].split("?")[0]
        elif "id=" in url:
            fid = url.split("id=")[1].split("&")[0]
        
        if not fid:
            print("✗ Could not extract file ID from URL")
            return None

        print(f"📁 File ID: {fid}")

        # Direct download URL
        download_url = f"https://drive.google.com/uc?export=download&id={fid}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        session = requests.Session()
        print(f"⬇️  Downloading: {download_url}")
        
        # First request
        response = session.get(download_url, headers=headers, stream=True, timeout=60)
        content_type = response.headers.get("Content-Type", "")
        
        # Check if we hit the virus scan warning page
        if "text/html" in content_type and response.status_code == 200:
            print("⚠️  Got HTML (virus scan page), looking for confirm token...")
            
            patterns = [
                r'id="uc-download-link"[^>]*href="([^"]*)"',
                r'confirm=([0-9A-Za-z_-]+)',
                r'download_warning[^>]*value="([^"]*)"',
                r'uuid=([0-9A-Za-z_-]+)',
                r'&amp;confirm=([0-9A-Za-z_-]+)'
            ]
            
            confirm_token = None
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    if 'href=' in pattern:
                        href = match.group(1).replace('&amp;', '&')
                        confirm_match = re.search(r'confirm=([^&]+)', href)
                        if confirm_match:
                            confirm_token = confirm_match.group(1)
                    else:
                        confirm_token = match.group(1)
                    
                    if confirm_token:
                        print(f"🔑 Found confirm token: {confirm_token}")
                        break
            
            if confirm_token:
                download_url = f"https://drive.google.com/uc?export=download&id={fid}&confirm={confirm_token}"
                print(f"🔄 Retrying with confirm token...")
                response = session.get(download_url, headers=headers, stream=True, timeout=60)
                content_type = response.headers.get("Content-Type", "")
        
        print(f"📊 Status: {response.status_code}, Type: {content_type}")
        
        if response.status_code == 200:
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"🗑️  Deleted old image")
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"💾 Saved as: {save_path}")
            
            try:
                img = Image.open(save_path)
                print(f"✅ Valid image: {img.size[0]}x{img.size[1]} {img.mode}")
                return img
            except Exception as e:
                print(f"✗ Not a valid image: {e}")
                return None
        
        elif response.status_code == 404:
            print("=" * 60)
            print("❌ ERROR 404 - FILE NOT FOUND")
            print(f"📋 File ID: {fid}")
            print("=" * 60)
            return None
        
        else:
            print(f"✗ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Download exception: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    return None

def download_image_with_auth(url, token, save_path):
    """Download image from Basecamp attachment"""
    try:
        r = requests.get(
            url, 
            headers={"Authorization": f"Bearer {token}"}, 
            timeout=30
        )
        if r.status_code == 200:
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"🗑️  Deleted old image")
            
            with open(save_path, "wb") as f:
                f.write(r.content)
            
            img = Image.open(save_path)
            print(f"✅ Downloaded from Basecamp: {img.size[0]}x{img.size[1]}")
            return img
    except Exception as e:
        print(f"✗ Basecamp download failed: {e}")
    return None
# ==================== GROQ VISION QC ====================
# ==================== HUGGING FACE VISION QC ====================
def perform_image_qc_with_huggingface(image: Image.Image, brand_context: str = "") -> str:
    """Perform visual QC using Hugging Face's Llama Vision model"""
    try:
        w, h = image.size
        print(f"🤖 Sending to Hugging Face Llama Vision...")
        print(f"   Original Image: {w}x{h}px")
        
        # Resize if needed
        max_size = 1024
        if w > max_size or h > max_size:
            if w > h:
                new_w = max_size
                new_h = int(h * (max_size / w))
            else:
                new_h = max_size
                new_w = int(w * (max_size / h))
            
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            print(f"   Resized to: {new_w}x{new_h}px")
        
        # Save with compression
        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        
        file_size = len(buffer.getvalue())
        print(f"   Compressed size: {file_size / 1024:.1f} KB")
        
        # Encode to base64
        import base64
        img_data = base64.b64encode(buffer.getvalue()).decode()
        image_url = f"data:image/jpeg;base64,{img_data}"
        
        brand_section = f"\n**Brand Context:**\n{brand_context}\n" if brand_context else ""
        
        prompt = f"""You are a Senior Visual QC Analyst.

Image Details: {image.size[0]}×{image.size[1]}px
{brand_section}

Objective: Perform a thorough QC of the creative, focusing on grammar, clarity, messaging, visual hierarchy, and brand consistency. Be professional, constructive, and balanced—acknowledge strengths before pointing out issues. Provide actionable recommendations.

Structured Analysis Approach

Top Section (Logo/Branding/Header)

Evaluate logo visibility, placement, clarity, and brand name consistency.

Check specially for any grammar mistake, spelling mistake, and header clarity.

Identify any branding inconsistencies or misalignments.

Middle Section (Copy Quality & Content)

Assess headline, subtext, product messaging, and tone.

Identify grammar, punctuation, clarity, or messaging issues.

Quote exact text for context when noting problems.

Middle Section (Design & Visuals)

Evaluate layout, alignment, composition, image quality, and visual hierarchy.

Identify elements that reduce readability or user focus.

Suggest design improvements if needed.

Bottom Section (CTA & Contact/Footer)

Check CTA clarity, placement, and actionability.

Ensure contact info is accurate and footer is consistent with brand guidelines.

Logo / Overall Brand Corrections

Check logo quality, color accuracy, alignment, and overall brand consistency.

Recommend specific corrections with reasoning.

Output Format (Copy Exactly)

Visual QC Analysis

Image Details: {image.size[0]}×{image.size[1]}px

Findings:

Top Section - [Logo/Branding/Header]: 

Issue: [Specific problem with context, meaning, and exact text/visuals]

Middle Section - [Copy Quality/Content]: 

Issue: [Grammar, clarity, or messaging problem with exact quotes]

Middle Section - [Design/Visual]: 

Issue: [Design/layout problem with explanation and impact]

Bottom Section - [CTA/Contact]: 

Issue: [CTA or contact problem with context and exact quotes]

Logo Corrections Needed: [Specific issues or "None - logo is correct"]

Current State: [What the logo shows]

Correction Required: [What needs fixing and why]

Reliable Rating System (0–10) and please dont score randomly be very effective  and strict don't give score more than 7 untill and unless its that much effective and good  and always give score according to said criterias and explain why did u deduct score and what was the issue where u have deducted the score too

Copy Quality: /10 → Grammar, clarity, messaging, and brand tone accuracy.

Design & Layout: /10 → Visual hierarchy, composition, alignment, readability.

CTA Effectiveness: /10 → Visibility, clarity, actionability, and conversion potential.

Branding Consistency: /10 → Logo, colors, header/footer, and overall brand alignment.

Overall Impact: /10 → Cohesive messaging, aesthetic appeal, and user experience.

Scoring Guidelines:

0–3: Major issues needing immediate correction

4–6: Some issues; moderately acceptable

7–8: Minor issues; mostly good

9–10: Excellent; no major corrections needed

Rules & Best Practices

Keep exactly 5 points; max 170 words in analysis.

Explain meaning and context for every issue.

Quote exact text for copy problems.

Focus on grammar, clarity, messaging, and actionable design improvements.

Ensure ratings reflect both problem severity and impact on conversion/brand perception.
Be very strict and effective  don't give score more than 7 untill and unless its that much effective and good """


        completion = get_groq_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        result = completion.choices[0].message.content.strip()
        print(f"✅ Vision QC completed ({len(result)} chars)")
        return result
        
    except Exception as e:
        error_msg = f"Hugging Face Vision API failed: {type(e).__name__}: {e}"
        print(f"✗ {error_msg}")
        traceback.print_exc()
        return error_msg

# ==================== TEXT QC ====================
def perform_text_qc(text, brand_context: str = "", is_reel: bool = False):
    """Perform text-only QC using Groq - Handles both reel scripts and poster copy"""
    try:
        if not text or len(text.strip()) < 10:
            return "⚠️ No content to analyze. Please provide text or an image."
        
        brand_section = f"\n**Brand Context:**\n{brand_context}\n" if brand_context else ""
        
        if is_reel:
            # Reel/Video Script QC Prompt
            prompt = f"""You are a Senior Reel/Video Content QC Analyst.

Reel/Video Script Content: "{text}"
{brand_section}

Objective: Conduct a comprehensive, professional QC of the reel/video script. Evaluate how the text translates into video,  focusing on grammar, clarity, messaging and focusing on engagement, visual storytelling, pacing, dialogue delivery , captions, CTA effectiveness, trend alignment, and brand voice consistency. Be balanced—acknowledge strengths, identify actionable issues, and quantify impact using a fair, category-wise scoring system.
Check specially for any grammar mistake, spelling mistake, and header clarity.
Analysis Categories & Weighted Scoring

Hook & Opening (25%) – Viewer engagement, attention-grabbing quality, and retention potential.

Visual Flow & Pacing (20%) – Scene transitions, timing, clarity, and rhythm of visual storytelling.
Dialogues (20%) – Script clarity, pronunciation, tone, and suitability for video delivery.

On-Screen Text, Captions & CTA (20%) – Readability, timing, messaging clarity, and call-to-action effectiveness.

Brand Voice & Trend Alignment (15%) – Consistency with brand personality, tone, and alignment with relevant reel/video trends.

Category Scoring (0–10) please dont score randomly be very effective  and strict don't give score more than 7 untill and unless its that much effective and good and always give score according to said criterias and  explain why did u deduct score and what was the issue where u have deducted the score too:

0–3: Major issue; severely affects clarity, engagement, or brand perception.

4–6: Moderate issue; noticeable, requires attention but not critical.

7–8: Minor issue; small improvements will enhance impact.

9–10: Excellent; fully meets expectations, no corrections needed.

Overall Script Score: Weighted average of the five categories → /10

Output Format (Copy Exactly)

Reel/Video Script QC Analysis

Findings:

[Category]: [One-line observation highlighting strength or issue]

Problem: [Quote exact text, explain issue context, and why it matters]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue context, and why it matters]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue context, and why it matters]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue context, and why it matters]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue context, and why it matters]

Score (0–10):

Overall Script Score: /10 (Weighted average based on category percentages)

Strict Rules & Best Practices

Exactly 5 points; no more, no less.

Always quote exact problematic text when analyzing copy issues.

Focus on video-specific performance: pacing, attention retention, clarity, and CTA impact.

Include positive observations wherever applicable.

Be professional, precise, and actionable.

Do not provide solutions or fixes—observations only.

Ensure evaluation reflects how the reel/video will perform in real audience scenarios
Be very strict and effective  don't give score more than 7 untill and unless its that much effective and good"""
        else:
            # Normal Poster Copy QC Prompt
            prompt = f"""You are a Professional Copy QC Analyst.

Text Content: "{text}"
{brand_section}

Objective: Conduct an in-depth, professional QC of the copy. Evaluate grammar, clarity, tone, messaging, persuasion, CTA effectiveness, and overall brand alignment. Be balanced: acknowledge strengths, identify actionable issues, and quantify impact using a reliable scoring system.
Check specially for any grammar mistake, spelling mistake, and header clarity.
Analysis Categories & Weighted Scoring

Language & Grammar (25%) – Grammar, spelling, punctuation, clarity, tone, and readability.

Messaging & Creativity (20%) – Originality, relevance, coherence, and alignment with brand voice.

Persuasion & Value Proposition (20%) – Effectiveness in highlighting benefits, selling points, and emotional appeal.

Call-to-Action (20%) – Clarity, urgency, visibility, and conversion potential.

Overall Impact & Brand Consistency (15%) – Professionalism, cohesiveness, trustworthiness, and tone consistency.

Category Scoring (0–10):Reliable Rating System (0–10) and please dont score randomly be very effective and strict strict don't give score more than 7 untill and unless its that much effective and good and always give score according to said criterias and explain and why did u deduct score and what was the issue where u have deducted the score too

0–3: Major issue; severely affects readability, clarity, or brand perception.

4–6: Moderate issue; noticeable, requires attention.

7–8: Minor issue; small improvements will enhance impact.

9–10: Excellent; fully meets expectations, no corrections needed.

Overall Copy Score: Weighted average → /10

Output Format (Copy Exactly)

Copy QC Analysis

Findings:

[Category]: [One-line observation highlighting strength or issue]

Problem: [Quote exact text, explain grammar, clarity, or messaging issue and why it matters]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue with context]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue with context]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue with context]

Score (0–10):

[Category]: [One-line observation]

Problem: [Quote exact text, explain issue with context]

Score (0–10):

Overall Copy Score: /10 (Weighted average based on category percentages)

Strict Rules & Best Practices

Exactly 5 points, no more, no less.

Always quote exact problematic text when analyzing.

Be critical but fair, professional, and precise.

Focus on grammar, clarity, tone, messaging, persuasion, and CTA effectiveness.

Include positive observations wherever applicable.

Do not suggest fixes—observations only.

Ensure evaluation reflects how the copy will perform with the audience and in real campaigns.
Be very strict and effective  don't give score more than 7 untill and unless its that much effective and good"""

        print(f"🤖 Sending to Groq Text API (Llama 3.3 70B)...")
        print(f"   Content Type: {'REEL/VIDEO SCRIPT' if is_reel else 'POSTER COPY'}")
        
        completion = get_groq_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3
        )
        
        result = completion.choices[0].message.content.strip()
        print(f"✅ Text QC completed ({len(result)} chars)")
        return result
        
    except Exception as e:
        error_msg = f"Text QC failed: {type(e).__name__}: {e}"
        print(f"✗ {error_msg}")
        return error_msg


def get_card_attachments(pid, cid, token):
    """Get image attachments from a Basecamp card"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}.json"
        r = requests.get(
            url, 
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.ok:
            attachments = r.json().get("attachments", [])
            images = [a for a in attachments if a.get("content_type", "").startswith("image/")]
            print(f"📎 Found {len(images)} image attachment(s)")
            return images
    except Exception as e:
        print(f"✗ Failed to get attachments: {e}")
    return []

def get_card_content(pid, cid, token):
    """Get text content from a Basecamp card"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}.json"
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.ok:
            content = strip_html(r.json().get("content", ""))
            print(f"📄 Card content: {len(content)} chars")
            return content
    except Exception as e:
        print(f"✗ Failed to get card content: {e}")
    return None

def post_comment_to_basecamp(pid, cid, text, token):
    """Post QC results as a comment to Basecamp with highlighted keywords"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}/comments.json"
        
        formatted_text = text.strip()
        
        # Step 1: Protect quoted text first
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, formatted_text)
        quote_placeholders = {}
        for i, quote in enumerate(quotes):
            placeholder = f"___QUOTE_{i}___"
            quote_placeholders[placeholder] = f'<span style="background:#fff3cd;color:#856404;padding:2px 5px;border-radius:3px;font-style:italic;">"{quote}"</span>'
            formatted_text = formatted_text.replace(f'"{quote}"', placeholder, 1)
        
        # Step 2: Convert **text** to bold
        def replace_bold(match):
            content = match.group(1)
            keywords = ['Issue', 'Problem', 'Reason', 'Suggestion', 'What Works Well', 'Findings']
            if any(kw in content for kw in keywords):
                return f'**{content}**'
            return f'<strong>{content}</strong>'
        
        formatted_text = re.sub(r'\*\*(.+?)\*\*', replace_bold, formatted_text)
        
        # Step 3: Highlight key section labels
        keywords_map = {
            r'\*\*Issue\*\*:': '<span style="background:#dc3545;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Issue</span>:',
            r'\*\*Problem\*\*:': '<span style="background:#dc3545;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Problem</span>:',
            r'\*\*Reason\*\*:': '<span style="background:#ffc107;color:#000;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Reason</span>:',
            r'\*\*Suggestion\*\*:': '<span style="background:#28a745;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Suggestion</span>:',
            r'\*\*What Works Well\*\*:': '<span style="background:#17a2b8;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">What Works Well</span>:',
            r'\*\*Findings\*\*:': '<span style="background:#6c757d;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Findings</span>:',
        }
        
        for pattern, replacement in keywords_map.items():
            formatted_text = re.sub(pattern, replacement, formatted_text)
        
        # Non-bold versions
        keywords_map_plain = {
            r'Issue:': '<span style="background:#dc3545;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Issue</span>:',
            r'Problem:': '<span style="background:#dc3545;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Problem</span>:',
            r'Reason:': '<span style="background:#ffc107;color:#000;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Reason</span>:',
            r'Suggestion:': '<span style="background:#28a745;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Suggestion</span>:',
            r'What Works Well:': '<span style="background:#17a2b8;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">What Works Well</span>:',
            r'Findings:': '<span style="background:#6c757d;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold;display:inline-block;margin:2px 0;">Findings</span>:',
        }
        
        for pattern, replacement in keywords_map_plain.items():
            formatted_text = re.sub(pattern, replacement, formatted_text)
        
        # Step 4: Restore quoted text
        for placeholder, html in quote_placeholders.items():
            formatted_text = formatted_text.replace(placeholder, html)
        
        # Step 5: Convert remaining markdown
        formatted_text = re.sub(r'### (.+)', r'<div style="font-size:16px;font-weight:bold;margin:10px 0 5px 0;color:#f8f9fa;">\1</div>', formatted_text)
        formatted_text = re.sub(r'^• (.+)$', r'&nbsp;&nbsp;&nbsp;• \1', formatted_text, flags=re.MULTILINE)
        formatted_text = re.sub(r'^(\d+)\. ', r'<br><strong>\1.</strong> ', formatted_text, flags=re.MULTILINE)
        formatted_text = formatted_text.replace('\n', '<br>')
        
        # Step 6: Final HTML wrapper
        html_style = "font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#f8f9fa;background:#2c3e50;padding:24px;border-radius:10px;line-height:1.9;box-shadow:0 2px 8px rgba(0,0,0,0.1);"
        html = f'<div style="{html_style}">\n{formatted_text}\n</div>'
        
        r = requests.post(
            url,
            json={"content": html},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        if r.ok:
            print(f"✅ Posted comment to Basecamp")
            return True
        else:
            print(f"✗ Failed to post comment: {r.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Post comment error: {e}")
        traceback.print_exc()
        return False
def get_queue_position(comment_id):
    """Get position of a comment in queue (1-indexed)"""
    with qc_queue.mutex:
        queue_list = list(qc_queue.queue)
        for i, task in enumerate(queue_list, 1):
            if task.comment_id == comment_id:
                return i
    return 0

def post_queue_notification(pid, cid, position, token):
    """Post queue position notification to Basecamp"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}/comments.json"
        
        html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#f8f9fa;background:#2c3e50;padding:20px;border-radius:10px;text-align:center;">
<div style="font-size:48px;margin-bottom:10px;">⏳</div>
<div style="font-size:18px;font-weight:bold;margin-bottom:10px;">Your QC request is queued</div>
<div style="font-size:32px;font-weight:bold;color:#3498db;margin:15px 0;">Position: #{position}</div>
<div style="color:#bdc3c7;font-size:13px;margin-top:10px;">You'll be notified when your analysis starts</div>
</div>"""
        
        r = requests.post(
            url,
            json={"content": html},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        if r.ok:
            print(f"✅ Posted queue notification (Position #{position})")
            return True
        else:
            print(f"✗ Failed to post queue notification: {r.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Queue notification error: {e}")
        return False

def post_processing_notification(pid, cid, token):
    """Notify user that their QC is starting"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}/comments.json"
        
        html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#f8f9fa;background:#27ae60;padding:20px;border-radius:10px;text-align:center;">
<div style="font-size:48px;margin-bottom:10px;">🤖</div>
<div style="font-size:18px;font-weight:bold;">Your QC analysis is starting now...</div>
</div>"""
        
        requests.post(
            url,
            json={"content": html},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
    except Exception as e:
        print(f"✗ Processing notification error: {e}")

def process_qc_task(task: QCTask):
    """Process a single QC task"""
    try:
        print(f"\n{'='*60}")
        print(f"🔄 PROCESSING TASK: Comment {task.comment_id}")
        print(f"   Project: {task.project_id}, Card: {task.card_id}")
        print(f"{'='*60}\n")
        
        token = get_access_token()
        if not token:
            print("❌ FATAL: Failed to get access token - check CONFIG credentials")
            print(f"   CLIENT_ID: {CONFIG['CLIENT_ID'][:20]}...")
            print(f"   ACCOUNT_ID: {CONFIG['ACCOUNT_ID']}")
            return
        
        # Notify user that processing is starting
        post_processing_notification(task.project_id, task.card_id, token)
        
        # Get project-specific image path
        image_path = get_project_image_path(task.project_id)
        image = None

        # Check Basecamp attachments
        print("🔍 Checking Basecamp attachments...")
        for att in get_card_attachments(task.project_id, task.card_id, token):
            img = download_image_with_auth(att["download_url"], token, image_path)
            if img:
                image = img
                print("✅ Got image from Basecamp")
                break

        # Check Google Drive URLs
        if not image and task.urls:
            print("🔍 Checking Google Drive URLs...")
            for url in task.urls:
                if "drive.google.com" in url:
                    img = download_image_to_disk(url, image_path)
                    if img:
                        image = img
                        print("✅ Got image from Google Drive")
                        break

        # Perform QC
        print("🔍 Performing QC...")
        if image:
            result = perform_image_qc_with_huggingface(image, task.full_context)
        else:
            # Clean up text content
            text_content = re.sub(r'@nokk\b', '', task.content, flags=re.IGNORECASE).strip()
            
            # Check if it's a reel script
            is_reel = False
            if '[reel]' in text_content.lower():
                is_reel = True
                # Remove the [reel] marker from content
                text_content = re.sub(r'\[reel\]', '', text_content, flags=re.IGNORECASE).strip()
                print("🎬 Detected REEL/VIDEO SCRIPT content")
            
            # Remove URLs from text
            for url in task.urls:
                text_content = text_content.replace(url, "").strip()
            
            if not text_content or len(text_content) < 10:
                text_content = get_card_content(task.project_id, task.card_id, token)
                # Check for [reel] in card content too
                if text_content and '[reel]' in text_content.lower():
                    is_reel = True
                    text_content = re.sub(r'\[reel\]', '', text_content, flags=re.IGNORECASE).strip()
            
            result = perform_text_qc(text_content, task.full_context, is_reel=is_reel)

        # Post results
        print("🔍 Posting results...")
        success = post_comment_to_basecamp(task.project_id, task.card_id, result, token)
        
        if success:
            print("✅ TASK COMPLETED SUCCESSFULLY")
        else:
            print("⚠️ TASK COMPLETED WITH ERRORS")
        
    except Exception as e:
        print(f"❌ Task processing error: {e}")
        traceback.print_exc()

def queue_worker():
    """Background worker that processes queue"""
    global is_processing, current_task
    
    while True:
        try:
            # Get next task (blocks until available)
            task = qc_queue.get()
            
            with processing_lock:
                is_processing = True
                current_task = task
            
            # Process the task
            process_qc_task(task)
            
            with processing_lock:
                is_processing = False
                current_task = None
            
            # Mark task as done
            qc_queue.task_done()
            
        except Exception as e:
            print(f"❌ Queue worker error: {e}")
            traceback.print_exc()
            with processing_lock:
                is_processing = False
                current_task = None
# ==================== WEBHOOK ====================
@app.route("/webhook/basecamp", methods=["POST"])
def basecamp_webhook():
    """Main webhook handler - adds tasks to queue"""
    try:
        print("\n" + "="*60)
        print(f"📨 WEBHOOK RECEIVED @ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        data = request.json
        kind = data.get("kind")
        rec = data.get("recording", {})
        cid = rec.get("id")
        
        content_raw = strip_html(rec.get("content", ""))
        content_lower = content_raw.lower()
        
        print(f"Kind: {kind}")
        print(f"Comment ID: {cid}")

        # Basic validation
        if kind != "comment_created":
            print(f"⏭️  Ignoring: not a comment")
            return jsonify({"status": "ignored", "reason": "not_comment"}), 200
            
        if cid in processed_comments:
            print(f"⏭️  Ignoring: already processed")
            return jsonify({"status": "ignored", "reason": "duplicate"}), 200
            
        if "@nokk" not in content_lower:
            print(f"⏭️  Ignoring: no @nokk trigger")
            return jsonify({"status": "ignored", "reason": "no_trigger"}), 200

        processed_comments.add(cid)
        
        pid = rec.get("bucket", {}).get("id")
        card_id = rec.get("parent", {}).get("id")
        
        if not pid or not card_id:
            print("✗ Missing project or card ID")
            return jsonify({"error": "missing_ids"}), 400

        print(f"Project ID: {pid}")
        print(f"Card ID: {card_id}")

        # Get project configuration
        project_config = get_project_config(pid)
        if project_config:
            brand_context = project_config["brand_context"]
        else:
            brand_context = ""

        # Extract URLs and user context
        urls = extract_urls(content_raw)
        user_context = re.sub(r'@nokk\b', '', content_raw, count=1, flags=re.IGNORECASE).strip()
        for url in urls:
            user_context = user_context.replace(url, "").strip()
        
        # Combine contexts
        if user_context:
            full_context = f"{brand_context}\n\nUser Brief: {user_context}"
        else:
            full_context = brand_context
        
        # Create task
        task = QCTask(
            comment_id=cid,
            project_id=pid,
            card_id=card_id,
            content=content_raw,
            urls=urls,
            brand_context=brand_context,
            full_context=full_context,
            timestamp=datetime.now().timestamp()
        )
        
        # Process synchronously (Render compatible)
        print(f"🔄 Processing task synchronously...")
        process_qc_task(task)
        print("="*60)
        print(f"✅ WEBHOOK COMPLETED - Task processed synchronously")
        print("="*60 + "\n")
        return jsonify({"status": "processed"}), 200

    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==================== STARTUP ====================
# Add this to your main block, BEFORE app.run():

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MULTI-PROJECT QC BOT v15.0 STARTING...")
    print("="*60)
    print(f"✓ Queue system enabled")
    print(f"✓ Image base directory: {IMAGE_BASE_DIR}")
    print(f"✓ Supported projects: {len(PROJECTS)}")
    
    # Create project folders
    for pid, config in PROJECTS.items():
        folder = os.path.join(IMAGE_BASE_DIR, config["name"].replace(" ", "_").lower())
        os.makedirs(folder, exist_ok=True)
        print(f"  ✓ {config['name']}: {folder}")
    
    print("="*60 + "\n")
    
    get_access_token()
    
    # Start queue worker thread
    # Disabled: Queue-based processing doesn't work on Render free tier
    # Background threads are killed on service restart
    # Using synchronous processing in webhook instead
    # worker_thread = threading.Thread(target=queue_worker, daemon=True)
    # worker_thread.start()
    # print("✅ Queue worker started!")
    
    print("\n✅ Bot ready! Waiting for webhooks...\n")
    print("📝 Processing mode: SYNCHRONOUS (Render compatible)\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    project_list = "\n".join([f"  • {p['name']} (ID: {pid})" for pid, p in PROJECTS.items()])
    
    return f"""<pre style="font-family:monospace;padding:20px;background:#f5f5f5;">
<b>🤖 Multi-Project QC Bot v15.0</b>

Status: <span style="color:green">● RUNNING</span>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: Hugging Face Llama Vision + Text

<b>Supported Projects ({len(PROJECTS)}):</b>
{project_list}

Usage:
  <b>For Image QC:</b>
  1. Comment: @nokk [optional brand brief]
  2. Attach image or provide Google Drive link
  
  <b>For Poster Copy QC:</b>
  1. Comment: @nokk
  2. Paste your poster copy text
  
  <b>For Reel/Video Script QC:</b>
  1. Comment: @nokk [reel]
  2. Paste your reel/video script
  
  3. Bot auto-detects project and applies brand context
  4. Receives QC with findings and issues

Features:
  ✓ Multi-project support
  ✓ Auto brand context detection
  ✓ Project-specific image storage
  ✓ Image + Text analysis
  ✓ Reel/Video script analysis
  ✓ Google Drive support
  ✓ Queue system for concurrent requests
</pre>"""

# ==================== STARTUP ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MULTI-PROJECT QC BOT v15.0 STARTING...")
    print("="*60)
    print(f"✓ Image base directory: {IMAGE_BASE_DIR}")
    print(f"✓ Supported projects: {len(PROJECTS)}")
    print(f"✓ HF_TOKEN configured: {CONFIG['GROQ_API_KEY'][:10]}...")
    
    # Create project folders
    for pid, config in PROJECTS.items():
        folder = os.path.join(IMAGE_BASE_DIR, config["name"].replace(" ", "_").lower())
        os.makedirs(folder, exist_ok=True)
        print(f"  ✓ {config['name']}: {folder}")
    
    print("="*60 + "\n")
    
    get_access_token()
    
    print("\n✅ Bot ready! Waiting for webhooks...\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
