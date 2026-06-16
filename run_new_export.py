import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from warfare_simulation.export.workbook_factory import WorkbookFactory
from warfare_simulation.export.generators import (
    DashboardGenerator, ProvincesGenerator, ResourcesGenerator,
    ArmyRegisterGenerator, CommandersGenerator, DiplomacyGenerator,
    LogisticsGenerator, EventLogGenerator
)

# --- NEW IMPORTS FOR PHASE 3 PIPELINE ---
from warfare_simulation.persistence.database import DatabaseManager
from warfare_simulation.config.config import ConfigManager
from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "campaign.xlsx")
DB_PATH = os.path.join(os.path.dirname(__file__), "campaign.db")

# 1. Initialize the Core Infrastructure
db = DatabaseManager(DB_PATH)
config_mgr = ConfigManager() # Note: If this complains about needing a path, we will fix it in a moment!

# 2. BOOTSTRAP THE CAMPAIGN! 
# (This reads JSON configs, populates SQLite, and returns hydrated repositories)
# Change this line:
repos = CampaignBootstrap.initialize(config_mgr, db, force=True)

# 3. Inject the LIVE repositories into our generators
factory = WorkbookFactory(generators=[
    DashboardGenerator(kingdom_repo=repos.kingdom),
    ProvincesGenerator(province_repo=repos.province), # Now injected!
    ResourcesGenerator(),
    ArmyRegisterGenerator(),
    CommandersGenerator(),
    DiplomacyGenerator(),
    LogisticsGenerator(),
    EventLogGenerator()
])

factory.export(OUTPUT_PATH)