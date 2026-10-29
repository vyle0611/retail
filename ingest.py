import os
import glob
import duckdb
import kagglehub

# ===================== CẤU HÌNH =====================
DATASET_HANDLE = "mkechinov/ecommerce-behavior-data-from-multi-category-store"
FILE_KEYWORD = "Nov"          # chỉ nạp file CSV có chữ này trong tên (vd "Nov" -> 2019-Nov.csv)
                              # đặt "" nếu muốn lấy file CSV đầu tiên
BRONZE_TABLE = "bronze_raw_events"
# ====================================================

md_token = os.environ.get("MOTHERDUCK_TOKEN")
kaggle_token = os.environ.get("KAGGLE_API_TOKEN")
if not md_token or not kaggle_token:
    raise ValueError("Thiếu MOTHERDUCK_TOKEN hoặc KAGGLE_API_TOKEN trong Environment Variables!")
os.environ["KAGGLE_API_TOKEN"] = kaggle_token

# 1. Tải dataset
print("Đang tải dataset từ Kaggle...")
download_path = kagglehub.dataset_download(DATASET_HANDLE)
print(f"Đã tải về: {download_path}")
version = os.path.basename(download_path.rstrip("/"))

# 2. Chọn file CSV
csv_files = sorted(glob.glob(os.path.join(download_path, "**", "*.csv"), recursive=True))
print("Các file CSV trong dataset:", [os.path.basename(f) for f in csv_files])
if not csv_files:
    raise FileNotFoundError("Không tìm thấy file CSV trong dataset!")

matched = [f for f in csv_files if FILE_KEYWORD.lower() in os.path.basename(f).lower()]
if not matched:
    raise FileNotFoundError(f"Không có file CSV nào chứa '{FILE_KEYWORD}' trong tên!")
target_file = matched[0]
file_name = os.path.basename(target_file)
print(f"File sẽ nạp: {file_name}")

# Khóa nhận diện: đổi phiên bản HOẶC đổi file thì sẽ nạp lại
load_key = f"{version}|{file_name}"

# 3. Kết nối MotherDuck
con = duckdb.connect(f"md:retail_db?motherduck_token={md_token}")

try:
    con.execute("""
        CREATE TABLE IF NOT EXISTS ingest_log (
            dataset VARCHAR, load_key VARCHAR, loaded_at TIMESTAMP
        )
    """)

    last = con.execute(
        "SELECT load_key FROM ingest_log WHERE dataset = ? ORDER BY loaded_at DESC LIMIT 1",
        [DATASET_HANDLE],
    ).fetchone()

    table_exists = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [BRONZE_TABLE],
    ).fetchone()[0] > 0

    if table_exists and last and last[0] == load_key:
        print(f"Dữ liệu không đổi ({load_key}), bỏ qua bước nạp.")
    else:
        print(f"Nạp lại Bronze: {last[0] if last else 'chưa có'} -> {load_key}")
        safe_path = target_file.replace("'", "''")
        con.execute(f"""
            CREATE OR REPLACE TABLE main.{BRONZE_TABLE} AS
            SELECT * FROM read_csv_auto('{safe_path}')
        """)
        con.execute(
            "INSERT INTO ingest_log VALUES (?, ?, now())",
            [DATASET_HANDLE, load_key],
        )
        n = con.execute(f"SELECT COUNT(*) FROM main.{BRONZE_TABLE}").fetchone()[0]
        print(f"Nạp Bronze thành công! Tổng số dòng: {n:,}")
finally:
    con.close()
