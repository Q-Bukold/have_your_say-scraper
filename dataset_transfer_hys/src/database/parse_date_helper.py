from datetime import datetime

# Helper function to parse dates or return None
def parse_date(date_str):
    if date_str == "None":
        return None
    else:
        try:
            date_object = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
            date_str = date_object.strftime("%Y-%m-%d %H:%M:%S")
            return date_str  # Adjust format if needed
        except ValueError as e:
            print(e)
            return None