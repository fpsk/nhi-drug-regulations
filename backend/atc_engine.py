import re
import os
import sqlite3
from backend.who_atc_database import WHO_ATC_DATABASE

# Comprehensive ATC (Anatomical Therapeutic Chemical) Classification Database
# Embedded with WHO 7-character Level 5 codes and Taiwan Traditional Chinese Brand Names

ATC_DATABASE = {
    "H05AA": {
        "atc_code": "H05AA",
        "class_name_en": "Parathyroid hormones and analogues / Osteoporosis Agents",
        "class_name_tc": "副甲狀腺素及類似劑 / 骨質疏鬆症治療藥物",
        "aliases": ["h05aa", "h05aa02", "teriparatide", "forteo", "骨復力", "復骨嚴", "骨質疏鬆", "副甲狀腺素"],
        "ingredients": [
            {
                "atc7": "H05AA02",
                "en": "Teriparatide",
                "tc": "特立帕肽 (副甲狀腺素)",
                "brand": "Forteo (骨復力 / 復骨嚴 / Forteo)"
            }
        ]
    },
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
        "aliases": ["a02bc", "a02bc01", "a02bc02", "a02bc03", "a02bc04", "a02bc05", "a02bc06", "ppi", "ppis", "質子泵抑制劑", "幫浦抑制劑", "氫離子幫浦", "氫離子幫浦阻斷劑", "消化性潰瘍用藥"],
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
            },
            {
                "atc7": "A02BC08",
                "en": "Vonoprazan",
                "tc": "沃諾拉贊",
                "brand": "Vocinti (富星錠)"
            }
        ]
    },
    "A02BA": {
        "atc_code": "A02BA",
        "class_name_en": "H2-receptor antagonists (H2 Blockers)",
        "class_name_tc": "H2受體阻斷劑 (乙型組織胺受體阻斷劑)",
        "aliases": ["a02ba", "a02ba01", "a02ba02", "a02ba03", "a02ba04", "h2 blocker", "h2-blocker", "h2ra", "乙型組織胺受體阻斷劑", "組織胺受體阻斷劑"],
        "ingredients": [
            {
                "atc7": "A02BA03",
                "en": "Famotidine",
                "tc": "法莫替丁",
                "brand": "Gaster (胃治潰)"
            },
            {
                "atc7": "A02BA01",
                "en": "Cimetidine",
                "tc": "西咪替丁",
                "brand": "Tagamet (泰胃美)"
            },
            {
                "atc7": "A02BA02",
                "en": "Ranitidine",
                "tc": "雷尼替丁",
                "brand": "Zantac (善胃得)"
            },
            {
                "atc7": "A02BA04",
                "en": "Nizatidine",
                "tc": "尼扎替丁",
                "brand": "Axid (艾胃得)"
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
        "aliases": ["c10aa", "c10aa01", "c10aa03", "c10aa05", "c10aa07", "statin", "statins", "降膽固醇藥", "降膽固醇", "降血脂藥", "降血脂", "血脂", "膽固醇"],
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
    "M01AH": {
        "atc_code": "M01AH",
        "class_name_en": "Coxibs (Selective COX-2 Inhibitors)",
        "class_name_tc": "選擇性COX-2抑制劑 (非類固醇抗發炎劑)",
        "aliases": ["m01ah", "m01ah01", "celebrex", "celecoxib", "西樂葆", "希樂葆", "關節炎", "止痛藥", "非類固醇抗發炎劑"],
        "ingredients": [
            {
                "atc7": "M01AH01",
                "en": "Celecoxib",
                "tc": "塞來昔布",
                "brand": "Celebrex (西樂葆 / 希樂葆 / Celebrex)"
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
    },
    "J05AF": {
        "atc_code": "J05AF",
        "class_name_en": "Nucleoside and nucleotide reverse transcriptase inhibitors / B-hepatitis antivirals",
        "class_name_tc": "核苷及核苷酸反轉錄酶抑制劑 / B型肝炎口服抗病毒藥物",
        "aliases": ["j05af", "j05af07", "j05af13", "j05af10", "j05af05", "tenofovir", "entecavir", "lamivudine", "viread", "vemlidy", "baraclude", "zeffix", "韋立得", "惠立妥", "貝樂克", "干安能", "B型肝炎"],
        "ingredients": [
            {
                "atc7": "J05AF07",
                "en": "Tenofovir disoproxil",
                "tc": "替諾福韋雙索酯",
                "brand": "Viread (惠立妥 / 雷克威 / 坦立普 / Viread)"
            },
            {
                "atc7": "J05AF13",
                "en": "Tenofovir alafenamide",
                "tc": "替諾福韋丙酚酚胺",
                "brand": "Vemlidy (韋立得 / Vemlidy)"
            },
            {
                "atc7": "J05AF10",
                "en": "Entecavir",
                "tc": "恩替卡韋",
                "brand": "Baraclude (貝樂克 / Baraclude)"
            },
            {
                "atc7": "J05AF05",
                "en": "Lamivudine",
                "tc": "拉米夫定",
                "brand": "Zeffix (干安能 / Zeffix)"
            }
        ]
    },
    "J05AR": {
        "atc_code": "J05AR",
        "class_name_en": "Antivirals for treatment of HIV infections, combinations",
        "class_name_tc": "HIV抗病毒藥物複方製劑 (人類免疫缺乏病毒)",
        "aliases": ["j05ar", "j05ar03", "j05ar18", "j05ar20", "truvada", "biktarvy", "genvoya", "hiv", "愛滋病", "愛滋", "抗人類免疫缺乏病毒藥品"],
        "ingredients": [
            {
                "atc7": "J05AR20",
                "en": "Bictegravir / Emtricitabine / Tenofovir Alafenamide",
                "tc": "比克替拉韋複方 (如 Biktarvy 必妥維)",
                "brand": "Biktarvy (必妥維)"
            },
            {
                "atc7": "J05AR13",
                "en": "Dolutegravir / Abacavir / Lamivudine",
                "tc": "多替拉韋複方 (如 Triumeq 綏美凱)",
                "brand": "Triumeq (綏美凱)"
            },
            {
                "atc7": "J05AR18",
                "en": "Elvitegravir / Cobicistat / Emtricitabine / Tenofovir",
                "tc": "艾維雷韋複方 (如 Genvoya 捷扶康)",
                "brand": "Genvoya (捷扶康)"
            },
            {
                "atc7": "J05AR03",
                "en": "Emtricitabine / Tenofovir",
                "tc": "恩曲他濱複方 (如 Truvada 舒發泰 / Descovy 達可揮)",
                "brand": "Truvada (舒發泰), Descovy (達可揮)"
            }
        ]
    },
    "S01ED": {
        "atc_code": "S01ED",
        "class_name_en": "Antiglaucoma preparations and miotics",
        "class_name_tc": "青光眼及高眼壓眼用製劑 (前列腺素衍生物 / β-阻斷劑 / 碳酸酐酶抑制劑)",
        "aliases": ["s01ed", "s01ee", "s01ec", "s01ea", "高眼壓及青光眼眼用製劑", "青光眼眼用製劑", "β-交感神經阻斷劑", "碳酸酐酶抑制劑", "前列腺素衍生物"],
        "ingredients": [
            {
                "atc7": "S01EE01",
                "en": "Latanoprost",
                "tc": "拉坦前列素 (如 Xalatan 舒而坦)",
                "brand": "Xalatan (舒而坦)"
            },
            {
                "atc7": "S01EE04",
                "en": "Travoprost",
                "tc": "曲伏前列素 (如 Travatan 舒壓坦)",
                "brand": "Travatan (舒壓坦)"
            },
            {
                "atc7": "S01EE03",
                "en": "Bimatoprost",
                "tc": "比馬前列素 (如 Lumigan 盧美根)",
                "brand": "Lumigan (盧美根)"
            },
            {
                "atc7": "S01EE05",
                "en": "Tafluprost",
                "tc": "他氟前列素 (如 Tapros 泰普羅斯)",
                "brand": "Tapros (泰普羅斯)"
            },
            {
                "atc7": "S01ED01",
                "en": "Timolol",
                "tc": "噻嗎洛爾 (如 Timoptol 青眼露)",
                "brand": "Timoptol (青眼露)"
            },
            {
                "atc7": "S01ED05",
                "en": "Carteolol",
                "tc": "卡替洛爾 (如 Mikelan 美開朗)",
                "brand": "Mikelan (美開朗)"
            },
            {
                "atc7": "S01EA05",
                "en": "Brimonidine",
                "tc": "溴莫尼定 (如 Alphagan 艾弗目)",
                "brand": "Alphagan (艾弗目)"
            },
            {
                "atc7": "S01EC03",
                "en": "Dorzolamide",
                "tc": "多佐胺 (如 Trusopt 舒露達)",
                "brand": "Trusopt (舒露達)"
            },
            {
                "atc7": "S01EC04",
                "en": "Brinzolamide",
                "tc": "布林佐胺 (如 Azopt 派頓)",
                "brand": "Azopt (派頓)"
            }
        ]
    },
    "S01XA": {
        "atc_code": "S01XA",
        "class_name_en": "Artificial tears and ocular lubricants",
        "class_name_tc": "人工淚液 / 乾眼症眼用製劑",
        "aliases": ["s01xa", "s01xa20", "人工淚液", "乾眼症眼用製劑"],
        "ingredients": [
            {
                "atc7": "S01XA20",
                "en": "Sodium Hyaluronate",
                "tc": "玻尿酸鈉人工淚液 (如 Hialid 愛麗點眼液)",
                "brand": "Hialid (愛麗點眼液)"
            },
            {
                "atc7": "S01XA20",
                "en": "Hypromellose / Carboxymethylcellulose",
                "tc": "纖維素類人工淚液 (如 Refresh / Tears Naturale)",
                "brand": "Refresh, Tears Naturale"
            },
            {
                "atc7": "S01XA20",
                "en": "Carbomer",
                "tc": "卡波姆眼用凝膠 (如 Vidisic 維蒂斯)",
                "brand": "Vidisic (維蒂斯)"
            }
        ]
    },
    "N06AB": {
        "atc_code": "N06AB",
        "class_name_en": "SSRIs / SNRIs / Antidepressants",
        "class_name_tc": "抗憂鬱劑 (SSRI / SNRI / 選擇性血清促進素再吸收抑制劑)",
        "aliases": ["n06ab", "n06ax", "ssri", "snri", "選擇性血清促進素再吸收抑制劑", "血清促進素及正腎上腺素再吸收抑制劑"],
        "ingredients": [
            {
                "atc7": "N06AB03",
                "en": "Fluoxetine",
                "tc": "氟西汀 (如 Prozac 百憂解)",
                "brand": "Prozac (百憂解)"
            },
            {
                "atc7": "N06AB06",
                "en": "Sertraline",
                "tc": "捨曲林 (如 Zoloft 樂復得)",
                "brand": "Zoloft (樂復得)"
            },
            {
                "atc7": "N06AB10",
                "en": "Escitalopram",
                "tc": "艾司西酞普蘭 (如 Lexapro 立普能)",
                "brand": "Lexapro (立普能)"
            },
            {
                "atc7": "N06AB05",
                "en": "Paroxetine",
                "tc": "帕羅西汀 (如 Seroxat 克憂果)",
                "brand": "Seroxat (克憂果)"
            },
            {
                "atc7": "N06AX16",
                "en": "Venlafaxine",
                "tc": "文拉法辛 (如 Efexor 速悅)",
                "brand": "Efexor (速悅)"
            },
            {
                "atc7": "N06AX21",
                "en": "Duloxetine",
                "tc": "度洛西汀 (如 Cymbalta 千憂解)",
                "brand": "Cymbalta (千憂解)"
            }
        ]
    },
    "N05AH": {
        "atc_code": "N05AH",
        "class_name_en": "Second generation antipsychotics (Atypical antipsychotics)",
        "class_name_tc": "第二代抗精神病藥品 (非典型抗精神病藥物)",
        "aliases": ["n05ah", "n05ax", "second generation antipsychotics", "第二代抗精神病藥品"],
        "ingredients": [
            {
                "atc7": "N05AX08",
                "en": "Risperidone",
                "tc": "利培酮 (如 Risperdal 理思必妥)",
                "brand": "Risperdal (理思必妥)"
            },
            {
                "atc7": "N05AH03",
                "en": "Olanzapine",
                "tc": "奧氮平 (如 Zyprexa 金普薩)",
                "brand": "Zyprexa (金普薩)"
            },
            {
                "atc7": "N05AH04",
                "en": "Quetiapine",
                "tc": "喹硫平 (如 Seroquel 思樂康)",
                "brand": "Seroquel (思樂康)"
            },
            {
                "atc7": "N05AX12",
                "en": "Aripiprazole",
                "tc": "阿立哌唑 (如 Abilify 安立復)",
                "brand": "Abilify (安立復)"
            },
            {
                "atc7": "N05AX13",
                "en": "Paliperidone",
                "tc": "帕利哌酮 (如 Invega 思維佳)",
                "brand": "Invega (思維佳)"
            },
            {
                "atc7": "N05AE05",
                "en": "Lurasidone",
                "tc": "魯拉西酮 (如 Latuda 樂途達)",
                "brand": "Latuda (樂途達)"
            }
        ]
    }
}

# Class-level regulation mapping (used when a 7-char ATC code does not have its own specific section override)
CLASS_REGULATION_MAPPING = {
    "C10AA": "2.6.1",   # Statins -> Lipids Table
    "M01AH": "1.1.5",   # Coxibs -> NSAIDs
    "H05AA": "5.6.2",   # Teriparatide -> Osteoporosis
    "L01FF": "9.69",    # PD-1/PD-L1 -> Immunotherapy
    "A10BK": "2.16",    # SGLT2 -> Heart Failure / CKD / Diabetes
    "A10BJ": "5.1.3",   # GLP-1 -> Diabetes / Obesity
    "A02BC": "7.1",     # PPIs -> Peptic Ulcer Drugs
    "A02BA": "7.1",     # H2 Blockers -> Peptic Ulcer Drugs
    "A05BA": "3.3.1",   # Hepatoprotectants -> Liver Therapy
    "B01AF": "2.1.4",   # Direct Xa inhibitors -> Anticoagulants
    "L04AB": "8.2.4",   # TNF-alpha -> Rheumatoid Arthritis
    "L04AC": "8.2.4",   # IL inhibitors -> Rheumatoid Arthritis
    "J05AF": "10.7.3",  # B-hepatitis antivirals -> HBV
    "J05AR": "10.9",    # HIV antivirals -> HIV
    "S01ED": "14.1",    # Glaucoma eye drops -> Glaucoma
    "S01XA": "14.5",    # Artificial tears -> Dry Eye
    "N06AB": "1.2.1",   # SSRIs/SNRIs -> Antidepressants
    "N05AH": "1.2.2.2", # Second generation antipsychotics
    "L01CD": "9.137",   # Taxanes (Cabazitaxel)
    "J01DI": "10.3.8",  # Siderophore cephalosporins (Cefiderocol)
    "B02BX": "4.2.8",   # Hemophilia siRNA (Fitusiran)
    "A16AX": "3.3.32",  # IBAT inhibitors (Maralixibat)
}


class ATCEngine:
    def __init__(self):
        self.atc_db = ATC_DATABASE
        self.who_db = WHO_ATC_DATABASE
        self._expand_cache = {}
        self._fuzzy_vocab = None  # Lazy-initialized bucketed vocabulary from SQLite
        self._db_ingredients_map = None  # Lazy-initialized ingredient -> Chinese/ATC map

    def _ensure_vocab_loaded(self):
        """Load distinct English brand tokens and generic ingredients once into memory buckets by first character."""
        if self._fuzzy_vocab is not None:
            return
        self._fuzzy_vocab = {}
        self._db_ingredients_map = {}
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT english_name, ingredient, chinese_name, atc_code FROM nhi_drugs")
            for eng, ing, chi, atc in cursor.fetchall():
                if eng:
                    first = eng.split()[0].lower()
                    if len(first) >= 4 and first.isalpha():
                        self._fuzzy_vocab.setdefault(first[0], set()).add(('english_name', first))
                if ing:
                    ing_low = ing.strip().lower()
                    if len(ing_low) >= 4:
                        self._fuzzy_vocab.setdefault(ing_low[0], set()).add(('ingredient', ing_low))
                        if ing_low not in self._db_ingredients_map and atc:
                            self._db_ingredients_map[ing_low] = {
                                "en": ing.strip().title(),
                                "tc": self.clean_taiwan_brand(chi) if chi else "",
                                "atc": atc
                            }
                        ing_base = ing_low.split()[0]
                        if (
                            len(ing_base) >= 5
                            and ing_base.isalpha()
                            and ing_base not in {"sodium", "calcium", "potassium", "magnesium", "human", "extract", "solution", "water", "glucose", "vitamin", "compound", "normal", "sterile", "purified", "dried", "activated"}
                            and ing_base not in self._db_ingredients_map
                            and atc
                        ):
                            self._db_ingredients_map[ing_base] = {
                                "en": ing_base.title(),
                                "tc": self.clean_taiwan_brand(chi) if chi else "",
                                "atc": atc
                            }
            conn.close()
        except Exception:
            pass

    def parse_brand(self, brand_str):
        if not brand_str:
            return "", []
        match = re.match(r'^([^\(]+)\s*\((.*?)\)', brand_str)
        if match:
            brand_en = match.group(1).strip()
            parts = [p.strip() for p in match.group(2).split('/')]
            brand_tc = [p for p in parts if any(ord(c) > 127 for c in p)]
            if not brand_tc:
                brand_tc = [p for p in parts if p.lower() != brand_en.lower()]
            return brand_en, brand_tc
        return brand_str.strip(), []

    def levenshtein_distance(self, s1, s2):
        if abs(len(s1) - len(s2)) > 2:
            return 3
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        if len(s2) == 0:
            return len(s1)
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            min_in_row = current_row[0]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                val = insertions if insertions < deletions else deletions
                if substitutions < val:
                    val = substitutions
                current_row.append(val)
                if val < min_in_row:
                    min_in_row = val
            if min_in_row > 2:
                return 3
            previous_row = current_row
        return previous_row[-1]

    def is_fuzzy_match(self, q, target):
        q = q.lower()
        target = target.lower()
        if len(q) < 4 or len(target) < 4:
            return q == target
        if abs(len(q) - len(target)) > 2:
            return False

        d = self.levenshtein_distance(q, target)
        if d <= 2:
            return True

        if abs(len(q) - len(target)) <= 1:
            s1 = set(q)
            s2 = set(target)
            intersection = len(s1.intersection(s2))
            union = len(s1.union(s2))
            if union > 0 and (intersection / union) >= 0.85:
                return True
        return False

    def clean_taiwan_brand(self, name):
        if not name:
            return ""
        parts = [p.strip() for p in re.split(r'[\"\'”’“‘]', name) if p.strip()]
        part = parts[-1] if parts else name
        part = re.sub(r'[\(（].*?[\)）]', '', part)
        for word in ['膜衣錠', '糖衣錠', '緩釋錠', '持續錠', '咀嚼錠', '舌下錠', '錠',
                     '軟膠囊', '硬膠囊', '持續性膠囊', '膠囊',
                     '濃縮注射液', '乾粉注射劑', '注射液', '注射劑', '針劑',
                     '點眼液', '點鼻液', '吸入劑', '噴霧劑', '乳膏', '軟膏', '凝膠', '藥膏',
                     '毫克', '微克', '公克', '公絲', '公撮', '國際單位', '毫升']:
            part = part.replace(word, '')
        part = re.sub(r'[A-Za-z0-9\.\-\%\/\s\+\,\*\#\_]+', '', part)
        part = re.sub(r'[０-９ａ-ｚＡ-Ｚ％（）＆＋，。]+', '', part)
        return part.strip()

    def get_db_connection(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nhi_drugs.db')
        return sqlite3.connect(db_path)

    def expand_query(self, query):
        """Given a search query, return matching ATC classes and their associated ingredients with rich metadata and fast spelling tolerance."""
        q_clean = query.strip().lower()
        if not q_clean:
            return []

        if q_clean in self._expand_cache:
            return self._expand_cache[q_clean]

        # Skip ATC drug expansion for pure section numbers (e.g., "9.124", "2.16.")
        if re.match(r'^\d+(\.\d+)+\.?$', q_clean):
            self._expand_cache[q_clean] = []
            return []

        matched_expansions = []

        # Step 1: Check WHO ATC Database first for exact/curated 7-char ATC, ingredient, or brand matches
        for atc7, winfo in self.who_db.items():
            atc_code = winfo.get("atc7", atc7)
            class_code = winfo.get("atc5", atc_code[:5])
            brand_str = winfo.get("brand", "")
            en_name = winfo.get("en", "")
            tc_name = winfo.get("tc", "")

            match = (
                q_clean == atc_code.lower() or
                q_clean == class_code.lower() or
                (len(q_clean) >= 3 and q_clean in en_name.lower()) or
                (len(q_clean) >= 2 and q_clean in tc_name.lower()) or
                (len(q_clean) >= 3 and q_clean in brand_str.lower())
            )
            if match:
                if not any(x.get("atc_code") == atc_code for x in matched_expansions):
                    brand_en, brand_tc = self.parse_brand(brand_str)
                    matched_expansions.append({
                        "atc_code": atc_code,
                        "class_code": class_code,
                        "class_name_en": winfo.get("class_en", "Therapeutic Class"),
                        "class_name_tc": winfo.get("class_tc", "治療類別"),
                        "ingredient_en": en_name,
                        "ingredient_tc": tc_name,
                        "brand_en": brand_en or en_name,
                        "brand_tc": brand_tc if brand_tc else [tc_name],
                        "is_brand": q_clean in brand_str.lower(),
                        "is_chinese": any(ord(c) > 127 for c in q_clean),
                        "searched_term": query,
                        "aliases": [atc_code.lower(), class_code.lower(), en_name.lower(), tc_name.lower()],
                        "primary_regulation": winfo.get("primary_regulation", "")
                    })

        # Step 2: Check standard class database for alias/code matching (e.g., 'statins', 'sglt2')
        for code, info in self.atc_db.items():
            if q_clean == code.lower() or any(q_clean == alias.lower() for alias in info.get("aliases", [])):
                if not any(x.get("class_code") == code for x in matched_expansions):
                    primary_regulation = CLASS_REGULATION_MAPPING.get(code, "")
                    matched_expansions.append({
                        "atc_code": info["atc_code"],
                        "class_code": info["atc_code"],
                        "class_name_en": info["class_name_en"],
                        "class_name_tc": info["class_name_tc"],
                        "ingredient_en": "",
                        "ingredient_tc": "",
                        "brand_en": "",
                        "brand_tc": [],
                        "is_brand": False,
                        "is_chinese": any(ord(c) > 127 for c in q_clean),
                        "searched_term": query,
                        "aliases": info.get("aliases", []),
                        "primary_regulation": primary_regulation
                    })

        # Step 3: Substring/exact search in SQLite
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nhi_code, english_name, chinese_name, ingredient, atc_code, form, price
            FROM nhi_drugs
            WHERE nhi_code = ? 
               OR atc_code = ? 
               OR english_name LIKE ? 
               OR chinese_name LIKE ? 
               OR ingredient LIKE ?
            LIMIT 50
        """, (q_clean.upper(), q_clean.upper(), f"%{q_clean}%", f"%{q_clean}%", f"%{q_clean}%"))
        rows = cursor.fetchall()

        # Step 4: Fast bucketed fuzzy matching ONLY if no matches found yet and query is an English drug-like word
        if not rows and not matched_expansions and len(q_clean) >= 5 and re.match(r'^[a-z]+$', q_clean):
            self._ensure_vocab_loaded()
            bucket = self._fuzzy_vocab.get(q_clean[0], set())
            candidates = []
            for typ, cand in bucket:
                if abs(len(q_clean) - len(cand)) <= 2 and self.is_fuzzy_match(q_clean, cand):
                    candidates.append((typ, cand))
                    if len(candidates) >= 3:
                        break

            for typ, val in candidates:
                if typ == 'english_name':
                    cursor.execute("""
                        SELECT nhi_code, english_name, chinese_name, ingredient, atc_code, form, price
                        FROM nhi_drugs
                        WHERE english_name LIKE ?
                        LIMIT 10
                    """, (f"{val}%",))
                else:
                    cursor.execute("""
                        SELECT nhi_code, english_name, chinese_name, ingredient, atc_code, form, price
                        FROM nhi_drugs
                        WHERE ingredient = ?
                        LIMIT 10
                    """, (val.upper(),))
                rows.extend(cursor.fetchall())

        conn.close()

        # Step 5: Process SQLite rows into standardized expansions grouped by ATC
        atc_groups = {}
        for nhi_code, eng, chi, ing, atc, form, price in rows:
            if not atc:
                continue

            if atc not in atc_groups:
                atc_groups[atc] = {
                    "nhi_code": nhi_code,
                    "eng_name": eng,
                    "chi_name": chi,
                    "ingredient": ing,
                    "form": form,
                    "price": price,
                    "brands_en": set(),
                    "brands_tc": set()
                }

            brand_en, brand_tc = self.parse_brand(f"{eng} ({chi})")
            if brand_en:
                clean_eng = brand_en.split()[0].title()
                if clean_eng.replace('.', '').replace('-', '').isalnum():
                    atc_groups[atc]["brands_en"].add(clean_eng)

            clean_tc = self.clean_taiwan_brand(chi)
            if clean_tc:
                atc_groups[atc]["brands_tc"].add(clean_tc)
            elif brand_tc:
                for b in brand_tc:
                    atc_groups[atc]["brands_tc"].add(b)

        for atc, data in atc_groups.items():
            if any(x.get("atc_code") == atc for x in matched_expansions):
                continue
            class_code = atc[:5] if len(atc) >= 5 else atc

            class_info = self.atc_db.get(class_code, {})
            who_info = self.who_db.get(atc, {})
            class_name_en = who_info.get("class_en") or class_info.get("class_name_en", "Therapeutic Class")
            class_name_tc = who_info.get("class_tc") or class_info.get("class_name_tc", "治療類別")
            class_aliases = class_info.get("aliases", [])

            brand_en_list = sorted(list(data["brands_en"]))
            brand_tc_list = sorted(list(data["brands_tc"]))

            brand_en_str = ", ".join(brand_en_list) if brand_en_list else data["eng_name"].split()[0].title()
            # Prefer exact 7-character WHO primary regulation over 5-character class fallback
            primary_regulation = who_info.get("primary_regulation") or CLASS_REGULATION_MAPPING.get(class_code, "")

            matched_expansions.append({
                "atc_code": atc,
                "class_code": class_code,
                "class_name_en": class_name_en,
                "class_name_tc": class_name_tc,
                "ingredient_en": data["ingredient"].title(),
                "ingredient_tc": who_info.get("tc") or (data["chi_name"].split('膠囊')[0].split('膜衣錠')[0].strip() if data["chi_name"] else ""),
                "brand_en": brand_en_str,
                "brand_tc": brand_tc_list,
                "is_brand": q_clean in brand_en_str.lower() or any(q_clean in b.lower() for b in brand_tc_list),
                "is_chinese": any(ord(c) > 127 for c in q_clean),
                "searched_term": query,
                "aliases": class_aliases + [atc.lower(), data["ingredient"].lower()],
                "primary_regulation": primary_regulation
            })

        if len(self._expand_cache) >= 1024:
            self._expand_cache.clear()
        self._expand_cache[q_clean] = matched_expansions
        return matched_expansions

    def find_related_terms(self, text):
        """Find ATC classes and ingredients mentioned in text (including section title drug patterns)."""
        # Strip concomitant background medication clauses (e.g. antiplatelets/anticoagulants in 7.1. Clause 2.(5))
        cleaned_text = re.sub(r'而需使用[^。；]*?病人得以使用', '病人得以使用', text)
        text_lower = cleaned_text.lower()
        header_lower = cleaned_text[:300].lower()
        title_lower = cleaned_text.split('\n', 1)[0].lower()

        found_classes = set()
        primary_ingredients = set()
        secondary_ingredients = set()

        is_class_section_title = (
            not re.search(r'[a-z]{4,}', title_lower)
            or 'antipsychotics' in title_lower
            or 'ssri' in title_lower
            or 'nsaid' in title_lower
        )

        for code, info in self.atc_db.items():
            class_matched = False
            class_in_header = False
            for alias in info["aliases"]:
                alias_low = alias.lower()
                if re.match(r'^[a-z0-9\-\s]+$', alias_low):
                    pat = r'(?<![a-z0-9])' + re.escape(alias_low) + r'(?![a-z0-9])'
                    if re.search(pat, text_lower):
                        class_matched = True
                        if re.search(pat, header_lower):
                            class_in_header = True
                            break
                else:
                    if alias_low in text_lower:
                        class_matched = True
                        if alias_low in header_lower:
                            class_in_header = True
                            break
            if class_matched:
                found_classes.add(info["class_name_tc"])
                # When a pharmacological class is the subject of a class-level section header/藥品種類, populate its representative drugs
                if is_class_section_title and class_in_header and code in {"A02BC", "A02BA", "A05BA", "C10AA", "J05AR", "S01ED", "S01XA", "N06AB", "N05AH"}:
                    for ing in info["ingredients"]:
                        primary_ingredients.add(f"{ing['en']} ({ing['tc']})")

            for ing in info["ingredients"]:
                en_low = ing["en"].lower()
                tc_low = ing["tc"].lower()
                if en_low in text_lower or tc_low in text_lower:
                    label = f"{ing['en']} ({ing['tc']})"
                    if en_low in title_lower or tc_low in title_lower:
                        primary_ingredients.add(label)
                    else:
                        secondary_ingredients.add(label)

        for code7, info7 in self.who_db.items():
            en_low = info7["en"].lower()
            tc_low = info7["tc"].lower()
            if en_low in text_lower or tc_low in text_lower:
                label = f"{info7['en']} ({info7['tc']})"
                if en_low in title_lower or tc_low in title_lower:
                    primary_ingredients.add(label)
                else:
                    secondary_ingredients.add(label)

        # Also extract explicit "GenericName (如BrandName)" patterns across title and body text
        stopwords = {
            "level", "stage", "class", "grade", "score", "type", "phase", "group", "table",
            "child-pugh", "nyha", "ecog", "era", "sglt2", "sglt-2", "nsaid", "nsaids", "dmard", "dmards",
            "immune", "factor", "recombinant", "human", "tablets", "injection", "solution", "capsules"
        }
        for m in re.finditer(r'([A-Za-z][A-Za-z0-9\-\+\.\/\s]{2,45}?)\s*(?:注射劑|口服製劑|內服液劑|緩釋劑型|眼用製劑|外用製劑|栓劑|植入劑|凍晶注射劑|膠囊|錠劑)?\s*[（\(]\s*[:：]?如\s*[:：]?\s*([^）\)]+)[）\)]', cleaned_text):
            gen_name = m.group(1).strip()
            brand_name = m.group(2).strip().split('、')[0].split('，')[0].split(',')[0].split('；')[0].split(';')[0].strip()
            # Clean leading section numbers or trailing dosage tokens
            gen_name = re.sub(r'^(?:\d+(?:\.\d+)*\.?\s*)+', '', gen_name).strip()
            gen_name = re.sub(r'\s+\d+(?:\.\d+)?\s*(?:mg|mcg|ug|g|ml|iu|%)\b.*$', '', gen_name, flags=re.IGNORECASE).strip()
            all_existing = primary_ingredients | secondary_ingredients
            if len(gen_name) >= 3 and gen_name.lower() not in stopwords and not any(gen_name.lower() in existing.lower() for existing in all_existing):
                label = f"{gen_name.title()} (如 {brand_name})"
                if m.start() <= len(title_lower):
                    primary_ingredients.add(label)
                else:
                    secondary_ingredients.add(label)

        # Match single-word generic ingredient names from NHI drug master DB (using ASCII boundary so Chinese-adjacent words match)
        self._ensure_vocab_loaded()
        if self._db_ingredients_map:
            for word in set(re.findall(r'[a-z]{5,}', text_lower)):
                if word in self._db_ingredients_map and word not in stopwords:
                    all_existing = primary_ingredients | secondary_ingredients
                    if not any(word in existing.lower() for existing in all_existing):
                        if word in title_lower:
                            primary_ingredients.add(word.title())
                        else:
                            secondary_ingredients.add(word.title())

        ordered_ingredients = sorted(list(primary_ingredients)) + [
            x for x in sorted(list(secondary_ingredients)) if x not in primary_ingredients
        ]
        return sorted(list(found_classes)), ordered_ingredients


if __name__ == "__main__":
    engine = ATCEngine()
    print("Test Forteo expansion:", engine.expand_query("forteo"))
    print("Test Teriparatide expansion:", engine.expand_query("teriparatide"))
