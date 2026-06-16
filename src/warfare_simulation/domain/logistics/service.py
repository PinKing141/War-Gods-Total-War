"""
Logistics domain service.

Orchestrates resource management, projects, and supply chains.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.validation import ValidationService
from warfare_simulation.core.exceptions import InvalidCampaignStateError, ResourceError
from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.constants import ResourceType, ProjectType
from .models import Resource, Project, SupplyRoute
from .repository import ResourceRepository, ProjectRepository, SupplyRouteRepository


logger = get_logger(__name__)


class LogisticsService(GameSystem):
    """
    Service for resource and logistics management.
    
    Handles resources, projects, and supply chains.
    """
    
    def __init__(
        self,
        resource_repo: ResourceRepository,
        project_repo: ProjectRepository,
        route_repo: SupplyRouteRepository,
        validator: ValidationService,
    ):
        """Initialize Logistics service."""
        super().__init__("Logistics")
        self.resource_repo = resource_repo
        self.project_repo = project_repo
        self.route_repo = route_repo
        self.validator = validator
    
    def initialize(self) -> None:
        """Initialize Logistics service."""
        logger.info("Logistics service initialized")
        self._initialized = True
    
    def create_resource(
        self,
        kingdom_id: int,
        resource_type: ResourceType,
        initial_stored: int,
        monthly_production: int,
    ) -> Resource:
        """
        Create a new resource tracking entry.
        
        Args:
            kingdom_id: Kingdom this resource belongs to
            resource_type: Type of resource
            initial_stored: Starting amount
            monthly_production: Production per turn
        
        Returns:
            Created resource
        """
        resource = Resource(
            kingdom_id=kingdom_id,
            resource_type=resource_type,
            stored=initial_stored,
            monthly_production=monthly_production,
        )
        
        created = self.resource_repo.create(resource)
        logger.info(f"Resource '{resource_type.value}' created for kingdom {kingdom_id}")
        return created
    
    def create_project(
        self,
        kingdom_id: int,
        name: str,
        project_type: ProjectType,
        cost_silver: int,
        duration: int,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            kingdom_id: Kingdom building project
            name: Project name
            project_type: Type of project
            cost_silver: Cost in silver
            duration: Turns to complete
        
        Returns:
            Created project
        """
        project = Project(
            kingdom_id=kingdom_id,
            name=name,
            project_type=project_type,
            cost_silver=cost_silver,
            turns_remaining=duration,
        )
        
        created = self.project_repo.create(project)
        logger.info(f"Project '{name}' created (cost: {cost_silver} silver)")
        return created
    
    def advance_resource_turn(self, resource_id: int) -> Resource:
        """
        Advance resource production/consumption for one turn.
        
        Args:
            resource_id: Resource to advance
        
        Returns:
            Updated resource
        """
        resource = self.resource_repo.get(resource_id)
        if not resource:
            raise InvalidCampaignStateError(f"Resource {resource_id} not found")
        
        # Validate production/consumption
        self.validator.validate_resource_production(
            resource.monthly_production,
            resource.monthly_consumption,
        )
        
        resource.advance_turn()
        
        updated = self.resource_repo.update(resource)
        logger.debug(
            f"Resource '{resource.resource_type.value}' advanced: "
            f"stored={updated.stored}"
        )
        
        return updated
    
    def advance_project_turn(self, project_id: int) -> Project:
        """
        Advance project progress.
        
        Args:
            project_id: Project to advance
        
        Returns:
            Updated project
        """
        project = self.project_repo.get(project_id)
        if not project:
            raise InvalidCampaignStateError(f"Project {project_id} not found")
        
        if not project.is_complete():
            project.advance_progress(10)  # 10% per turn (5 turns total by default)
            
            updated = self.project_repo.update(project)
            logger.debug(f"Project '{project.name}' advanced: {updated.progress_percent}%")
            
            if updated.is_complete():
                logger.info(f"Project '{project.name}' COMPLETED")
            
            return updated
        
        return project
    
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute logistics systems for this turn.
        
        Args:
            turn_number: Current campaign turn
        """
        # Advance all resources
        for resource in self.resource_repo.list_all():
            self.advance_resource_turn(resource.id)
        
        # Advance all projects
        for project in self.project_repo.get_active():
            self.advance_project_turn(project.id)
    
    def validate_state(self) -> list:
        """
        Validate all logistics state.
        
        Returns:
            List of validation error messages
        """
        errors = []
        for resource in self.resource_repo.list_all():
            try:
                self.validator.validate_resource_production(
                    resource.monthly_production,
                    resource.monthly_consumption,
                )
            except Exception as e:
                errors.append(str(e))
        return errors
