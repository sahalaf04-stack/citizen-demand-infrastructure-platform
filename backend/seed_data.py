"""
Generates demo data. District entries below are REAL, not fabricated:

- name/state: from NITI Aayog's official list of 112 "Aspirational Districts"
  (launched 2018) - districts formally designated by the Government of India
  as under-developed and prioritized for accelerated development.
  Source: https://niti.gov.in/aspirational-districts-programme
- population: 2011 Census of India district totals (most recent full census).
- infra_deficit_score: NOT an official composite figure. It's an illustrative
  0-1 proxy derived from each district's Aspirational District standing
  (all 6 below carry that designation, so all start "high-deficit") with
  manual variation for demo purposes. Swap this for NITI Aayog's actual
  monthly Aspirational Districts delta-ranking composite score
  (championsofchange.gov.in) for production use - that data is public but
  requires scraping/API access this scaffold doesn't include.
- planned_budget_cr: illustrative placeholder, not sourced. Replace with
  real scheme-wise allocations (PMGSY, Jal Jeevan Mission, etc.) from
  data.gov.in or state treasury portals.
"""
import random
from dotenv import load_dotenv

load_dotenv()  # so ANTHROPIC_API_KEY is picked up when running this script directly

from database import SessionLocal, engine, Base
from models import District, CitizenRequest
from nlp_pipeline import process_request

random.seed(42)

DISTRICTS = [
    # Karnataka - relevant to demo audience. Aspirational District since 2018.
    {"name": "Raichur", "state": "Karnataka", "population": 1928812, "infra_deficit_score": 0.74, "planned_budget_cr": 42.0, "lat": 16.21, "lon": 77.35},
    # Maharashtra - tribal-majority, Aspirational District since 2018.
    {"name": "Nandurbar", "state": "Maharashtra", "population": 1648295, "infra_deficit_score": 0.69, "planned_budget_cr": 55.0, "lat": 21.38, "lon": 74.37},
    # Bihar - Aspirational District since 2018.
    {"name": "Purnia", "state": "Bihar", "population": 3264619, "infra_deficit_score": 0.81, "planned_budget_cr": 38.0, "lat": 25.78, "lon": 87.48},
    # Kerala - Aspirational District since 2018 (flood/landslide-prone highland district).
    {"name": "Wayanad", "state": "Kerala", "population": 817420, "infra_deficit_score": 0.52, "planned_budget_cr": 28.0, "lat": 11.60, "lon": 76.08},
    # Himachal Pradesh - Aspirational District, mountainous/hard-to-reach terrain.
    {"name": "Chamba", "state": "Himachal Pradesh", "population": 519080, "infra_deficit_score": 0.65, "planned_budget_cr": 20.0, "lat": 32.55, "lon": 76.13},
    # Gujarat - Aspirational District since 2018, tribal-majority.
    {"name": "Dahod", "state": "Gujarat", "population": 2127086, "infra_deficit_score": 0.71, "planned_budget_cr": 47.0, "lat": 22.83, "lon": 74.26},
]

# A handful of hand-written sample complaints per category/language for the
# demo dataset. These are original placeholder sentences, not sourced text.
SAMPLES = {
    "road": {
        "en": ["The main road near the market has large potholes causing accidents.",
               "Bridge connecting the village to the highway has been damaged for months."],
        "hi": ["Bazaar ke paas sadak mein bade gaddhe hain jinse durghatna ho rahi hai.",
               "Gaon ko highway se jodne wala pul kai mahino se kharab hai."],
        "kn": ["Maarukatteya baLi raste tumba haddagalu iddu apaghaatakke kaarana aagide.",
               "Halliyannu highway ge sambandhisuva seenkarige tingalugalinda haani aagide."],
    },
    "water": {
        "en": ["No piped water supply for the last two weeks in our locality.",
               "The community borewell has run dry and there is no backup source."],
        "hi": ["Hamare mohalle mein pichhle do hafton se paani ki supply nahi hai.",
               "Samudayik borewell sukh gaya hai aur koi doosra srot nahi hai."],
        "kn": ["Nam bhagadalli kaledu vaarangalinda kolaayi neeru bandilla.",
               "Samudaayika borewell baththi hoyithu, beri moolagalilla."],
    },
    "electricity": {
        "en": ["Frequent power outages every evening for the past month.",
               "The transformer near our street has been sparking and needs urgent repair."],
        "hi": ["Pichhle ek mahine se har shaam bijli baar baar jaa rahi hai.",
               "Hamari gali ke paas ka transformer chingari de raha hai, turant marammat chahiye."],
    },
    "sanitation": {
        "en": ["Garbage has not been collected from our street in over ten days.",
               "The public toilet complex is unusable due to lack of maintenance."],
        "hi": ["Hamari gali se das dinon se kachra nahi utha hai.",
               "Sarvajanik shauchalaya rakhrakhaav ki kami ke karan istemaal ke laayak nahi hai."],
    },
}

URGENCY_TAGS = {"road": " This is urgent as an accident already happened.",
                "water": "", "electricity": "", "sanitation": ""}


def seed(num_requests: int = 180):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    db.query(CitizenRequest).delete()
    db.query(District).delete()
    db.commit()

    district_objs = []
    for d in DISTRICTS:
        obj = District(**d)
        db.add(obj)
        district_objs.append(obj)
    db.commit()
    for obj in district_objs:
        db.refresh(obj)

    categories = list(SAMPLES.keys())
    created = 0
    while created < num_requests:
        district = random.choice(district_objs)
        category = random.choices(categories, weights=[0.35, 0.3, 0.2, 0.15])[0]
        lang = random.choice(list(SAMPLES[category].keys()))
        base_text = random.choice(SAMPLES[category][lang])
        if random.random() < 0.15:
            base_text += URGENCY_TAGS.get(category, "")

        extracted = process_request(base_text, lang)

        jitter = lambda v: v + random.uniform(-0.05, 0.05)
        req = CitizenRequest(
            raw_text=base_text,
            language=lang,
            translated_text=extracted["translated_text"],
            category=extracted["category"],
            urgency=extracted["urgency"],
            lat=jitter(district.lat),
            lon=jitter(district.lon),
            district_id=district.id,
        )
        db.add(req)
        created += 1

    db.commit()
    db.close()
    print(f"Seeded {len(DISTRICTS)} districts and {created} citizen requests.")


if __name__ == "__main__":
    seed()
