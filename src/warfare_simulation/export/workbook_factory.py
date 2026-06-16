import os
import openpyxl
from typing import List
from warfare_simulation.export.base_generator import SheetGenerator

class WorkbookFactory:
    """Orchestrates the creation of the modular campaign spreadsheet."""
    
    def __init__(self, generators: List[SheetGenerator]):
        self.generators = generators

    def export(self, output_path: str):
        """Builds the workbook and triggers all injected sheet generators."""
        wb = openpyxl.Workbook()
        
# Openpyxl creates a default 'Sheet'.
        default_sheet = wb.active
        if default_sheet is not None:  # This line keeps Pylance/VS Code happy!
            default_sheet.title = "Temp"

        # Run all our modular generators (we don't have any yet!)
        for generator in self.generators:
            generator.generate(wb)

        # Clean up the default empty sheet if we generated real ones
        if len(wb.sheetnames) > 1 and "Temp" in wb.sheetnames:
            del wb["Temp"]

        # Save the new file!
        wb.save(output_path)
        print(f"Success: Modular campaign exported to {output_path}")