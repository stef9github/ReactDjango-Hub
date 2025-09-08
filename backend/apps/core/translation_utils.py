"""
Utilitaires de Traduction Médicale pour la Terminologie Chirurgicale Français-Anglais
Spécialisé pour la pratique chirurgicale et les plateformes SaaS médicales.

Medical Translation Utilities for French-English Medical Terminology
Specialized for surgical practice and medical SaaS platforms.
"""

from typing import Dict, Optional
from django.conf import settings
from django.utils.translation import gettext as _, get_language


class MedicalTranslator:
    """
    Traducteur de terminologie médicale pour la pratique chirurgicale français-anglais.
    French-primary medical terminology translator for surgical practice.
    """
    
    # Surgical Procedures - French primary with German and English support
    SURGICAL_PROCEDURES = {
        'fr': {
            'appendicectomie': {'en': 'appendectomy', 'de': 'Blinddarmoperation'},
            'cholécystectomie': {'en': 'cholecystectomy', 'de': 'Gallenblasenentfernung'},
            'arthroplastie': {'en': 'arthroplasty', 'de': 'Gelenkersatz'},
            'craniotomie': {'en': 'craniotomy', 'de': 'Kraniotomie'},
            'mastectomie': {'en': 'mastectomy', 'de': 'Mastektomie'},
            'transplantation': {'en': 'transplantation', 'de': 'Transplantation'},
            'laparoscopie': {'en': 'laparoscopy', 'de': 'Laparoskopie'},
            'endoscopie': {'en': 'endoscopy', 'de': 'Endoskopie'},
            'biopsie': {'en': 'biopsy', 'de': 'Biopsie'},
            'suture': {'en': 'suture', 'de': 'Naht'}
        },
        'en': {
            'appendectomy': {'fr': 'appendicectomie', 'de': 'Blinddarmoperation'},
            'cholecystectomy': {'fr': 'cholécystectomie', 'de': 'Gallenblasenentfernung'},
            'arthroplasty': {'fr': 'arthroplastie', 'de': 'Gelenkersatz'},
            'craniotomy': {'fr': 'craniotomie', 'de': 'Kraniotomie'},
            'mastectomy': {'fr': 'mastectomie', 'de': 'Mastektomie'},
            'transplantation': {'fr': 'transplantation', 'de': 'Transplantation'},
            'laparoscopy': {'fr': 'laparoscopie', 'de': 'Laparoskopie'},
            'endoscopy': {'fr': 'endoscopie', 'de': 'Endoskopie'},
            'biopsy': {'fr': 'biopsie', 'de': 'Biopsie'},
            'suture': {'fr': 'suture', 'de': 'Naht'}
        },
        'de': {
            'Blinddarmoperation': {'fr': 'appendicectomie', 'en': 'appendectomy'},
            'Gallenblasenentfernung': {'fr': 'cholécystectomie', 'en': 'cholecystectomy'},
            'Gelenkersatz': {'fr': 'arthroplastie', 'en': 'arthroplasty'},
            'Kraniotomie': {'fr': 'craniotomie', 'en': 'craniotomy'},
            'Mastektomie': {'fr': 'mastectomie', 'en': 'mastectomy'},
            'Transplantation': {'fr': 'transplantation', 'en': 'transplantation'},
            'Laparoskopie': {'fr': 'laparoscopie', 'en': 'laparoscopy'},
            'Endoskopie': {'fr': 'endoscopie', 'en': 'endoscopy'},
            'Biopsie': {'fr': 'biopsie', 'en': 'biopsy'},
            'Naht': {'fr': 'suture', 'en': 'suture'}
        }
    }
    
    # Medical Equipment - French to English
    MEDICAL_EQUIPMENT = {
        'fr_to_en': {
            'bistouri': 'scalpel',
            'forceps': 'forceps',
            'ciseaux chirurgicaux': 'surgical scissors',
            'clamps hémostatiques': 'hemostatic clamps',
            'écarteurs': 'retractors',
            'trocarts': 'trocars',
            'endoscope': 'endoscope',
            'respirateur artificiel': 'ventilator',
            'moniteur cardiaque': 'cardiac monitor',
            'défibrillateur': 'defibrillator'
        },
        'en_to_fr': {
            'scalpel': 'bistouri',
            'forceps': 'forceps', 
            'surgical scissors': 'ciseaux chirurgicaux',
            'hemostatic clamps': 'clamps hémostatiques',
            'retractors': 'écarteurs',
            'trocars': 'trocarts',
            'endoscope': 'endoscope',
            'ventilator': 'respirateur artificiel',
            'cardiac monitor': 'moniteur cardiaque',
            'defibrillator': 'défibrillateur'
        }
    }
    
    # Patient Data Fields
    PATIENT_FIELDS = {
        'fr_to_en': {
            'nom': 'last_name',
            'prénom': 'first_name',
            'date de naissance': 'birth_date',
            'sexe': 'gender',
            'adresse': 'address',
            'téléphone': 'phone',
            'courriel': 'email',
            'antécédents médicaux': 'medical_history',
            'allergies': 'allergies',
            'médicaments': 'medications',
            'diagnostic': 'diagnosis',
            'traitement': 'treatment'
        },
        'en_to_fr': {
            'last_name': 'nom',
            'first_name': 'prénom',
            'birth_date': 'date de naissance',
            'gender': 'sexe',
            'address': 'adresse',
            'phone': 'téléphone',
            'email': 'courriel',
            'medical_history': 'antécédents médicaux',
            'allergies': 'allergies',
            'medications': 'médicaments',
            'diagnosis': 'diagnostic',
            'treatment': 'traitement'
        }
    }
    
    @classmethod
    def translate_term(cls, term: str, source_lang: str = 'en', 
                      target_lang: str = 'fr', category: str = 'general') -> str:
        """
        Translate a medical term between French and English.
        
        Args:
            term: Medical term to translate
            source_lang: Source language ('en' or 'fr')
            target_lang: Target language ('en' or 'fr')  
            category: Category of medical term ('procedures', 'equipment', 'patient_fields')
            
        Returns:
            Translated term or original if not found
        """
        if source_lang == target_lang:
            return term
            
        translation_key = f"{source_lang}_to_{target_lang}"
        
        # Select appropriate dictionary based on category
        if category == 'procedures':
            dictionary = cls.SURGICAL_PROCEDURES.get(translation_key, {})
        elif category == 'equipment':
            dictionary = cls.MEDICAL_EQUIPMENT.get(translation_key, {})
        elif category == 'patient_fields':
            dictionary = cls.PATIENT_FIELDS.get(translation_key, {})
        else:
            # Search all dictionaries for general translation
            for dict_set in [cls.SURGICAL_PROCEDURES, cls.MEDICAL_EQUIPMENT, cls.PATIENT_FIELDS]:
                dictionary = dict_set.get(translation_key, {})
                if term.lower() in dictionary:
                    return dictionary[term.lower()]
            return term
            
        return dictionary.get(term.lower(), term)
    
    @classmethod
    def translate_dict(cls, data: Dict, source_lang: str = 'en', 
                      target_lang: str = 'fr', category: str = 'patient_fields') -> Dict:
        """
        Translate dictionary keys/values for medical data.
        
        Args:
            data: Dictionary to translate
            source_lang: Source language
            target_lang: Target language
            category: Category of medical terms
            
        Returns:
            Dictionary with translated keys/values
        """
        if source_lang == target_lang:
            return data
            
        translated = {}
        for key, value in data.items():
            # Translate key
            translated_key = cls.translate_term(key, source_lang, target_lang, category)
            
            # Translate value if it's a string and looks like medical term
            if isinstance(value, str) and len(value.split()) <= 3:
                translated_value = cls.translate_term(value, source_lang, target_lang, category)
            else:
                translated_value = value
                
            translated[translated_key] = translated_value
            
        return translated


def get_user_language(request) -> str:
    """Get user's preferred language from request."""
    return getattr(request.user, 'language', 'en') if hasattr(request, 'user') else 'en'


def translate_response(data: Dict, language: str = 'en') -> Dict:
    """Translate API response data to user's preferred language."""
    if language == 'en':
        return data
        
    translator = MedicalTranslator()
    return translator.translate_dict(data, 'en', language, 'general')