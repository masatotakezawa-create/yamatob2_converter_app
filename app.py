import pandas as pd
import streamlit as st
from datetime import datetime
import io
import re

# 画面設定
st.set_page_config(page_title="B2クラウドデータ変換ツール", layout="centered")

st.title("📦 ヤマト B2クラウド データ変換ツール")
st.write("サスケから出力したCSVファイルをドラッグ＆ドロップしてください。")

# 住所（住所1）から「市区郡町村」と「町・番地」を切り分ける処理
def extract_city_and_town(address_str):
    if pd.isna(address_str) or not address_str:
        return "", ""
    
    address = str(address_str).strip()
    
    # 都道府県が含まれている場合は安全のために除去
    address = re.sub(r'^(東京都|北海道|(京都|大阪)府|.{2,3}県)', '', address)
    
    # 市区町村のパターンマッチ
    match = re.match(r'^(.+?[市区町村]|.+?郡.+?[町村])(.*)$', address)
    if match:
        city = match.group(1)
        town = match.group(2)
    else:
        # マッチしない場合は全体を町・番地側へ流す
        city = ""
        town = address
        
    return city[:12], town[:16]

# ファイルアップローダー
uploaded_file = st.file_uploader("サスケのCSVファイルを選択", type=["csv"])

if uploaded_file is not None:
    try:
        # サスケのCSV読み込み
        df_saaske = pd.read_csv(uploaded_file, encoding="cp932")
        st.success(f"データ読み込み成功: {len(df_saaske)} 件")

        # B2クラウド標準フォーマット（95列）
        b2_columns = [
            "お客様管理番号", "送り状種類", "クール区分", "伝票番号", "出荷予定日", 
            "お届け予定日", "配達時間帯", "お届け先コード", "お届け先電話番号", 
            "お届け先電話番号枝番", "お届け先郵便番号", "お届け先都道府県", "お届け先市区郡町村", 
            "お届け先町・番地", "お届け先アパートマンション名", "お届け先会社・部門１", 
            "お届け先会社・部門２", "お届け先名", "お届け先名(ｶﾅ)", "敬称", 
            "ご依頼主コード", "ご依頼主電話番号", "ご依頼主電話番号枝番", "ご依頼主郵便番号", 
            "ご依頼主都道府県", "ご依頼主市区郡町村", "ご依頼主町・番地", 
            "ご依頼主アパートマンション", "ご依頼主名", "ご依頼主名(ｶﾅ)", "品名コード１", 
            "品名１", "品名コード２", "品名２", "荷扱い１", "荷扱い２", "記事", 
            "ｺﾚｸﾄ代金引換額（税込)", "内消費税額等", "止置き", "営業所コード", "発行枚数", 
            "個数口表示フラグ", "請求先顧客コード", "請求先分類コード", "運賃管理番号", 
            "クロネコwebコレクトデータ登録", "クロネコwebコレクト加盟店番号", 
            "クロネコwebコレクト申込受付番号１", "クロネコwebコレクト申込受付番号２", 
            "クロネコwebコレクト申込受付番号３", "お届け予定ｅメール利用区分", 
            "お届け予定ｅメールe-mailアドレス", "入力機種", "お届け予定ｅメールメッセージ", 
            "お届け完了ｅメール利用区分", "お届け完了ｅメールe-mailアドレス", 
            "お届け完了ｅメールメッセージ", "クロネコ収納代行利用区分", "予備", 
            "収納代行請求金額(税込)", "収納代行内消費税額等", "収納代行請求先郵便番号", 
            "収納代行請求先住所", "収納代行請求先住所（アパートマンション名）", 
            "収納代行請求先会社・部門名１", "収納代行請求先会社・部門名２", 
            "収納代行請求先名(漢字)", "収納代行請求先名(カナ)", "収納代行問合せ先名(漢字)", 
            "収納代行問合せ先郵便番号", "収納代行問合せ先住所", 
            "収納代行問合せ先住所（アパートマンション名）", "収納代行問合せ先電話番号", 
            "収納代行管理番号", "収納代行品名", "収納代行備考", "複数口くくりキー", 
            "検索キータイトル1", "検索キー1", "検索キータイトル2", "検索キー2", 
            "検索キータイトル3", "検索キー3", "検索キータイトル4", "検索キー4", 
            "検索キータイトル5", "検索キー5", "予備.1", "予備.2", "投函予定メール利用区分", 
            "投函予定メールe-mailアドレス", "投函予定メールメッセージ", 
            "投函完了メール（お届け先宛）利用区分", "投函完了メール（お届け先宛）e-mailアドレス", 
            "投函完了メール（お届け先宛）メールメッセージ", 
            "投函完了メール（ご依頼主宛）利用区分", "投函完了メール（ご依頼主宛）e-mailアドレス", 
            "投函完了メール（ご依頼主宛）メールメッセージ"
        ]

        df_b2 = pd.DataFrame(columns=b2_columns)

        # 1. 基本情報マッピング
        df_b2["お届け先電話番号"] = df_saaske["電話番号"].astype(str).str.replace("-", "")
        df_b2["お届け先郵便番号"] = df_saaske["郵便番号"].astype(str).str.replace("-", "")
        df_b2["お届け先都道府県"] = df_saaske["都道府県"].fillna("")
        
        # 2. 住所の切り分け処理（市区郡町村 / 町・番地）
        city_town_pairs = [extract_city_and_town(addr) for addr in df_saaske["住所1"]]
        df_b2["お届け先市区郡町村"] = [pair[0] for pair in city_town_pairs]
        df_b2["お届け先町・番地"] = [pair[1] for pair in city_town_pairs]
        
        # 3. 建物名（住所2がある場合）
        if "住所2" in df_saaske.columns:
            df_b2["お届け先アパートマンション名"] = df_saaske["住所2"].fillna("").astype(str).str[:16]

        df_b2["お届け先名"] = df_saaske["病院名"].astype(str).str[:16]
        
        # 4. 固定値データ
        df_b2["送り状種類"] = "0"  # 発払い
        df_b2["出荷予定日"] = datetime.now().strftime("%Y/%m/%d")
        df_b2["品名１"] = "書類"
        df_b2["請求先顧客コード"] = "0366795957"
        df_b2["運賃管理番号"] = "01"
        
        # 5. ご依頼主情報
        df_b2["ご依頼主電話番号"] = "0366795957"
        df_b2["ご依頼主郵便番号"] = "1500043"
        df_b2["ご依頼主都道府県"] = "東京都"
        df_b2["ご依頼主市区郡町村"] = "渋谷区"
        df_b2["ご依頼主町・番地"] = "道玄坂2-6-14"
        df_b2["ご依頼主アパートマンション"] = "野村不動産道玄坂ビル2階"
        df_b2["ご依頼主名"] = "株式会社バリューメディカル"

        st.subheader("変換データプレビュー")
        st.dataframe(df_b2[["出荷予定日", "お届け先名", "お届け先郵便番号", "お届け先都道府県", "お届け先市区郡町村", "お届け先町・番地", "お届け先アパートマンション名"]].head())

        # CSV出力（ヘッダー付き・Shift-JIS）
        csv_buffer = io.StringIO()
        df_b2.to_csv(csv_buffer, index=False, encoding="cp932")
        
        st.download_button(
            label="B2クラウド用CSVをダウンロード",
            data=csv_buffer.getvalue(),
            file_name=f"b2_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")