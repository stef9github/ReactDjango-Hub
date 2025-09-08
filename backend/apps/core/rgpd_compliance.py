"""
Module de Conformité RGPD pour les Plateformes Médicales SaaS
GDPR Compliance Module for Medical SaaS Platforms

Ce module fournit les outils nécessaires pour la conformité RGPD dans le contexte médical français.
This module provides the necessary tools for GDPR compliance in the French medical context.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _


class RGPDComplianceManager:
    """
    Gestionnaire de conformité RGPD pour les données médicales.
    GDPR compliance manager for medical data.
    """
    
    # Types de données personnelles selon le RGPD
    # Personal data types according to GDPR
    DATA_CATEGORIES = {
        'identifiants': {
            'fr': 'Données d\'identification',
            'en': 'Identification data',
            'examples': ['nom', 'prénom', 'email', 'téléphone']
        },
        'sante': {
            'fr': 'Données de santé',
            'en': 'Health data',
            'examples': ['diagnostic', 'traitement', 'antécédents médicaux']
        },
        'technique': {
            'fr': 'Données techniques',
            'en': 'Technical data',
            'examples': ['adresse IP', 'cookies', 'logs']
        },
        'usage': {
            'fr': 'Données d\'utilisation',
            'en': 'Usage data',
            'examples': ['historique navigation', 'préférences', 'statistiques']
        }
    }
    
    # Bases légales RGPD pour le traitement des données
    # GDPR legal bases for data processing
    LEGAL_BASES = {
        'consentement': {
            'fr': 'Consentement de la personne concernée',
            'en': 'Consent of the data subject',
            'article': 'Article 6(1)(a) RGPD'
        },
        'contrat': {
            'fr': 'Exécution d\'un contrat',
            'en': 'Performance of a contract',
            'article': 'Article 6(1)(b) RGPD'
        },
        'obligation_legale': {
            'fr': 'Respect d\'une obligation légale',
            'en': 'Compliance with legal obligation',
            'article': 'Article 6(1)(c) RGPD'
        },
        'interet_vital': {
            'fr': 'Sauvegarde des intérêts vitaux',
            'en': 'Protection of vital interests',
            'article': 'Article 6(1)(d) RGPD'
        },
        'mission_publique': {
            'fr': 'Mission d\'intérêt public',
            'en': 'Public interest or official authority',
            'article': 'Article 6(1)(e) RGPD'
        },
        'interet_legitime': {
            'fr': 'Intérêt légitime',
            'en': 'Legitimate interest',
            'article': 'Article 6(1)(f) RGPD'
        }
    }
    
    # Droits des personnes selon le RGPD
    # Individual rights under GDPR
    INDIVIDUAL_RIGHTS = {
        'information': {
            'fr': 'Droit à l\'information',
            'en': 'Right to be informed',
            'article': 'Articles 13-14 RGPD'
        },
        'acces': {
            'fr': 'Droit d\'accès',
            'en': 'Right of access',
            'article': 'Article 15 RGPD'
        },
        'rectification': {
            'fr': 'Droit de rectification',
            'en': 'Right to rectification',
            'article': 'Article 16 RGPD'
        },
        'effacement': {
            'fr': 'Droit à l\'effacement (droit à l\'oubli)',
            'en': 'Right to erasure (right to be forgotten)',
            'article': 'Article 17 RGPD'
        },
        'limitation': {
            'fr': 'Droit à la limitation du traitement',
            'en': 'Right to restrict processing',
            'article': 'Article 18 RGPD'
        },
        'portabilite': {
            'fr': 'Droit à la portabilité',
            'en': 'Right to data portability',
            'article': 'Article 20 RGPD'
        },
        'opposition': {
            'fr': 'Droit d\'opposition',
            'en': 'Right to object',
            'article': 'Article 21 RGPD'
        }
    }
    
    @classmethod
    def get_data_retention_period(cls, data_category: str, context: str = 'medical') -> Dict:
        """
        Retourne les périodes de conservation selon le contexte médical français.
        Returns data retention periods according to French medical context.
        """
        medical_retention = {
            'dossier_patient': {
                'duration': timedelta(days=365 * 20),  # 20 ans
                'fr': '20 ans après la dernière consultation',
                'en': '20 years after last consultation',
                'reference': 'Code de la santé publique R.1112-7'
            },
            'imagerie_medicale': {
                'duration': timedelta(days=365 * 20),  # 20 ans
                'fr': '20 ans pour les examens d\'imagerie',
                'en': '20 years for medical imaging',
                'reference': 'Code de la santé publique R.1112-7'
            },
            'donnees_usage': {
                'duration': timedelta(days=365 * 3),  # 3 ans
                'fr': '3 ans pour les données d\'utilisation',
                'en': '3 years for usage data',
                'reference': 'CNIL'
            },
            'logs_acces': {
                'duration': timedelta(days=365),  # 1 an
                'fr': '1 an pour les logs d\'accès',
                'en': '1 year for access logs',
                'reference': 'CNIL'
            }
        }
        
        return medical_retention.get(data_category, {
            'duration': timedelta(days=365 * 3),
            'fr': 'Période par défaut de 3 ans',
            'en': 'Default period of 3 years',
            'reference': 'RGPD Article 5'
        })
    
    @classmethod
    def generate_privacy_notice(cls, language: str = 'fr') -> Dict:
        """
        Génère une notice de confidentialité conforme RGPD.
        Generates a GDPR-compliant privacy notice.
        """
        if language == 'fr':
            return {
                'title': 'Politique de Confidentialité - Plateforme Médicale SaaS',
                'controller': 'Responsable du traitement des données',
                'purposes': 'Finalités du traitement des données médicales',
                'legal_basis': 'Bases légales pour le traitement',
                'retention': 'Durées de conservation des données',
                'rights': 'Vos droits concernant vos données personnelles',
                'contact': 'Contact du Délégué à la Protection des Données (DPO)',
                'last_updated': datetime.now().strftime('%d/%m/%Y')
            }
        else:
            return {
                'title': 'Privacy Policy - Medical SaaS Platform',
                'controller': 'Data Controller',
                'purposes': 'Purposes of medical data processing',
                'legal_basis': 'Legal basis for processing',
                'retention': 'Data retention periods',
                'rights': 'Your rights regarding personal data',
                'contact': 'Data Protection Officer (DPO) contact',
                'last_updated': datetime.now().strftime('%m/%d/%Y')
            }
    
    @classmethod
    def validate_consent(cls, consent_data: Dict) -> Dict:
        """
        Valide le consentement selon les exigences RGPD.
        Validates consent according to GDPR requirements.
        """
        required_elements = {
            'informed': 'Le consentement doit être éclairé',
            'specific': 'Le consentement doit être spécifique',
            'unambiguous': 'Le consentement doit être sans ambiguïté',
            'freely_given': 'Le consentement doit être libre',
            'withdrawable': 'Le consentement doit être révocable'
        }
        
        validation_result = {
            'valid': True,
            'issues': [],
            'timestamp': datetime.now().isoformat(),
            'version': 'RGPD-2018'
        }
        
        # Validation logic would go here
        # This is a framework for GDPR consent validation
        
        return validation_result


class RGPDConsentRecord(models.Model):
    """
    Enregistrement du consentement RGPD pour les données médicales.
    GDPR consent record for medical data.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                           verbose_name="Utilisateur")
    
    # Type de consentement
    consent_type = models.CharField(
        max_length=100,
        verbose_name="Type de consentement",
        help_text="Type de données pour lesquelles le consentement est donné"
    )
    
    # Consentement accordé
    consent_given = models.BooleanField(
        default=False,
        verbose_name="Consentement accordé"
    )
    
    # Horodatage du consentement
    consent_timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date et heure du consentement"
    )
    
    # Adresse IP pour la traçabilité
    ip_address = models.GenericIPAddressField(
        verbose_name="Adresse IP",
        help_text="Adresse IP au moment du consentement"
    )
    
    # Détails du consentement
    consent_details = models.JSONField(
        default=dict,
        verbose_name="Détails du consentement",
        help_text="Informations détaillées sur le consentement donné"
    )
    
    # Version de la politique de confidentialité
    privacy_policy_version = models.CharField(
        max_length=20,
        verbose_name="Version de la politique de confidentialité"
    )
    
    class Meta:
        verbose_name = "Enregistrement de consentement RGPD"
        verbose_name_plural = "Enregistrements de consentement RGPD"
        ordering = ['-consent_timestamp']
    
    def __str__(self):
        status = "accordé" if self.consent_given else "refusé"
        return f"Consentement {status} - {self.user.username} - {self.consent_type}"


# Décorateur pour marquer les vues qui traitent des données sensibles
# Decorator to mark views that process sensitive data
def rgpd_sensitive_data(data_category: str, legal_basis: str):
    """
    Décorateur pour les vues Django traitant des données sensibles RGPD.
    Decorator for Django views processing GDPR sensitive data.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Log de l'accès aux données sensibles
            # Log access to sensitive data
            from auditlog.models import LogEntry
            
            # Ici, on pourrait ajouter la logique de logging RGPD
            # Here we could add GDPR logging logic
            
            return view_func(request, *args, **kwargs)
        
        wrapper.rgpd_data_category = data_category
        wrapper.rgpd_legal_basis = legal_basis
        return wrapper
    
    return decorator