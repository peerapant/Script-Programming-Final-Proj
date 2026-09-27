import re
from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd


class ExcelMappingRepository:
    @staticmethod
    def sanitize_filename(name: Any) -> str:
        if pd.isna(name):
            return ""
        return re.sub(r'[\\/*?:"<>|]', '_', str(name).strip())

    @staticmethod
    def clean_id(val: Any) -> str:
        if pd.isna(val):
            return ""
        val_str = str(val).strip()
        return val_str[:-2] if val_str.endswith('.0') else val_str

    @staticmethod
    def normalize_date(val: Any) -> str:
        if pd.isna(val) or val is None or str(val).strip() == '':
            return ""

        if isinstance(val, (pd.Timestamp, np.datetime64)):
            dt = pd.to_datetime(val)
            y = dt.year - 543 if dt.year > 2500 else dt.year
            return f"{y:04d}-{dt.month:02d}-{dt.day:02d}"

        val_str = str(val).strip()

        if len(val_str) == 6 and val_str.isdigit():
            day, month, yy = int(val_str[:2]), int(val_str[2:4]), int(val_str[4:])
            year_be = 2500 + yy if yy > 50 else 2543 + yy
            return f"{year_be - 543:04d}-{month:02d}-{day:02d}"

        try:
            val_str_clean = val_str.split(' ')[0]
            parts = re.split(r'[/\-.]', val_str_clean)
            if len(parts) == 3:
                p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
                if p3 > 2000:
                    year = p3 - 543 if p3 > 2500 else p3
                    month, day = (p2, p1) if p1 > 12 else (p1, p2)
                    return f"{year:04d}-{month:02d}-{day:02d}"
                elif p1 > 2000:
                    year = p1 - 543 if p1 > 2500 else p1
                    return f"{year:04d}-{p2:02d}-{p3:02d}"
        except Exception:
            pass

        return val_str

    def parse_mapping_dataframe(self, df: pd.DataFrame) -> Dict[Tuple[str, str], str]:
        df.iloc[:, 0] = df.iloc[:, 0].ffill()
        mapping = {}

        for _, row in df.iterrows():
            norm_date = self.normalize_date(row.iloc[0])
            key_id = self.clean_id(row.iloc[1])
            rock_name = self.sanitize_filename(row.iloc[2])

            if key_id and rock_name and norm_date:
                mapping[(norm_date, key_id)] = rock_name

        return mapping