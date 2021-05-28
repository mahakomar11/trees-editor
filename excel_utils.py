import pandas as pd
from typing import Dict


class ExcelTable:
    def __init__(self, path):
        self.path = path
        self.sheets = pd.read_excel(self.path, sheet_name=None)  # type: Dict[str: pd.DataFrame]

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        return self.sheets[sheet_name]

    def write_to_sheet(self, sheet_name: str, df: pd.DataFrame, with_index=False, to_rewrite=True) -> None:
        self.sheets[sheet_name] = df
        with pd.ExcelWriter(self.path) as writer:
            for sheet, sheet_df in self.sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet, index=with_index)
