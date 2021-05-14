import pandas as pd


def read_sheet(spread, sheet):
    sheet = spread.worksheet(sheet)
    return pd.DataFrame(sheet.get_all_records())


def write_to_sheet(spread, sheet, df, with_index=False, to_rewrite=True):
    if to_rewrite:
        spread.worksheet(sheet).clear()
    if with_index:
        df = df.reset_index()
    spread.worksheet(sheet).update([df.columns.values.tolist()] + df.values.tolist())