import json
import requests
import urllib.parse
from datetime import datetime

# ================= CẤU HÌNH =================
# Link JSON bạn cung cấp. 
# LƯU Ý: Nếu link này trả về trang web (HTML) thay vì text JSON, script sẽ báo lỗi.
# Bạn cần đảm bảo đây là link trực tiếp tới file raw JSON hoặc API Endpoint.
JSON_URL = "https://cktv.pro" 
# Tên file M3U xuất ra
OUTPUT_FILE = "cakhiatv.m3u"
# ============================================

def decode_monplayer_url(url):
    """
    Hàm giải mã link dạng monplayer:// thành link http gốc
    """
    if not url: return None
    try:
        # Nếu là link monplayer thì decode
        if url.startswith("monplayer://"):
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed.query)
            if 'link' in query:
                return query['link'][0]
        # Nếu là link http/https bình thường thì giữ nguyên
        return url
    except Exception:
        return url

def process_item(item, group_name, m3u_lines):
    """
    Hàm xử lý từng kênh/trận đấu riêng lẻ và thêm vào list
    """
    try:
        name = item.get("name", "No Name")
        
        # Lấy logo (ưu tiên ảnh cover)
        logo = ""
        if item.get("image"):
            logo = item["image"].get("url", "")
        
        # Lấy Link stream
        stream_url = ""
        if item.get("remote_data"):
            raw_url = item["remote_data"].get("url", "")
            stream_url = decode_monplayer_url(raw_url)
        
        # Lấy ID (dùng cho tvg-id)
        c_id = item.get("id", "")

        # Chỉ thêm vào nếu có link stream
        if stream_url:
            # Tạo metadata cho M3U
            # Dòng info: #EXTINF:-1 tvg-id="id" tvg-logo="logo" group-title="Group", Tên kênh
            meta = f'#EXTINF:-1 tvg-id="{c_id}" tvg-logo="{logo}" group-title="{group_name}", {name}'
            m3u_lines.append(meta)
            
            # Thêm headers giả lập trình duyệt để tránh bị chặn (quan trọng cho link cktv.pro)
            if "cktv.pro" in stream_url:
                m3u_lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
                m3u_lines.append(f'#EXTVLCOPT:http-referrer=https://cktv.pro/')
            
            m3u_lines.append(stream_url)
            
    except Exception as e:
        print(f"Lỗi khi xử lý item {item.get('name')}: {e}")

def main():
    print(f"🔄 Đang tải dữ liệu từ: {JSON_URL}")
    
    # Headers giả lập trình duyệt
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        response = requests.get(JSON_URL, headers=headers, timeout=15)
        
        # Kiểm tra xem có phải JSON không
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("❌ LỖI: URL trả về không phải là JSON hợp lệ (Có thể là HTML trang chủ).")
            print("👉 Vui lòng kiểm tra lại link API chính xác (F12 -> Network Tab).")
            return

        # Khởi tạo nội dung M3U
        m3u_lines = ["#EXTM3U"]
        m3u_lines.append(f"#EXTINF:-1, 🕒 Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        m3u_lines.append("http://localhost/info") # Link dummy

        # Duyệt qua các Groups chính
        if "groups" in data:
            for group in data["groups"]:
                group_name = group.get("name", "Khác")
                print(f"📂 Đang xử lý nhóm: {group_name}")

                # TRƯỜNG HỢP 1: Group chứa danh sách 'channels' (thường là Bóng đá)
                if "channels" in group and group["channels"]:
                    for channel in group["channels"]:
                        process_item(channel, group_name, m3u_lines)

                # TRƯỜNG HỢP 2: Group lồng nhau trong 'groups' (thường là mục Giải trí/Related)
                # Ví dụ: Mục "Nội dung hấp dẫn" -> chứa các group con như "VTVGO", "Gà Vàng"
                elif "groups" in group and group["groups"]:
                    # Trong trường hợp này, các phần tử con trong 'groups' đóng vai trò là kênh
                    for sub_item in group["groups"]:
                        # Đôi khi tên group cha quá dài, ta lấy tên group con làm tên kênh luôn
                        process_item(sub_item, group_name, m3u_lines)

        # Ghi ra file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        
        print(f"✅ HOÀN TẤT! File playlist đã được lưu tại: {OUTPUT_FILE}")
        print(f"📊 Tổng số kênh/trận đấu: {len(m3u_lines)//2}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi kết nối mạng: {e}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")

if __name__ == "__main__":
    main()
