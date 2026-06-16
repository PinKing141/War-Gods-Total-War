"""
Custom exception classes for the campaign engine.

All exceptions inherit from a base class to allow easy catching of campaign-specific errors.
"""


class CampaignEngineError(Exception):
    """
    Base exception class for all campaign engine errors.
    
    All domain-specific exceptions inherit from this class.
    This allows code to catch any campaign engine error with:
        except CampaignEngineError:
    """
    pass


class InvalidCampaignStateError(CampaignEngineError):
    """
    Raised when the campaign state is invalid or inconsistent.
    
    Examples:
    - A unit is deployed to a province that doesn't exist
    - Population goes negative
    - Treasury goes negative (if that's disallowed)
    - A faction is in an impossible diplomatic state
    """
    pass


class ResourceError(CampaignEngineError):
    """
    Raised when a domain tries to use resources it doesn't have.
    
    Examples:
    - Kingdom tries to spend 5000 silver but only has 3000
    - A province tries to garrison more troops than it has space for
    - Building a fortification costs more iron than is available
    """
    pass


class ValidationError(CampaignEngineError):
    """
    Raised when configuration data or entity state fails validation.
    
    Examples:
    - JSON config file contains invalid data (bad types, missing required fields)
    - A game rule is violated (e.g., unit morale < 0)
    - An entity has inconsistent relationships (e.g., commander not found)
    """
    pass


class DatabaseError(CampaignEngineError):
    """
    Raised when a database operation fails.
    
    Examples:
    - SQLite connection error
    - Query fails
    - Schema migration fails
    - Transaction rollback needed
    """
    pass


class ConfigurationError(CampaignEngineError):
    """
    Raised when application configuration is invalid.
    
    Examples:
    - Config file not found
    - Config file malformed
    - Required setting is missing
    - Invalid setting value
    """
    pass


class RepositoryError(CampaignEngineError):
    """
    Raised when a repository operation fails.
    
    Examples:
    - Entity not found
    - Entity already exists (duplicate)
    - CRUD operation fails
    """
    pass


class DomainServiceError(CampaignEngineError):
    """
    Raised when a domain service operation fails.
    
    Examples:
    - Turn advancement fails validation
    - Service not initialized
    - Operation violates domain rules
    """
    pass


class ExportError(CampaignEngineError):
    """
    Raised when spreadsheet export fails.
    
    Examples:
    - File write fails
    - Workbook generation fails
    - Sheet data is incomplete
    """
    pass
