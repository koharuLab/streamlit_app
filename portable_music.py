import streamlit as st
from PIL import Image
import imagehash
import json
import numpy as np

# ------------------------------------------------------------------
# ① 事前データの読み込み
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_album_features(json_path="album_features.json"):
    """JSONファイルから事前生成済みアルバム特徴量（例：pHash）データを読み込みます"""
    with open(json_path, "r", encoding="utf-8") as f:
        features = json.load(f)
    return features

album_features = load_album_features()

# アルバムデータベース：キーは JSON 内の画像ファイル名、値は対応する YouTube 動画URL
album_database = {
    "album1.png": "https://youtu.be/i8adbqn6ZAo",
    "album2.png": "https://youtu.be/vmULD6h-K9Q",
    "album3.png": "https://youtu.be/5Rbv2JWK8ww"
}

# ------------------------------------------------------------------
# ② 初期設定：Streamlit 表示
# ------------------------------------------------------------------
st.title("PortableMusic - アルバムジャケット認識")

# ------------------------------------------------------------------
# ③ ユーザー入力：カメラ画像取得
# ------------------------------------------------------------------
uploaded_file = st.camera_input("カメラでアルバムジャケットを撮影してください")

if uploaded_file is not None:
    # アップロードされた画像を Pillow Image オブジェクトとして取得
    original_image = Image.open(uploaded_file)
    
    # 画像のサイズから中央正方形を計算し、切り抜く
    width, height = original_image.size
    factor = 0.6
    side = int(min(width, height) * factor)
    left = (width - side) // 2
    top = (height - side) // 2
    cropped_image = original_image.crop((left, top, left + side, top + side))
    
    # 切り抜いた画像を表示
    st.image(cropped_image, caption='識別範囲', use_container_width=True)

# ------------------------------------------------------------------
# ④ ユーティリティ関数：pHash 計算と比較
# ------------------------------------------------------------------
def compute_upload_phash(uploaded_image: Image.Image):
    """
    アップロードされた Pillow 形式の画像から pHash（ImageHash オブジェクト）を計算します
    """
    return imagehash.phash(uploaded_image)

def find_best_match(uploaded_phash, album_features, threshold=23):
    """
    事前データの各アルバムの pHash とアップロード画像の pHash の hamming 距離で照合し、
    最も距離が短い（＝類似度が高い）アルバムを返します。  
    threshold 以下であればマッチありと判断します。
    """
    best_match = None
    best_distance = None
    for album_img, features in album_features.items():
        # JSON に保存されている pHash は文字列なので、ImageHash オブジェクトに変換
        reference_phash = imagehash.hex_to_hash(features["pHash"])
        distance = uploaded_phash - reference_phash  # hamming distance の算出
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_match = album_img
    # 閾値以下ならマッチあり
    if best_distance is not None and best_distance <= threshold:
        return best_match, best_distance
    else:
        return None, best_distance

# ------------------------------------------------------------------
# ⑤ 画像認識 & 動画表示処理
# ------------------------------------------------------------------
if uploaded_file is not None:
    # ※すでに 'cropped_image' は先のブロックで作成済みなので、それを利用
    
    # 切り抜いた画像から pHash を計算
    uploaded_phash = compute_upload_phash(cropped_image)
    
    # 事前情報と比較（hamming distance により類似アルバムを検索）
    matched_album, distance = find_best_match(uploaded_phash, album_features)
    
    if matched_album:
        album_name = matched_album.split('.')[0]
        st.write(f"アルバムジャケット認識: **{album_name}** (距離: {distance}) 🎵")
        youtube_url = album_database.get(matched_album, None)
        if youtube_url:
            st.video(youtube_url)
        else:
            st.write("対応する YouTube 動画の情報が登録されていません。")
    else:
        st.write("アルバムジャケットが認識できませんでした。別の画像をお試しください。")
