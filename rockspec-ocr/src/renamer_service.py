from typing import Dict, Optional, Tuple


class ImageRenamerService:
    @staticmethod
    def format_mag_str(mag: float) -> str:
        if mag <= 0:
            return "0"
        if mag >= 1000:
            val = mag / 1000.0
            return f"X{int(val)}k" if val.is_integer() else f"X{val:.2f}".rstrip('0').rstrip('.') + "k"
        else:
            return f"X{int(mag)}" if mag.is_integer() else f"X{mag:.2f}".rstrip('0').rstrip('.')

    def generate_new_filename(self, rock_name: str, point_num: int, zoom_num: int, mag: float, ext: str) -> str:
        mag_str = self.format_mag_str(mag)
        return f"{rock_name}-{point_num}.{zoom_num}_{mag_str}{ext}"

    @staticmethod
    def check_dual_key_status(
        file_id: str, 
        current_drive_name: str, 
        logged_file_map: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """
        ตรวจสอบว่าไฟล์บน Drive มีการถูกเปลี่ยนชื่อจากภายนอกหรือไม่ (External Renamed)
        - logged_file_map: {file_id: last_known_name}
        """
        if file_id in logged_file_map:
            last_name = logged_file_map[file_id]
            if last_name != current_drive_name:
                return True, last_name  # ถูกเปลี่ยนชื่อข้างนอก
        return False, None