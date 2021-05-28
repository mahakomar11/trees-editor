import pandas as pd
import gspread


def read_sheet(spread, sheet):
    sheet = spread.worksheet(sheet)
    return pd.DataFrame(sheet.get_all_records())


def write_to_sheet(spread, sheet, df, with_index=False, to_rewrite=True):
    if to_rewrite:
        spread.worksheet(sheet).clear()
    if with_index:
        df = df.reset_index()
    spread.worksheet(sheet).update([df.columns.values.tolist()] + df.values.tolist())


class SpreadTable:
    def __init__(self, name : str):
        gc = gspread.service_account()
        self.spread = gc.open(name)

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        return read_sheet(self.spread, sheet_name)

    def write_to_sheet(self, sheet_name: str, data: pd.DataFrame, with_index=False, to_rewrite=False) -> None:
        write_to_sheet(self.spread, sheet_name, data, with_index=with_index, to_rewrite=to_rewrite)