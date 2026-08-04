"""
Health suggestions / precautions for each disease the model can predict.
Each entry contains:
  - description: a short, plain-language description of the condition
  - precautions: 4 practical self-care / precaution tips
  - severity: a rough urgency label used to color-code the result in the UI
  - doctor: whether the condition generally needs a doctor's visit

NOTE: This information is generic and for educational purposes only.
It is NOT a substitute for professional medical advice, diagnosis, or treatment.
"""

HEALTH_SUGGESTIONS = {
    "Fungal infection": {
        "description": "A common skin condition caused by fungal overgrowth, often in warm, moist areas of the body.",
        "precautions": ["Keep the affected area clean and dry", "Wear loose, breathable cotton clothing",
                         "Avoid sharing towels or personal items", "Use antifungal powder/cream as advised"],
        "severity": "low", "doctor": False
    },
    "Allergy": {
        "description": "An immune reaction to a substance (allergen) such as pollen, dust, or food.",
        "precautions": ["Identify and avoid known triggers", "Keep windows closed during high pollen days",
                         "Use antihistamines if recommended", "Keep living spaces dust-free"],
        "severity": "low", "doctor": False
    },
    "GERD": {
        "description": "Gastroesophageal Reflux Disease — stomach acid frequently flows back into the esophagus.",
        "precautions": ["Avoid large or late-night meals", "Reduce spicy, fatty, and acidic foods",
                         "Elevate the head while sleeping", "Avoid lying down right after eating"],
        "severity": "medium", "doctor": True
    },
    "Chronic cholestasis": {
        "description": "A condition where bile flow from the liver is reduced or blocked.",
        "precautions": ["Follow a low-fat diet", "Stay well hydrated", "Avoid alcohol",
                         "Get regular liver function checkups"],
        "severity": "high", "doctor": True
    },
    "Drug Reaction": {
        "description": "An adverse reaction of the body to a medication.",
        "precautions": ["Stop the suspected medication and consult a doctor", "Note down all recent medications",
                         "Avoid self-medicating further", "Seek emergency care if breathing difficulty occurs"],
        "severity": "medium", "doctor": True
    },
    "Peptic ulcer diseae": {
        "description": "Open sores that develop on the inner lining of the stomach or upper small intestine.",
        "precautions": ["Avoid NSAIDs like ibuprofen/aspirin", "Eat smaller, frequent meals",
                         "Limit alcohol and smoking", "Manage stress levels"],
        "severity": "medium", "doctor": True
    },
    "AIDS": {
        "description": "A chronic condition caused by HIV that weakens the immune system.",
        "precautions": ["Follow prescribed antiretroviral therapy strictly", "Maintain a nutritious diet",
                         "Practice safe hygiene to avoid infections", "Get regular medical monitoring"],
        "severity": "high", "doctor": True
    },
    "Diabetes ": {
        "description": "A metabolic condition where blood sugar levels are consistently too high.",
        "precautions": ["Monitor blood sugar regularly", "Follow a balanced, low-sugar diet",
                         "Exercise regularly", "Take prescribed medication/insulin on schedule"],
        "severity": "high", "doctor": True
    },
    "Gastroenteritis": {
        "description": "Inflammation of the stomach and intestines, usually causing diarrhea and vomiting.",
        "precautions": ["Stay hydrated with oral rehydration solutions", "Eat bland, easy-to-digest food",
                         "Rest as much as possible", "Practice strict hand hygiene"],
        "severity": "medium", "doctor": False
    },
    "Bronchial Asthma": {
        "description": "A chronic condition causing narrowing and inflammation of the airways.",
        "precautions": ["Avoid known triggers (smoke, dust, cold air)", "Keep rescue inhaler accessible",
                         "Practice breathing exercises", "Get regular pulmonary checkups"],
        "severity": "medium", "doctor": True
    },
    "Hypertension ": {
        "description": "Consistently elevated blood pressure that can strain the heart and arteries.",
        "precautions": ["Reduce salt intake", "Exercise regularly", "Manage stress and get enough sleep",
                         "Monitor blood pressure regularly"],
        "severity": "high", "doctor": True
    },
    "Migraine": {
        "description": "A neurological condition causing intense, often one-sided, throbbing headaches.",
        "precautions": ["Rest in a quiet, dark room", "Stay hydrated and maintain regular meals",
                         "Identify and avoid personal triggers", "Manage stress levels"],
        "severity": "low", "doctor": False
    },
    "Cervical spondylosis": {
        "description": "Age-related wear affecting the spinal disks in the neck.",
        "precautions": ["Maintain good posture", "Do gentle neck stretching exercises",
                         "Use an ergonomic pillow while sleeping", "Avoid heavy lifting"],
        "severity": "low", "doctor": False
    },
    "Paralysis (brain hemorrhage)": {
        "description": "Loss of muscle function often caused by bleeding in the brain — a medical emergency.",
        "precautions": ["Seek emergency medical help immediately", "Keep the person still and calm",
                         "Do not give food or water", "Note the time symptoms started"],
        "severity": "high", "doctor": True
    },
    "Jaundice": {
        "description": "Yellowing of skin/eyes caused by elevated bilirubin, often linked to liver issues.",
        "precautions": ["Stay well hydrated", "Avoid alcohol and fatty foods", "Get plenty of rest",
                         "Get liver function tests done"],
        "severity": "medium", "doctor": True
    },
    "Malaria": {
        "description": "A mosquito-borne disease caused by a parasite, causing fever and chills.",
        "precautions": ["Use mosquito nets and repellents", "Complete the full antimalarial course",
                         "Stay hydrated and rest", "Seek medical care promptly for fever"],
        "severity": "high", "doctor": True
    },
    "Chicken pox": {
        "description": "A highly contagious viral infection causing itchy blisters and fever.",
        "precautions": ["Isolate to avoid spreading infection", "Avoid scratching blisters",
                         "Use calamine lotion for itching", "Keep nails trimmed and clean"],
        "severity": "medium", "doctor": False
    },
    "Dengue": {
        "description": "A mosquito-borne viral infection causing high fever, rash, and joint pain.",
        "precautions": ["Use mosquito repellents and nets", "Stay hydrated",
                         "Avoid NSAIDs/aspirin (use paracetamol instead)", "Monitor platelet count with a doctor"],
        "severity": "high", "doctor": True
    },
    "Typhoid": {
        "description": "A bacterial infection spread through contaminated food/water, causing prolonged fever.",
        "precautions": ["Drink only safe, boiled/filtered water", "Maintain strict food hygiene",
                         "Complete the prescribed antibiotic course", "Rest and stay hydrated"],
        "severity": "high", "doctor": True
    },
    "hepatitis A": {
        "description": "A viral liver infection usually spread through contaminated food or water.",
        "precautions": ["Practice good hand hygiene", "Drink safe, clean water",
                         "Avoid alcohol during recovery", "Get plenty of rest"],
        "severity": "medium", "doctor": True
    },
    "Hepatitis B": {
        "description": "A viral infection that attacks the liver, spread through infected blood/body fluids.",
        "precautions": ["Get vaccinated if not already", "Avoid sharing needles/personal items",
                         "Avoid alcohol", "Get regular liver monitoring"],
        "severity": "high", "doctor": True
    },
    "Hepatitis C": {
        "description": "A viral infection affecting the liver, often spread through blood contact.",
        "precautions": ["Avoid alcohol", "Avoid sharing needles/personal items",
                         "Follow prescribed antiviral treatment", "Get regular liver checkups"],
        "severity": "high", "doctor": True
    },
    "Hepatitis D": {
        "description": "A liver infection that only occurs in people already infected with Hepatitis B.",
        "precautions": ["Get vaccinated against Hepatitis B", "Avoid alcohol",
                         "Avoid sharing needles/personal items", "Regular liver function monitoring"],
        "severity": "high", "doctor": True
    },
    "Hepatitis E": {
        "description": "A liver infection usually spread through contaminated water.",
        "precautions": ["Drink only safe, clean water", "Maintain good hygiene",
                         "Avoid alcohol during recovery", "Rest and stay hydrated"],
        "severity": "medium", "doctor": True
    },
    "Alcoholic hepatitis": {
        "description": "Liver inflammation caused by heavy, long-term alcohol consumption.",
        "precautions": ["Stop alcohol consumption completely", "Follow a nutritious, liver-friendly diet",
                         "Get regular liver monitoring", "Seek support for alcohol dependence if needed"],
        "severity": "high", "doctor": True
    },
    "Tuberculosis": {
        "description": "A serious bacterial infection that mainly affects the lungs.",
        "precautions": ["Complete the full course of prescribed antibiotics", "Cover mouth when coughing",
                         "Ensure good ventilation at home", "Maintain a nutritious diet"],
        "severity": "high", "doctor": True
    },
    "Common Cold": {
        "description": "A mild viral infection of the nose and throat.",
        "precautions": ["Rest and stay hydrated", "Use steam inhalation for congestion",
                         "Avoid cold beverages", "Wash hands frequently"],
        "severity": "low", "doctor": False
    },
    "Pneumonia": {
        "description": "An infection that inflames the air sacs in one or both lungs.",
        "precautions": ["Rest and stay hydrated", "Take prescribed antibiotics fully if bacterial",
                         "Use a humidifier for easier breathing", "Seek care if breathing worsens"],
        "severity": "high", "doctor": True
    },
    "Dimorphic hemmorhoids(piles)": {
        "description": "Swollen veins in the lower rectum or anus causing discomfort and bleeding.",
        "precautions": ["Increase dietary fiber and water intake", "Avoid straining during bowel movements",
                         "Use sitz baths for relief", "Avoid prolonged sitting"],
        "severity": "low", "doctor": False
    },
    "Heart attack": {
        "description": "A blockage of blood flow to the heart muscle — a medical emergency.",
        "precautions": ["Call emergency services immediately", "Chew an aspirin if advised and not allergic",
                         "Keep the person calm and seated", "Avoid any physical exertion"],
        "severity": "high", "doctor": True
    },
    "Varicose veins": {
        "description": "Swollen, twisted veins usually appearing in the legs.",
        "precautions": ["Elevate legs when resting", "Avoid standing/sitting for long periods",
                         "Wear compression stockings if advised", "Exercise regularly"],
        "severity": "low", "doctor": False
    },
    "Hypothyroidism": {
        "description": "A condition where the thyroid gland doesn't produce enough hormones.",
        "precautions": ["Take prescribed thyroid medication consistently", "Get regular thyroid function tests",
                         "Maintain a balanced diet", "Get adequate sleep"],
        "severity": "medium", "doctor": True
    },
    "Hyperthyroidism": {
        "description": "A condition where the thyroid gland produces excess hormones.",
        "precautions": ["Follow prescribed treatment plan", "Limit caffeine and stimulants",
                         "Get regular thyroid monitoring", "Manage stress levels"],
        "severity": "medium", "doctor": True
    },
    "Hypoglycemia": {
        "description": "Abnormally low blood sugar levels, common in people with diabetes.",
        "precautions": ["Eat small, frequent meals", "Carry a fast-acting sugar source",
                         "Monitor blood sugar regularly", "Avoid skipping meals"],
        "severity": "medium", "doctor": True
    },
    "Osteoarthristis": {
        "description": "A degenerative joint condition causing pain and stiffness.",
        "precautions": ["Maintain a healthy weight", "Do low-impact exercises like swimming",
                         "Use joint support/braces if needed", "Apply hot/cold therapy for pain relief"],
        "severity": "low", "doctor": False
    },
    "Arthritis": {
        "description": "Inflammation of one or more joints causing pain and stiffness.",
        "precautions": ["Stay physically active with gentle exercise", "Maintain a healthy weight",
                         "Apply hot/cold packs for pain relief", "Take anti-inflammatory medication as advised"],
        "severity": "medium", "doctor": True
    },
    "(vertigo) Paroymsal  Positional Vertigo": {
        "description": "A condition causing sudden spinning sensations triggered by head position changes.",
        "precautions": ["Sit or lie down immediately when dizzy", "Avoid sudden head movements",
                         "Try repositioning maneuvers under guidance", "Avoid driving during episodes"],
        "severity": "low", "doctor": False
    },
    "Acne": {
        "description": "A skin condition causing pimples, often due to clogged hair follicles.",
        "precautions": ["Wash face gently twice a day", "Avoid picking or popping pimples",
                         "Use non-comedogenic skincare products", "Maintain a balanced diet"],
        "severity": "low", "doctor": False
    },
    "Urinary tract infection": {
        "description": "An infection in any part of the urinary system, most often the bladder.",
        "precautions": ["Drink plenty of water", "Urinate frequently, don't hold it in",
                         "Maintain good hygiene", "Complete prescribed antibiotics fully"],
        "severity": "medium", "doctor": True
    },
    "Psoriasis": {
        "description": "A chronic skin condition causing rapid buildup of skin cells and scaly patches.",
        "precautions": ["Keep skin moisturized", "Avoid known triggers like stress",
                         "Get some sunlight exposure in moderation", "Avoid harsh soaps and scratching"],
        "severity": "low", "doctor": False
    },
    "Impetigo": {
        "description": "A highly contagious bacterial skin infection common in children.",
        "precautions": ["Keep the affected area clean and covered", "Avoid scratching or touching sores",
                         "Wash hands frequently", "Avoid sharing towels/clothing until healed"],
        "severity": "low", "doctor": False
    },
}


def get_health_suggestion(disease: str) -> dict:
    """Return suggestion info for a disease, with a safe fallback."""
    return HEALTH_SUGGESTIONS.get(disease, {
        "description": "General condition detected based on the symptoms provided.",
        "precautions": ["Get adequate rest", "Stay hydrated", "Monitor your symptoms closely",
                         "Consult a healthcare professional for an accurate diagnosis"],
        "severity": "medium",
        "doctor": True
    })
