import re

# Comprehensive Medical Disease & Condition Ontology for Taiwan NHI Regulations
# Ensures 100% bilingual translation across Oncology, Gastroenterology, Rheumatology,
# Neurology, Dermatology, Cardiology, Hematology, Endocrinology, and Clinical Nutrition / Vitamins.

DISEASE_DATABASE = {
    # Vitamin & Nutrient Deficiency Indications (維生素與營養缺乏症 - 附表三-A)
    "scurvy": {
        "en": "Scurvy (Vitamin C Deficiency)",
        "tc_terms": ["壞血病"],
        "aliases": ["scurvy", "vitamin c deficiency"]
    },
    "rickets": {
        "en": "Rickets / Osteomalacia (Vitamin D Deficiency)",
        "tc_terms": ["佝僂病", "骨軟化症", "尿毒症腎性骨質病變"],
        "aliases": ["rickets", "osteomalacia", "renal osteodystrophy"]
    },
    "night_blindness": {
        "en": "Night Blindness / Xerophthalmia (Vitamin A Deficiency)",
        "tc_terms": ["夜盲症", "眼球乾燥症", "角膜軟化症", "皮膚角化異常症"],
        "aliases": ["night blindness", "xerophthalmia", "keratomalacia"]
    },
    "pellagra": {
        "en": "Pellagra (Niacin / Vitamin B3 Deficiency)",
        "tc_terms": ["癩皮症"],
        "aliases": ["pellagra", "niacin deficiency"]
    },
    "megaloblastic_anemia": {
        "en": "Megaloblastic Anemia (Vitamin B12 / Folic Acid Deficiency)",
        "tc_terms": ["巨球性貧血", "巨大紅血球貧血症"],
        "aliases": ["megaloblastic anemia", "vitamin b12 deficiency", "folic acid deficiency"]
    },
    "beriberi_thiamine": {
        "en": "Thiamine Deficiency / Malabsorption Syndrome (Vitamin B1)",
        "tc_terms": ["維生素B1缺乏症", "營養吸收障礙症候群", "酒精戒斷症候群"],
        "aliases": ["thiamine deficiency", "beriberi", "malabsorption syndrome", "alcohol withdrawal syndrome"]
    },
    "angular_cheilitis": {
        "en": "Angular Cheilitis (Vitamin B2 Deficiency)",
        "tc_terms": ["口角炎"],
        "aliases": ["angular cheilitis", "vitamin b2 deficiency"]
    },

    # Hepatology & Gastroenterology (肝膽與腸胃)
    "hepatoprotectants": {
        "en": "Hepatoprotectants / Liver Protective Agents",
        "tc_terms": ["肝庇護劑", "保肝劑", "護肝劑", "水飛薊素", "水飛薊", "西利馬林", "利加隆", "熊去氧膽酸", "優思", "強體力蒙", "合寶麥斯"],
        "aliases": [
            "hepatoprotectant", "hepatoprotectants", "hepatoprotective agent", "hepatoprotective agents", 
            "liver protective agent", "liver protective agents", "hepatoprotective",
            "silymarin", "silybin", "legalon", "silygen", "hepalgen", "silybon", "silyrin", "silybest", "kewei",
            "ursodeoxycholic acid", "ursodiol", "udca", "urso",
            "ornithine", "aspartate", "hepa-merz", "hepaneed",
            "glycyrrhizin", "snmc", "minophagen"
        ]
    },
    "cirrhosis": {
        "en": "Liver Cirrhosis",
        "tc_terms": ["肝硬化", "代償性肝硬化", "失代償性肝硬化", "代償不全肝硬化"],
        "aliases": ["cirrhosis", "liver cirrhosis", "hepatic cirrhosis"]
    },
    "hepatitis": {
        "en": "Hepatitis B / Hepatitis C (HBV DNA / HCV RNA)",
        "tc_terms": ["肝炎", "慢性B型肝炎", "慢性C型肝炎", "B型肝炎", "C型肝炎", "急性肝炎", "肝炎發作", "B型肝炎病毒量", "血清HBV DNA"],
        "aliases": ["hepatitis", "hbv", "hcv", "hepatitis b", "hepatitis c", "hbvdna", "hbv dna", "hbv-dna", "hcvrna", "hcv rna", "hcv-rna"]
    },
    "liver_cancer": {
        "en": "Liver Cancer / Hepatocellular Carcinoma",
        "tc_terms": ["肝癌", "肝細胞癌"],
        "aliases": ["liver cancer", "hcc"]
    },
    "ulcerative_colitis": {
        "en": "Ulcerative Colitis (UC)",
        "tc_terms": ["潰瘍性結腸炎", "潰瘍性大腸炎"],
        "aliases": ["ulcerative colitis", "uc"]
    },
    "crohn_disease": {
        "en": "Crohn's Disease (CD)",
        "tc_terms": ["克隆氏症", "克羅恩病"],
        "aliases": ["crohn's disease", "crohns", "cd"]
    },
    "ibd": {
        "en": "Inflammatory Bowel Disease (IBD)",
        "tc_terms": ["發炎性腸道疾病", "炎症性腸病"],
        "aliases": ["inflammatory bowel disease", "ibd"]
    },
    "peptic_ulcer": {
        "en": "Peptic Ulcer Disease",
        "tc_terms": ["消化性潰瘍", "胃潰瘍", "十二指腸潰瘍", "潰瘍穿孔"],
        "aliases": ["peptic ulcer", "pud", "gastric ulcer", "duodenal ulcer", "ulcer"]
    },
    "gerd": {
        "en": "Gastroesophageal Reflux Disease",
        "tc_terms": ["逆流性食道炎", "胃食道逆流症", "胃食道逆流", "Barrett"],
        "aliases": ["gerd", "reflux esophagitis", "reflux", "barrett's esophagus"]
    },
    "gi_bleeding": {
        "en": "Gastrointestinal Bleeding / Hemorrhage",
        "tc_terms": ["消化道出血", "上消化道出血", "胃腸道出血", "出血", "蜘蛛膜下出血"],
        "aliases": ["bleeding", "gi bleeding", "upper gi bleeding", "ugib", "hemorrhage", "haemorrhage", "subarachnoid hemorrhage"]
    },
    "prophylaxis_prevention": {
        "en": "Disease / Ulcer / Bleeding Prevention & Prophylaxis",
        "tc_terms": ["預防", "復發預防", "壓力性潰瘍"],
        "aliases": ["prevention", "prophylaxis", "prevent", "stress ulcer"]
    },
    "h_pylori": {
        "en": "Helicobacter pylori Infection",
        "tc_terms": ["幽門螺旋桿菌"],
        "aliases": ["h. pylori", "h pylori", "helicobacter pylori"]
    },
    "nausea_vomiting": {
        "en": "Nausea and Vomiting (CINV / Antiemetic)",
        "tc_terms": ["止吐", "噁心", "嘔吐"],
        "aliases": ["nausea", "vomiting", "emesis", "antiemetic", "cinv"]
    },
    "diarrhea": {
        "en": "Diarrhea",
        "tc_terms": ["腹瀉", "止瀉"],
        "aliases": ["diarrhea", "diarrhoea", "antidiarrheal"]
    },
    "constipation": {
        "en": "Constipation",
        "tc_terms": ["便祕", "便秘", "瀉劑"],
        "aliases": ["constipation", "laxative"]
    },
    "pancreatitis_short_bowel": {
        "en": "Pancreatitis / Pancreatic Insufficiency / Short Bowel Syndrome",
        "tc_terms": ["胰臟炎", "慢性胰臟炎", "嚴重胰臟炎", "胰液分泌不全", "囊狀性纖維化", "短腸症"],
        "aliases": ["pancreatitis", "pancreatic insufficiency", "cystic fibrosis", "short bowel syndrome"]
    },

    # Oncology (癌症與腫瘤)
    "triple_negative_breast_cancer": {
        "en": "Triple-Negative Breast Cancer (TNBC)",
        "tc_terms": ["三陰性乳癌", "轉移性三陰性乳癌"],
        "aliases": ["triple negative breast cancer", "tnbc"]
    },
    "breast_cancer": {
        "en": "Breast Cancer",
        "tc_terms": ["乳癌", "乳腺癌", "轉移性乳癌"],
        "aliases": ["breast cancer"]
    },
    "lung_cancer": {
        "en": "Lung Cancer",
        "tc_terms": ["肺癌", "非小細胞肺癌", "小細胞肺癌", "肺腺癌"],
        "aliases": ["lung cancer", "nsclc", "sclc"]
    },
    "prostate_cancer": {
        "en": "Prostate Cancer",
        "tc_terms": ["前列腺癌", "攝護腺癌", "前列腺腺癌"],
        "aliases": ["prostate cancer"]
    },
    "ovarian_cancer": {
        "en": "Ovarian Cancer",
        "tc_terms": ["卵巢癌", "卵巢上皮癌", "輸卵管癌", "原發性腹膜癌"],
        "aliases": ["ovarian cancer"]
    },
    "gist": {
        "en": "Gastrointestinal Stromal Tumor (GIST)",
        "tc_terms": ["胃腸基質瘤", "胃腸道基質腫瘤", "腸胃道間質瘤"],
        "aliases": ["gastrointestinal stromal tumor", "gist"]
    },
    "nasopharyngeal_carcinoma": {
        "en": "Nasopharyngeal Carcinoma",
        "tc_terms": ["鼻咽癌"],
        "aliases": ["nasopharyngeal carcinoma", "npc"]
    },
    "head_neck_cancer": {
        "en": "Head and Neck Cancer",
        "tc_terms": ["頭頸部癌", "下咽癌", "喉癌", "口腔癌"],
        "aliases": ["head and neck cancer", "hnscc"]
    },
    "melanoma": {
        "en": "Melanoma",
        "tc_terms": ["黑色素瘤", "惡性黑色素瘤"],
        "aliases": ["melanoma"]
    },
    "neuroendocrine_tumor": {
        "en": "Neuroendocrine Tumor (NET)",
        "tc_terms": ["神經內分泌腫瘤", "胰臟神經內分泌腫瘤"],
        "aliases": ["neuroendocrine tumor", "net"]
    },
    "thyroid_cancer": {
        "en": "Thyroid Cancer",
        "tc_terms": ["甲狀腺癌", "分化型甲狀腺癌"],
        "aliases": ["thyroid cancer"]
    },
    "renal_cell_carcinoma": {
        "en": "Renal Cell Carcinoma (RCC)",
        "tc_terms": ["腎細胞癌", "轉移性腎細胞癌"],
        "aliases": ["renal cell carcinoma", "rcc"]
    },
    "urothelial_carcinoma": {
        "en": "Urothelial Carcinoma / Bladder Cancer",
        "tc_terms": ["尿路上皮癌", "膀胱癌"],
        "aliases": ["urothelial carcinoma", "bladder cancer"]
    },
    "colorectal_cancer": {
        "en": "Colorectal Cancer",
        "tc_terms": ["大腸直腸癌", "大腸癌", "直腸癌"],
        "aliases": ["colorectal cancer", "colon cancer"]
    },
    "pancreatic_cancer": {
        "en": "Pancreatic Cancer",
        "tc_terms": ["胰臟癌", "胰腺癌"],
        "aliases": ["pancreatic cancer"]
    },
    "multiple_myeloma": {
        "en": "Multiple Myeloma",
        "tc_terms": ["多發性骨髓瘤"],
        "aliases": ["multiple myeloma"]
    },
    "leukemia": {
        "en": "Leukemia",
        "tc_terms": ["白血病", "血癌", "急性骨髓性白血病", "慢性骨髓性白血病"],
        "aliases": ["leukemia", "aml", "cml", "all", "cll"]
    },
    "lymphoma": {
        "en": "Lymphoma (NHL / DLBCL / PTCL / HL)",
        "tc_terms": ["淋巴瘤", "淋巴腫瘤", "淋巴癌", "霍奇金淋巴瘤", "非霍奇金淋巴瘤", "瀰漫性大B細胞淋巴瘤", "周邊T細胞淋巴瘤"],
        "aliases": ["lymphoma", "dlbcl", "ptcl", "nhl", "hodgkin lymphoma"]
    },
    "gastric_esophageal_cancer": {
        "en": "Gastric / Esophageal Cancer",
        "tc_terms": ["胃癌", "胃食道接合處腺癌", "胃食道接合處", "食道癌", "食道鱗狀細胞癌"],
        "aliases": ["gastric cancer", "stomach cancer", "esophageal cancer", "gej cancer"]
    },
    "cholangiocarcinoma": {
        "en": "Cholangiocarcinoma / Biliary Tract Cancer",
        "tc_terms": ["膽管癌", "肝內膽管癌", "膽道癌"],
        "aliases": ["cholangiocarcinoma", "biliary tract cancer", "bile duct cancer"]
    },
    "glioblastoma_brain_tumor": {
        "en": "Glioblastoma / Malignant Glioma / Brain Tumor",
        "tc_terms": ["多形神經膠母細胞瘤", "神經膠母細胞瘤", "星狀細胞瘤", "惡性神經膠質瘤", "腦瘤"],
        "aliases": ["glioblastoma", "gbm", "astrocytoma", "glioma", "brain tumor"]
    },
    "endometrial_cervical_cancer": {
        "en": "Endometrial / Cervical Cancer",
        "tc_terms": ["子宮內膜癌", "子宮頸癌"],
        "aliases": ["endometrial cancer", "uterine cancer", "cervical cancer"]
    },
    "neuroblastoma": {
        "en": "Neuroblastoma",
        "tc_terms": ["神經母細胞瘤"],
        "aliases": ["neuroblastoma"]
    },
    "neurofibromatosis": {
        "en": "Neurofibromatosis (NF1)",
        "tc_terms": ["神經纖維瘤", "叢狀神經纖維瘤"],
        "aliases": ["neurofibromatosis", "nf1", "plexiform neurofibroma"]
    },
    "sarcoma": {
        "en": "Soft Tissue Sarcoma / Osteosarcoma",
        "tc_terms": ["肉瘤", "軟組織肉瘤", "骨肉瘤"],
        "aliases": ["sarcoma", "soft tissue sarcoma", "osteosarcoma"]
    },

    # Dermatology & Infections (皮膚與真菌感染)
    "onychomycosis": {
        "en": "Onychomycosis / Tinea Unguium",
        "tc_terms": ["足趾甲癬", "手指甲癬", "甲癬", "灰指甲", "灰趾甲", "甲真菌病"],
        "aliases": ["onychomycosis", "tinea unguium", "fungal nail infection", "nail fungus", "toenail fungus"]
    },
    "tinea": {
        "en": "Tinea (Ringworm / Dermatophytosis)",
        "tc_terms": ["體癬", "股癬", "頭癬", "手足癬", "皮真菌病"],
        "aliases": ["tinea", "ringworm", "tinea corporis", "tinea cruris", "tinea capitis", "tinea pedis"]
    },
    "fungal_infection": {
        "en": "Fungal Infection / Mycosis (Aspergillosis / Mucormycosis / Candidiasis)",
        "tc_terms": ["黴菌感染", "真菌感染", "念珠菌感染", "念珠性陰道炎", "汗斑", "麴菌症", "白黴菌病", "隱球菌", "Cryptococcus"],
        "aliases": ["fungal infection", "mycosis", "candidiasis", "tinea versicolor", "aspergillosis", "mucormycosis", "cryptococcus"]
    },
    "hidradenitis_suppurativa": {
        "en": "Hidradenitis Suppurativa",
        "tc_terms": ["化膿性汗腺炎"],
        "aliases": ["hidradenitis suppurativa", "hs"]
    },
    "atopic_dermatitis": {
        "en": "Atopic Dermatitis",
        "tc_terms": ["異位性皮膚炎", "濕疹"],
        "aliases": ["atopic dermatitis", "eczema"]
    },
    "urticaria": {
        "en": "Chronic Urticaria",
        "tc_terms": ["蕁麻疹", "慢性特發性蕁麻疹", "慢性自發性蕁麻疹"],
        "aliases": ["urticaria", "hives"]
    },

    # Rheumatology & Immunology (風濕免疫)
    "gpp": {
        "en": "Generalized Pustular Psoriasis (GPP)",
        "tc_terms": ["全身型急性發作膿疱性乾癬", "膿疱性乾癬"],
        "aliases": ["generalized pustular psoriasis", "gpp"]
    },
    "psoriasis": {
        "en": "Psoriasis / Psoriatic Arthritis",
        "tc_terms": ["乾癬", "銀屑病", "乾癬性關節炎"],
        "aliases": ["psoriasis", "psoriatic arthritis"]
    },
    "sle": {
        "en": "Systemic Lupus Erythematosus",
        "tc_terms": ["紅斑性狼瘡", "系統性紅斑性狼瘡", "狼瘡"],
        "aliases": ["systemic lupus erythematosus", "sle", "lupus"]
    },
    "ra": {
        "en": "Rheumatoid Arthritis / Juvenile Idiopathic Arthritis (JIA)",
        "tc_terms": ["類風濕性關節炎", "類風濕關節炎", "幼年型慢性關節炎", "幼年型特異性關節炎"],
        "aliases": ["rheumatoid arthritis", "jia", "juvenile idiopathic arthritis", "juvenile arthritis"]
    },
    "ankylosing_spondylitis": {
        "en": "Ankylosing Spondylitis",
        "tc_terms": ["僵直性脊椎炎"],
        "aliases": ["ankylosing spondylitis"]
    },
    "vasculitis": {
        "en": "Vasculitis / Dermatomyositis",
        "tc_terms": ["血管炎", "皮肌炎", "多發性肌炎", "硬皮症", "貝西氏症"],
        "aliases": ["vasculitis", "dermatomyositis", "polymyositis", "scleroderma", "behcet's disease"]
    },

    # Cardiology & Cardiovascular (心血管)
    "heart_failure": {
        "en": "Heart Failure",
        "tc_terms": ["心臟衰竭", "心衰竭", "慢性心衰竭", "收縮性心衰竭", "急性心衰竭", "心力衰竭", "充血性心臟衰竭"],
        "aliases": ["heart failure", "chf", "hfref", "hfpef"]
    },
    "stroke": {
        "en": "Stroke / Cerebrovascular Accident",
        "tc_terms": ["腦中風", "中風", "缺血性腦中風", "出血性腦中風", "腦血管疾病"],
        "aliases": ["stroke", "cva", "cerebrovascular accident"]
    },
    "myocardial_infarction": {
        "en": "Myocardial Infarction",
        "tc_terms": ["心肌梗塞", "急性心肌梗塞", "冠狀動脈疾病", "冠心病"],
        "aliases": ["myocardial infarction", "mi", "heart attack", "coronary artery disease", "cad"]
    },
    "atrial_fibrillation": {
        "en": "Atrial Fibrillation",
        "tc_terms": ["心房顫動", "心房纖維顫動", "房顫"],
        "aliases": ["atrial fibrillation", "af", "afib"]
    },
    "thrombosis": {
        "en": "Thrombosis / Pulmonary Embolism",
        "tc_terms": ["血栓", "深靜脈血栓", "肺栓塞", "靜脈血栓栓塞", "栓塞"],
        "aliases": ["thrombosis", "dvt", "pulmonary embolism", "pe", "embolism", "thromboembolism"]
    },
    "hypertension": {
        "en": "Hypertension",
        "tc_terms": ["高血壓", "原發性高血壓"],
        "aliases": ["hypertension", "htn", "high blood pressure"]
    },
    "hyperlipidemia": {
        "en": "Hyperlipidemia / Hypercholesterolemia",
        "tc_terms": ["高脂血症", "高膽固醇血症", "高三酸甘油酯血症", "血脂異常"],
        "aliases": ["hyperlipidemia", "hypercholesterolemia", "dyslipidemia"]
    },

    # Neurology & Psychiatry (神經與精神科)
    "migraine": {
        "en": "Migraine",
        "tc_terms": ["偏頭痛", "慢性偏頭痛"],
        "aliases": ["migraine"]
    },
    "myasthenia_gravis": {
        "en": "Myasthenia Gravis",
        "tc_terms": ["重症肌無力"],
        "aliases": ["myasthenia gravis", "mg"]
    },
    "multiple_sclerosis": {
        "en": "Multiple Sclerosis",
        "tc_terms": ["多發性硬化症"],
        "aliases": ["multiple sclerosis", "ms"]
    },
    "parkinson": {
        "en": "Parkinson's Disease",
        "tc_terms": ["帕金森氏症", "帕金森病", "巴金森氏症"],
        "aliases": ["parkinson's disease", "parkinsons"]
    },
    "alzheimer": {
        "en": "Alzheimer's Disease / Dementia",
        "tc_terms": ["阿茲海默症", "失智症", "老年痴呆症"],
        "aliases": ["alzheimer's disease", "dementia", "alzheimers"]
    },
    "epilepsy": {
        "en": "Epilepsy",
        "tc_terms": ["癲癇", "癲癇症"],
        "aliases": ["epilepsy", "seizure"]
    },
    "schizophrenia": {
        "en": "Schizophrenia",
        "tc_terms": ["思覺失調症", "精神分裂症"],
        "aliases": ["schizophrenia"]
    },
    "bipolar": {
        "en": "Bipolar Disorder",
        "tc_terms": ["雙相情緒障礙症", "躁鬱症"],
        "aliases": ["bipolar disorder", "bipolar"]
    },
    "depression": {
        "en": "Major Depressive Disorder",
        "tc_terms": ["憂鬱症", "重度憂鬱症"],
        "aliases": ["depression", "mdd"]
    },

    # Respiratory & Nephrology & Endocrinology (呼吸、腎臟與內分泌)
    "asthma": {
        "en": "Asthma",
        "tc_terms": ["氣喘", "哮喘"],
        "aliases": ["asthma"]
    },
    "copd": {
        "en": "Chronic Obstructive Pulmonary Disease",
        "tc_terms": ["慢性阻塞性肺病", "肺氣腫", "慢性支氣管炎"],
        "aliases": ["chronic obstructive pulmonary disease", "copd"]
    },
    "ipf": {
        "en": "Idiopathic Pulmonary Fibrosis (IPF)",
        "tc_terms": ["特發性肺纖維化"],
        "aliases": ["idiopathic pulmonary fibrosis", "ipf"]
    },
    "ckd": {
        "en": "Chronic Kidney Disease",
        "tc_terms": ["慢性腎臟病", "慢性腎衰竭", "末期腎臟病", "透析"],
        "aliases": ["chronic kidney disease", "ckd", "esrd", "dialysis"]
    },
    "hypoparathyroidism": {
        "en": "Hypoparathyroidism",
        "tc_terms": ["副甲狀腺機能低下症", "副甲狀腺功能低下症", "甲狀旁腺功能減退症"],
        "aliases": ["hypoparathyroid"]
    },
    "hyperparathyroidism": {
        "en": "Hyperparathyroidism",
        "tc_terms": ["副甲狀腺機能亢進症", "副甲狀腺功能亢進症", "甲狀旁腺功能亢進症"],
        "aliases": ["hyperparathyroid"]
    },
    "diabetes": {
        "en": "Diabetes Mellitus",
        "tc_terms": ["糖尿病", "第一型糖尿病", "第二型糖尿病"],
        "aliases": ["diabetes mellitus", "t2dm", "t1dm"]
    },
    "osteoporosis": {
        "en": "Osteoporosis",
        "tc_terms": ["骨質疏鬆症", "骨質疏鬆"],
        "aliases": ["osteoporosis"]
    },
    "acromegaly": {
        "en": "Acromegaly",
        "tc_terms": ["肢端肥大症"],
        "aliases": ["acromegaly"]
    },
    "gout": {
        "en": "Gout / Hyperuricemia",
        "tc_terms": ["痛風", "痛風性關節炎", "高尿酸血症"],
        "aliases": ["gout", "hyperuricemia"]
    },
    "hemophilia": {
        "en": "Hemophilia",
        "tc_terms": ["血友病", "第八凝血因子", "第九凝血因子"],
        "aliases": ["hemophilia"]
    },
    "anemia": {
        "en": "Anemia",
        "tc_terms": ["貧血", "腎性貧血", "缺鐵性貧血"],
        "aliases": ["anemia"]
    },
    "itp": {
        "en": "Immune Thrombocytopenia (ITP)",
        "tc_terms": ["特發性血小板減少性紫斑症", "血小板減少症"],
        "aliases": ["immune thrombocytopenia", "itp"]
    },
    "pah": {
        "en": "Pulmonary Arterial Hypertension (PAH)",
        "tc_terms": ["肺動脈高血壓", "肺動脈高壓", "肺高壓"],
        "aliases": ["pulmonary arterial hypertension", "pulmonary hypertension", "pah"]
    },
    "pad": {
        "en": "Peripheral Arterial Disease (PAD)",
        "tc_terms": ["周邊動脈疾病", "周邊血管疾病", "間歇性跛行"],
        "aliases": ["peripheral arterial disease", "peripheral vascular disease", "pad", "pvd", "intermittent claudication", "claudication"]
    },
    "cardiomyopathy": {
        "en": "Hypertrophic Cardiomyopathy (HCM)",
        "tc_terms": ["肥厚性心肌病變", "心肌病變", "心室肥大"],
        "aliases": ["hypertrophic cardiomyopathy", "cardiomyopathy", "hcm"]
    },
    "neutropenia": {
        "en": "Neutropenia / Leukopenia",
        "tc_terms": ["嗜中性白血球低下", "嗜中性白血球", "白血球低下", "骨髓抑制"],
        "aliases": ["neutropenia", "febrile neutropenia", "leukopenia", "myelosuppression"]
    },
    "mpn_myelofibrosis": {
        "en": "Myelofibrosis / Essential Thrombocythemia / Polycythemia Vera",
        "tc_terms": ["骨髓纖維化", "原發性血小板過多症", "血小板過多症", "真性紅血球增多症"],
        "aliases": ["myelofibrosis", "essential thrombocythemia", "thrombocythemia", "polycythemia vera"]
    },
    "pnh": {
        "en": "Paroxysmal Nocturnal Hemoglobinuria (PNH)",
        "tc_terms": ["陣發性夜間血紅素尿症"],
        "aliases": ["paroxysmal nocturnal hemoglobinuria", "pnh"]
    },
    "hae": {
        "en": "Hereditary Angioedema (HAE)",
        "tc_terms": ["遺傳性血管性水腫"],
        "aliases": ["hereditary angioedema", "hae", "angioedema"]
    },
    "pneumonia_respiratory_infection": {
        "en": "Pneumonia / Respiratory & ENT Infection",
        "tc_terms": ["肺炎", "社區性肺炎", "院內感染型肺炎", "急性下呼吸道感染", "呼吸道感染", "急性化膿性中耳炎", "急性化膿性鼻竇炎", "中耳炎", "外耳炎", "鼻竇炎"],
        "aliases": ["pneumonia", "community-acquired pneumonia", "nosocomial pneumonia", "respiratory tract infection", "otitis media", "otitis externa", "sinusitis"]
    },
    "uti_intraabdominal_sepsis": {
        "en": "UTI / Intra-abdominal Infection / Sepsis / Bacterial Infection",
        "tc_terms": ["泌尿道感染", "複雜性泌尿道感染", "腎盂腎炎", "腹腔內感染", "複雜性腹內感染", "敗血症", "菌血症", "骨盆感染", "皮膚組織感染", "細菌感染", "多重抗藥性", "革蘭氏陰性菌", "革蘭氏陽性菌", "淋病尿道炎", "軟性下疳"],
        "aliases": ["urinary tract infection", "uti", "pyelonephritis", "intra-abdominal infection", "sepsis", "bacteremia", "bacterial infection", "mrsa", "gonorrhea"]
    },
    "c_difficile": {
        "en": "Clostridioides difficile Infection / Pseudomembranous Colitis",
        "tc_terms": ["困難梭狀桿菌", "梭狀桿菌", "假膜性結腸炎", "抗生素引起之腸炎"],
        "aliases": ["c. difficile", "clostridioides difficile", "clostridium difficile", "pseudomembranous colitis", "cdad"]
    },
    "herpes_cmv": {
        "en": "Herpes Simplex / Herpes Zoster / CMV Infection",
        "tc_terms": ["疱疹", "單純性疱疹", "帶狀疱疹", "巨細胞病毒"],
        "aliases": ["herpes", "hsv", "herpes simplex", "shingles", "herpes zoster", "zoster", "cmv", "cytomegalovirus"]
    },
    "hiv_aids": {
        "en": "HIV / AIDS",
        "tc_terms": ["人類免疫缺乏病毒", "後天免疫缺乏症候群", "愛滋病"],
        "aliases": ["hiv", "aids", "human immunodeficiency virus"]
    },
    "covid19_influenza": {
        "en": "COVID-19 / Influenza",
        "tc_terms": ["新型冠狀病毒", "新型冠狀病毒", "流感", "流行性感冒", "狂犬病", "破傷風"],
        "aliases": ["covid-19", "covid", "sars-cov-2", "coronavirus", "influenza", "flu", "rabies", "tetanus"]
    },
    "tuberculosis": {
        "en": "Tuberculosis (TB)",
        "tc_terms": ["結核病", "肺結核"],
        "aliases": ["tuberculosis", "tb"]
    },
    "pain_neuralgia": {
        "en": "Chronic / Breakthrough / Neuropathic Pain",
        "tc_terms": ["疼痛", "慢性頑固性疼痛", "突發性疼痛", "神經痛", "帶狀疱疹皮膚病灶後神經痛", "纖維肌痛症", "口腔潰爛"],
        "aliases": ["pain", "chronic pain", "breakthrough pain", "neuropathic pain", "neuralgia", "postherpetic neuralgia", "phn", "fibromyalgia", "mucositis"]
    },
    "insomnia_narcolepsy": {
        "en": "Insomnia / Sleep Disorder / Narcolepsy",
        "tc_terms": ["失眠", "睡眠障礙", "安眠藥物", "猝睡症"],
        "aliases": ["insomnia", "sleep disorder", "narcolepsy"]
    },
    "spasticity_als_sma": {
        "en": "Spasticity / ALS / Spinal Muscular Atrophy (SMA)",
        "tc_terms": ["痙攣", "肌肉痙攣", "運動神經元疾病", "肌萎縮性脊髓側索硬化症", "脊髓性肌肉萎縮症", "SMN1"],
        "aliases": ["spasticity", "muscle spasm", "als", "amyotrophic lateral sclerosis", "motor neuron disease", "mnd", "sma", "spinal muscular atrophy"]
    },
    "adhd": {
        "en": "Attention-Deficit / Hyperactivity Disorder (ADHD)",
        "tc_terms": ["注意力不足過動症", "過動症"],
        "aliases": ["adhd", "attention deficit hyperactivity disorder"]
    },
    "sedation_anesthesia": {
        "en": "ICU Sedation / Anesthesia / Mechanical Ventilation",
        "tc_terms": ["鎮靜", "全身麻醉", "手術麻醉", "人工呼吸器", "神經肌肉阻斷劑", "局部麻醉"],
        "aliases": ["sedation", "anesthesia", "anaesthesia", "mechanical ventilation", "ventilator"]
    },
    "sjogren": {
        "en": "Sjögren's Syndrome (Xerostomia)",
        "tc_terms": ["修格蘭氏症候群", "口乾燥症", "口腔乾燥"],
        "aliases": ["sjogren", "sjogren's syndrome", "xerostomia", "dry mouth"]
    },
    "nmosd": {
        "en": "Neuromyelitis Optica Spectrum Disorder (NMOSD)",
        "tc_terms": ["泛視神經脊髓炎"],
        "aliases": ["neuromyelitis optica", "nmosd"]
    },
    "organ_transplant": {
        "en": "Organ / Stem Cell Transplantation",
        "tc_terms": ["腎臟移植", "肝臟移植", "心臟移植", "肝、腎移植", "骨髓移植", "造血幹細胞移植", "器官移植"],
        "aliases": ["organ transplant", "kidney transplant", "renal transplant", "liver transplant", "heart transplant", "stem cell transplant", "hsct", "bone marrow transplant"]
    },
    "kawasaki": {
        "en": "Kawasaki Disease",
        "tc_terms": ["川崎病", "川崎氏症"],
        "aliases": ["kawasaki disease", "kawasaki"]
    },
    "ppp": {
        "en": "Palmoplantar Pustulosis (PPP) / Leprosy ENL",
        "tc_terms": ["掌蹠膿皰症", "痲瘋性結節性紅斑"],
        "aliases": ["palmoplantar pustulosis", "ppp", "erythema nodosum leprosum"]
    },
    "bph_oab_urology": {
        "en": "BPH / Overactive Bladder / Interstitial Cystitis / Urolithiasis",
        "tc_terms": ["前列腺增生", "攝護腺肥大", "良性前列腺肥大", "頻尿", "急尿", "尿失禁", "膀胱過動症", "間質性膀胱炎", "泌尿道結石", "腎小管性酸毒症", "勃起機能障礙"],
        "aliases": ["bph", "benign prostatic hyperplasia", "prostate hyperplasia", "overactive bladder", "oab", "urinary incontinence", "interstitial cystitis", "urolithiasis", "kidney stones", "renal tubular acidosis"]
    },
    "endometriosis_gynecology": {
        "en": "Endometriosis / Uterine Fibroids / Hyperprolactinemia",
        "tc_terms": ["子宮內膜異位", "子宮內膜異位症", "子宮肌瘤", "高乳促素血症", "泌乳", "性早熟", "引產", "纖維性囊腫乳房"],
        "aliases": ["endometriosis", "uterine fibroids", "hyperprolactinemia", "precocious puberty", "labor induction"]
    },
    "endocrine_growth_bone": {
        "en": "Growth Hormone Deficiency / Cushing's / Paget's / Hypercalcemia",
        "tc_terms": ["生長激素缺乏症", "透納氏症候群", "努南氏症候群", "庫欣氏病", "庫欣氏症候群", "高血鈣", "高血鈣症", "變形性骨炎", "異位性骨化症", "軟骨發育不全症", "低磷酸鹽佝僂症", "IGF-I"],
        "aliases": ["growth hormone deficiency", "turner syndrome", "noonan syndrome", "cushing's disease", "cushing syndrome", "hypercalcemia", "paget's disease", "paget disease", "achondroplasia", "xlh"]
    },
    "rare_metabolic": {
        "en": "Rare Metabolic & Lysosomal Storage Diseases (MPS, Gaucher, Pompe, Fabry, Wilson, Porphyria)",
        "tc_terms": ["黏多醣症", "高雪氏症", "龐貝氏症", "法布瑞氏症", "威爾森氏", "紫質症", "急性肝紫質症", "高血氨", "血氨症", "尿素循環代謝障礙", "進行性家族性肝內膽汁滯留症", "阿拉吉歐症候群", "芳香族L-胺基酸類脫羧基酶缺乏症", "胱胺酸血症", "膽酸合成障礙", "代謝性酸中毒", "先天性代謝異常", "低血磷", "靜脈營養", "惡病質", "甲醇中毒", "藥物中毒"],
        "aliases": ["mucopolysaccharidosis", "mps", "gaucher disease", "gaucher", "pompe disease", "pompe", "fabry disease", "fabry", "wilson's disease", "wilson disease", "porphyria", "hyperammonemia", "urea cycle disorder", "pfic", "alagille syndrome", "aadc deficiency", "cystinosis", "metabolic acidosis", "parenteral nutrition", "cachexia"]
    },
    "glaucoma": {
        "en": "Glaucoma / Ocular Hypertension",
        "tc_terms": ["青光眼", "高眼壓", "降眼壓"],
        "aliases": ["glaucoma", "ocular hypertension", "intraocular pressure"]
    },
    "dry_eye_cornea": {
        "en": "Dry Eye Syndrome / Keratitis / Conjunctivitis",
        "tc_terms": ["乾眼症", "人工淚液", "角膜炎", "角膜潰瘍", "結膜炎", "眼瞼炎", "白內障"],
        "aliases": ["dry eye", "artificial tears", "keratitis", "corneal ulcer", "conjunctivitis", "blepharitis", "cataract"]
    },
    "retinal_macular_uveitis": {
        "en": "Macular Degeneration (AMD / DME) / Retinopathy / Uveitis",
        "tc_terms": ["黃斑部病變", "多足型脈絡膜血管病變", "視網膜病變", "早產兒視網膜病變", "視網膜靜脈阻塞", "雷伯氏遺傳視神經病變", "急性視網膜壞死症", "葡萄膜炎"],
        "aliases": ["macular degeneration", "amd", "wamd", "diabetic macular edema", "dme", "retinal vein occlusion", "rvo", "pcv", "retinopathy of prematurity", "rop", "lhon", "uveitis", "retinitis"]
    },
    "dermatology_other": {
        "en": "Acne / Scabies / Genital Warts / Actinic Keratosis",
        "tc_terms": ["痤瘡", "青春痘", "疥瘡", "生殖器疣", "光化性角化症", "毛囊炎", "尋常性鬚瘡", "慢性腿部潰瘍", "潰瘍傷口"],
        "aliases": ["acne", "isotretinoin", "scabies", "genital warts", "condyloma", "actinic keratosis", "folliculitis", "leg ulcer"]
    },
    "rds_neonatal": {
        "en": "Neonatal Respiratory Distress Syndrome (RDS)",
        "tc_terms": ["呼吸窘迫症候群"],
        "aliases": ["respiratory distress syndrome", "rds", "surfactant"]
    }
}

class DiseaseEngine:
    def __init__(self):
        self.disease_db = DISEASE_DATABASE

    def expand_query(self, query):
        """Given a query in English or Chinese, return matching disease entries using word boundary and substring matching."""
        q_clean = query.strip().lower()
        if not q_clean:
            return []
            
        matched_keys = set()
        is_q_chinese = any(ord(c) > 127 for c in q_clean)

        for key, info in self.disease_db.items():
            terms_to_check = [info["en"]] + info["aliases"] + info["tc_terms"]
            for term in terms_to_check:
                t_clean = term.lower()
                is_t_chinese = any(ord(c) > 127 for c in t_clean)
                
                if is_q_chinese or is_t_chinese:
                    # For Chinese, require >= 2 chars or exact match to prevent single char clutter
                    if q_clean in t_clean or t_clean in q_clean:
                        if len(q_clean) >= 2 or q_clean == t_clean:
                            matched_keys.add(key)
                            break
                else:
                    # For English, use exact match for short queries or word boundary search
                    if len(q_clean) <= 2:
                        if q_clean == t_clean or any(q_clean == a.lower() for a in info["aliases"]):
                            matched_keys.add(key)
                            break
                    else:
                        if re.search(r'\b' + re.escape(q_clean) + r'\b', t_clean) or re.search(r'\b' + re.escape(t_clean) + r'\b', q_clean):
                            matched_keys.add(key)
                            break

        results = []
        for key in matched_keys:
            info = self.disease_db[key]
            results.append({
                "disease_key": key,
                "english_name": info["en"],
                "chinese_terms": info["tc_terms"],
                "aliases": info["aliases"]
            })
        return results

    def extract_diseases_from_text(self, text):
        """Extract all mentioned diseases in text and return clean bilingual list."""
        found_diseases = []
        text_lower = text.lower()

        for key, info in self.disease_db.items():
            matched = False
            for tc in info["tc_terms"]:
                if tc in text:
                    matched = True
                    break
            if not matched:
                for alias in info["aliases"]:
                    if len(alias) >= 3 and re.search(r'\b' + re.escape(alias.lower()) + r'\b', text_lower):
                        matched = True
                        break

            if matched:
                found_diseases.append({
                    "english": info["en"],
                    "chinese": info["tc_terms"][0],
                    "all_tc_terms": info["tc_terms"]
                })

        return found_diseases

if __name__ == "__main__":
    engine = DiseaseEngine()
    print("Expand query 'scurvy':", engine.expand_query("scurvy"))
