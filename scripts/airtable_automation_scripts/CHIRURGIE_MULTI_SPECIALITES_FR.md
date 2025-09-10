# 🏥 Application Chirurgie Multi-Spécialités - Extension Complète pour le Marché Français

## 📊 Analyse du Marché des Chirurgiens en France

### **Distribution des Spécialités Chirurgicales (2024)**

D'après les données du Conseil National de l'Ordre des Médecins, voici la répartition des **~15,000 chirurgiens** en France :

| Rang | Spécialité | Nombre | % | Cumul % | Inclus |
|------|------------|--------|---|---------|---------|
| 1 | **Chirurgie Générale & Digestive** | 2,850 | 19% | 19% | ✅ |
| 2 | **Chirurgie Orthopédique** | 2,400 | 16% | 35% | ✅ |
| 3 | **Ophtalmologie** | 1,950 | 13% | 48% | ✅ |
| 4 | **Gynécologie Chirurgicale** | 1,500 | 10% | 58% | ✅ |
| 5 | **Urologie** | 1,200 | 8% | 66% | ✅ |
| 6 | **ORL** (actuel) | 900 | 6% | 72% | ✅ |
| 7 | **Chirurgie Plastique** | 750 | 5% | 77% | ✅ |
| 8 | **Chirurgie Vasculaire** | 600 | 4% | 81% | ✅ |
| 9 | Neurochirurgie | 450 | 3% | 84% | ❌ |
| 10 | Chirurgie Cardiaque | 300 | 2% | 86% | ❌ |

**➡️ Les 8 premières spécialités représentent 81% des chirurgiens français**

---

## 🎯 Analyse Détaillée par Spécialité

### **1. CHIRURGIE GÉNÉRALE & DIGESTIVE** (2,850 chirurgiens - 19%)

#### **Procédures Principales**

```python
PROCEDURES_DIGESTIVES = {
    # Urgences Abdominales (40% de l'activité)
    'appendicectomie': {
        'ccam': 'HHFA001',
        'tarif_secu': 354.60,
        'duree_moyenne': 45,
        'hospitalisation': 'ambulatoire/1-2j',
        'anesthesie': 'generale',
        'urgence': True
    },
    'cholecystectomie': {
        'ccam': 'HMFC004',
        'tarif_secu': 478.80,
        'duree_moyenne': 60,
        'technique': 'coelioscopie',
        'hospitalisation': 'ambulatoire/1j'
    },
    'hernie_inguinale': {
        'ccam': 'LMMA009',
        'tarif_secu': 359.40,
        'duree_moyenne': 45,
        'technique': 'prothese',
        'hospitalisation': 'ambulatoire'
    },
    
    # Chirurgie Cancérologique (30%)
    'colectomie': {
        'ccam': 'HHFA011',
        'tarif_secu': 897.60,
        'duree_moyenne': 180,
        'hospitalisation': '5-7j',
        'chimio_associee': True,
        'rcp_obligatoire': True  # Réunion Concertation Pluridisciplinaire
    },
    'gastrectomie': {
        'ccam': 'HFFA004',
        'tarif_secu': 1123.20,
        'duree_moyenne': 240,
        'hospitalisation': '7-10j',
        'nutrition_post_op': 'parentérale'
    },
    
    # Chirurgie Proctologique (20%)
    'hemorroidectomie': {
        'ccam': 'EHFA003',
        'tarif_secu': 287.40,
        'duree_moyenne': 30,
        'anesthesie': 'generale/rachi',
        'douleur_post_op': 'forte',
        'soins_locaux': 'bains_siege'
    },
    'fistule_anale': {
        'ccam': 'EJFA002',
        'tarif_secu': 334.80,
        'duree_moyenne': 45,
        'technique': 'seton/lambeau',
        'cicatrisation': '6-8_semaines'
    },
    
    # Chirurgie Bariatrique (10%)
    'sleeve_gastrectomie': {
        'ccam': 'HFCA009',
        'tarif_secu': 1567.20,
        'duree_moyenne': 120,
        'suivi_obligatoire': '2_ans',
        'equipe_pluridisciplinaire': True,
        'vitamines_vie': True
    }
}

# Protocoles Post-Opératoires Spécifiques
PROTOCOLES_DIGESTIF = {
    'reprise_transit': {
        'jeune_post_op': '24-48h',
        'reprise_liquides': 'J1',
        'reprise_solides': 'J2-J3',
        'surveillance': 'occlusion'
    },
    'anticoagulation': {
        'prevention': 'HBPM_30j',
        'chirurgie_cancer': 'prolongee_3mois'
    },
    'antibioprophylaxie': {
        'standard': 'cefazoline_2g',
        'allergie': 'clindamycine+gentamicine'
    },
    'drains': {
        'redon': 'ablation_J2-J3',
        'lame': 'ablation_<100ml/24h'
    }
}

# Documents Spécifiques
DOCUMENTS_DIGESTIF = [
    'consentement_coelioscopie',
    'info_jeune_preop',
    'consignes_regime_post_op',
    'fiche_stomie',  # Si applicable
    'carnet_suivi_bariatrique',
    'ordonnance_IPP',  # Inhibiteurs pompe protons
    'ordonnance_antiemetiques',
    'certificat_arret_sport_6semaines'
]
```

#### **Équipements Spécifiques**
- Colonne de coelioscopie HD/4K
- Instruments de thermofusion (LigaSure, Ultracision)
- Agrafes mécaniques (GIA, TA)
- Table d'opération articulée
- Échographe per-opératoire

---

### **2. CHIRURGIE ORTHOPÉDIQUE & TRAUMATOLOGIE** (2,400 chirurgiens - 16%)

#### **Procédures Principales**

```python
PROCEDURES_ORTHO = {
    # Chirurgie Prothétique (40%)
    'pth_totale': {  # Prothèse Totale Hanche
        'ccam': 'NEKA010',
        'tarif_secu': 1789.20,
        'duree_moyenne': 90,
        'implants': 'titanium/ceramique',
        'voie_abord': 'anterieure/posterieure',
        'reeduc': '3_mois',
        'arret_travail': '3_mois'
    },
    'ptg_totale': {  # Prothèse Totale Genou
        'ccam': 'NFKA006',
        'tarif_secu': 1689.60,
        'duree_moyenne': 90,
        'navigation': 'optionnelle',
        'reeducation': 'immediate',
        'flexion_objectif': '120_degres'
    },
    
    # Traumatologie (35%)
    'fracture_femur': {
        'ccam': 'NBCA001',
        'tarif_secu': 892.80,
        'urgence': True,
        'delai_max': '48h',
        'osteosynthese': 'clou/plaque',
        'anticoagulation': 'obligatoire'
    },
    'fracture_radius': {
        'ccam': 'MZCA002',
        'tarif_secu': 446.40,
        'technique': 'plaque_palmaire',
        'immobilisation': '6_semaines',
        'kine': 'immediate_doigts'
    },
    
    # Arthroscopie (15%)
    'arthroscopie_genou': {
        'ccam': 'NFCC001',
        'tarif_secu': 334.80,
        'duree_moyenne': 30,
        'indications': 'menisque/ligament',
        'ambulatoire': True,
        'bequilles': '2-4_semaines'
    },
    'arthroscopie_epaule': {
        'ccam': 'MZCC001',
        'tarif_secu': 478.80,
        'position': 'beach_chair/laterale',
        'attelle': '4-6_semaines',
        'reeducation': '3_mois'
    },
    
    # Chirurgie du Rachis (10%)
    'hernie_discale': {
        'ccam': 'LDFA002',
        'tarif_secu': 1123.20,
        'technique': 'microdiscectomie',
        'duree': 60,
        'lever': 'J0_soir',
        'arret_travail': '6_semaines'
    }
}

# Protocoles Spécifiques Orthopédie
PROTOCOLES_ORTHO = {
    'antibioprophylaxie': {
        'standard': 'cefazoline_2g',
        'allergie': 'vancomycine',
        'prothese': 'prolongee_24h'
    },
    'thromboprophylaxie': {
        'pth_ptg': 'HBPM_35j',
        'fracture': 'selon_mobilite',
        'arthroscopie': 'bas_contention'
    },
    'reeducation': {
        'immediat': ['mobilisation_passive', 'cryotherapie'],
        'j1': ['lever_premier', 'marche_deambulateur'],
        'j2': ['escaliers', 'autonomie'],
        'kine_ville': 'ordonnance_30_seances'
    },
    'analgesie_multimodale': {
        'peridurale': 'si_membre_inferieur',
        'blocs_nerveux': 'systematique',
        'protocole_epargne_morphine': True
    }
}

# Documents Spécifiques Orthopédie
DOCUMENTS_ORTHO = [
    'consentement_prothese',
    'livret_patient_prothese',
    'ordonnance_anticoagulants',
    'ordonnance_kinesitherapie',
    'ordonnance_attelle_orthese',
    'certificat_sport_3-6mois',
    'fiche_precautions_prothese',
    'carnet_suivi_prothese',
    'ordonnance_transport_ambulance'
]

# Matériel Spécifique
EQUIPEMENTS_ORTHO = {
    'imagerie': ['amplificateur_brillance', 'echographe'],
    'implants': ['clous', 'plaques', 'vis', 'protheses'],
    'instrumentation': ['moteurs', 'navigateur', 'robot'],
    'arthroscopie': ['colonne', 'shavers', 'pompe'],
    'traction': ['table_traction', 'orthoprothese']
}
```

---

### **3. OPHTALMOLOGIE** (1,950 chirurgiens - 13%)

#### **Procédures Principales**

```python
PROCEDURES_OPHTALMO = {
    # Chirurgie de la Cataracte (70% de l'activité)
    'phacoemulsification': {
        'ccam': 'BFGA004',
        'tarif_secu': 355.57,
        'duree_moyenne': 15,
        'anesthesie': 'topique/peribulbaire',
        'implant': 'monofocal/multifocal/torique',
        'ambulatoire': True,
        'bilateral': 'differe_1semaine'
    },
    
    # Chirurgie Réfractive (15%)
    'lasik': {
        'ccam': 'non_rembourse',
        'tarif_moyen': 3000,  # Pour les 2 yeux
        'duree': 20,
        'technique': 'femtoseconde',
        'criteres': 'myopie<-10D',
        'arret_lentilles': '15j_avant'
    },
    'pkr': {
        'ccam': 'non_rembourse',
        'tarif_moyen': 2500,
        'recuperation': 'plus_longue',
        'douleur': '48h',
        'lentille_pansement': '5j'
    },
    
    # Glaucome (10%)
    'trabeculectomie': {
        'ccam': 'BDGA002',
        'tarif_secu': 446.78,
        'duree': 45,
        'suivi': 'intensif_1mois',
        'mitomycine': 'peroperatoire',
        'ajustements': 'sutures_lyse'
    },
    'implant_drainage': {
        'ccam': 'BDGA006',
        'tarif_secu': 892.56,
        'types': 'Ahmed/Baerveldt',
        'pression_cible': '<15mmHg'
    },
    
    # Rétine (5%)
    'vitrectomie': {
        'ccam': 'BJGA002',
        'tarif_secu': 1120.45,
        'duree': 60,
        'indications': 'decollement/diabete',
        'gaz': 'SF6/C3F8',
        'position': 'face_down_7j'
    },
    'injections_ivt': {
        'ccam': 'BGLB001',
        'tarif_secu': 83.60,
        'molecules': 'anti-VEGF',
        'frequence': 'mensuelle',
        'surveillance': 'PIO_30min'
    }
}

# Protocoles Post-Opératoires Ophtalmologie
PROTOCOLES_OPHTALMO = {
    'collyres_post_cataracte': {
        'antibiotique': 'ofloxacine_x4_7j',
        'corticoide': 'dexamethasone_degressif_3sem',
        'ains': 'indometacine_x3_3sem',
        'mydriase': 'tropicamide_si_besoin'
    },
    'post_glaucome': {
        'corticoides': 'intenses_6sem',
        'atropine': 'cyclopegie_2sem',
        'massages': 'globe_oculaire',
        'laser_sutures': 'si_pression_haute'
    },
    'post_retine': {
        'positionnement': 'crucial',
        'interdiction_avion': 'si_gaz_6sem',
        'collyres': 'antibio+cortico+dilatation',
        'surveillance': 'hebdomadaire_1mois'
    },
    'urgences_ophtalmo': {
        'baisse_vision': 'consultation_immediate',
        'douleur_intense': 'urgence',
        'rougeur_purulente': 'dans_24h'
    }
}

# Documents Spécifiques Ophtalmologie
DOCUMENTS_OPHTALMO = [
    'consentement_cataracte',
    'choix_implant',
    'devis_chirurgie_refractive',
    'consignes_pre_operatoires',
    'ordonnance_collyres',
    'certificat_aptitude_conduite',
    'fiche_positionnement_gaz',
    'calendrier_injections',
    'fiche_urgence_ophtalmo'
]

# Équipements Spécifiques
EQUIPEMENTS_OPHTALMO = {
    'microscope': 'Zeiss/Leica',
    'phaco': 'Alcon/AMO',
    'laser': 'excimer/femtoseconde',
    'oct': 'tomographie',
    'biometrie': 'IOLMaster',
    'vitrectome': '25/27_gauge'
}
```

---

### **4. GYNÉCOLOGIE CHIRURGICALE** (1,500 chirurgiens - 10%)

#### **Procédures Principales**

```python
PROCEDURES_GYNECO = {
    # Chirurgie Fonctionnelle (40%)
    'hysterectomie': {
        'ccam': 'JKFA018',
        'tarif_secu': 892.80,
        'voies': 'vaginale/coelioscopique/abdominale',
        'duree': 90,
        'indications': 'fibrome/adenomyose/cancer',
        'menopause_induite': 'si_ovariectomie'
    },
    'myomectomie': {
        'ccam': 'JKFC001',
        'tarif_secu': 669.60,
        'preservation_fertilite': True,
        'voie': 'coelioscopique/hysteroscopique',
        'contraception': '3_mois_post'
    },
    
    # Chirurgie du Prolapsus (25%)
    'promontofixation': {
        'ccam': 'JDFA007',
        'tarif_secu': 1116.00,
        'technique': 'coelioscopique',
        'prothese': 'polypropylene',
        'reeducation_perineale': 'obligatoire'
    },
    'colpoperineorraphie': {
        'ccam': 'JMFA010',
        'tarif_secu': 446.40,
        'voie': 'vaginale',
        'duree': 60,
        'rapports': 'interdits_6sem'
    },
    
    # Chirurgie de l'Incontinence (20%)
    'tob_tot': {  # Bandelette sous-urétrale
        'ccam': 'JDDB001',
        'tarif_secu': 558.00,
        'duree': 30,
        'efficacite': '85%',
        'risque_retention': '5%'
    },
    
    # Chirurgie Oncologique (15%)
    'conisation': {
        'ccam': 'JKFA001',
        'tarif_secu': 223.20,
        'technique': 'anse_diathermique',
        'analyse_marges': 'obligatoire',
        'surveillance': 'frottis_6mois'
    },
    'mastectomie': {
        'ccam': 'QEFA003',
        'tarif_secu': 669.60,
        'ganglion_sentinelle': True,
        'reconstruction': 'immediate/differee',
        'drainage': '3-5j'
    }
}

# Protocoles Spécifiques Gynécologie
PROTOCOLES_GYNECO = {
    'preparation_coelioscopie': {
        'regime': 'sans_residu_3j',
        'preparation_digestive': 'fleet',
        'position': 'trendelenburg',
        'sondage': 'systematique'
    },
    'soins_post_op': {
        'lever': 'j0_soir',
        'sonde_vesicale': 'ablation_j1',
        'alimentation': 'reprise_j0',
        'douche': 'autorisee_j2'
    },
    'contraception': {
        'pre_op': 'arret_pilule_1mois',
        'post_op': 'reprise_cycle_suivant',
        'si_cancer': 'contre_indication_hormones'
    },
    'surveillance_cancer': {
        'marqueurs': 'CA125_CA19-9',
        'imagerie': 'TDM_TAP',
        'consultation': 'tous_3mois_2ans'
    }
}

# Documents Spécifiques Gynécologie
DOCUMENTS_GYNECO = [
    'consentement_hysterectomie',
    'info_menopause_chirurgicale',
    'fiche_reeducation_perineale',
    'consignes_rapports_sexuels',
    'ordonnance_oestrogenes_locaux',
    'certificat_arret_travail_4-6sem',
    'fiche_auto_sondage',  # Si rétention
    'carnet_surveillance_oncologique'
]
```

---

### **5. UROLOGIE** (1,200 chirurgiens - 8%)

#### **Procédures Principales**

```python
PROCEDURES_UROLOGIE = {
    # Chirurgie Prostatique (35%)
    'resection_prostate': {
        'ccam': 'JGFA015',
        'tarif_secu': 1004.40,
        'technique': 'bipolaire/laser',
        'duree': 60,
        'sondage': '48h',
        'troubles_ejaculation': '90%'
    },
    'prostatectomie_radicale': {
        'ccam': 'JGFC002',
        'tarif_secu': 1789.20,
        'technique': 'robot/coelioscopie',
        'preservation_nerfs': 'si_possible',
        'incontinence': '10-30%',
        'dysfonction_erectile': '30-70%'
    },
    
    # Chirurgie Lithiasique (30%)
    'ureteroscopie': {
        'ccam': 'JCGE002',
        'tarif_secu': 669.60,
        'laser': 'holmium',
        'sonde_jj': '7-15j',
        'analyse_calcul': 'obligatoire'
    },
    'nlpc': {  # Néphrolithotomie percutanée
        'ccam': 'JCGA002',
        'tarif_secu': 1339.20,
        'position': 'ventral',
        'nephrostomie': '24-48h',
        'risque_hemorragie': '5%'
    },
    
    # Chirurgie Vésicale (20%)
    'rtuv': {  # Résection tumeur vessie
        'ccam': 'JDFC001',
        'tarif_secu': 558.00,
        'recidive': '50-70%',
        'mitomycine': 'post_immediat',
        'surveillance': 'cystoscopie_3mois'
    },
    'cystectomie': {
        'ccam': 'JDFA004',
        'tarif_secu': 2236.80,
        'derivation': 'bricker/neovessie',
        'duree': 300,
        'complications': 'majeures_30%'
    },
    
    # Chirurgie Génitale (15%)
    'cure_varicocele': {
        'ccam': 'JHFA008',
        'tarif_secu': 334.80,
        'fertilite': 'amelioration_40%',
        'voie': 'coelioscopique/inguinale'
    },
    'posthectomie': {
        'ccam': 'JHFA002',
        'tarif_secu': 167.40,
        'anesthesie': 'locale/generale',
        'pansement': '10j',
        'rapports': 'interdits_4sem'
    }
}

# Protocoles Spécifiques Urologie
PROTOCOLES_UROLOGIE = {
    'sondage_vesical': {
        'duree_moyenne': '24-72h',
        'irrigation': 'si_hematique',
        'ablation': 'apres_urine_claire',
        'education': 'auto_sondage_si_retention'
    },
    'sondes_jj': {
        'indication': 'post_ureteroscopie',
        'duree': '7-30j',
        'symptomes': 'urgences/douleurs',
        'ablation': 'cystoscopie_locale'
    },
    'instillations_vesicales': {
        'bCG': 'immunotherapie_6sem',
        'mitomycine': 'chimiotherapie',
        'retention': '2h',
        'surveillance': 'ECBU_avant'
    },
    'reeducation_erectile': {
        'ipde5': 'sildenafil/tadalafil',
        'injections': 'alprostadil',
        'vacuum': 'dispositif_erection',
        'implant': 'si_echec_medical'
    }
}

# Documents Spécifiques Urologie
DOCUMENTS_UROLOGIE = [
    'consentement_prostatectomie',
    'info_troubles_sexuels',
    'fiche_auto_sondage',
    'calendrier_mictionnel',
    'ordonnance_alpha_bloquants',
    'ordonnance_anticholinergiques',
    'fiche_exercices_perinee',
    'carnet_surveillance_PSA',
    'ordonnance_IPDE5'
]
```

---

### **6. ORL - CHIRURGIE CERVICO-FACIALE** (900 chirurgiens - 6%)
*[Déjà détaillé dans la version originale]*

---

### **7. CHIRURGIE PLASTIQUE, RECONSTRUCTRICE & ESTHÉTIQUE** (750 chirurgiens - 5%)

#### **Procédures Principales**

```python
PROCEDURES_PLASTIQUE = {
    # Chirurgie Reconstructrice (50%)
    'reconstruction_mammaire': {
        'ccam': 'QEMA004',
        'tarif_secu': 1116.00,
        'techniques': 'prothese/lambeau_dorsal/DIEP',
        'duree': 120-360,
        'symetrisation': 'souvent_necessaire',
        'suivi': 'IRM_annuelle'
    },
    'lambeau_libre': {
        'ccam': 'QZMA002',
        'tarif_secu': 2236.80,
        'microchirurgie': True,
        'monitoring': 'doppler_horaire',
        'anticoagulation': 'protocole_specifique'
    },
    
    # Chirurgie Esthétique (35%)
    'augmentation_mammaire': {
        'ccam': 'non_rembourse',
        'tarif_moyen': 5000,
        'implants': 'silicone/serum',
        'voie': 'areolaire/sous_mammaire',
        'arret_sport': '6_semaines',
        'echo_controle': 'annuelle'
    },
    'rhinoplastie': {
        'ccam': 'GAFA002',  # Si fonctionnelle
        'tarif': 3500-6000,
        'duree': 90,
        'attelle': '7j',
        'oedeme': 'resolution_3mois',
        'resultat_final': '1an'
    },
    'lifting_facial': {
        'ccam': 'non_rembourse',
        'tarif_moyen': 7000,
        'duree': 180,
        'techniques': 'SMAS/deep_plane',
        'drains': '24-48h',
        'reprise_sociale': '15j'
    },
    
    # Chirurgie de la Main (15%)
    'syndrome_canal_carpien': {
        'ccam': 'AHPA009',
        'tarif_secu': 223.20,
        'anesthesie': 'locale/loco_regionale',
        'duree': 15,
        'attelle': 'non',
        'reprise_immediate': True
    },
    'maladie_dupuytren': {
        'ccam': 'MJFA006',
        'tarif_secu': 446.40,
        'technique': 'aponeurotomie/aponevectomie',
        'reeducation': 'intensive',
        'recidive': '20-60%'
    }
}

# Protocoles Spécifiques Chirurgie Plastique
PROTOCOLES_PLASTIQUE = {
    'soins_cicatrices': {
        'massage': '2x/jour_3mois',
        'silicone': 'plaques/gel',
        'protection_solaire': 'totale_1an',
        'hydratation': 'quotidienne'
    },
    'surveillance_implants': {
        'clinique': 'annuelle',
        'echographie': 'annuelle',
        'irm': 'si_doute_rupture',
        'changement': '10-15ans'
    },
    'drains_aspiratifs': {
        'surveillance': 'quantite_aspect',
        'ablation': '<30ml/24h',
        'education': 'vidange_domicile'
    },
    'contention': {
        'soutien_gorge': 'jour_nuit_6sem',
        'panty': 'liposuccion_6sem',
        'bande': 'abdominoplastie_1mois'
    }
}

# Documents Spécifiques Plastique
DOCUMENTS_PLASTIQUE = [
    'devis_detaille_esthetique',
    'consentement_specifique_cosmetique',
    'photos_pre_post_op',
    'fiche_soins_cicatrices',
    'certificat_psychologique',  # Si demandé
    'ordonnance_contention',
    'carnet_suivi_implants',
    'attestation_reflexion_15j'  # Légal pour esthétique
]
```

---

### **8. CHIRURGIE VASCULAIRE** (600 chirurgiens - 4%)

#### **Procédures Principales**

```python
PROCEDURES_VASCULAIRE = {
    # Chirurgie Artérielle (50%)
    'endarteriectomie_carotide': {
        'ccam': 'EBFA003',
        'tarif_secu': 892.80,
        'duree': 90,
        'shunt': 'si_necessaire',
        'surveillance_neuro': 'intensive',
        'antiagregants': 'a_vie'
    },
    'pontage_femoro_poplite': {
        'ccam': 'ECFA010',
        'tarif_secu': 1339.20,
        'materiel': 'veine/prothese',
        'duree': 180,
        'surveillance_pouls': 'horaire',
        'marche': 'j1'
    },
    'angioplastie_stent': {
        'ccam': 'EDAF001',
        'tarif_secu': 669.60,
        'voie': 'femorale/radiale',
        'antiagregation': 'double_3mois',
        'controle_doppler': '1mois'
    },
    
    # Chirurgie Veineuse (35%)
    'stripping_saphene': {
        'ccam': 'EJFA002',
        'tarif_secu': 446.40,
        'technique': 'invagination',
        'contention': '6_semaines',
        'marche': 'immediate'
    },
    'evla_laser': {  # Endoveineuse laser
        'ccam': 'EJNF001',
        'tarif_secu': 558.00,
        'anesthesie': 'tumescente',
        'ambulatoire': True,
        'reprise': 'j1'
    },
    'sclerotherapie': {
        'ccam': 'EJNF002',
        'tarif_secu': 111.60,
        'seances': 'multiples',
        'contention': '3_semaines',
        'marche': '30min_post'
    },
    
    # Chirurgie des Accès Vasculaires (15%)
    'fistule_av': {
        'ccam': 'EZFA001',
        'tarif_secu': 669.60,
        'maturation': '6_semaines',
        'surveillance': 'thrill_fremissement',
        'utilisation': 'dialyse'
    },
    'catheter_central': {
        'ccam': 'EPLF002',
        'tarif_secu': 167.40,
        'voie': 'jugulaire/sous_claviere',
        'rx_controle': 'obligatoire',
        'pansement': 'sterile_hebdo'
    }
}

# Protocoles Spécifiques Vasculaire
PROTOCOLES_VASCULAIRE = {
    'anticoagulation': {
        'prevention': 'HBPM_prophylactique',
        'therapeutique': 'heparine_relais_AVK',
        'naco': 'si_FA',
        'surveillance': 'INR_TP_TCA'
    },
    'surveillance_vasculaire': {
        'pouls': 'pedieux_tibial_post',
        'doppler': 'index_cheville_bras',
        'capillaroscopie': 'si_troubles_troph',
        'echo_doppler': 'controle_3-6mois'
    },
    'contention_elastique': {
        'classe_2': 'standard_post_op',
        'classe_3': 'si_insuffisance_severe',
        'duree': '3mois_minimum',
        'renouvellement': 'tous_6mois'
    },
    'reeducation_marche': {
        'immediate': 'lever_j0',
        'progressive': 'augmentation_distance',
        'test_marche': '6min',
        'escaliers': 'j2-j3'
    }
}

# Documents Spécifiques Vasculaire
DOCUMENTS_VASCULAIRE = [
    'consentement_risques_vasculaires',
    'ordonnance_antiagregants',
    'ordonnance_anticoagulants',
    'ordonnance_bas_contention',
    'carnet_surveillance_INR',
    'fiche_soins_fistule',
    'certificat_ALD',
    'education_signes_alerte'
]
```

---

## 📊 Matrice des Fonctionnalités par Spécialité

| Fonctionnalité | Digestif | Ortho | Ophtalmo | Gynéco | Uro | ORL | Plastique | Vasculaire |
|----------------|----------|-------|----------|---------|-----|-----|-----------|------------|
| **Planning Multi-sites** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Urgences 24/7** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| **Bloc Ambulatoire** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Coelioscopie/Endoscopie** | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| **Microscope Opératoire** | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| **Robot Chirurgical** | ✅ | ✅ | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ |
| **Imagerie Per-op** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Implants/Prothèses** | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| **Chimiothérapie Locale** | ✅ | ❌ | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ |
| **Réanimation Post-op** | ✅ | ✅ | ❌ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| **Rééducation Intensive** | ⚠️ | ✅ | ❌ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |
| **Suivi Oncologique** | ✅ | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Esthétique Pure** | ❌ | ❌ | ✅ | ⚠️ | ❌ | ✅ | ✅ | ⚠️ |
| **Pédiatrie** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |

**Légende**: ✅ Essentiel | ⚠️ Occasionnel | ❌ Non applicable

---

## 🔧 Configuration Multi-Spécialités de l'Application

### **Architecture Modulaire**

```python
class ConfigurationSpecialite:
    """Configuration par spécialité chirurgicale"""
    
    SPECIALITES = {
        'DIGESTIF': {
            'code': 'DIG',
            'couleur': '#E74C3C',  # Rouge
            'icone': '🔴',
            'modules': ['urgences', 'coelioscopie', 'oncologie', 'bariatrie'],
            'documents_specifiques': 15,
            'duree_moyenne_intervention': 90,
            'taux_ambulatoire': 0.40,
            'equipes': ['chirurgien', 'anesthesiste', 'ibode', 'aide'],
            'localisations': ['bloc_principal', 'bloc_urgences', 'endoscopie']
        },
        
        'ORTHOPEDIQUE': {
            'code': 'ORT',
            'couleur': '#3498DB',  # Bleu
            'icone': '🦴',
            'modules': ['trauma', 'protheses', 'arthroscopie', 'rachis', 'pediatrie'],
            'documents_specifiques': 12,
            'duree_moyenne_intervention': 75,
            'taux_ambulatoire': 0.35,
            'equipes': ['chirurgien', 'anesthesiste', 'ampli', 'kine'],
            'localisations': ['bloc_ortho', 'bloc_urgences', 'bloc_septique']
        },
        
        'OPHTALMOLOGIE': {
            'code': 'OPH',
            'couleur': '#16A085',  # Turquoise
            'icone': '👁️',
            'modules': ['cataracte', 'refractif', 'glaucome', 'retine', 'pediatrie'],
            'documents_specifiques': 9,
            'duree_moyenne_intervention': 25,
            'taux_ambulatoire': 0.95,
            'equipes': ['chirurgien', 'infirmiere', 'orthoptiste'],
            'localisations': ['bloc_ophtalmo', 'salle_laser', 'salle_injections']
        },
        
        'GYNECOLOGIE': {
            'code': 'GYN',
            'couleur': '#E91E63',  # Rose
            'icone': '🤱',
            'modules': ['obstetrique', 'fonctionnel', 'oncologie', 'fertilite', 'senologie'],
            'documents_specifiques': 11,
            'duree_moyenne_intervention': 60,
            'taux_ambulatoire': 0.45,
            'equipes': ['chirurgien', 'anesthesiste', 'sage_femme', 'aide'],
            'localisations': ['bloc_gyneco', 'bloc_obstetrique', 'bloc_urgences']
        },
        
        'UROLOGIE': {
            'code': 'URO',
            'couleur': '#F39C12',  # Orange
            'icone': '💧',
            'modules': ['endoscopie', 'lithiase', 'oncologie', 'andrologie', 'pediatrie'],
            'documents_specifiques': 10,
            'duree_moyenne_intervention': 60,
            'taux_ambulatoire': 0.50,
            'equipes': ['chirurgien', 'anesthesiste', 'infirmiere'],
            'localisations': ['bloc_uro', 'salle_lithotritie', 'salle_endoscopie']
        },
        
        'ORL': {
            'code': 'ORL',
            'couleur': '#9B59B6',  # Violet
            'icone': '👂',
            'modules': ['otologie', 'rhinologie', 'laryngologie', 'pediatrie', 'cancero'],
            'documents_specifiques': 8,
            'duree_moyenne_intervention': 45,
            'taux_ambulatoire': 0.60,
            'equipes': ['chirurgien', 'anesthesiste', 'audiometriste'],
            'localisations': ['bloc_orl', 'salle_endoscopie', 'bloc_pediatrique']
        },
        
        'PLASTIQUE': {
            'code': 'PLA',
            'couleur': '#1ABC9C',  # Vert menthe
            'icone': '✨',
            'modules': ['reconstructrice', 'esthetique', 'main', 'brules', 'pediatrie'],
            'documents_specifiques': 14,
            'duree_moyenne_intervention': 120,
            'taux_ambulatoire': 0.30,
            'equipes': ['chirurgien', 'anesthesiste', 'infirmiere_bloc'],
            'localisations': ['bloc_plastique', 'bloc_main', 'cabinet_laser']
        },
        
        'VASCULAIRE': {
            'code': 'VAS',
            'couleur': '#C0392B',  # Rouge foncé
            'icone': '❤️',
            'modules': ['arteriel', 'veineux', 'acces_vasculaires', 'endovasculaire'],
            'documents_specifiques': 9,
            'duree_moyenne_intervention': 90,
            'taux_ambulatoire': 0.25,
            'equipes': ['chirurgien', 'anesthesiste', 'angiologue'],
            'localisations': ['bloc_vasculaire', 'salle_hybride', 'salle_echo']
        }
    }
```

### **Personnalisation des Protocoles**

```python
class ProtocolesMultiSpecialites:
    """Protocoles adaptés par spécialité"""
    
    def generer_protocole_post_op(self, specialite, procedure):
        """Génère le protocole post-opératoire spécifique"""
        
        protocole_base = {
            'surveillance': self.get_surveillance_specifique(specialite),
            'medications': self.get_medications_standard(specialite, procedure),
            'reeducation': self.get_reeducation_plan(specialite, procedure),
            'suivi': self.get_calendrier_suivi(specialite, procedure),
            'consignes': self.get_consignes_patient(specialite, procedure)
        }
        
        # Ajouts spécifiques par spécialité
        if specialite == 'ORTHOPEDIQUE':
            protocole_base['appui'] = self.get_protocole_appui(procedure)
            protocole_base['mobilisation'] = self.get_protocole_mobilisation(procedure)
            
        elif specialite == 'OPHTALMOLOGIE':
            protocole_base['collyres'] = self.get_protocole_collyres(procedure)
            protocole_base['protection'] = self.get_protection_oculaire(procedure)
            
        elif specialite == 'UROLOGIE':
            protocole_base['sondage'] = self.get_protocole_sondage(procedure)
            protocole_base['mictions'] = self.get_surveillance_mictionnelle(procedure)
            
        # ... etc pour chaque spécialité
        
        return protocole_base
```

### **Interface Utilisateur Adaptive**

```typescript
interface InterfaceMultiSpecialites {
  // Thème visuel par spécialité
  theme: {
    primaryColor: string;      // Couleur principale de la spécialité
    secondaryColor: string;
    icon: string;
    logo: string;
  };
  
  // Formulaires spécifiques
  forms: {
    programmation: SpecialtyProgrammingForm;
    consultation: SpecialtyConsultationForm;
    compte_rendu: SpecialtyReportForm;
  };
  
  // Vues calendrier adaptées
  calendar: {
    defaultView: 'month' | 'week' | 'day';
    slotDuration: number;      // 15min pour ophtalmo, 60min pour digestif
    colorCoding: LocationBased | ProcedureBased | UrgencyBased;
  };
  
  // Documents personnalisés
  documents: {
    templates: DocumentTemplate[];
    requiredByProcedure: Map<Procedure, Document[]>;
    consentForms: ConsentForm[];
  };
  
  // Workflows spécifiques
  workflows: {
    standard: WorkflowStep[];
    urgence: UrgencyWorkflow;
    ambulatoire: AmbulatoireWorkflow;
    hospitalisation: HospitalisationWorkflow;
  };
}
```

---

## 💰 Modèle Économique Multi-Spécialités

### **Tarification SaaS par Spécialité**

| Spécialité | Nb Praticiens | Prix/mois | Marché Potentiel/an |
|------------|---------------|-----------|---------------------|
| Digestif | 2,850 | 299€ | 10.2M€ |
| Orthopédie | 2,400 | 349€ | 10.0M€ |
| Ophtalmologie | 1,950 | 399€ | 9.3M€ |
| Gynécologie | 1,500 | 279€ | 5.0M€ |
| Urologie | 1,200 | 299€ | 4.3M€ |
| ORL | 900 | 249€ | 2.7M€ |
| Plastique | 750 | 449€ | 4.0M€ |
| Vasculaire | 600 | 279€ | 2.0M€ |
| **TOTAL** | **11,150** | **Moy: 329€** | **47.5M€** |

### **Modules Additionnels**

```python
MODULES_PREMIUM = {
    'robot_chirurgical': {
        'prix': 99,  # €/mois
        'specialites': ['digestif', 'urologie', 'gyneco', 'ortho'],
        'features': ['planning_robot', 'protocoles_robot', 'maintenance']
    },
    'imagerie_3d': {
        'prix': 79,
        'specialites': ['ortho', 'plastique', 'orl'],
        'features': ['reconstruction_3d', 'planning_preop', 'guides']
    },
    'telemedicine': {
        'prix': 59,
        'specialites': 'toutes',
        'features': ['consultation_video', 'suivi_distance', 'ordonnances']
    },
    'ia_assistant': {
        'prix': 149,
        'specialites': 'toutes',
        'features': ['codage_auto', 'aide_decision', 'predictions']
    }
}
```

---

## 🚀 Stratégie de Déploiement

### **Phase 1: MVP Multi-Spécialités (Mois 1-3)**
1. Core commun (planning, patients, documents)
2. Digestif + Orthopédie (35% du marché)
3. Templates de base par spécialité

### **Phase 2: Extension Majeure (Mois 4-6)**
1. Ophtalmologie + Gynécologie (23% additionnel)
2. Modules spécialisés (coelioscopie, microscope)
3. Intégrations CCAM complètes

### **Phase 3: Couverture Complète (Mois 7-9)**
1. Urologie + Plastique + Vasculaire
2. Modules premium (robot, 3D)
3. API pour intégrations tierces

### **Phase 4: Intelligence & Optimisation (Mois 10-12)**
1. IA prédictive
2. Optimisation des blocs
3. Analytics avancés

---

## ✅ Conclusion

Cette extension multi-spécialités permet de :
- **Adresser 81% du marché français** (11,150 chirurgiens)
- **Potentiel de revenus de 47.5M€/an**
- **Économies d'échelle** sur le développement
- **Cross-selling** entre spécialités
- **Position dominante** sur le marché français

Le système reste **hautement configurable** tout en partageant un **noyau technique commun**, permettant une maintenance efficace et des évolutions rapides.