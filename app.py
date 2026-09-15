import pandas as pd
import streamlit as st
from datetime import datetime
import io
import re

# 画面設定
st.set_page_config(page_title="B2クラウドデータ変換ツール", layout="centered")

st.title("📦 ヤマト B2クラウド データ変換ツール")
st.write("サスケから出力したCSVファイルをドラッグ＆ドロップしてください。")

# 住所から市区郡町村を抽出する関数
def split_address(full_address):
    if pd.isna(full_address) or not full_address:
        return "", ""
    
    full_address = str(full_address).strip()
    
    # 都道府県が含まれている場合は除去
    full_address = re.sub(r'^(東京都|北海道|(京都|大阪)府|.{2,3}県)', '', full_address)
    
    # 市区郡町村パターン（〇〇市/〇〇区/〇〇郡〇〇町/〇〇郡〇〇村/〇〇町/〇〇村）
    match = re.match(r'^(.+?[市区町村]|.+?郡.+?[町村])(.*)$', full_address)
    if match:
        city = match.group(1)
        town = match.group(2)
    else:
        # 分割できなかった場合のセーフティ
        city = full_address[:12]
        town = full_address[12:]
        
    return city[:12], town[:16] # ヤマトB2の文字数制限に合わせてカット

# ファイルアップローダー
uploaded_file = st.file_uploader("サスケのCSVファイルを選択", type=["csv"])

if uploaded_file is not None:
    try:
        # サスケのCSV読み込み（Shift-JIS想定）
        df_saaske = pd.read_csv(uploaded_file, encoding="cp932")
        st.success(f"データ読み込み成功: {len(df_saaske)} 件")

        # B2クラウド標準フォーマット（95列）の枠組みを作成
        b2_columns = [
            "お客様管理番号", "送り状種類", "クール区分", "伝票番号", "出荷予定日", 
            "お届け予定日", "配達時間帯", "お届け先コード", "お届け先電話番号", 
            "お届け先電話番号枝番", "お届け先郵便番号", "お届け先住所", 
            "お届け先アパートマンション名", "お届け先会社・部門１", "お届け先会社・部門２", 
            "お届け先名", "お届け先名(ｶﾅ)", "敬称", "ご依頼主コード", "ご依頼主電話番号", 
            "ご依頼主電話番号枝番", "ご依頼主郵便番号", "ご依頼主住所", 
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

        # マッピング処理
        df_b2["お届け先電話番号"] = df_saaske["電話番号"].astype(str).str.replace("-", "")
        df_b2["お届け先郵便番号"] = df_saaske["郵便番号"].astype(str).str.replace("-", "")
        
        # 住所の分割適用（市区町村 / 町・番地）
        full_addresses = df_saaske["都道府県"].fillna("") + df_saaske["住所1"].fillna("")
        split_results = [split_address(addr) for addr in full_addresses]
        
        df_b2["お届け先住所"] = [res[0] for res in split_results]                # 市区郡町村
        df_b2["お届け先アパートマンション名"] = [res[1] for res in split_results] # 町名・番地
        
        df_b2["お届け先名"] = df_saaske["病院名"].astype(str).str[:16]  # 全角16文字制限
        
        # 固定値データ
        df_b2["送り状種類"] = "0"  # 発払い
        df_b2["出荷予定日"] = datetime.now().strftime("%Y/%m/%d")
        df_b2["品名１"] = "書類"
        df_b2["請求先顧客コード"] = "0366795957"
        df_b2["運賃管理番号"] = "01"
        
        # ご依頼主情報（固定）
        df_b2["ご依頼主電話番号"] = "03-6679-5957"
        df_b2["ご依頼主郵便番号"] = "150-0043"
        df_b2["ご依頼主住所"] = "東京都渋谷区道玄坂２－６－１４"
        df_b2["ご依頼主アパートマンション"] = "野村不動産道玄坂ビル２階"
        df_b2["ご依頼主名"] = "株式会社バリューメディカル"

        st.subheader("変換データプレビュー")
        st.dataframe(df_b2[["出荷予定日", "お届け先名", "お届け先郵便番号", "お届け先住所", "お届け先アパートマンション名", "品名１"]].head())

        # CSVダウンロードボタン
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