# controllers/exceptions.py
"""
Exceptions metier de l'application SGC.

Ces exceptions permettent de distinguer les erreurs fonctionnelles
(regles metier) des erreurs techniques (BDD, reseau).
"""


class SGCError(Exception):
    """Exception de base pour toutes les erreurs metier SGC."""


class StockInsuffisantError(SGCError):
    """Stock disponible insuffisant pour satisfaire la demande."""


class VenteDejaPayeeError(SGCError):
    """Action impossible : la vente est deja entierement payee."""


class VenteAnnuleeError(SGCError):
    """Action impossible : la vente a deja ete annulee."""


class VentePayeeNonAnnulableError(SGCError):
    """Une vente payee ne peut pas etre annulee."""


class PermissionRefuseeError(SGCError):
    """L'utilisateur n'a pas les droits necessaires pour cette action."""


class EntiteIntrouvableError(SGCError):
    """L'entite demandee n'existe pas en base de donnees."""


class DoublonError(SGCError):
    """Un enregistrement identique existe deja."""


class ValidationError(SGCError):
    """Les donnees fournies ne passent pas la validation metier."""
