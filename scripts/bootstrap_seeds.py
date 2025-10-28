# save as scripts/bootstrap_seeds.py and run: python scripts/bootstrap_seeds.py
import os, json, re
from pathlib import Path

ROOT = Path(".")
(Path("docs")).mkdir(parents=True, exist_ok=True)
(Path("rules")).mkdir(parents=True, exist_ok=True)
(Path("workflow")).mkdir(parents=True, exist_ok=True)

# ---------- 1) Field Dictionary (codebook.csv) ----------
codebook_rows = [
    ("source","Data source identifier, e.g., 'DSLD','Amazon','Knowde','Internal'","DSLD"),
    ("source_record_id","Source-specific id (e.g., asin, upcSku, URL slug)","B06WRNG37C / 8 92985 00071 3"),
    ("product_name","Human-readable product or ingredient name","MycoAdrenal; Vitamin D3 + K2"),
    ("brand","Brand or company (retail brand)","ecoNugenics; Dr. Berg Nutritionals"),
    ("company_name","Company/manufacturer name","Musim Mas Group; leosglutenfree.com"),
    ("link","Product page URL","https://..."),
    ("on_market","1 on-market; 0 off-market or unknown","1"),
    ("entry_date","Entry/first-seen date in source","2023-06-22"),
    ("form","Physical form e.g., Capsule, Softgel, Powder","Capsule"),
    ("serving_size","Declared serving size count, as numeric","2"),
    ("serving_unit","Declared serving size unit e.g., Capsule(s)","Capsule(s)"),
    ("net_quantity","Count or mass per package, if available","60"),
    ("net_unit","Unit for net_quantity","Vegetarian Capsule(s)"),
    ("ingredients","Array of ingredient names (normalized)","[...names...]"),
    ("other_ingredients","Array of 'other ingredients' or excipients","[...names...]"),
    ("dosage_value","Per-serving quantity for ingredient or blend","1500"),
    ("dosage_unit","Unit for dosage_value (canonical mass unit)","mg"),
    ("dose_count_unit","Count units used in label context","Capsule(s)"),
    ("claims","Marketing/structure-function claims","Structure/Function"),
    ("statements","Regulatory or caution statements","FDA Disclaimer"),
    ("target_groups","Target groups","Adult; Vegan; Gluten free"),
    ("certifications","Certifications & compliance","Halal, Kosher, RSPO, ..."),
    ("ingredient_taxonomy","Botanical/INCI/Common name mapping","INCI: Caprylic/Capric Triglyceride"),
    ("provenance","Crawl time, hash, extractor notes","crawl_ts, sha256, extractor=..."),
]
with open(ROOT/"docs"/"codebook.csv","w",encoding="utf-8") as f:
    f.write("field,description,example\n")
    for r in codebook_rows:
        f.write(",".join([str(x).replace(",",";") for x in r]) + "\n")

# ---------- 2) Synonyms ----------
synonym_pairs = [
    ("Vitamin D3","cholecalciferol"),
    ("Vitamin D3","D3"),
    ("Vitamin K2","menaquinone-7"),
    ("Vitamin K2","MK-7"),
    ("Vitamin K2","MK7"),
    ("Glycerin","Glycerine"),
    ("Glycerin","Glycerol"),
    ("Caprylic/Capric Triglyceride","MCT"),
    ("Caprylic/Capric Triglyceride","Medium Chain Triglycerides"),
    ("Sorbitan Monostearate","SMS"),
    ("Sodium Stearoyl Lactylate","SSL"),
    ("Polyglycerol Polyricinoleate","PGPR"),
    ("Propylene Glycol Monostearate","PGMS"),
    ("Polyglycerol Fatty Acid Esters","PGE"),
    ("Reishi Mushroom","Ganoderma lucidum"),
    ("Turkey Tail Mushroom","Trametes versicolor"),
    ("Turkey Tail Mushroom","Coriolus versicolor"),
    ("Maitake Mushroom","Grifola frondosa"),
    ("Shiitake Mushroom","Lentinula edodes"),
    ("Cordyceps sinensis","Ophiocordyceps sinensis"),
]
with open(ROOT/"rules"/"synonyms.csv","w",encoding="utf-8") as f:
    f.write("ingredient,alias\n")
    for a,b in synonym_pairs:
        f.write(f"{a},{b}\n")

# ---------- 3) Units ----------
unit_rows = [
    ("mg","mg","mass","1",""),
    ("milligram","mg","mass","1","synonym"),
    ("g","mg","mass","1000",""),
    ("gram","mg","mass","1000","synonym"),
    ("mcg","mg","mass","0.001",""),
    ("microgram","mg","mass","0.001","synonym"),
    ("IU","IU","activity","","Ingredient-specific; do not convert by default"),
    ("Capsule(s)","count","count","","count unit"),
    ("Softgel(s)","count","count","","count unit"),
    ("Tablet(s)","count","count","","count unit"),
    ("Gram(s)","mg","mass","1000","normalize DSLD label mass")
]
with open(ROOT/"rules"/"units.csv","w",encoding="utf-8") as f:
    f.write("unit,canonical,quantity_type,to_mg,notes\n")
    for r in unit_rows:
        f.write(",".join(r) + "\n")

# ---------- 4) Targets ----------
targets = [
    "Vitamin D3","Vitamin K2","Biotin","Magnesium","Zinc",
    "Caprylic/Capric Triglyceride","Glycerin","Tocotrienols","Cordyceps","Reishi Mushroom"
]
with open(ROOT/"workflow"/"targets.txt","w",encoding="utf-8") as f:
    f.write("\n".join(targets))

print("Seeds written to docs/codebook.csv, rules/synonyms.csv, rules/units.csv, workflow/targets.txt")
