import streamlit as st
import zipfile
import json
import os
import re
import io

# --- 1. 基本関数（ロジックは元のコードを継承） ---
def get_lists_from_sb3(uploaded_file):
    lists_info = {}
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        with zip_ref.open('project.json') as f:
            project_data = json.load(f)
        for target in project_data['targets']:
            if 'lists' in target:
                for lid, ldata in target['lists'].items():
                    # ldata[0] はリスト名, ldata[1] は中身の配列
                    lists_info[ldata[0]] = ldata[1]
    return lists_info, project_data

def create_updated_sb3(uploaded_file, project_data, target_list_name, new_list):
    # project.jsonの書き換え
    for target in project_data['targets']:
        if 'lists' in target:
            for lid, ldata in target['lists'].items():
                if ldata[0] == target_list_name:
                    ldata[1] = new_list

    # 新しいsb3ファイルをメモリ上で作成
    output_buffer = io.BytesIO()
    with zipfile.ZipFile(uploaded_file, 'r') as bin_in:
        with zipfile.ZipFile(output_buffer, 'w') as bin_out:
            for item in bin_in.infolist():
                if item.filename == 'project.json':
                    bin_out.writestr('project.json', json.dumps(project_data, ensure_ascii=False))
                else:
                    bin_out.writestr(item.filename, bin_in.read(item.filename))
    return output_buffer.getvalue()

# --- 2. Streamlit UI の構築 ---
st.set_page_config(page_title="Scratch List Updater", layout="centered")
st.title("Scratch リスト更新ツール 🚀")

# ステップ1: ファイルアップロード
uploaded_file = st.file_uploader("SB3ファイルをアップロードしてください", type="sb3")

if uploaded_file:
    # リスト情報を取得
    lists_info, project_data = get_lists_from_sb3(uploaded_file)
    
    st.divider()
    st.subheader("1. 編集するリストを選択")
    list_names = list(lists_info.keys())
    selected_list = st.selectbox("書き換えたいリストを選んでください", list_names)

    if selected_list:
        current_data = lists_info[selected_list]
        st.write(f"現在の項目数: **{len(current_data)}** 件")
        
        # ステップ2: 内容の編集
        st.subheader("2. 新しい内容を入力")
        # デフォルト値として現在のリストを表示
        input_text = st.text_area(
            "1行に1項目ずつ入力してください（カンマ・タブ区切りも対応）",
            value="\n".join(map(str, current_data)),
            height=200
        )

        # ステップ3: 保存設定
        st.subheader("3. 書き出し設定")
        base_name = os.path.splitext(uploaded_file.name)[0]
        output_name = st.text_input("保存するファイル名", value=f"{base_name}_updated.sb3")

        # 実行ボタン
        if st.button("変換を実行する"):
            # 入力テキストのパース（元の正規表現ロジックを流用）
            new_list = [item.strip() for item in re.split('[\n,\t;]', input_text) if item.strip()]
            
            # 更新されたバイナリを作成
            updated_sb3_bin = create_updated_sb3(uploaded_file, project_data, selected_list, new_list)
            
            st.success(f"「{selected_list}」を {len(new_list)} 件に更新しました！")
            
            # ダウンロードボタンを表示
            st.download_button(
                label="更新済みSB3をダウンロード",
                data=updated_sb3_bin,
                file_name=output_name,
                mime="application/octet-stream"
            )
