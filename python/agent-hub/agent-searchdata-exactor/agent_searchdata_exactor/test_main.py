from exator import extract_html_sync, extract_and_save_html_sync

# 获取HTML内容并保存文件
result = extract_and_save_html_sync("https://opencamp.cn/gosim/camp/MoFA2025")
if result["success"]:
    print(f"文件已保存到: {result['file_path']}")
