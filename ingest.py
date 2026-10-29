import os
import glob
import duckdb
import kagglehub

# 1. Lấy Token từ môi trường
md_token = os.environ.get("MOTHERDUCK_TOKEN")
kaggle_token = os.environ.get("KAGGLE_API_TOKEN")

if not md_token or not kaggle_token:
    raise ValueError("Thiếu MOTHERDUCK_TOKEN hoặc KAGGLE_API_TOKEN trong Environment Variables!")

# Thiết lập biến môi trường cho kagglehub nhận diện
os.environ["KAGGLE_API_TOKEN"] = kaggle_token

print("Đang tải dataset từ Kaggle...")
dataset_handle = "mkechinov/ecommerce-behavior-data-from-multi-category-store"
download_path = kagglehub.dataset_download(dataset_handle)
print(f"Đã tải thành công về: {download_path}")

# 2. Tìm file CSV trong thư mục vừa tải
csv_files = glob.glob(f"{download_path}/*.csv")
if not csv_files:
    raise FileNotFoundError("Không tìm thấy file CSV trong dataset!")
target_file = csv_files[0]

print("Đang kết nối MotherDuck và nạp dữ liệu vào tầng Bronze...")
# 3. Kết nối MotherDuck và nạp vào database 'retail_db'
con = duckdb.connect(f"md:retail_db?motherduck_token={md_token}")

con.execute(f"""
    CREATE TABLE IF NOT EXISTS bronze_raw_events AS 
    SELECT * FROM read_csv_auto('{target_file}')
""")

print("Nạp dữ liệu vào tầng Bronze thành công!")
con.close()
