"""
Kingdom domain models.

The Kingdom entity represents the player's realm with:
- Treasury and economic state
- Population and loyalty
- Morale and stability
- Turn-based progression
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from warfare_simulation.core.base import GameEntity
from warfare_simulation.core.constants import (
    DEFAULT_MORALE, DEFAULT_LOYALTY, DEFAULT_MONTHLY_INCOME, DEFAULT_MONTHLY_EXPENSES
)


@dataclass
class Kingdom(GameEntity):
    """
    Represents a kingdom/realm in the campaign.
    
    Attributes:
        name: Kingdom name (e.g., "The Dominion of Auster")
        ruler_name: Name of the ruler
        population: Total population (minimum 1000)
        treasury_silver: Available currency
        monthly_income: Income per turn
        monthly_expenses: Expenses per turn
        morale: National morale (0-100)
        loyalty: Noble loyalty (0-100)
        grain_stores: Food reserves (in months)
        current_day: Current day in month (1-31)
        current_turn: Current turn number
        current_month: Current month in year (1-12)
        current_year: Current year
    """
    
    name: str = ""
    ruler_name: str = ""
    population: int = 0
    treasury_silver: int = 0
    monthly_income: int = DEFAULT_MONTHLY_INCOME
    monthly_expenses: int = DEFAULT_MONTHLY_EXPENSES
    morale: int = DEFAULT_MORALE
    loyalty: int = DEFAULT_LOYALTY
    grain_stores: int = 0  # Months of food
    current_day: int = 1
    current_turn: int = 1
    current_month: int = 1  # 1-12
    current_year: int = 1
    
    def advance_turn(self) -> None:
        """
        Advance the kingdom by one turn.
        
        Updates:
        - Treasury (add income, subtract expenses)
        - Month/year counter
        - Morale adjustments
        """
        # Update treasury
        net_income = self.monthly_income - self.monthly_expenses
        self.treasury_silver += net_income
        
        # Advance time
        self.current_day = 1
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        
        self.current_turn += 1
        self.mark_updated()
    
    def spend_silver(self, amount: int) -> None:
        """
        Spend silver from treasury.
        
        Args:
            amount: Amount to spend
        
        Raises:
            ValueError: If insufficient funds
        """
        if amount > self.treasury_silver:
            raise ValueError(
                f"Cannot spend {amount} silver; only have {self.treasury_silver}"
            )
        self.treasury_silver -= amount
        self.mark_updated()
    
    def gain_silver(self, amount: int) -> None:
        """
        Gain silver to treasury.
        
        Args:
            amount: Amount to gain
        """
        self.treasury_silver += amount
        self.mark_updated()
    
    def consume_grain(self, months: int) -> bool:
        """
        Consume grain stores.
        
        Args:
            months: Months of grain to consume
        
        Returns:
            True if sufficient grain, False otherwise
        """
        if months > self.grain_stores:
            return False
        
        self.grain_stores -= months
        self.mark_updated()
        return True
    
    def add_grain(self, months: int) -> None:
        """Add grain to stores."""
        self.grain_stores += months
        self.mark_updated()
    
    def set_morale(self, morale: int) -> None:
        """
        Set kingdom morale (0-100).
        
        Args:
            morale: Morale value
        
        Raises:
            ValueError: If out of range
        """
        if not 0 <= morale <= 100:
            raise ValueError(f"Morale must be 0-100, got {morale}")
        self.morale = morale
        self.mark_updated()
    
    def set_loyalty(self, loyalty: int) -> None:
        """
        Set noble loyalty (0-100).
        
        Args:
            loyalty: Loyalty value
        
        Raises:
            ValueError: If out of range
        """
        if not 0 <= loyalty <= 100:
            raise ValueError(f"Loyalty must be 0-100, got {loyalty}")
        self.loyalty = loyalty
        self.mark_updated()
    
    def get_net_income(self) -> int:
        """Calculate net income (monthly income - expenses)."""
        return self.monthly_income - self.monthly_expenses
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        base = super().to_dict()
        base.update({
            "name": self.name,
            "ruler_name": self.ruler_name,
            "population": self.population,
            "treasury_silver": self.treasury_silver,
            "monthly_income": self.monthly_income,
            "monthly_expenses": self.monthly_expenses,
            "morale": self.morale,
            "loyalty": self.loyalty,
            "grain_stores": self.grain_stores,
            "current_day": self.current_day,
            "current_turn": self.current_turn,
            "current_month": self.current_month,
            "current_year": self.current_year,
        })
        return base


@dataclass
class Treasury(GameEntity):
    """
    Detailed treasury record for a kingdom.
    
    Tracks income/expense categories separately.
    """
    
    kingdom_id: int = 0
    tax_income: int = 0  # From provinces
    trade_income: int = 0  # From trade routes
    other_income: int = 0
    military_expense: int = 0  # Army upkeep
    logistics_expense: int = 0  # Supply chains
    construction_expense: int = 0  # Building projects
    other_expense: int = 0
    
    def get_total_income(self) -> int:
        """Sum all income sources."""
        return self.tax_income + self.trade_income + self.other_income
    
    def get_total_expense(self) -> int:
        """Sum all expense categories."""
        return (
            self.military_expense + self.logistics_expense +
            self.construction_expense + self.other_expense
        )
    
    def get_net(self) -> int:
        """Calculate net (income - expense)."""
        return self.get_total_income() - self.get_total_expense()
