import os
import requests
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db, auth
import re


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

# ------------------ Groq AI Setup ------------------
# GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_KEY_HERE")
GROQ_API_KEY="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"

from groq import Groq
groq_client = Groq(api_key=GROQ_API_KEY)

def gemini_generate(prompt):
    """Call Groq LLM. Returns object with .text like Gemini did."""
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2048,
    )
    class _R:
        def __init__(self, t): self.text = t
    return _R(completion.choices[0].message.content)

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
        result = cloudinary.uploader.upload(
            base64_data,
            folder="srec_campusconnect",
            resource_type="image",
            transformation=[
                {"width": 900, "crop": "limit"},
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ]
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

# =====================================================================
# RICH SREC KNOWLEDGE BASE — Verified from AICTE Disclosure 2024-25
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
        "Anti-Ragging Committee is chaired by Principal Dr. A. Soundarrajan (99420 69911). "
        "Nodal Officer: Dr. J. Selvakumar, Professor/CSE (99942 66855). "
        "Details: <a href='https://srec.ac.in/aboutus/antiragging' target='_blank'>Anti-Ragging Policy</a>"
    ),
    'wec': (
        "👩 SREC has a Women Empowerment Cell (WEC) / POSH committee for women's safety and empowerment.\n"
        "Details: <a href='https://srec.ac.in/facilities/wec' target='_blank'>WEC at SREC</a>"
    ),

    # ===================================================================
    # FACULTY & LEADERSHIP — Verified from AICTE Disclosure 2024-25
    # ===================================================================

    # PRINCIPAL
    'principal': (
        "👨‍💼 <b>Principal of SREC: Dr. A. Soundarrajan</b><br>"
        "📧 Email: <a href='mailto:principal@srec.ac.in'>principal@srec.ac.in</a><br>"
        "📞 Mobile: 99420 69911<br>"
        "He also serves as Chairperson of the Academic Council and the Anti-Ragging Committee.<br>"
        "More: <a href='https://srec.ac.in/aboutus/principal' target='_blank'>srec.ac.in/aboutus/principal</a>"
    ),

    # DIRECTOR ACADEMICS
    'director': (
        "🎓 <b>Director (Academics) of SREC: Dr. N. R. Alamelu</b><br>"
        "She serves as Director (Academics) for the entire Sri Ramakrishna Group of Institutions under SNR Sons Charitable Trust.<br>"
        "She is also the Managing Trustee of SREC Alumni Association Charitable Trust and a member of the Governing Council and Academic Council."
    ),
    'director academics': (
        "🎓 <b>Director (Academics): Dr. N. R. Alamelu</b><br>"
        "She heads academics for Sri Ramakrishna Group of Institutions and is a Governing Council & Academic Council member at SREC."
    ),

    # GOVERNING COUNCIL
    'chairman': (
        "🏛️ <b>Chairman (Governing Council): Sri. R. Sundar</b><br>"
        "Managing Trustee, S.N.R Sons Charitable Trust, Coimbatore – 641 044."
    ),
    'vice chairman': (
        "🏛️ <b>Vice Chairman (Governing Council): Sri. S. Narendran</b><br>"
        "Joint Managing Trustee, S.N.R Sons Charitable Trust, Coimbatore."
    ),
    'governing council': (
        "🏛️ <b>SREC Governing Council (2024-25):</b><br>"
        "• <b>Chairman:</b> Sri. R. Sundar (Managing Trustee, SNR Sons Charitable Trust)<br>"
        "• <b>Vice Chairman:</b> Sri. S. Narendran (Joint Managing Trustee)<br>"
        "• <b>Director (Academics):</b> Dr. N. R. Alamelu<br>"
        "• <b>Principal / Secretary:</b> Dr. A. Soundarrajan<br>"
        "• <b>HOD Mech (Internal):</b> Dr. P. Karuppuswamy<br>"
        "• <b>HOD Nanoscience (Internal):</b> Dr. P. Moorthi<br>"
        "Governing Council meets twice a year. Last meetings: 27 GC on 09.04.2024, 28 GC on 27.12.2024."
    ),

    # ACADEMIC COUNCIL
    'academic council': (
        "📋 <b>SREC Academic Council 2024-25:</b><br>"
        "Chairperson: Dr. A. Soundarrajan (Principal)<br>"
        "Dept. Chairpersons in the Council:<br>"
        "• CSE: Dr. M. S. Geetha Devasena | IT: Dr. M. Senthamil Selvi<br>"
        "• ECE: Dr. M. Jagadeeswari | EEE: Dr. S. Allirani<br>"
        "• Mech: Dr. P. Karuppuswamy | Aero: Dr. P. Chandramohan<br>"
        "• BME: Dr. B. Sharmila | Civil: Dr. E. Sarojini<br>"
        "• EIE: Dr. K. Srinivasan | AI&DS: Dr. V. Karpagam<br>"
        "• MBA: Dr. R. Mary Metilda | Nano: Dr. P. Moorthi<br>"
        "• Maths: Dr. A. Sekar | Chemistry: Dr. L. Ragunath<br>"
        "• English: Dr. Vichitra Sivaji | Physics: Dr. K. Uthayarani<br>"
        "Last meeting: 21st meeting on 13.12.2024"
    ),
    'academic coordinator': (
        "📋 The Academic leadership at SREC is structured as follows:<br><br>"
        "🎓 <b>Director (Academics):</b> Dr. N. R. Alamelu<br>"
        "👨‍💼 <b>Principal / Academic Council Chair:</b> Dr. A. Soundarrajan<br><br>"
        "Each department has a <b>Chairperson</b> who oversees academics for that department. "
        "For SREC's academic calendar and regulations, visit: "
        "<a href='https://srec.ac.in/academics' target='_blank'>srec.ac.in/academics</a>"
    ),

    # =====================  HODs  =====================
    'hod cse': (
        "💻 <b>HOD of CSE (Computer Science & Engineering):</b><br>"
        "👩‍💼 <b>Dr. M. S. GEETHA DEVASENA</b><br>"
        "Designation: Professor & Head, CSE<br>"
        "Qualification: M.E (CSE), Ph.D | Specialization: Image Processing<br>"
        "Also serves as Controller of Examinations (CoE) at SREC.<br>"
        "More: <a href='https://srec.ac.in/department/cse/faculty' target='_blank'>CSE Faculty</a>"
    ),
    'hod it': (
        "💡 <b>HOD of IT (Information Technology):</b><br>"
        "👩‍💼 <b>Dr. N. Susila</b><br>"
        "Designation: Professor & Head, IT<br>"
        "Qualification: B.E (CSE), M.E (CSE), Ph.D | Experience: 24+ years<br>"
        "📧 susila.n@srec.ac.in<br>"
        "More: <a href='https://srec.ac.in/department/it/faculty' target='_blank'>IT Faculty</a>"
    ),
    'hod ece': (
        "📡 <b>HOD of ECE (Electronics & Communication Engineering):</b><br>"
        "👩‍💼 <b>Dr. M. Jagadeeswari</b><br>"
        "Designation: Professor & Head, ECE<br>"
        "📞 94863 55965<br>"
        "More: <a href='https://srec.ac.in/department/ece/faculty' target='_blank'>ECE Faculty</a>"
    ),
    'hod eee': (
        "⚡ <b>HOD of EEE (Electrical & Electronics Engineering):</b><br>"
        "👩‍💼 <b>Dr. S. Allirani</b><br>"
        "Designation: Associate Professor & Chairperson/EEE (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/eee' target='_blank'>EEE Department</a>"
    ),
    'hod mech': (
        "🔧 <b>HOD of Mechanical Engineering:</b><br>"
        "👨‍💼 <b>Dr. P. Karuppuswamy</b><br>"
        "Designation: Professor & Head, Mechanical Engineering<br>"
        "Member of both Governing Council and Academic Council.<br>"
        "More: <a href='https://srec.ac.in/department/mech' target='_blank'>Mech Department</a>"
    ),
    'hod aero': (
        "✈️ <b>HOD of Aeronautical Engineering:</b><br>"
        "👨‍💼 <b>Dr. P. Chandramohan</b><br>"
        "Designation: Professor & Chairperson/AERO (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/aero' target='_blank'>Aero Department</a>"
    ),
    'hod bme': (
        "🏥 <b>HOD of Biomedical Engineering:</b><br>"
        "👩‍💼 <b>Dr. B. Sharmila</b><br>"
        "Designation: Chairperson/BME (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/bme' target='_blank'>BME Department</a>"
    ),
    'hod eie': (
        "🔌 <b>HOD of Electronics & Instrumentation Engineering:</b><br>"
        "👨‍💼 <b>Dr. K. Srinivasan</b><br>"
        "Designation: Professor & Chairperson/EIE (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/eie' target='_blank'>EIE Department</a>"
    ),
    'hod civil': (
        "🏗️ <b>HOD of Civil Engineering:</b><br>"
        "👩‍💼 <b>Dr. E. Sarojini</b><br>"
        "Designation: Chairperson/CIVIL (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/civil' target='_blank'>Civil Department</a>"
    ),
    'hod aids': (
        "🤖 <b>HOD of AI & Data Science:</b><br>"
        "👩‍💼 <b>Dr. V. Karpagam</b><br>"
        "Designation: Chairperson/AI&DS (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/btech' target='_blank'>AI&DS Department</a>"
    ),
    'hod ra': (
        "🦾 <b>HOD of Robotics & Automation:</b><br>"
        "👨‍💼 <b>Dr. A. Murugarajan</b><br>"
        "Designation: Chairperson/RAE (Academic Council)<br>"
        "More: <a href='https://srec.ac.in/department/robotics' target='_blank'>R&A Department</a>"
    ),
    'hod mba': (
        "📊 <b>HOD of MBA:</b><br>"
        "👩‍💼 <b>Dr. R. Mary Metilda</b><br>"
        "Designation: Professor & Head, MBA<br>"
        "Also serves as Online Grievance Redressal Convener at SREC.<br>"
        "More: <a href='https://srec.ac.in/department/mba' target='_blank'>MBA Department</a>"
    ),
    'hod maths': (
        "🔢 <b>HOD of Mathematics:</b><br>"
        "👨‍💼 <b>Dr. A. Sekar</b><br>"
        "Designation: Professor & Head, Mathematics | Also Transport In-charge<br>"
        "📞 99652 26824"
    ),
    'hod chemistry': (
        "🧪 <b>HOD of Chemistry:</b><br>"
        "👨‍💼 <b>Dr. L. Raghunath</b><br>"
        "Designation: Professor & Head, Chemistry | Also Senior Deputy Warden (Men's Hostel 2)<br>"
        "📞 98944 02345"
    ),
    'hod physics': (
        "⚛️ <b>HOD of Physics:</b><br>"
        "👩‍💼 <b>Dr. K. Uthayarani</b><br>"
        "Designation: Professor & Head, Physics (Senior Faculty)<br>"
        "Also member of IQAC and Online Grievance Redressal Committee."
    ),
    'hod english': (
        "📝 <b>HOD of English:</b><br>"
        "👩‍💼 <b>Dr. Vichitra Sivaji</b><br>"
        "Designation: Head, English Department"
    ),
    'hod nano': (
        "🔬 <b>HOD of Nanoscience & Technology:</b><br>"
        "👨‍💼 <b>Dr. P. Moorthi</b><br>"
        "Designation: Professor & Head, Nanoscience and Technology<br>"
        "Member of Governing Council and Academic Council."
    ),
    'all hods': (
        "👥 <b>All Heads of Departments at SREC (2024-25):</b><br><br>"
        "• <b>CSE:</b> Dr. A. Grace Selvarani (also CoE)<br>"
        "• <b>IT:</b> Dr. N. Susila<br>"
        "• <b>ECE:</b> Dr. M. Jagadeeswari<br>"
        "• <b>EEE:</b> Dr. S. Allirani<br>"
        "• <b>Mechanical:</b> Dr. P. Karuppuswamy<br>"
        "• <b>Aeronautical:</b> Dr. P. Chandramohan<br>"
        "• <b>BME:</b> Dr. B. Sharmila<br>"
        "• <b>Civil:</b> Dr. E. Sarojini<br>"
        "• <b>EIE:</b> Dr. K. Srinivasan<br>"
        "• <b>AI & DS:</b> Dr. V. Karpagam<br>"
        "• <b>Robotics & Automation:</b> Dr. A. Murugarajan<br>"
        "• <b>MBA:</b> Dr. R. Mary Metilda<br>"
        "• <b>Nanoscience:</b> Dr. P. Moorthi<br>"
        "• <b>Maths:</b> Dr. A. Sekar<br>"
        "• <b>Chemistry:</b> Dr. L. Raghunath<br>"
        "• <b>Physics:</b> Dr. K. Uthayarani<br>"
        "• <b>English:</b> Dr. Vichitra Sivaji<br>"
        "• <b>Director (Academics):</b> Dr. N. R. Alamelu"
    ),

    # CONTROLLER OF EXAMINATIONS
    'coe': (
        "📋 <b>Controller of Examinations (CoE): Dr. A. Grace Selvarani</b><br>"
        "She is also Professor & Head of the CSE department.<br>"
        "For exam-related queries: <a href='https://srec.ac.in/controllerofexaminations' target='_blank'>COE Page</a>"
    ),
    'controller of examinations': (
        "📋 <b>Controller of Examinations (CoE): Dr. A. Grace Selvarani</b><br>"
        "She is also Professor & Head of the CSE department at SREC.<br>"
        "Exam info: <a href='https://srec.ac.in/controllerofexaminations' target='_blank'>COE Page</a>"
    ),

    # IQAC
    'iqac': (
        "🏆 <b>IQAC (Internal Quality Assurance Cell) at SREC</b><br>"
        "Key IQAC members include:<br>"
        "• Dr. M. Jagadeeswari (Prof & Head, ECE)<br>"
        "• Dr. K. Uthayarani (Prof & Head, Physics)<br>"
        "• Dr. N. Sathish Kumar (Professor, ECE & Head CCE)<br>"
        "• Dr. V. Rukkumani (Assoc. Professor, EIE)<br>"
        "More: <a href='https://srec.ac.in/iqac' target='_blank'>IQAC Page</a>"
    ),

    # CCE (Centre for Continuing Education)
    'cce': (
        "📚 <b>CCE (Centre for Continuing Education) Head: Dr. N. Sathish Kumar</b><br>"
        "Designation: Professor/ECE and Head, CCE<br>"
        "Also Organizing Secretary of the Governing Council."
    ),

    # KEY FACULTY
    'faculty count': (
        "👨‍🏫 SREC has <b>271+ faculty members</b> as of 2024-25.<br>"
        "• 104 faculty hold Ph.D degrees<br>"
        "• 105 are pursuing Ph.D<br>"
        "• Faculty-to-student ratio: approximately 1:20 to 1:30<br>"
        "Full list: <a href='https://srec.ac.in/department' target='_blank'>Department Pages</a>"
    ),
    'how many teachers': (
        "👨‍🏫 SREC has <b>271+ faculty members</b> (2024-25 data).<br>"
        "• 104 hold Ph.D | 105 are pursuing Ph.D<br>"
        "• Faculty-to-student ratio: ~1:20 to 1:30<br>"
        "The college also has a strong team of non-teaching and administrative staff."
    ),
    'how many students': (
        "👩‍🎓 SREC has <b>4,400+ students</b> enrolled across all programmes (2024-25).<br>"
        "• UG intake: 180 seats each in CSE, ECE; 90 in Mech, EEE, others<br>"
        "• Hostel capacity: 1,900 students across 4 hostel blocks<br>"
        "• Total alumni: 18,700+"
    ),

    # HOSTEL WARDENS
    'warden': (
        "🏠 <b>Hostel Wardens at SREC:</b><br>"
        "• <b>Men's Hostel 2 (Senior Deputy Warden):</b> Dr. L. Raghunath (Prof & Head, Chemistry) — 📞 98944 02345<br>"
        "• <b>Women's Hostel (Senior Deputy Warden):</b> Dr. R. Brindha (Asst. Prof, English) — 📞 97897 46897<br>"
        "• <b>Boys' Deputy Warden:</b> Mr. R. Rajesh<br>"
        "• <b>Boys' Deputy Warden:</b> Mr. M. Nagarajapandian<br>"
        "Hostel info: <a href='https://srec.ac.in/facilities/hostel' target='_blank'>Hostel Details</a>"
    ),

    # TRANSPORT IN-CHARGE
    'transport incharge': (
        "🚌 <b>Transport In-charge: Dr. A. Sekar</b><br>"
        "Designation: Professor & Head, Mathematics | 📞 99652 26824<br>"
        "Bus route info: <a href='https://srec.ac.in/facilities/transport' target='_blank'>Transport Details</a>"
    ),

    # PHYSICAL DIRECTOR
    'physical director': (
        "⚽ <b>Physical Director: Mr. S. Nithyanandan</b><br>"
        "📞 98421 17374<br>"
        "Sports facilities: <a href='https://srec.ac.in/beyondclassrooms/sports' target='_blank'>Sports at SREC</a>"
    ),

    # KEY PROFESSORS
    'selvakumar': (
        "👨‍💼 <b>Dr. J. Selvakumar</b> — Professor, CSE Department<br>"
        "Roles: Anti-Ragging Nodal Officer, IQAC Member, Academic Council Member<br>"
        "📞 99942 66855"
    ),
    'grace selvarani': (
        "👩‍💼 <b>Dr. A. Grace Selvarani</b> — Professor & Head, CSE + Controller of Examinations<br>"
        "Qualification: M.E (CSE), Ph.D | Specialization: Image Processing<br>"
        "Member of Academic Council and Online Grievance Committee<br>"
        "Recipient of <b>Best Faculty Award 2017-18</b> from Cognizant (CTS)"
    ),
    'sathish kumar': (
        "👨‍💼 <b>Dr. N. Sathish Kumar</b> — Professor, ECE & Head of CCE (Centre for Continuing Education)<br>"
        "Organizing Secretary of the Governing Council | IQAC Member"
    ),

    # TIMINGS
    'office hours': (
        "🕗 <b>SREC Office Hours:</b> 8:30 AM to 5:00 PM<br>"
        "📚 <b>Academic Hours:</b> 8:45 AM to 4:40 PM<br>"
        "📞 Phone: <a href='tel:04222460088'>0422-2460088</a>"
    ),
    'college timings': (
        "🕗 <b>SREC Timings:</b><br>"
        "• Office Hours: 8:30 AM – 5:00 PM<br>"
        "• Academic Hours: 8:45 AM – 4:40 PM<br>"
        "• 📞 0422-2460088 | 📠 0422-2461089"
    ),
    'fax': "📠 SREC Fax: 0422-2461089",
    'landline': "📞 SREC Phone: <a href='tel:04222460088'>0422-2460088</a>",

    # NIRF RANKING
    'nirf': (
        "🏆 <b>SREC NIRF Ranking 2025:</b> Ranked in the <b>151–200 band</b> in Engineering category nationally!<br>"
        "Previous: 151-200 in NIRF 2024 also. Consistently improving!<br>"
        "Also ranked <b>550 under B.Tech</b> by Collegedunia 2025."
    ),
    'ranking': (
        "🏅 <b>SREC Rankings (2024-25):</b><br>"
        "• <b>NIRF 2025:</b> 151-200 band (Engineering category)<br>"
        "• <b>Careers 360:</b> AAA rated — 'India's Best Engineering Institute 2024'<br>"
        "• <b>The Week:</b> Top 28 Best Engineering Colleges<br>"
        "• <b>Times of India:</b> Top 10 Engineering Colleges (region)"
    ),

    # PLACEMENTS (Updated NIRF 2024-25 data)
    'placement': (
        "💼 <b>SREC Placements 2024 (NIRF Data):</b><br>"
        "• <b>UG students placed:</b> 745 | <b>PG placed:</b> 34<br>"
        "• <b>UG Median Salary:</b> ₹4.80 LPA | <b>PG Median:</b> ₹5.00 LPA<br>"
        "• <b>Highest Package:</b> ₹28 LPA (CSE/IT/ECE)<br>"
        "• <b>Placement Rate:</b> ~86% (NIRF 2024)<br>"
        "• 78 UG + 3 PG students opted for higher studies<br>"
        "Top Recruiters: Zoho, Capgemini, Amazon, PayPal, Cognizant, DBS, TCS, Accenture, L&T<br>"
        "Contact: <a href='https://srec.ac.in/placement/contact' target='_blank'>Placement Cell</a>"
    ),
    'salary': (
        "💰 <b>SREC Salary Packages (2024 NIRF data):</b><br>"
        "• UG Median: ₹4.80 LPA | PG Median: ₹5.00 LPA<br>"
        "• Highest: ₹28 LPA (common in CSE, IT, ECE)<br>"
        "• Average: ~₹4 LPA across all branches"
    ),
    'recruiters': (
        "🏢 <b>Top Recruiters at SREC:</b><br>"
        "Zoho, Capgemini, Amazon, PayPal, Cognizant (CTS), DBS Bank, TCS, Infosys, "
        "Wipro, Accenture, Tech Mahindra, L&T, Saint Gobain, Sanmar Group, "
        "Inmovidu Technologies, Softtek, Dhyan Infotech, Ford India, TVS, Ashok Leyland, "
        "TAFE, Mahindra & Mahindra, Pricol, Murugappa Group and 100+ more!<br>"
        "MoUs signed with 100+ companies.<br>"
        "See all: <a href='https://srec.ac.in/placement/recruiters' target='_blank'>All Recruiters</a>"
    ),

    # CAMPUS DETAILS
    'campus': (
        "🏫 <b>SREC Campus Details:</b><br>"
        "• Area: 45–49 acres<br>"
        "• Location: Vattamalaipalayam, N.G.G.O Colony, Coimbatore – 641 022<br>"
        "• Nearest Railway Station: Coimbatore Junction (16 km)<br>"
        "• Nearest Airport: Coimbatore International Airport (16 km)<br>"
        "• 30 college buses for transport<br>"
        "• ATM, cafeteria, health centre, sports complex on campus"
    ),
    'area': "📐 SREC campus is spread across <b>45–49 acres</b> in Vattamalaipalayam, Coimbatore.",
    'distance': (
        "📍 SREC is about <b>16 km from Coimbatore Railway Station</b> and "
        "<b>16 km from Coimbatore International Airport</b>."
    ),

    # HOSTEL
    'hostel': (
        "🏠 <b>SREC Hostels:</b><br>"
        "• 4 hostel blocks total — 3 for boys, 1 for girls<br>"
        "• Total capacity: 1,900 students<br>"
        "• Facilities: Internet, power backup, 24hr water, health support<br>"
        "• 24-hour ambulance available on campus (connected to Sri Ramakrishna Hospital)<br>"
        "• Warden (Boys): Dr. L. Raghunath | Warden (Girls): Dr. R. Brindha<br>"
        "Details: <a href='https://srec.ac.in/facilities/hostel' target='_blank'>Hostel Info</a>"
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
    msg_lower = msg.lower()

    # ---------------------------------------------------------------
    # PRIORITY PASS 1 — HOD / Head of Department queries
    # Must come first so "hod cse" doesn't accidentally match generic 'cse' key
    # ---------------------------------------------------------------
    hod_patterns = [
        # CSE
        (['hod cse', 'head of cse', 'head cse', 'hod computer science',
          'who is hod cse', 'who is head of cse', 'hod of cse',
          'head of computer science', 'cse hod', 'cse head',
          'computer science hod', 'who heads cse'], 'hod cse'),
        # IT
        (['hod it', 'head of it', 'head it', 'hod information technology',
          'who is hod it', 'who is head of it', 'hod of it', 'it hod',
          'information technology hod', 'who heads it', 'it head',
          'head of information technology'], 'hod it'),
        # ECE
        (['hod ece', 'head of ece', 'head ece', 'hod electronics',
          'who is hod ece', 'who is head of ece', 'hod of ece', 'ece hod',
          'electronics hod', 'ece head', 'head of electronics',
          'who heads ece'], 'hod ece'),
        # EEE
        (['hod eee', 'head of eee', 'head eee', 'hod electrical',
          'who is hod eee', 'who is head of eee', 'hod of eee', 'eee hod',
          'electrical hod', 'eee head'], 'hod eee'),
        # MECH
        (['hod mech', 'head of mech', 'head mech', 'hod mechanical',
          'who is hod mech', 'who is head of mechanical', 'hod of mech',
          'mech hod', 'mechanical hod', 'mech head', 'mechanical head',
          'who heads mechanical'], 'hod mech'),
        # AERO
        (['hod aero', 'head of aero', 'hod aeronautical',
          'who is hod aero', 'who is head of aero', 'hod of aero',
          'aero hod', 'aeronautical hod', 'aero head', 'aeronautical head'], 'hod aero'),
        # BME
        (['hod bme', 'head of bme', 'hod biomedical',
          'who is hod bme', 'who is head of bme', 'hod of bme',
          'bme hod', 'biomedical hod', 'bme head', 'biomedical head'], 'hod bme'),
        # EIE
        (['hod eie', 'head of eie', 'hod instrumentation',
          'who is hod eie', 'hod of eie', 'eie hod', 'eie head',
          'instrumentation hod'], 'hod eie'),
        # CIVIL
        (['hod civil', 'head of civil', 'hod civil engineering',
          'who is hod civil', 'hod of civil', 'civil hod', 'civil head'], 'hod civil'),
        # AI&DS
        (['hod ai', 'head of ai', 'hod aids', 'hod ai&ds', 'hod data science',
          'who is hod ai', 'ai hod', 'aids hod', 'ai ds hod',
          'head of ai and data science', 'data science hod'], 'hod aids'),
        # RA
        (['hod robotics', 'head of robotics', 'hod ra', 'hod automation',
          'who is hod robotics', 'robotics hod', 'ra hod', 'automation hod'], 'hod ra'),
        # MBA
        (['hod mba', 'head of mba', 'hod management',
          'who is hod mba', 'mba hod', 'mba head', 'management hod'], 'hod mba'),
        # MATHS
        (['hod maths', 'hod math', 'head of maths', 'hod mathematics',
          'who is hod maths', 'maths hod', 'math hod', 'mathematics hod'], 'hod maths'),
        # CHEMISTRY
        (['hod chemistry', 'head of chemistry', 'hod chem',
          'who is hod chemistry', 'chemistry hod', 'chem hod'], 'hod chemistry'),
        # PHYSICS
        (['hod physics', 'head of physics',
          'who is hod physics', 'physics hod'], 'hod physics'),
        # ENGLISH
        (['hod english', 'head of english',
          'who is hod english', 'english hod'], 'hod english'),
        # NANO
        (['hod nano', 'head of nano', 'hod nanoscience',
          'nano hod', 'nanoscience hod'], 'hod nano'),
        # ALL HODs
        (['all hod', 'list of hod', 'all heads', 'list of heads',
          'hod list', 'all department heads', 'department heads',
          'who are the hods', 'names of hods'], 'all hods'),
    ]
    for keywords, key in hod_patterns:
        if any(kw in msg_lower for kw in keywords):
            if key in SREC_KNOWLEDGE:
                return SREC_KNOWLEDGE[key]

    # ---------------------------------------------------------------
    # PRIORITY PASS 2 — Faculty / staff role queries
    # ---------------------------------------------------------------
    role_patterns = [
        # Principal
        (['who is the principal', 'who is principal', 'name of principal',
          'principal name', 'principal of srec', 'who is dr soundarrajan',
          'soundarrajan', 'head of college', 'who runs srec'], 'principal'),
        # Director Academics
        (['director academics', 'director of academics', 'who is the director',
          'academic director', 'dr alamelu', 'n.r. alamelu', 'nr alamelu'], 'director academics'),
        # Academic Coordinator / Council
        (['academic coordinator', 'academic council', 'who coordinates academics',
          'coordinator academics', 'who is the academic coordinator'], 'academic coordinator'),
        # COE
        (['controller of examination', 'controller of exam', 'coe srec',
          'who is coe', 'who is controller', 'grace selvarani',
          'head of examinations'], 'coe'),
        # Chairman
        (['chairman of srec', 'who is chairman', 'managing trustee',
          'r sundar', 'trust chairman'], 'chairman'),
        # Vice Chairman
        (['vice chairman', 'joint managing trustee', 'narendran'], 'vice chairman'),
        # Governing Council
        (['governing council', 'governing body', 'gc members'], 'governing council'),
        # Warden
        (['warden', 'hostel warden', 'hostel incharge', 'hostel in-charge',
          'who is warden', 'girls warden', 'boys warden'], 'warden'),
        # Transport
        (['transport incharge', 'transport in charge', 'bus incharge',
          'who manages transport', 'transport head'], 'transport incharge'),
        # Physical Director
        (['physical director', 'sports director', 'sports incharge',
          'who is physical director', 'nithyanandan'], 'physical director'),
        # IQAC
        (['iqac', 'quality assurance', 'internal quality'], 'iqac'),
        # CCE
        (['cce', 'centre for continuing education', 'continuing education'], 'cce'),
        # Key professors
        (['selvakumar', 'dr selvakumar', 'j selvakumar'], 'selvakumar'),
        (['grace selvarani', 'a grace selvarani', 'dr grace'], 'grace selvarani'),
        (['sathish kumar', 'n sathish kumar', 'dr sathish'], 'sathish kumar'),
        # HOW MANY TEACHERS / FACULTY
        (['how many teacher', 'how many faculty', 'how many professor',
          'number of teacher', 'number of faculty', 'total teacher',
          'total faculty', 'faculty count', 'faculty strength',
          'staff count', 'how many staff'], 'faculty count'),
        # HOW MANY STUDENTS
        (['how many student', 'total student', 'student strength',
          'student count', 'number of student'], 'how many students'),
    ]
    for keywords, key in role_patterns:
        if any(kw in msg_lower for kw in keywords):
            if key in SREC_KNOWLEDGE:
                return SREC_KNOWLEDGE[key]

    # ---------------------------------------------------------------
    # PRIORITY PASS 3 — General knowledge map
    # ---------------------------------------------------------------
    keyword_map = [
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
        (['recruiter', 'company', 'companies', 'top companies'], 'recruiters'),
        (['placement', 'placed', 'campus drive', 'job', 'campus recruitment'], 'placement'),
        (['fee', 'fees', 'tuition', 'cost'], 'fees'),
        (['international', 'foreign', 'nri'], 'international'),
        (['tnea', 'tancet', 'gate admission'], 'tnea'),
        (['admission', 'apply', 'application', 'join srec', 'how to join'], 'admission'),
        (['eligibility', 'cutoff', 'cut off'], 'eligibility'),
        (['timetable', 'time table', 'exam schedule', 'exam time'], 'timetable'),
        (['result', 'results', 'grade', 'mark sheet'], 'result'),
        (['exam', 'examination', 'semester exam', 'end sem', 'internal exam'], 'exam'),
        (['controller of exam', 'controller of examination'], 'coe'),
        (['nirf', 'nirf ranking', 'nirf 2025'], 'nirf'),
        (['ranking', 'rank', 'careers 360', 'rated', 'rating', 'best college rank'], 'ranking'),
        (['ai data science', 'btech ai', 'aids department'], 'ai'),
        (['robotics', 'automation', 'rae department'], 'robotics'),
        (['aeronautical', 'aero department'], 'aeronautical'),
        (['biomedical', 'bme department'], 'biomedical'),
        (['civil engineering', 'civil department'], 'civil'),
        (['mechanical engineering', 'mech department'], 'mechanical'),
        (['eee department', 'electrical engineering'], 'eee'),
        (['ece department', 'electronics and communication'], 'ece'),
        (['it department', 'information technology department'], 'it'),
        (['cse department', 'computer science department'], 'cse'),
        (['mba department', 'management department'], 'mba'),
        (['pg programme', 'pg program', 'postgraduate', 'm.tech', 'mtech'], 'pg'),
        (['ug programme', 'ug program', 'undergraduate', 'b.e', 'b.tech', 'be programme'], 'ug'),
        (['departments', 'all departments'], 'departments'),
        (['courses', 'programmes', 'programs offered'], 'courses'),
        (['yoga', 'meditation', 'wellness'], 'yoga'),
        (['ncc'], 'ncc'),
        (['nss', 'national service'], 'nss'),
        (['csi', 'computer society'], 'csi'),
        (['clubs', 'student club', 'student activities', 'extracurricular'], 'clubs'),
        (['sports', 'basketball', 'cricket', 'football', 'volleyball', 'games', 'badminton'], 'sports'),
        (['atm', 'bank', 'south indian bank'], 'atm'),
        (['cafeteria', 'canteen', 'food', 'mess'], 'cafeteria'),
        (['wifi', 'wi-fi', 'internet', 'network'], 'wifi'),
        (['healthcare', 'medical', 'health center', 'health centre', 'doctor', 'ambulance'], 'healthcare'),
        (['transport', 'bus', 'college bus', 'bus route'], 'transport'),
        (['hostel', 'accommodation', 'stay', 'room', 'dormitory'], 'hostel'),
        (['library', 'books', 'digital resources', 'e-library', 'opac'], 'library'),
        (['infrastructure', 'campus facility', 'facilities'], 'infrastructure'),
        (['campus', 'campus area', 'campus size'], 'campus'),
        (['distance', 'how far', 'km from', 'nearest railway', 'nearest airport'], 'distance'),
        (['office hours', 'office time', 'working hours'], 'office hours'),
        (['college timing', 'college time', 'class time', 'academic hours'], 'college timings'),
        (['fax', 'fax number'], 'fax'),
        (['landline', 'telephone', 'std'], 'landline'),
        (['news', 'latest news', 'announcement'], 'news'),
        (['event', 'events', 'upcoming event', 'fest'], 'events'),
        (['gallery', 'photos', 'pictures'], 'gallery'),
        (['magazine'], 'magazine'),
        (['alumni', 'old students', 'alumnus', 'pass out'], 'alumni'),
        (['global partner', 'partners'], 'partners'),
        (['nba accreditation', 'nba approved'], 'nba'),
        (['naac', 'a+ grade', 'naac accreditation'], 'naac'),
        (['vision'], 'vision'),
        (['mission'], 'mission'),
        (['affiliation', 'anna university', 'affiliated to'], 'affiliation'),
        (['autonomous', 'autonomous college'], 'autonomous'),
        (['principal', 'head of college'], 'principal'),
        (['phone', 'hotline', 'call srec', 'contact number'], 'phone'),
        (['email', 'mail srec'], 'email'),
        (['website', 'official site', 'official link'], 'website'),
        (['contact', 'reach srec', 'reach out', 'contact details'], 'contact'),
        (['location', 'address', 'how to reach', 'directions', 'map', 'where is srec'], 'location'),
        (['established', 'founded', 'when was srec', 'year founded'], 'established'),
        (['founder', 'trust', 'snr sons', 'managed by'], 'founder'),
        (['about srec', 'what is srec', 'tell me about srec', 'about college'], 'about'),
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
# SENTIMENT ANALYSIS
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
        reset_link = auth.generate_password_reset_link(email)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'msg': 'Email not found or error occurred.'})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    ROLE_CODES = {
        'faculty': 'SREC@FAC2025',
        'admin':   'SREC@ADM2025'
    }
    if request.method == 'POST':
        userid      = request.form.get('userid', '').strip()
        password    = request.form.get('password', '')
        role        = request.form.get('role', 'student')
        access_code = request.form.get('access_code', '').strip()

        if not userid.endswith('@srec.ac.in'):
            return render_template('signup.html', error='Only @srec.ac.in emails are allowed.')

        import re as _re
        if (len(password) < 8 or
            not _re.search(r'[A-Z]', password) or
            not _re.search(r'[0-9]', password) or
            not _re.search(r'[^A-Za-z0-9]', password)):
            return render_template('signup.html', error='Password must be 8+ chars with uppercase, number & special character.')

        if role in ('faculty', 'admin'):
            if access_code != ROLE_CODES.get(role, ''):
                return render_template('signup.html', error='Invalid access code for selected role.')

        if not userid or not password:
            return render_template('signup.html', error='Email and password required.')

        try:
            user = auth.create_user(email=userid, password=password)
            auth.set_custom_user_claims(user.uid, {'role': role})
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
# CHATBOT ROUTE
# =====================================================================
@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '').strip()
    if not user_msg:
        return jsonify({'response': "Hey! Send me a message and I'll help you out 😊"})

    msg_lower = user_msg.lower().strip()

    # ── BUG FIX: Clear stale QP session if user types something unrelated ──
    if session.get('awaiting_qp_subject'):
        is_subject = any(s.lower() in msg_lower for s in ['mad','beee','sensors'])
        is_unrelated = (
            len(msg_lower) > 15 or
            any(w in msg_lower for w in ['who','what','how','where','when','why','tell','is ','are ']) or
            any(c in msg_lower for c in ['!','?'])
        )
        if not is_subject and is_unrelated:
            session.pop('awaiting_qp_subject', None)

    # ── 1. PROFANITY / ABUSE ─────────────────────────────────────────
    abuse_words = ['fuck','fck','fuk','bitch','bastard','shit','wtf','wth',
                   'idiot','stupid','dumb','crap','cock','dick','sex','porn',
                   'hate you','useless','worthless','asshole']
    if any(w in msg_lower for w in abuse_words):
        session.pop('awaiting_qp_subject', None)
        return jsonify({'response': (
            "Hey, let's keep things respectful here 😊<br>"
            "I'm here to help with SREC queries — what would you like to know?"
        )})

    # ── 2. GREETINGS ─────────────────────────────────────────────────
    greetings = {'hi','hello','hii','hiii','hey','heyy','yo','sup','howdy',
                 'greetings','hola','namaste','vanakkam','hai','helo','hiya'}
    if msg_lower in greetings or any(msg_lower.startswith(g+' ') for g in ['hi','hello','hey','hii']):
        session.pop('awaiting_qp_subject', None)
        return jsonify({'response': (
            "Hey there! 👋 Welcome to <b>SREC Bot</b> — your campus assistant! 😊<br><br>"
            "Ask me about:<br>"
            "👨‍💼 HODs & Faculty &nbsp;·&nbsp; 📚 Courses &nbsp;·&nbsp; 💼 Placements<br>"
            "🏫 Facilities &nbsp;·&nbsp; 📄 Question Papers &nbsp;·&nbsp; 🎉 Clubs<br><br>"
            "Try: <i>'Who is the HOD of CSE?'</i> 😊"
        )})

    # ── 3. THANKS ────────────────────────────────────────────────────
    thanks = {'ok','okay','thanks','thank you','thx','ty','thank u',
              'thankyou','tysm','tq','nice','cool','great','got it','sure','alright'}
    if msg_lower in thanks:
        session.pop('awaiting_qp_subject', None)
        return jsonify({'response': "You're welcome! 😊 Anything else about SREC?"})

    # ── 4. GOODBYE ───────────────────────────────────────────────────
    bye_words = {'bye','goodbye','see you','see ya','later','cya','tata','gn','good night'}
    if msg_lower in bye_words or msg_lower.startswith('bye') or msg_lower.startswith('good night'):
        session.pop('awaiting_qp_subject', None)
        return jsonify({'response': "Bye! 👋 Take care and all the best!"})

    # ── 5. IDENTITY ──────────────────────────────────────────────────
    identity_triggers = ['who are you','what are you','are you a bot','are you human',
                         'your name','what is your name','introduce yourself','who r u',
                         'wat r u','what r u']
    if any(q in msg_lower for q in identity_triggers):
        return jsonify({'response': (
            "I'm <b>SREC Bot</b> 🤖 — your campus FAQ assistant for "
            "Sri Ramakrishna Engineering College!<br>"
            "Ask me anything about SREC 😊"
        )})

    # ── 6. WHO CREATED YOU ───────────────────────────────────────────
    created_triggers = ['who created you','who made you','who built you','who made u',
                        'who developed you','who coded you','who is your creator','who made this']
    if any(q in msg_lower for q in created_triggers):
        return jsonify({'response': (
            "I was built by Second year SREC students Pitambar, Sowmya and Sivabalan as part of the <b>CampusConnect</b> project 🚀<br>"
            "I run on a custom NLP engine trained on SREC data 😊"
        )})

    # ── 7. WHAT IS CAMPUSCONNECT ─────────────────────────────────────
    platform_triggers = ['what is this platform','what is campusconnect','about this app',
                         'about campusconnect','what is this website']
    if any(q in msg_lower for q in platform_triggers):
        return jsonify({'response': (
            "🎓 <b>CampusConnect</b> is an AI-driven social platform exclusively for SREC students!<br>"
            "Post updates, view club events, access question papers, and chat with me for any SREC query 😊"
        )})

    # ── 8. HELP ──────────────────────────────────────────────────────
    help_triggers = ['help','what can you do','options','menu','what do you know','features']
    if any(t in msg_lower for t in help_triggers):
        return jsonify({'response': (
            "Here's what I can do! 😊<br><br>"
            "👨‍💼 <b>Faculty</b> — Principal, HODs of all 17 depts, wardens<br>"
            "🏫 <b>College info</b> — history, NAAC A+, NIRF ranking, accreditation<br>"
            "📚 <b>Courses</b> — 12 UG + 7 PG + MBA<br>"
            "💼 <b>Placements</b> — stats, top recruiters, packages<br>"
            "🏠 <b>Facilities</b> — hostel, library, transport, sports<br>"
            "📄 <b>Question Papers</b> — MAD, BEEE, SENSORS<br>"
            "🎉 <b>Clubs</b> — NCC, NSS, AI Club, CSI<br><br>"
            "Example: <i>Who is the HOD of IT?</i> | <i>What's the placement rate?</i>"
        )})

    # ── 9. EMOTION SUPPORT ───────────────────────────────────────────
    emotion_response = get_emotion_response(user_msg)
    if emotion_response:
        return jsonify({'response': emotion_response})

    # ── 10. QUESTION PAPERS (role-secured) ───────────────────────────
    qp_triggers = ['question paper','previous year','pyq','past paper',
                   'old question','model paper','previous question']
    if any(t in msg_lower for t in qp_triggers):
        if 'user' not in session:
            return jsonify({'response': "You need to be logged in to access question papers 🔒"})
        if session.get('role') not in ['student','faculty','admin']:
            return jsonify({'response': "Question papers are only for SREC students and faculty ❌"})
        session['awaiting_qp_subject'] = True
        return jsonify({'response': (
            "Sure! 📚 Which subject do you need?<br>"
            "<b>MAD</b> &nbsp;·&nbsp; <b>BEEE</b> &nbsp;·&nbsp; <b>SENSORS</b>"
        )})

    if session.get('awaiting_qp_subject') and 'user' in session:
        for subject in SUBJECTS.keys():
            if msg_lower == subject.lower() or subject.lower() in msg_lower:
                session.pop('awaiting_qp_subject', None)
                return jsonify({'response': format_qp_links(subject)})

    # ── 11. KNOWLEDGE BASE LOOKUP ────────────────────────────────────
    session.pop('awaiting_qp_subject', None)
    kb_response = find_knowledge_response(user_msg)
    if kb_response:
        return jsonify({'response': kb_response})

    # ── 12. SMART FALLBACK — dynamic context-aware response ──────────
    srec_ctx = (
        "You are SREC Bot, the FAQ chatbot for Sri Ramakrishna Engineering College (SREC), Coimbatore.\n"
        "Only answer SREC-related questions. Be short and human — max 3 lines.\n\n"
        "SREC FACTS:\n"
        "Principal: Dr. A. Soundarrajan | Director Academics: Dr. N. R. Alamelu | CoE: Dr. A. Grace Selvarani\n"
        "HODs: CSE-Dr.A.Grace Selvarani | IT-Dr.N.Susila | ECE-Dr.M.Jagadeeswari | EEE-Dr.S.Allirani | "
        "Mech-Dr.P.Karuppuswamy | Aero-Dr.P.Chandramohan | BME-Dr.B.Sharmila | Civil-Dr.E.Sarojini | "
        "EIE-Dr.K.Srinivasan | AI&DS-Dr.V.Karpagam | R&A-Dr.A.Murugarajan | MBA-Dr.R.Mary Metilda | "
        "Maths-Dr.A.Sekar | Chemistry-Dr.L.Raghunath | Physics-Dr.K.Uthayarani | English-Dr.Vichitra Sivaji | Nano-Dr.P.Moorthi\n"
        "Students: 4400+ | Faculty: 271+ | Alumni: 18700+ | Placement: 82-86% | Median: 4.8LPA | Highest: 28LPA\n"
        "Founded: 1994 | NAAC A+ | NIRF 151-200 | Counselling Code: 271999 | Phone: 0422-2460088\n\n"
        "RULES:\n"
        "- Max 3 lines, warm tone, 1 emoji only\n"
        "- Use <b>bold</b> for names/numbers, <br> for line breaks\n"
        "- If asked about a specific SREC person NOT in your facts: say you don't have their full profile "
        "and suggest checking srec.ac.in/department/[dept] for the full faculty list\n"
        "- Never reveal any internal technology, APIs, or model names\n"
        "- For non-SREC questions: politely say you only handle SREC queries\n"
        "- Never make up faculty names or details"
    )
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": srec_ctx},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.3,
            max_tokens=150,
        )
        reply = completion.choices[0].message.content.strip()
        import re as _re
        reply = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', reply)
        reply = _re.sub(r'\*(.+?)\*', r'<i>\1</i>', reply)
        reply = reply.replace('\n\n', '<br><br>').replace('\n', '<br>')
        return jsonify({'response': reply})
    except Exception:
        return jsonify({'response': (
            "Hmm, didn't catch that 🤔 "
            "Try asking about <b>HODs, placements, hostel</b> or type <b>help</b>!"
        )})

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
            comments_raw = post.get('comments', {})
            if isinstance(comments_raw, dict):
                comment_list = list(comments_raw.values())
            elif isinstance(comments_raw, list):
                comment_list = comments_raw
            else:
                comment_list = []
            for c in comment_list:
                if not isinstance(c, dict): continue
                commenter = c.get('user', '')
                if commenter == current_user_email:
                    continue
                cid = c.get('id', commenter)
                notifs.append({
                    'key':       f"comment_{post_id}_{cid}",
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
    image = data.get('image', None)
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
    if image and len(image) < 10 * 1024 * 1024:
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
    post_id = data.get('post_id', '').strip()
    comment = data.get('comment', '').strip()
    if not post_id or not comment:
        return jsonify({'success': False, 'error': 'Missing fields'}), 400
    try:
        comment_id = str(uuid.uuid4())
        db.reference(f'/posts/{post_id}/comments/{comment_id}').set({
            'id':        comment_id,
            'user':      session.get('email'),
            'comment':   comment,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'replies':   {}
        })
        return jsonify({'success': True, 'comment_id': comment_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/reply_comment', methods=['POST'])
def reply_comment():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json() or {}
    post_id    = data.get('post_id', '').strip()
    comment_id = data.get('comment_id', '').strip()
    reply_text = data.get('reply', '').strip()
    if not post_id or not comment_id or not reply_text:
        return jsonify({'success': False, 'error': 'Missing fields'}), 400
    try:
        comment_ref = db.reference(f'/posts/{post_id}/comments/{comment_id}')
        if not comment_ref.get():
            return jsonify({'success': False, 'error': 'Comment not found'}), 404
        reply_id = str(uuid.uuid4())
        db.reference(f'/posts/{post_id}/comments/{comment_id}/replies/{reply_id}').set({
            'id':        reply_id,
            'user':      session.get('email'),
            'reply':     reply_text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        return jsonify({'success': True, 'reply_id': reply_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    category = data.get('category', 'other').strip()
    if not title:
        return jsonify({'success': False, 'msg': 'Title required'}), 400
    event_id = str(uuid.uuid4())
    db.reference('/events').child(event_id).set({
        'id': event_id, 'title': title, 'desc': desc,
        'datetime': dt, 'venue': venue, 'category': category,
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
        'venue': data.get('venue', ''),
        'category': data.get('category', 'other')
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
        response = gemini_generate(prompt)
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
        response = gemini_generate(prompt)
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
    students_raw = ref.get() or {}
    students = []
    now = datetime.now()
    for suid, s in students_raw.items():
        try:
            joined = datetime.strptime(s.get('joined_at',''), '%Y-%m-%d %H:%M:%S')
            diff_mins = int((now - joined).total_seconds() / 60)
            if diff_mins > 240:
                ref.child(suid).delete()
                continue
            if diff_mins < 1:    dur = 'just joined'
            elif diff_mins < 60: dur = f'{diff_mins} min ago'
            else:                dur = f'{diff_mins//60}h {diff_mins%60}m'
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
            ref.child(uid).delete()
        else:
            ref.child(uid).set(user_email)
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


# =====================================================================
# STUDY ROOM QUIZ — Gemini-powered AI quiz generation
# =====================================================================
QUIZ_SUBJECT_CONTEXT = {
    'MAD':             'Mobile Application Development for Android: Activities, Intents, UI layouts, RecyclerView, SQLite, JSON, Retrofit, Material Design',
    'BEEE':            'Basics of Electrical and Electronics Engineering: DC circuits, Ohm Law, Kirchhoff Laws, AC circuits, transformers, motors, PN junction, BJT, Op-Amp',
    'SENSORS':         'Sensors and Applications: temperature, pressure, proximity, IR, ultrasonic sensors, transducers, signal conditioning, ADC, IoT sensor interfacing',
    'Mathematics':     'Engineering Mathematics: limits, differentiation, integration, differential equations, matrices, Laplace transforms, Fourier series',
    'Physics':         'Engineering Physics: wave optics, laser, fibre optics, quantum mechanics, semiconductor physics, superconductivity, nanomaterials',
    'Chemistry':       'Engineering Chemistry: corrosion, electrochemistry, polymers, water treatment, fuel cells, spectroscopy, green chemistry',
    'Programming':     'C Programming: data types, operators, control flow, functions, arrays, pointers, structures, file IO',
    'Data Structures': 'Data Structures: arrays, linked lists, stacks, queues, binary trees, BST, graphs, BFS DFS, sorting algorithms, time complexity',
    'Networks':        'Computer Networks: OSI model, TCP IP stack, IP addressing, subnetting, routing protocols, DNS, HTTP, network security',
    'DBMS':            'Database Management Systems: ER model, relational algebra, SQL, normalization, transactions, ACID, indexing, concurrency control',
    'Machine Learning':'Machine Learning: supervised unsupervised learning, regression, SVM, decision trees, neural networks, overfitting, evaluation metrics',
    'Operating Systems':'Operating Systems: process management, CPU scheduling, deadlocks, memory management, virtual memory, paging, file systems',
    'Other':           'General Engineering fundamentals of electronics, programming, mathematics, core engineering concepts for 2nd year B.E B.Tech',
}

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    data    = request.get_json() or {}
    subject = data.get('subject', 'Other').strip()
    n       = max(5, min(int(data.get('count', 10)), 15))
    context = QUIZ_SUBJECT_CONTEXT.get(subject,
                  subject + ' core 2nd year B.E B.Tech engineering concepts')

    prompt = (
        "You are an engineering professor creating an MCQ quiz.\n"
        "Generate exactly " + str(n) + " multiple-choice questions for: " + subject + "\n"
        "Context: " + context + "\n\n"
        "Rules:\n"
        "1. Appropriate for 2nd year B.E/B.Tech students\n"
        "2. Each question has exactly 4 options (A, B, C, D), only ONE correct\n"
        "3. Vary difficulty: mix easy, medium, hard\n"
        "4. Be specific and factual\n"
        "5. No duplicate questions\n\n"
        "Return ONLY valid compact JSON, no markdown, no extra text:\n"
        '{"subject":"' + subject + '","questions":[{"q":"Question?","options":{"A":"...","B":"...","C":"...","D":"..."},"answer":"A","explanation":"Why A is correct"}]}'
    )

    try:
        resp = gemini_generate(prompt)
        raw  = resp.text.strip()
        if raw.startswith('```'):
            lines = raw.split('\n')
            raw = '\n'.join(lines[1:])
            if raw.rstrip().endswith('```'):
                raw = raw.rstrip()[:-3]
        import json as _json
        quiz = _json.loads(raw.strip())
        qs   = [q for q in quiz.get('questions', [])
                if all(k in q for k in ('q', 'options', 'answer'))]
        quiz['questions'] = qs[:n]
        if not qs:
            raise ValueError('No valid questions parsed from Gemini response')
        return jsonify({'success': True, 'quiz': quiz})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/save_quiz_result', methods=['POST'])
def save_quiz_result():
    if 'user' not in session: return jsonify({'success': False}), 401
    data = request.get_json() or {}
    uid  = session.get('user', '')
    try:
        rid = str(uuid.uuid4())
        db.reference('/quiz_results/' + uid + '/' + rid).set({
            'user':      session.get('email', ''),
            'subject':   data.get('subject', ''),
            'score':     int(data.get('score', 0)),
            'total':     int(data.get('total', 0)),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)