import re
from backend.who_atc_database import WHO_ATC_DATABASE

# Comprehensive ATC (Anatomical Therapeutic Chemical) Classification Database
# Embedded with WHO 7-character Level 5 codes and Taiwan Traditional Chinese Brand Names

ATC_DATABASE = {
    "L01EX": {
        "atc_code": "L01EX",
        "class_name_en": "Other protein kinase inhibitors / Targeted Antineoplastics",
        "class_name_tc": "蛋白激酶抑制劑 / 標靶抗癌藥物 (VEGFR/TKI 標靶藥物)",
        "aliases": ["l01ex", "l01ex29", "l01xe", "蛋白激酶抑制劑", "標靶抗癌藥物", "標靶藥物", "tki", "vegfr 抑制劑"],
        "ingredients": [
            {
                "atc7": "L01EX29",
                "en": "Fruquintinib",
                "tc": "芙奎替尼 (呋喹替尼)",
                "brand": "Fruzaqla (愛優特 / 芙奎替尼)"
            },
            {
                "atc7": "L01EX05",
                "en": "Regorafenib",
                "tc": "瑞戈非尼",
                "brand": "Stivarga (癌瑞格)"
            },
            {
                "atc7": "L01EX08",
                "en": "Lenvatinib",
                "tc": "樂伐替尼",
                "brand": "Lenvima (樂衛瑪)"
            },
            {
                "atc7": "L01EX07",
                "en": "Cabozantinib",
                "tc": "卡博替尼",
                "brand": "Cabometyx (衛佳妥)"
            },
            {
                "atc7": "L01EX01",
                "en": "Sunitinib",
                "tc": "舒尼替尼",
                "brand": "Sutent (索坦)"
            },
            {
                "atc7": "L01EX02",
                "en": "Sorafenib",
                "tc": "索拉非尼",
                "brand": "Nexavar (蕾莎瓦)"
            }
        ]
    },
    "A05BA": {
        "atc_code": "A05BA",
        "class_name_en": "Liver Therapy / Hepatoprotectants",
        "class_name_tc": "肝臟治療劑 / 肝庇護劑 (保肝劑)",
        "aliases": ["a05ba", "a05ba03", "liver therapy", "hepatoprotectants", "hepatoprotective drugs", "保肝劑", "護肝劑", "肝庇護劑", "保肝藥", "護肝藥"],
        "ingredients": [
            {
                "atc7": "A05BA03",
                "en": "Silymarin",
                "tc": "水飛薊素",
                "brand": "Legalon (利加隆), Silygen (西利甘), Hepalgen (肝樂妥), Silybon (喜力本), Silyrin (喜力林), Kewei (可威)"
            },
            {
                "atc7": "A05BA03",
                "en": "Silybin",
                "tc": "水飛薊賓",
                "brand": "Silybest (喜利百解)"
            },
            {
                "atc7": "A05BA02",
                "en": "Ursodeoxycholic Acid",
                "tc": "熊去氧膽酸",
                "brand": "Urso (優思), Ursodiol (熊膽酸)"
            },
            {
                "atc7": "A05BA06",
                "en": "L-Ornithine L-Aspartate",
                "tc": "L-鳥氨酸-L-門冬氨酸",
                "brand": "Hepa-Merz (合寶麥斯), Hepaneed (肝必能)"
            },
            {
                "atc7": "A05BA08",
                "en": "Glycyrrhizin",
                "tc": "甘草甜素",
                "brand": "Stronger Neo-Minophagen C (強體力蒙 C / SNMC)"
            }
        ]
    },
    "A10BK": {
        "atc_code": "A10BK",
        "class_name_en": "SGLT2 inhibitors (Sodium-glucose co-transporter 2 inhibitors)",
        "class_name_tc": "SGLT2 抑制劑 (鈉-葡萄糖共同輸送器-2 抑制劑 / 排糖藥)",
        "aliases": ["a10bk", "a10bk01", "a10bk02", "a10bk03", "a10bk04", "sglt2", "sglt2i", "sglt2 抑制劑", "排糖藥", "鈉葡萄糖共同輸送器抑制劑"],
        "ingredients": [
            {
                "atc7": "A10BK03",
                "en": "Empagliflozin",
                "tc": "恩格列淨",
                "brand": "Jardiance (恩智平 / 恩格列淨)"
            },
            {
                "atc7": "A10BK01",
                "en": "Dapagliflozin",
                "tc": "達格列淨",
                "brand": "Forxiga (福可適 / 達格列淨)"
            },
            {
                "atc7": "A10BK02",
                "en": "Canagliflozin",
                "tc": "卡格列淨",
                "brand": "Invokana (可糖平 / 卡格列淨)"
            },
            {
                "atc7": "A10BK04",
                "en": "Ertugliflozin",
                "tc": "埃爾格列淨",
                "brand": "Steglatro (捷適妥)"
            }
        ]
    },
    "A10BJ": {
        "atc_code": "A10BJ",
        "class_name_en": "GLP-1 receptor agonists (Glucagon-like peptide-1 receptor agonists)",
        "class_name_tc": "GLP-1 受體促效劑 (腸泌素 / 瘦瘦針)",
        "aliases": ["a10bj", "a10bj06", "a10bj05", "a10bj02", "glp1", "glp-1", "glp1a", "腸泌素", "瘦瘦針"],
        "ingredients": [
            {
                "atc7": "A10BJ06",
                "en": "Semaglutide",
                "tc": "司美格魯肽",
                "brand": "Ozempic (胰島讚 / 易速妥), Wegovy (週輕看), Rybelsus (瑞倍適)"
            },
            {
                "atc7": "A10BJ05",
                "en": "Dulaglutide",
                "tc": "度拉糖肽",
                "brand": "Trulicity (易度糖)"
            },
            {
                "atc7": "A10BJ02",
                "en": "Liraglutide",
                "tc": "利拉魯肽",
                "brand": "Victoza (維克妥), Saxenda (善纖達)"
            },
            {
                "atc7": "A10BJ09",
                "en": "Tirzepatide",
                "tc": "替爾泊肽",
                "brand": "Mounjaro (猛健樂), Zepbound"
            }
        ]
    },
    "A10BH": {
        "atc_code": "A10BH",
        "class_name_en": "DPP-4 inhibitors (Dipeptidyl peptidase 4 inhibitors)",
        "class_name_tc": "DPP-4 抑制劑 (二基勝肽酶-4 抑制劑)",
        "aliases": ["a10bh", "a10bh01", "a10bh02", "a10bh03", "a10bh04", "dpp4", "dpp-4", "dpp4i"],
        "ingredients": [
            {
                "atc7": "A10BH01",
                "en": "Sitagliptin",
                "tc": "西格列汀",
                "brand": "Januvia (捷適妥 / 佳糖維)"
            },
            {
                "atc7": "A10BH02",
                "en": "Vildagliptin",
                "tc": "維格列汀",
                "brand": "Galvus (高糖優)"
            },
            {
                "atc7": "A10BH03",
                "en": "Saxagliptin",
                "tc": "沙格列汀",
                "brand": "Onglyza (安立澤)"
            },
            {
                "atc7": "A10BH05",
                "en": "Linagliptin",
                "tc": "利格列汀",
                "brand": "Trajenta (歐唐靜)"
            }
        ]
    },
    "A02BC": {
        "atc_code": "A02BC",
        "class_name_en": "Proton pump inhibitors (PPIs)",
        "class_name_tc": "PPI類 (氫離子幫浦抑制劑)",
        "aliases": ["a02bc", "a02bc01", "a02bc02", "a02bc03", "a02bc04", "a02bc05", "a02bc06", "ppi", "ppis", "質子泵抑制劑", "幫浦抑制劑", "氫離子幫浦"],
        "ingredients": [
            {
                "atc7": "A02BC01",
                "en": "Omeprazole",
                "tc": "歐美拉唑",
                "brand": "Losec (樂酸克), Omez"
            },
            {
                "atc7": "A02BC05",
                "en": "Esomeprazole",
                "tc": "埃索美拉唑",
                "brand": "Nexium (耐能 / 耐斯恩), Esomez"
            },
            {
                "atc7": "A02BC03",
                "en": "Lansoprazole",
                "tc": "蘭索拉唑",
                "brand": "Takepron (泰克胃通)"
            },
            {
                "atc7": "A02BC06",
                "en": "Dexlansoprazole",
                "tc": "右蘭索拉唑",
                "brand": "Dexilant (得喜胃通)"
            },
            {
                "atc7": "A02BC02",
                "en": "Pantoprazole",
                "tc": "潘托拉唑",
                "brand": "Pantoloc (潘妥洛克), Controloc"
            },
            {
                "atc7": "A02BC04",
                "en": "Rabeprazole",
                "tc": "雷貝拉唑",
                "brand": "Pariet (百抑潰)"
            }
        ]
    },
    "C09AA": {
        "atc_code": "C09AA",
        "class_name_en": "ACE inhibitors (Angiotensin-converting enzyme inhibitors)",
        "class_name_tc": "ACEi類 (血管收縮素轉化酶抑制劑)",
        "aliases": ["c09aa", "c09aa01", "c09aa02", "c09aa05", "acei", "ace inhibitor", "ace-i"],
        "ingredients": [
            {
                "atc7": "C09AA01",
                "en": "Captopril",
                "tc": "卡托普利",
                "brand": "Capoten (開博通)"
            },
            {
                "atc7": "C09AA02",
                "en": "Enalapril",
                "tc": "依那普利",
                "brand": "Renitec (悅復隆)"
            },
            {
                "atc7": "C09AA05",
                "en": "Ramipril",
                "tc": "雷米普利",
                "brand": "Tritace (壓特靈)"
            },
            {
                "atc7": "C09AA03",
                "en": "Lisinopril",
                "tc": "賴諾普利",
                "brand": "Zestril (捷適樂)"
            }
        ]
    },
    "C09CA": {
        "atc_code": "C09CA",
        "class_name_en": "Angiotensin II receptor blockers (ARBs)",
        "class_name_tc": "ARB類 (血管收縮素受體阻斷劑)",
        "aliases": ["c09ca", "c09ca01", "c09ca03", "c09ca04", "c09ca06", "c09ca07", "arb", "arbs"],
        "ingredients": [
            {
                "atc7": "C09CA01",
                "en": "Losartan",
                "tc": "氯沙坦",
                "brand": "Cozaar (可速壓)"
            },
            {
                "atc7": "C09CA03",
                "en": "Valsartan",
                "tc": "擷沙坦",
                "brand": "Diovan (代壓平)"
            },
            {
                "atc7": "C09CA04",
                "en": "Irbesartan",
                "tc": "厄貝沙坦",
                "brand": "Aprovel (安博律)"
            },
            {
                "atc7": "C09CA06",
                "en": "Atacand",
                "tc": "坎地沙坦",
                "brand": "Candesartan"
            },
            {
                "atc7": "C09CA07",
                "en": "Telmisartan",
                "tc": "泰米沙坦",
                "brand": "Micardis (美卡定)"
            }
        ]
    },
    "C10AA": {
        "atc_code": "C10AA",
        "class_name_en": "HMG-CoA reductase inhibitors (Statins)",
        "class_name_tc": "Statins類 (HMG-CoA還原酶抑制劑 / 降血脂藥)",
        "aliases": ["c10aa", "c10aa01", "c10aa03", "c10aa05", "c10aa07", "statin", "statins", "降膽固醇藥"],
        "ingredients": [
            {
                "atc7": "C10AA05",
                "en": "Atorvastatin",
                "tc": "阿托伐他汀",
                "brand": "Lipitor (立普妥)"
            },
            {
                "atc7": "C10AA07",
                "en": "Rosuvastatin",
                "tc": "瑞舒伐他汀",
                "brand": "Crestor (冠脂妥)"
            },
            {
                "atc7": "C10AA01",
                "en": "Simvastatin",
                "tc": "辛伐他汀",
                "brand": "Zocor (素果)"
            },
            {
                "atc7": "C10AA03",
                "en": "Pravastatin",
                "tc": "普伐他汀",
                "brand": "Mevalotin (美瓦洛)"
            }
        ]
    },
    "B01AF": {
        "atc_code": "B01AF",
        "class_name_en": "Direct factor Xa inhibitors (DOACs / NOACs)",
        "class_name_tc": "DOACs (新型口服抗凝血劑 / 直接Xa因子抑制劑)",
        "aliases": ["b01af", "b01af01", "b01af02", "b01af03", "b01ae07", "doac", "doacs", "noac", "noacs"],
        "ingredients": [
            {
                "atc7": "B01AF01",
                "en": "Rivaroxaban",
                "tc": "利伐沙班",
                "brand": "Xarelto (拜瑞妥)"
            },
            {
                "atc7": "B01AF02",
                "en": "Apixaban",
                "tc": "阿哌沙班",
                "brand": "Eliquis (艾利克)"
            },
            {
                "atc7": "B01AF03",
                "en": "Edoxaban",
                "tc": "艾多沙班",
                "brand": "Lixiana (里仙達)"
            },
            {
                "atc7": "B01AE07",
                "en": "Dabigatran",
                "tc": "達比加群",
                "brand": "Pradaxa (普達信)"
            }
        ]
    }
}

class ATCEngine:
    def __init__(self):
        self.atc_db = ATC_DATABASE
        self.who_db = WHO_ATC_DATABASE

    def expand_query(self, query):
        """Given a search query, return matching ATC classes and their associated ingredients."""
        q_clean = query.strip().lower()
        if not q_clean:
            return []

        matched_expansions = []

        # Check WHO ATC 7-Character Database
        for code7, info7 in self.who_db.items():
            if q_clean in [code7.lower(), info7["en"].lower(), info7["tc"].lower()]:
                matched_expansions.append({
                    "atc_code": info7["atc7"],
                    "class_name_en": info7["class_en"],
                    "class_name_tc": info7["class_tc"],
                    "reason": f"WHO ATC7 Direct Match: {info7['atc7']} ({info7['en']})",
                    "ingredients": [{"en": info7["en"], "tc": info7["tc"], "brand": info7["brand"], "atc7": info7["atc7"]}],
                    "aliases": [info7["atc7"].lower(), info7["en"].lower(), info7["tc"].lower()]
                })

        # Check Standard ATC Database
        for code, info in self.atc_db.items():
            is_match = False
            matched_reason = ""

            if q_clean == code.lower():
                is_match = True
                matched_reason = f"Exact ATC Code: {code}"

            if not is_match:
                for alias in info["aliases"]:
                    alias_clean = alias.lower()
                    if len(alias_clean) <= 4:
                        if re.search(r'\b' + re.escape(alias_clean) + r'\b', q_clean):
                            is_match = True
                            matched_reason = f"Matched Class Alias: {alias}"
                            break
                    else:
                        if alias_clean in q_clean or q_clean in alias_clean:
                            is_match = True
                            matched_reason = f"Matched Class Alias: {alias}"
                            break

            if not is_match:
                for ing in info["ingredients"]:
                    ing_en = ing["en"].lower()
                    ing_tc = ing["tc"].lower()
                    ing_atc7 = ing.get("atc7", "").lower()
                    brand_str = ing.get("brand", "").lower()
                    
                    if ing_atc7 and ing_atc7 == q_clean:
                        is_match = True
                        matched_reason = f"Matched 7-Char ATC Code: {ing.get('atc7')}"
                        break
                    if ing_en in q_clean or q_clean in ing_en:
                        is_match = True
                        matched_reason = f"Matched Ingredient: {ing['en']} ({ing['tc']})"
                        break
                    if ing_tc in q_clean or q_clean in ing_tc:
                        is_match = True
                        matched_reason = f"Matched Ingredient: {ing['tc']}"
                        break
                    if brand_str and (q_clean in brand_str or any(b in q_clean for b in re.findall(r'[a-zA-Z0-9\-]+|[\u4e00-\u9fa5]+', brand_str) if len(b)>1)):
                        is_match = True
                        matched_reason = f"Matched Trade Brand: {ing.get('brand')}"
                        break

            if is_match:
                matched_expansions.append({
                    "atc_code": info["atc_code"],
                    "class_name_en": info["class_name_en"],
                    "class_name_tc": info["class_name_tc"],
                    "reason": matched_reason,
                    "ingredients": info["ingredients"],
                    "aliases": info["aliases"]
                })

        return matched_expansions

    def find_related_terms(self, text):
        """Find ATC classes and ingredients mentioned in text."""
        text_lower = text.lower()
        found_classes = set()
        found_ingredients = set()

        for code, info in self.atc_db.items():
            class_matched = False
            for alias in info["aliases"]:
                if len(alias) <= 4:
                    if re.search(r'\b' + re.escape(alias.lower()) + r'\b', text_lower):
                        class_matched = True
                        break
                else:
                    if alias.lower() in text_lower:
                        class_matched = True
                        break
            if class_matched:
                found_classes.add(info["class_name_tc"])

            for ing in info["ingredients"]:
                if ing["en"].lower() in text_lower or ing["tc"].lower() in text_lower:
                    found_ingredients.add(f"{ing['en']} ({ing['tc']})")

        for code7, info7 in self.who_db.items():
            if info7["en"].lower() in text_lower or info7["tc"].lower() in text_lower:
                found_ingredients.add(f"{info7['en']} ({info7['tc']})")

        return list(found_classes), list(found_ingredients)

if __name__ == "__main__":
    engine = ATCEngine()
    print("Test L01FF02 (Pembrolizumab):", engine.expand_query("L01FF02"))
    print("Test L04AB04 (Adalimumab):", engine.expand_query("L04AB04"))
