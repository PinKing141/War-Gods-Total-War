import os
import pytest
import openpyxl

# Define the paths
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
GOLDEN_MASTER_PATH = os.path.join(FIXTURES_DIR, "golden_master.xlsx")

# Update this to wherever your new Phase 4 modular engine will save its output
NEW_EXPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "campaign.xlsx") 

@pytest.fixture
def golden_master_workbook():
    """Loads the legacy golden master workbook."""
    assert os.path.exists(GOLDEN_MASTER_PATH), "Golden master fixture not found!"
    return openpyxl.load_workbook(GOLDEN_MASTER_PATH, data_only=True)

@pytest.fixture
def new_export_workbook():
    """Loads the newly generated modular workbook."""
    assert os.path.exists(NEW_EXPORT_PATH), "New modular export not found. Have you run the new engine?"
    return openpyxl.load_workbook(NEW_EXPORT_PATH, data_only=True)

def test_sheet_names_and_row_counts_parity(golden_master_workbook, new_export_workbook):
    """
    Verifies that the new modular export has the exact same sheets 
    and the exact same number of rows per sheet as the legacy monolith.
    """
    golden_sheets = golden_master_workbook.sheetnames
    new_sheets = new_export_workbook.sheetnames

    # 1. Assert Sheet Names Match Exactly
    assert golden_sheets == new_sheets, f"Sheet name mismatch.\nExpected: {golden_sheets}\nGot: {new_sheets}"

    # 2. Assert Row Counts Match per Sheet
    for sheet_name in golden_sheets:
        golden_ws = golden_master_workbook[sheet_name]
        new_ws = new_export_workbook[sheet_name]

        # Calculate actual data rows (openpyxl's max_row can sometimes include empty formatted cells)
        golden_row_count = sum(1 for row in golden_ws.iter_rows(values_only=True) if any(cell is not None for cell in row))
        new_row_count = sum(1 for row in new_ws.iter_rows(values_only=True) if any(cell is not None for cell in row))

        assert new_row_count == golden_row_count, (
            f"Row count mismatch on sheet '{sheet_name}'. "
            f"Expected {golden_row_count} rows, but got {new_row_count}."
        )