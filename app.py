import os
import requests
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db, auth
import re

# 2026 Gemini SDK
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = 'srec_demo_secret_2025'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set True if HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# ------------------ Firebase Admin Setup ------------------
cred = credentials.Certificate("october11-868ab-firebase-adminsdk-fbsvc-3edad1544c.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://october11-868ab-default-rtdb.firebaseio.com/'
})

FIREBASE_API_KEY = "AIzaSyCS_00jpLwOXDuSoPK8pRhJL9jbzwC5-wc"

# ------------------ Google Custom Search ------------------
CSE_API_KEY = "AIzaSyDnA4mSjKF3fNZJIkKwqVkjmcmomc0uNmc"
CSE_CX = "22ebcf6c51cdb481d"

# ------------------ Gemini AI Setup ------------------
GEMINI_API_KEY = "AIzaSyDxtMVWQERZ3sxURK8EVevOA6dWQ_mzf40"
client = genai.Client(api_key=GEMINI_API_KEY)

# ------------------ Cloudinary Setup ------------------
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = "dxmnmfloq",
    api_key    = "572959442148374",
    api_secret = "2s7ZkndxzWC6IAsmtO_nPjb5PY0",
    secure     = True
)

def upload_to_cloudinary(base64_data):
    """Upload a base64 image to Cloudinary and return the secure URL."""
    try:
        # Cloudinary accepts base64 directly with the data URI prefix
        result = cloudinary.uploader.upload(
            base64_data,
            folder="srec_campusconnect",   # Organizes images in a folder
            resource_type="image",
            transformation=[
                {"width": 900, "crop": "limit"},  # Max width 900px
                {"quality": "auto:good"},          # Auto compress quality
                {"fetch_format": "auto"}           # Auto best format (webp etc)
            ]
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

# =====================================================================
# RICH SREC KNOWLEDGE BASE (scraped from srec.ac.in)
# =====================================================================
SREC_KNOWLEDGE = {

    # === GENERAL ===
    'about': (
        "🏫 Sri Ramakrishna Engineering College (SREC) was established in 1994 by SNR Sons Charitable Trust "
        "in Coimbatore, Tamil Nadu. It's one of the best engineering colleges in the region — autonomous, "
        "AICTE-approved, and affiliated to Anna University. SREC currently has 4,400+ students and 271+ faculty! "
        "Check out more at 👉 <a href='https://srec.ac.in/aboutus' target='_blank'>srec.ac.in/aboutus</a>"
    ),
    'srec': (
        "🏫 SREC stands for Sri Ramakrishna Engineering College! It was founded in 1994 and is run by "
        "SNR Sons Charitable Trust. It's an autonomous college affiliated to Anna University and is "
        "NAAC re-accredited with A+ grade 🎉"
    ),
    'established': "📅 SREC was established in the year 1994 by SNR Sons Charitable Trust.",
    'founder': "SREC is managed by SNR Sons Charitable Trust, which has a legacy of over four and a half decades in education and healthcare.",
    'location': (
        "📍 SREC is located at Vattamalaipalayam, N.G.G.O Colony P.O, Coimbatore - 641 022, Tamil Nadu. "
        "You can find it on Google Maps here: 👉 <a href='https://goo.gl/maps/ANnVSdJxQ7kZ69JH7' target='_blank'>Open Map</a>"
    ),
    'address': (
        "📍 Vattamalaipalayam, N.G.G.O Colony P.O, Coimbatore - 641 022, Tamil Nadu, India."
    ),
    'accreditation': (
        "🏆 SREC is Re-accredited by NAAC with 'A+' grade. Seven B.E/B.Tech programmes are also accredited "
        "by the National Board of Accreditation (NBA), New Delhi — and this has been going on since 2003! "
        "Also rated AAA by Careers 360 as 'India's Best Engineering Institute 2024'."
    ),
    'naac': "🏆 SREC is Re-accredited by NAAC with 'A+' grade — one of the top ratings a college can get!",
    'nba': "Seven B.E/B.Tech programmes at SREC are NBA accredited and have been since 2003. That's a solid record! 💪",
    'ranking': (
        "🏅 SREC has some impressive rankings! Careers 360 rated it AAA (India's Best 2024), "
        "The Week ranked it in Top 28 Best Engineering Colleges, and Times of India listed it in Top 10. "
        "Pretty proud of our college! 😊"
    ),
    'vision': (
        "🌟 SREC's Vision: 'To become a world class university excelling in multidisciplinary domain "
        "through cutting-edge technologies and impactful societal contributions for sustainable development.'"
    ),
    'mission': (
        "🎯 SREC's Mission is to provide quality education that builds strong technical, analytical and "
        "managerial skills. They also focus on creativity, innovation, ethics, leadership and entrepreneurship "
        "for holistic development of students."
    ),
    'affiliation': "📜 SREC is affiliated to Anna University, Chennai and is an autonomous institution.",
    'autonomous': "Yes! SREC is an autonomous institution — meaning it has the freedom to design its own curriculum and conduct its own exams.",
    'counselling code': "📋 SREC's counselling code is **2719 99** — keep this handy for TNEA admissions!",

    # === CONTACT ===
    'contact': (
        "📞 You can reach SREC at:\n"
        "• Phone: <a href='tel:+917530089996'>+91 75300 89996</a>\n"
        "• Email: <a href='mailto:principal@srec.ac.in'>principal@srec.ac.in</a>\n"
        "• Website: <a href='https://srec.ac.in' target='_blank'>srec.ac.in</a>"
    ),
    'phone': "📞 SREC Hotline: <a href='tel:+917530089996'>+91 75300 89996</a>",
    'email': "📧 Email: <a href='mailto:principal@srec.ac.in'>principal@srec.ac.in</a>",
    'website': "🌐 Official website: <a href='https://srec.ac.in' target='_blank'>srec.ac.in</a>",
    'principal': (
        "👨‍💼 For details about the Principal, visit: "
        "<a href='https://srec.ac.in/aboutus/principal' target='_blank'>srec.ac.in/aboutus/principal</a>"
    ),

    # === COURSES ===
    'courses': (
        "📚 SREC offers a wide range of programmes:\n\n"
        "🎓 <b>12 UG (B.E/B.Tech) Programmes:</b>\n"
        "Aeronautical, Biomedical, Civil, Mechanical, ECE, EEE, EIE, IT, CSE, "
        "Robotics & Automation, AI & Data Science, M.Tech CSE (5-Year Integrated)\n\n"
        "🎓 <b>7 PG Programmes:</b>\n"
        "Manufacturing Engg, Power Electronics & Drives, VLSI Design, CSE, "
        "Embedded Systems, Control & Instrumentation, Nanoscience & Technology\n\n"
        "📊 <b>MBA</b> in Business & Management\n\n"
        "See all: <a href='https://srec.ac.in/academics/courseoffered' target='_blank'>View All Courses</a>"
    ),
    'ug': (
        "🎓 SREC's Undergraduate programmes (B.E/B.Tech): Aeronautical Engineering, Biomedical Engineering, "
        "Civil Engineering, Mechanical Engineering, ECE, EEE, Electronics & Instrumentation, "
        "Information Technology, CSE, Robotics & Automation, AI & Data Science, "
        "and M.Tech CSE (5-Year Integrated). That's 12 programmes! 🙌"
    ),
    'pg': (
        "🎓 SREC's PG programmes: Manufacturing Engineering, Power Electronics & Drives, VLSI Design, "
        "CSE, Embedded System Technologies, Control & Instrumentation Engineering, and Nanoscience & Technology."
    ),
    'mba': "📊 Yes! SREC offers an MBA programme too. Check details at <a href='https://srec.ac.in/department/mba' target='_blank'>srec.ac.in/department/mba</a>",
    'cse': "💻 The CSE department at SREC is one of the most popular! Check it out: <a href='https://srec.ac.in/department/cse' target='_blank'>srec.ac.in/department/cse</a>",
    'it': "💡 IT Department: <a href='https://srec.ac.in/department/it' target='_blank'>srec.ac.in/department/it</a>",
    'ece': "📡 ECE Department: <a href='https://srec.ac.in/department/ece' target='_blank'>srec.ac.in/department/ece</a>",
    'eee': "⚡ EEE Department: <a href='https://srec.ac.in/department/eee' target='_blank'>srec.ac.in/department/eee</a>",
    'mechanical': "🔧 Mechanical Department: <a href='https://srec.ac.in/department/mech' target='_blank'>srec.ac.in/department/mech</a>",
    'civil': "🏗️ Civil Engineering Department: <a href='https://srec.ac.in/department/civil' target='_blank'>srec.ac.in/department/civil</a>",
    'aeronautical': "✈️ Aeronautical Engineering Department: <a href='https://srec.ac.in/department/aero' target='_blank'>srec.ac.in/department/aero</a>",
    'biomedical': "🏥 Biomedical Engineering Department: <a href='https://srec.ac.in/department/bme' target='_blank'>srec.ac.in/department/bme</a>",
    'robotics': "🤖 Robotics & Automation Department: <a href='https://srec.ac.in/department/robotics' target='_blank'>srec.ac.in/department/robotics</a>",
    'ai': "🤖 AI & Data Science Department (B.Tech): <a href='https://srec.ac.in/department/btech' target='_blank'>srec.ac.in/department/btech</a>",
    'departments': "🏛️ All departments: <a href='https://srec.ac.in/departments' target='_blank'>srec.ac.in/departments</a>",

    # === ADMISSIONS ===
    'admission': (
        "📝 Admissions at SREC:\n"
        "• UG (B.E/B.Tech): Through <b>TNEA</b> counselling\n"
        "• PG (M.E/M.Tech): Through <b>TANCET / GATE</b>\n"
        "• MBA: Through TANCET\n"
        "• Counselling Code: <b>2719 99</b>\n\n"
        "Apply here 👉 <a href='https://srec.ac.in/academics/online_admission' target='_blank'>Online Admission</a>"
    ),
    'tnea': (
        "📋 SREC participates in TNEA (Tamil Nadu Engineering Admissions) for UG admissions. "
        "SREC's counselling code is <b>2719 99</b>. "
        "Check eligibility: <a href='https://srec.ac.in/academics/eligibility' target='_blank'>Eligibility Info</a>"
    ),
    'eligibility': (
        "📋 For admission eligibility details, visit: "
        "<a href='https://srec.ac.in/academics/eligibility' target='_blank'>srec.ac.in/academics/eligibility</a>"
    ),
    'fees': (
        "💰 For fee details and payment, visit the official page: "
        "<a href='https://srec.ac.in/service/tuitionfees' target='_blank'>Fee Payment Portal</a>\n"
        "Generally: UG ~₹1.75L/year, PG ~₹60K/year, MBA ~₹41-60K/year (approximate figures)."
    ),
    'international': (
        "🌍 SREC accepts international students too! For details: "
        "<a href='https://srec.ac.in/academics/international_admission' target='_blank'>International Admissions</a>"
    ),

    # === PLACEMENTS ===
    'placement': (
        "💼 SREC has an excellent placement record — around <b>82% annual campus placement rate</b>! "
        "Top recruiters include: Infosys, Wipro, CTS, Accenture, Tech Mahindra, L&T, Saint Gobain, "
        "Sanmar Group, Murugappa Group and many more.\n\n"
        "Placement cell contact: <a href='https://srec.ac.in/placement/contact' target='_blank'>Placement Contact</a>"
    ),
    'recruiters': (
        "🏢 Top companies that recruit from SREC: Infosys, Wipro, CTS (Cognizant), Accenture, "
        "Tech Mahindra, L&T, Saint Gobain, Sanmar Group, Murugappa Group, Ford India, TVS, "
        "Ashok Leyland, TAFE, Mahindra & Mahindra and many more!\n"
        "See more: <a href='https://srec.ac.in/placement/recruiters' target='_blank'>All Recruiters</a>"
    ),
    'salary': "For salary package details, I'd suggest checking the placement office directly. You can contact them at <a href='https://srec.ac.in/placement/contact' target='_blank'>this page</a>.",
    'internship': (
        "🏭 Internships are a part of the B.E/B.Tech curriculum at SREC! Students intern with companies like "
        "Pricol Technologies, L&T, IIT Madras Health Innovation Park, Paxterra Solutions, Ashok Leyland, "
        "TAFE, TVS, Ford India, and Mahindra & Mahindra for 3–6 months."
    ),

    # === FACILITIES ===
    'library': (
        "📖 SREC's Central Library is massive — 35,172 sq.ft with seating for 100 people! "
        "It has 70,737 books covering 27,651 titles, plus digital resources like Scopus and ProQuest.\n"
        "More info: <a href='https://srec.ac.in/facilities/library' target='_blank'>Central Library</a>"
    ),
    'hostel': (
        "🏠 SREC has separate hostels for boys and girls with great facilities — internet, power backup, "
        "water supply, and health support. Comfortable stay for outstation students!\n"
        "Details: <a href='https://srec.ac.in/facilities/hostel' target='_blank'>Hostel Info</a>"
    ),
    'transport': (
        "🚌 SREC provides college buses covering various routes for students and staff.\n"
        "Check routes: <a href='https://srec.ac.in/facilities/transport' target='_blank'>Transport Details</a>"
    ),
    'healthcare': (
        "🏥 SREC has an on-campus health centre for students. "
        "Details: <a href='https://srec.ac.in/facilities/healthcare' target='_blank'>Healthcare Facility</a>"
    ),
    'wifi': "📶 SREC has campus-wide Wi-Fi connectivity for all students and staff!",
    'atm': "🏧 There's a South Indian Bank counter and ATM right on the SREC campus! Convenient, right? 😊",
    'sports': (
        "⚽ SREC has great sports facilities — basketball, volleyball, cricket, soccer, indoor games and more!\n"
        "Check: <a href='https://srec.ac.in/beyondclassrooms/sports' target='_blank'>Sports at SREC</a>"
    ),
    'infrastructure': (
        "🏗️ SREC has state-of-the-art infrastructure including modern labs, an auditorium, "
        "cafeteria, ATM, hostel, sports facilities and more.\n"
        "See: <a href='https://srec.ac.in/facilities' target='_blank'>Campus Infrastructure</a>"
    ),
    'gpu': (
        "💻 SREC has a GPU Education Centre powered by NVIDIA, Bangalore — for CUDA and Parallel Computing. Super cool! 🔥\n"
        "Details: <a href='https://srec.ac.in/gec' target='_blank'>GPU Education Center</a>"
    ),
    'cafeteria': "🍽️ Yes, SREC has a cafeteria and canteen on campus for students and staff!",

    # === CLUBS & ACTIVITIES ===
    'clubs': (
        "🎉 SREC has lots of student clubs and activities:\n"
        "• NCC, NSS, CSI\n"
        "• AI Student Club\n"
        "• Salesforce Trailhead\n"
        "• Yoga & Meditation\n"
        "• Tamil Mandram\n"
        "• Sports teams\n"
        "• SREC-HTIC (IIT-M) Wearable Club\n\n"
        "Check them out: <a href='https://srec.ac.in/beyondclassrooms/clubs' target='_blank'>All Clubs</a>"
    ),
    'ncc': "🎖️ SREC has an active NCC unit! Learn more: <a href='https://srec.ac.in/beyondclassrooms/ncc' target='_blank'>NCC at SREC</a>",
    'nss': "🤝 SREC has an NSS (National Service Scheme) unit actively involved in community service: <a href='https://srec.ac.in/beyondclassrooms/nss' target='_blank'>NSS at SREC</a>",
    'csi': "💻 SREC has a CSI (Computer Society of India) student branch: <a href='https://srec.ac.in/beyondclassrooms/csi' target='_blank'>CSI at SREC</a>",
    'ai club': "🤖 SREC has an AI Student Club! Check it out: <a href='https://srec.ac.in/ai/' target='_blank'>AI Club</a>",
    'yoga': "🧘 SREC promotes wellness with a Yoga & Meditation program! <a href='https://srec.ac.in/beyondclassrooms/yoga' target='_blank'>Yoga at SREC</a>",

    # === RESEARCH & INNOVATION ===
    'research': (
        "🔬 SREC has a strong research culture with average annual funding of ₹3.4 crore from agencies like "
        "AICTE, DST, CSIR, DRDO and more! There are also MoUs with IIT Madras, IISc, and international universities.\n"
        "More: <a href='https://srec.ac.in/rd/researchcommittee' target='_blank'>Research at SREC</a>"
    ),
    'incubation': (
        "🚀 SREC has the SREC SPARK Incubation Foundation to support budding entrepreneurs!\n"
        "Details: <a href='https://srec.ac.in/incubation' target='_blank'>Incubation Center</a>"
    ),
    'innovation': (
        "💡 SREC has a Centre for Collaborative Innovation (CoIN), MoE IIC, and Industry Institute "
        "Interface Cell (IIIC) to promote innovation among students.\n"
        "CoIN: <a href='https://srec.ac.in/coin' target='_blank'>CoIN</a> | "
        "IIIC: <a href='https://srec.ac.in/iiic' target='_blank'>IIIC</a>"
    ),
    'patent': "📜 SREC has generated patents through its research activities. Details: <a href='https://srec.ac.in/rd/patentgenerated' target='_blank'>Patent Info</a>",

    # === INDUSTRY ===
    'industry': (
        "🤝 SREC collaborates with many industries! MoUs with Robert Bosch, L&T, Siemens, GE, "
        "Texas Instruments, Cisco, Pricol, Tech Mahindra, IIT Madras and many international universities.\n"
        "See: <a href='https://srec.ac.in/beyondclassrooms/industry_collaborations' target='_blank'>Industry Collaborations</a>"
    ),
    'mou': (
        "📑 SREC has signed MoUs with major companies and institutions: Robert Bosch, L&T, Cameron, "
        "Siemens, GE, Texas Instruments, Cisco, IIT Madras, IISc Bangalore, and international universities "
        "in Australia, South Africa, Korea, and Spain!"
    ),
    'labs': (
        "🔬 Industry-sponsored labs at SREC include:\n"
        "• Altran Centre for Innovation\n"
        "• GE Centre for Innovation & Research\n"
        "• SIEMENS Authorized Training Centre (PLM)\n"
        "• Intel Intelligent Systems Lab\n"
        "• Texas Instruments Embedded Systems Lab\n"
        "• GPU Education Centre (NVIDIA)\n"
        "• Salzer Centre of Excellence (Power Systems)\n"
        "...and more!"
    ),

    # === EVENTS & NEWS ===
    'events': (
        "🎊 For upcoming events, check: <a href='https://srec.ac.in/events' target='_blank'>srec.ac.in/events</a>\n"
        "You can also see events right here on the SREC Dashboard above! 👆"
    ),
    'news': "📰 Latest news: <a href='https://srec.ac.in/news' target='_blank'>srec.ac.in/news</a>",
    'gallery': "📸 Photo Gallery: <a href='https://srec.ac.in/gallery' target='_blank'>srec.ac.in/gallery</a>",
    'magazine': "📖 SREC Magazine: <a href='https://srec.ac.in/magazine' target='_blank'>srec.ac.in/magazine</a>",

    # === STATS ===
    'students': "👩‍🎓 SREC currently has 4,400+ students enrolled across all programmes!",
    'faculty': "👨‍🏫 SREC has 271+ faculty members, of whom 104 hold Ph.D degrees, with 105 pursuing Ph.D!",
    'alumni': "🎓 SREC has 18,700+ proud alumni working across the globe in top organizations!",
    'partners': "🤝 SREC has more than 2,350+ global partners — a huge network!",

    # === EXAM & COE ===
    'exam': (
        "📝 For exam-related info (timetables, results), check:\n"
        "COE: <a href='https://srec.ac.in/controllerofexaminations' target='_blank'>Controller of Examinations</a>\n"
        "Recent results are also posted on the SREC website news section!"
    ),
    'result': (
        "📊 For exam results, visit: <a href='https://srec.ac.in/news' target='_blank'>SREC News Page</a> "
        "or the Controller of Examinations: <a href='https://srec.ac.in/controllerofexaminations' target='_blank'>COE</a>"
    ),
    'timetable': (
        "📅 Exam timetables are published on the SREC news page: "
        "<a href='https://srec.ac.in/news' target='_blank'>srec.ac.in/news</a>"
    ),

    # === ANTI RAGGING & POLICIES ===
    'ragging': (
        "🚫 SREC has a strict anti-ragging policy. Any form of ragging is completely prohibited. "
        "Details: <a href='https://srec.ac.in/aboutus/antiragging' target='_blank'>Anti-Ragging Policy</a>"
    ),
    'wec': (
        "👩 SREC has a Women Empowerment Cell (WEC) / POSH committee for women's safety and empowerment.\n"
        "Details: <a href='https://srec.ac.in/facilities/wec' target='_blank'>WEC at SREC</a>"
    ),
}

# =====================================================================
# QUESTION PAPERS
# =====================================================================
SUBJECTS = {
    'MAD': 'https://drive.google.com/drive/folders/1fTqb8Lx_RVyWyEusfjvYMk8UkD7A95Sm',
    'BEEE': 'https://drive.google.com/drive/folders/1x8xJQ1DoBg0X8mBvgm_Ybo2Iy7o9oDUY',
    'SENSORS': 'https://drive.google.com/drive/folders/1DGEgyiTZQy9e_Ez80dg3aHxO9qdc4tJG'
}

def format_qp_links(subject):
    link = SUBJECTS.get(subject.upper())
    if not link:
        return "⚠️ Hmm, I don't have that subject yet! Available right now: " + ", ".join(SUBJECTS.keys()) + ". More subjects will be added soon 😊"
    return f"📄 Here are the question papers for <b>{subject.upper()}</b>: <a href='{link}' target='_blank'>Click to Open on Google Drive</a> 🎉"

# =====================================================================
# EMOTION DETECTION
# =====================================================================
EMOTION_KEYWORDS = {
    'stressed': ['stressed', 'stress', 'tired', 'overwhelmed', "can't handle", 'burnt out', 'burnout', 'exhausted', 'pressure'],
    'sad': ['sad', 'depressed', 'hopeless', 'alone', 'failed', 'crying', 'unhappy', 'upset', 'miserable'],
    'anxious': ['anxious', 'anxiety', 'nervous', 'worried', 'panic', 'scared', 'fear', 'worried about exam'],
    'angry': ['angry', 'frustrated', 'annoyed', 'irritated', 'mad']
}

def get_emotion_response(msg):
    msg = msg.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(k in msg for k in keywords):
            responses = {
                'stressed': "Hey, I totally get it — college life can be super stressful sometimes 😔 But you're doing better than you think! Take a short break, talk to a friend or a trusted person. You've got this! 💪 If you need support, reach out to the college counsellor.",
                'sad': "I'm really sorry you're feeling this way 💙 You're definitely not alone — lots of students go through tough phases. Please talk to someone you trust — a friend, a faculty mentor, or a counsellor. Things will get better, I promise!",
                'anxious': "It's okay to feel nervous — it means you care! 😊 Take a deep breath, break your tasks into small steps, and tackle one thing at a time. You've overcome challenges before, and you'll get through this too! 💪",
                'angry': "I hear you! It's totally okay to feel frustrated sometimes 😤 Take a little break, do something you enjoy, and come back with fresh energy. Things will look better soon!"
            }
            return responses[emotion]
    return None

# =====================================================================
# SMART KEYWORD MATCHING
# =====================================================================
def find_knowledge_response(msg):
    """Try to find the best matching knowledge base entry for a message."""
    msg_lower = msg.lower()

    # Direct keyword matches (order matters - more specific first)
    keyword_map = [
        # Specific queries
        (['counselling code', 'counseling code', '2719'], 'counselling code'),
        (['anti ragging', 'ragging'], 'ragging'),
        (['women empowerment', 'wec', 'posh'], 'wec'),
        (['gpu center', 'gpu centre', 'nvidia'], 'gpu'),
        (['ai club', 'ai student club'], 'ai club'),
        (['incubation', 'spark', 'startup', 'entrepreneur'], 'incubation'),
        (['innovation', 'coin', 'iiic'], 'innovation'),
        (['mou', 'memorandum', 'collaboration'], 'mou'),
        (['industry lab', 'sponsored lab'], 'labs'),
        (['industry', 'industry partner'], 'industry'),
        (['patent'], 'patent'),
        (['research'], 'research'),
        (['internship', 'intern'], 'internship'),
        (['salary', 'package', 'ctc', 'lpa'], 'salary'),
        (['recruiter', 'company', 'companies'], 'recruiters'),
        (['placement', 'placed', 'campus drive', 'job'], 'placement'),
        (['fee', 'fees', 'tuition', 'cost'], 'fees'),
        (['international', 'foreign', 'nri'], 'international'),
        (['tnea', 'tancet', 'gate admission'], 'tnea'),
        (['admission', 'apply', 'application', 'join srec', 'how to join'], 'admission'),
        (['eligibility', 'cutoff', 'cut off', 'marks'], 'eligibility'),
        (['timetable', 'time table', 'exam schedule', 'schedule'], 'timetable'),
        (['result', 'results', 'grade', 'marks'], 'result'),
        (['exam', 'examination', 'semester exam', 'end sem'], 'exam'),
        (['coe', 'controller of exam'], 'exam'),
        (['ai data science', 'artificial intelligence', 'data science', 'btech ai'], 'ai'),
        (['robotics', 'automation'], 'robotics'),
        (['aeronautical', 'aero'], 'aeronautical'),
        (['biomedical', 'bme'], 'biomedical'),
        (['civil'], 'civil'),
        (['mechanical', 'mech'], 'mechanical'),
        (['eee', 'electrical'], 'eee'),
        (['ece', 'electronics communication'], 'ece'),
        (['it department', 'information technology'], 'it'),
        (['cse', 'computer science'], 'cse'),
        (['mba', 'management'], 'mba'),
        (['pg programme', 'pg program', 'postgraduate', 'm.tech', 'mtech', 'me programme'], 'pg'),
        (['ug programme', 'ug program', 'undergraduate', 'be programme', 'btech programme', 'b.e', 'b.tech'], 'ug'),
        (['department', 'departments'], 'departments'),
        (['course', 'courses', 'programme', 'programs'], 'courses'),
        (['yoga', 'meditation', 'wellness'], 'yoga'),
        (['ncc'], 'ncc'),
        (['nss', 'national service'], 'nss'),
        (['csi', 'computer society'], 'csi'),
        (['club', 'clubs', 'student activities', 'extracurricular'], 'clubs'),
        (['sports', 'basketball', 'cricket', 'football', 'volleyball', 'games'], 'sports'),
        (['atm', 'bank', 'south indian bank'], 'atm'),
        (['cafeteria', 'canteen', 'food', 'mess'], 'cafeteria'),
        (['wifi', 'wi-fi', 'internet', 'network'], 'wifi'),
        (['healthcare', 'medical', 'health center', 'health centre', 'doctor'], 'healthcare'),
        (['transport', 'bus', 'college bus', 'route'], 'transport'),
        (['hostel', 'accommodation', 'stay', 'room'], 'hostel'),
        (['library', 'books', 'digital resources', 'e-library', 'opac'], 'library'),
        (['infrastructure', 'facilities', 'campus facility'], 'infrastructure'),
        (['news', 'latest news', 'announcement'], 'news'),
        (['event', 'events', 'upcoming', 'fest'], 'events'),
        (['gallery', 'photos', 'pictures'], 'gallery'),
        (['magazine'], 'magazine'),
        (['alumni', 'old students', 'alumnus'], 'alumni'),
        (['how many students', 'student count', 'total students', 'strength'], 'students'),
        (['faculty', 'professor', 'staff', 'teacher'], 'faculty'),
        (['partners', 'global partners', 'partner'], 'partners'),
        (['nba accreditation', 'nba'], 'nba'),
        (['naac', 'a+ grade', 'accreditation'], 'naac'),
        (['ranking', 'rank', 'careers 360', 'rated', 'rating'], 'ranking'),
        (['vision'], 'vision'),
        (['mission'], 'mission'),
        (['affiliation', 'anna university', 'affiliated'], 'affiliation'),
        (['autonomous'], 'autonomous'),
        (['principal', 'head of college'], 'principal'),
        (['phone', 'mobile', 'hotline', 'call srec'], 'phone'),
        (['email', 'mail'], 'email'),
        (['website', 'official site', 'link'], 'website'),
        (['contact', 'reach srec', 'reach out'], 'contact'),
        (['where is', 'location', 'address', 'how to reach', 'directions', 'map'], 'location'),
        (['established', 'founded', 'when was srec', 'start'], 'established'),
        (['founder', 'trust', 'snr', 'managed by'], 'founder'),
        (['about srec', 'what is srec', 'tell me about srec', 'srec info'], 'about'),
        (['srec'], 'srec'),
    ]

    for keywords, key in keyword_map:
        if any(kw in msg_lower for kw in keywords):
            if key in SREC_KNOWLEDGE:
                return SREC_KNOWLEDGE[key]
    return None

# =====================================================================
# FIREBASE LOGIN HELPER
# =====================================================================
def verify_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload)
    return resp.json()

# =====================================================================
# SENTIMENT ANALYSIS (server-side)
# =====================================================================
def analyze_sentiment(text):
    text = text.lower()
    positive_words = ['great','amazing','love','happy','excited','awesome','fantastic','wonderful',
                      'good','best','excellent','proud','thank','congrats','congratulations','brilliant',
                      'yay','superb','outstanding','nice','perfect','beautiful','incredible','joy','enjoy']
    negative_words = ['sad','angry','hate','worst','bad','terrible','awful','horrible','annoyed',
                      'frustrated','fail','failed','disappointed','sucks','pathetic','boring','ugh',
                      'stressed','tired','depressed','worried','anxious','difficult','struggling']
    ps = sum(1 for w in positive_words if w in text)
    ns = sum(1 for w in negative_words if w in text)
    if ps > ns: return 'positive'
    if ns > ps: return 'negative'
    return 'neutral'

# =====================================================================
# ROUTES
# =====================================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        userid = request.form.get('userid')
        password = request.form.get('password')
        result = verify_password(userid, password)
        if 'idToken' in result:
            try:
                user = auth.get_user_by_email(userid)
                role = user.custom_claims.get('role', 'student') if user.custom_claims else 'student'
                session.permanent = True
                session.update({'user': user.uid, 'email': user.email, 'role': role})
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f"Login failed: {str(e)}"
        else:
            error = "Invalid email or password."
    return render_template('login.html', error=error)

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.get_json().get('email', '').strip()
    if not email.endswith('@srec.ac.in'):
        return jsonify({'success': False, 'msg': 'Invalid SREC email.'})
    try:
        # Firebase sends a password reset email automatically
        reset_link = auth.generate_password_reset_link(email)
        # In production, send via your email service (SMTP/SendGrid etc.)
        # For now Firebase handles it if you use the client SDK on frontend
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'msg': 'Email not found or error occurred.'})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Role access codes — keep these secret, change regularly
    ROLE_CODES = {
        'faculty': 'SREC@FAC2025',
        'admin':   'SREC@ADM2025'
    }
    if request.method == 'POST':
        userid      = request.form.get('userid', '').strip()
        password    = request.form.get('password', '')
        role        = request.form.get('role', 'student')
        access_code = request.form.get('access_code', '').strip()

        # Server-side email domain check
        if not userid.endswith('@srec.ac.in'):
            return render_template('signup.html', error='Only @srec.ac.in emails are allowed.')

        # Server-side password strength
        import re as _re
        if (len(password) < 8 or
            not _re.search(r'[A-Z]', password) or
            not _re.search(r'[0-9]', password) or
            not _re.search(r'[^A-Za-z0-9]', password)):
            return render_template('signup.html', error='Password must be 8+ chars with uppercase, number & special character.')

        # Server-side role access code check
        if role in ('faculty', 'admin'):
            if access_code != ROLE_CODES.get(role, ''):
                return render_template('signup.html', error='Invalid access code for selected role.')

        if not userid or not password:
            return render_template('signup.html', error='Email and password required.')

        try:
            user = auth.create_user(email=userid, password=password)
            auth.set_custom_user_claims(user.uid, {'role': role})
            # Store user profile in DB
            db.reference(f'/users/{user.uid}').set({
                'email': userid,
                'role': role,
                'joined': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'bio': ''
            })
            session.permanent = True
            session.update({'user': user.uid, 'email': user.email, 'role': role})
            return redirect(url_for('dashboard'))
        except Exception as e:
            err_msg = str(e)
            if 'EMAIL_EXISTS' in err_msg or 'already exists' in err_msg.lower():
                return render_template('signup.html', error='This email is already registered. Try logging in.')
            return render_template('signup.html', error=f'Signup failed: {err_msg}')

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    posts = db.reference('/posts').get() or {}
    events = db.reference('/events').get() or {}
    events_sorted = sorted(events.values(), key=lambda x: x.get('timestamp', ''))
    user_email = session.get('email')
    uid = session.get('user')
    user_posts_count = sum(1 for p in posts.values() if p.get('user') == user_email)
    user_data = db.reference(f'/users/{uid}').get() or {}
    user_bio = user_data.get('bio', '')
    return render_template('dashboard.html', user=user_email, role=session.get('role'),
                           posts=posts, post_count=user_posts_count, events=events_sorted,
                           user_bio=user_bio)

# =====================================================================
# CHATBOT ROUTE - FRIENDLY, SMART & RESPONSIVE
# =====================================================================
@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '').strip()
    if not user_msg:
        return jsonify({'response': "Hey! Send me a message and I'll help you out 😊"})

    msg_lower = user_msg.lower()

    # ------ GREETINGS ------
    greetings = ['hi', 'hello', 'hii', 'hiii', 'hey', 'heyy', 'yo', 'sup', 'what\'s up', 'howdy', 'greetings']
    if msg_lower in greetings or msg_lower.startswith('hi ') or msg_lower.startswith('hello ') or msg_lower.startswith('hey '):
        session.pop('awaiting_qp_subject', None)
        return jsonify({
            'response': (
                "Hey there! 👋 Welcome to SREC Bot — your friendly campus assistant! 😊<br><br>"
                "I can help you with:<br>"
                "📚 Courses & Departments<br>"
                "🎓 Admissions & Eligibility<br>"
                "💼 Placements & Internships<br>"
                "🏫 Campus Facilities<br>"
                "📄 Question Papers<br>"
                "🎉 Clubs & Events<br><br>"
                "Just ask me anything about SREC!"
            )
        })

    # ------ THANKS / BYE ------
    thanks = ['ok', 'okay', 'thanks', 'thank you', 'thx', 'ty', 'thank u', 'thankyou', 'tysm', 'tq']
    if msg_lower in thanks:
        session.pop('awaiting_qp_subject', None)
        return jsonify({'response': "You're welcome! 😊 Feel free to ask me anything else anytime!"})

    bye_words = ['bye', 'goodbye', 'see you', 'see ya', 'later', 'cya']
    if msg_lower in bye_words:
        session.pop('awaiting_qp_subject', None)
        return jsonify({'response': "Bye bye! 👋 Take care and all the best! Come back anytime 😊"})

    # ------ BOT IDENTITY ------
    identity_q = ['who are you', 'what are you', 'are you a bot', 'are you human', 'are you ai', 'your name', 'what is your name']
    if any(q in msg_lower for q in identity_q):
        return jsonify({'response': "I'm SREC Bot 🤖 — your friendly AI assistant for Sri Ramakrishna Engineering College! I'm here to help you with anything about SREC. Ask away! 😊"})

    # ------ EMOTION DETECTION ------
    emotion_response = get_emotion_response(user_msg)
    if emotion_response:
        return jsonify({'response': emotion_response})

    # ------ QUESTION PAPER INTENT ------
    qp_triggers = ['question paper', 'previous year', 'pyq', 'past paper', 'old question', 'model paper', 'previous question']
    if any(t in msg_lower for t in qp_triggers):
        session['awaiting_qp_subject'] = True
        if 'user' not in session:
            session.pop('awaiting_qp_subject', None)
            return jsonify({'response': "Oops! You need to be logged in to access question papers 🔒 Please login first!"})
        if session.get('role') not in ['student', 'faculty', 'admin']:
            session.pop('awaiting_qp_subject', None)
            return jsonify({'response': "Sorry! Question papers are only available for SREC students and faculty ❌"})
        return jsonify({'response': "Sure! 📚 Which subject's question papers do you need?<br>Available subjects: <b>MAD, BEEE, SENSORS</b><br>Just type the subject name!"})

    # ------ SUBJECT HANDLING ------
    if session.get('awaiting_qp_subject'):
        if 'user' not in session:
            session.pop('awaiting_qp_subject', None)
            return jsonify({'response': "Please login to access question papers 🔒"})
        if session.get('role') not in ['student', 'faculty', 'admin']:
            session.pop('awaiting_qp_subject', None)
            return jsonify({'response': "Access restricted ❌ Only students and faculty can access question papers."})
        for subject in SUBJECTS.keys():
            if msg_lower == subject.lower() or subject.lower() in msg_lower:
                session.pop('awaiting_qp_subject', None)
                return jsonify({'response': format_qp_links(subject)})
        return jsonify({'response': "Hmm, I didn't catch that subject 🤔 Please type one of these: <b>MAD, BEEE, SENSORS</b>"})

    # ------ KNOWLEDGE BASE MATCH ------
    kb_response = find_knowledge_response(user_msg)
    if kb_response:
        return jsonify({'response': kb_response})

    # ------ HELP MENU ------
    help_triggers = ['help', 'what can you do', 'options', 'menu', 'what do you know']
    if any(t in msg_lower for t in help_triggers):
        return jsonify({
            'response': (
                "Here's what I can help you with! 😊<br><br>"
                "🏫 <b>About SREC</b> — history, accreditation, rankings<br>"
                "📚 <b>Courses</b> — UG, PG, MBA programmes<br>"
                "📝 <b>Admissions</b> — TNEA, eligibility, fees<br>"
                "💼 <b>Placements</b> — recruiters, placement stats<br>"
                "🏠 <b>Facilities</b> — hostel, library, transport, WiFi<br>"
                "🎉 <b>Clubs</b> — NCC, NSS, AI Club, Sports<br>"
                "🔬 <b>Research</b> — incubation, innovation, MoUs<br>"
                "📄 <b>Question Papers</b> — past exam papers<br>"
                "📞 <b>Contact</b> — phone, email, location<br><br>"
                "Just type your question naturally — I'll do my best! 🤖"
            )
        })

    # ------ DEFAULT (friendly fallback) ------
    return jsonify({
        'response': (
            "Hmm, I'm not quite sure about that one! 🤔<br>"
            "I know a lot about SREC — try asking me about <b>courses, admissions, placements, "
            "facilities, clubs, or question papers</b>!<br>"
            "Or type <b>'help'</b> to see everything I can do 😊"
        )
    })

@app.route('/widget')
def widget(): return render_template('chat_widget.html')

# =====================================================================
# POSTS & SOCIAL
# =====================================================================

@app.route('/get_notifications')
def get_notifications():
    if 'user' not in session:
        return jsonify({'notifications': []})
    current_user_email = session.get('email', '')
    try:
        posts_data = db.reference('/posts').get() or {}
        notifs = []
        for post_id, post in posts_data.items():
            if post.get('user') != current_user_email:
                continue
            post_content = post.get('content', '')
            post_preview = (post_content[:40] + '...') if len(post_content) > 40 else post_content
            # Like notifications
            likes = post.get('likes', {})
            for uid, liker_email in likes.items():
                if liker_email == current_user_email:
                    continue
                notifs.append({
                    'key':          f"like_{post_id}_{uid}",
                    'type':         'like',
                    'by':           liker_email,
                    'post_preview': post_preview,
                    'timestamp':    post.get('timestamp', '')
                })
            # Comment notifications
            comments = post.get('comments', [])
            comment_list = list(comments.values()) if isinstance(comments, dict) else (comments if isinstance(comments, list) else [])
            for idx, c in enumerate(comment_list):
                commenter = c.get('user', '')
                if commenter == current_user_email:
                    continue
                notifs.append({
                    'key':       f"comment_{post_id}_{idx}_{commenter}",
                    'type':      'comment',
                    'by':        commenter,
                    'comment':   c.get('comment', ''),
                    'timestamp': c.get('timestamp', post.get('timestamp', ''))
                })
        notifs.reverse()
        return jsonify({'notifications': notifs[:20]})
    except Exception as e:
        return jsonify({'notifications': [], 'error': str(e)})


@app.route('/add_post', methods=['POST'])
def add_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    image = data.get('image', None)  # base64 image from frontend
    if not content: return jsonify({'success': False}), 400
    sentiment = analyze_sentiment(content)
    post_id = str(uuid.uuid4())
    anonymous = data.get('anonymous', False)
    tags = data.get('tags', [])
    post_data = {
        'user': 'Anonymous' if anonymous else session.get('email'),
        'real_user': session.get('email'),
        'anonymous': anonymous,
        'tags': tags, 'content': content,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'likes': {}, 'comments': [],
        'sentiment': sentiment, 'pinned': False
    }
    if image and len(image) < 10 * 1024 * 1024:  # 10MB base64 limit
        image_url = upload_to_cloudinary(image)
        if image_url:
            post_data['image'] = image_url
    db.reference('/posts').child(post_id).set(post_data)
    return jsonify({'success': True, 'post_id': post_id})

@app.route('/like_post', methods=['POST'])
def like_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    post_id = request.get_json().get('post_id')
    ref = db.reference(f'/posts/{post_id}/likes')
    likes = ref.get() or {}
    uid = session.get('user')
    if uid in likes: likes.pop(uid)
    else: likes[uid] = session.get('email')
    ref.set(likes)
    return jsonify({'success': True, 'likes': len(likes)})

@app.route('/comment_post', methods=['POST'])
def comment_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json() or {}
    post_id, comment = data.get('post_id'), data.get('comment', '').strip()
    ref = db.reference(f'/posts/{post_id}/comments')
    comments = ref.get() or []
    comments.append({'user': session.get('email'), 'comment': comment,
                     'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')})
    ref.set(comments)
    return jsonify({'success': True})

@app.route('/delete_post', methods=['POST'])
def delete_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    post_id = request.get_json().get('post_id')
    ref = db.reference(f'/posts/{post_id}')
    post = ref.get()
    if post and (post.get('user') == session.get('email') or session.get('role') == 'admin'):
        ref.delete()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403

@app.route('/edit_post', methods=['POST'])
def edit_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json() or {}
    post_id = data.get('post_id')
    new_content = data.get('content', '').strip()
    if not new_content: return jsonify({'success': False, 'msg': 'Content cannot be empty'})
    ref = db.reference(f'/posts/{post_id}')
    post = ref.get()
    if post and post.get('user') == session.get('email'):
        sentiment = analyze_sentiment(new_content)
        ref.update({'content': new_content, 'edited': True, 'sentiment': sentiment})
        return jsonify({'success': True})
    return jsonify({'success': False, 'msg': 'Unauthorized'}), 403

@app.route('/pin_post', methods=['POST'])
def pin_post():
    if session.get('role') != 'admin': return jsonify({'success': False}), 403
    post_id = request.get_json().get('post_id')
    ref = db.reference(f'/posts/{post_id}')
    post = ref.get()
    if post:
        pinned = not post.get('pinned', False)
        ref.update({'pinned': pinned})
        return jsonify({'success': True, 'pinned': pinned})
    return jsonify({'success': False}), 404

@app.route('/save_bio', methods=['POST'])
def save_bio():
    if 'user' not in session: return jsonify({'success': False}), 401
    bio = request.get_json().get('bio', '').strip()
    uid = session.get('user')
    db.reference(f'/users/{uid}').update({'bio': bio})
    return jsonify({'success': True})

# =====================================================================
# EVENTS (Admin Only)
# =====================================================================
@app.route('/add_event', methods=['POST'])
def add_event():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'msg': 'Unauthorized'}), 403
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    desc = data.get('desc', '').strip()
    dt = data.get('datetime', '')
    venue = data.get('venue', '').strip()
    if not title:
        return jsonify({'success': False, 'msg': 'Title required'}), 400
    event_id = str(uuid.uuid4())
    db.reference('/events').child(event_id).set({
        'id': event_id, 'title': title, 'desc': desc,
        'datetime': dt, 'venue': venue,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    return jsonify({'success': True})

@app.route('/edit_event', methods=['POST'])
def edit_event():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'msg': 'Unauthorized'}), 403
    data = request.get_json() or {}
    event_id = data.get('event_id')
    if not event_id:
        return jsonify({'success': False, 'msg': 'Event ID required'}), 400
    ref = db.reference(f'/events/{event_id}')
    ref.update({
        'title': data.get('title', ''),
        'desc': data.get('desc', ''),
        'datetime': data.get('datetime', ''),
        'venue': data.get('venue', '')
    })
    return jsonify({'success': True})

@app.route('/delete_event', methods=['POST'])
def delete_event():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'msg': 'Unauthorized'}), 403
    event_id = request.get_json().get('event_id')
    db.reference(f'/events/{event_id}').delete()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =====================================================================
# INIT & RUN
# =====================================================================
events_ref = db.reference('/events')
if not events_ref.get():
    events_ref.set({})

# =====================================================================
# INNOVATION ROUTES
# =====================================================================

@app.route('/enhance_post', methods=['POST'])
def enhance_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    text = request.get_json().get('text', '').strip()
    if not text: return jsonify({'enhanced': None})
    try:
        prompt = f"""You are helping a college student improve their social media post.
Enhance the following post to make it clearer, more engaging and friendly.
Keep the meaning exactly the same. Keep it under 500 characters. 
Return ONLY the improved post text, nothing else.

Original post: {text}"""
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        enhanced = response.text.strip().strip('"').strip("'")
        return jsonify({'enhanced': enhanced})
    except Exception as e:
        return jsonify({'enhanced': None, 'error': str(e)})


@app.route('/campus_pulse')
def campus_pulse():
    if 'user' not in session: return jsonify({'summary': 'Please log in.'})
    try:
        posts_data = db.reference('/posts').get() or {}
        today = datetime.now().strftime('%Y-%m-%d')
        today_posts = [p.get('content','') for p in posts_data.values()
                       if p.get('timestamp','').startswith(today) and p.get('content')][:30]
        if not today_posts:
            return jsonify({'summary': 'No posts today yet — be the first to share something! 🌅'})
        posts_text = '\n'.join(f'- {p}' for p in today_posts)
        prompt = f"""You are an AI analyst for a college campus social platform.
Based on these student posts from today, write a 2-sentence friendly campus mood summary.
Sound like a helpful news anchor, not a robot. Be warm and specific.

Today's posts:
{posts_text}

Write only the 2-sentence summary:"""
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return jsonify({'summary': response.text.strip()})
    except Exception as e:
        return jsonify({'summary': 'Campus pulse unavailable right now. Try again later!'})


@app.route('/study_room', methods=['GET', 'POST'])
def study_room():
    if 'user' not in session: return jsonify({'students': []})
    user_email = session.get('email','')
    uid = session.get('user','')
    ref = db.reference('/study_room')
    if request.method == 'POST':
        data = request.get_json() or {}
        action = data.get('action')
        subject = data.get('subject', 'General')
        if action == 'join':
            ref.child(uid).set({
                'email': user_email,
                'subject': subject,
                'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        elif action == 'leave':
            ref.child(uid).delete()
        return jsonify({'success': True})
    # GET — return all current studying users
    students_raw = ref.get() or {}
    students = []
    now = datetime.now()
    for suid, s in students_raw.items():
        # Auto-expire after 4 hours
        try:
            joined = datetime.strptime(s.get('joined_at',''), '%Y-%m-%d %H:%M:%S')
            diff_mins = int((now - joined).total_seconds() / 60)
            if diff_mins > 240:
                ref.child(suid).delete()
                continue
            if diff_mins < 1:   dur = 'just joined'
            elif diff_mins < 60: dur = f'{diff_mins} min ago'
            else:               dur = f'{diff_mins//60}h {diff_mins%60}m'
        except:
            dur = ''
        students.append({'email': s.get('email',''), 'subject': s.get('subject',''), 'duration': dur})
    return jsonify({'students': students})


@app.route('/react_post', methods=['POST'])
def react_post():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json() or {}
    post_id = data.get('post_id')
    reaction = data.get('reaction')
    uid = session.get('user','')
    user_email = session.get('email','')
    if not post_id or not reaction: return jsonify({'success': False})
    try:
        ref = db.reference(f'/posts/{post_id}/reactions/{reaction}')
        existing = ref.get() or {}
        if uid in existing:
            ref.child(uid).delete()  # Toggle off
        else:
            ref.child(uid).set(user_email)  # Toggle on
        all_reactions = db.reference(f'/posts/{post_id}/reactions').get() or {}
        return jsonify({'success': True, 'reactions': all_reactions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/get_reactions')
def get_reactions():
    if 'user' not in session: return jsonify({'reactions': {}})
    try:
        posts = db.reference('/posts').get() or {}
        result = {}
        for pid, post in posts.items():
            if post.get('reactions'):
                result[pid] = post['reactions']
        return jsonify({'reactions': result})
    except:
        return jsonify({'reactions': {}})


@app.route('/mood_checkin', methods=['POST'])
def mood_checkin():
    if 'user' not in session: return jsonify({'success': False}), 401
    mood = request.get_json().get('mood', 'okay')
    uid = session.get('user','')
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        db.reference(f'/mood_checkins/{today}/{uid}').set(mood)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})


@app.route('/get_users')
def get_users():
    if 'user' not in session: return jsonify({'users': []})
    try:
        users_data = db.reference('/users').get() or {}
        current_email = session.get('email','')
        users = [v.get('email','').split('@')[0]
                 for v in users_data.values()
                 if v.get('email') and v.get('email') != current_email]
        return jsonify({'users': users})
    except:
        return jsonify({'users': []})


if __name__ == '__main__':
    app.run(debug=True)