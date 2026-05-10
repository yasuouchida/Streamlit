import streamlit as st
import zipfile
import json
import os
import re
import io

# --- 1. 基本関数 ---
def get_lists_from_sb3(uploaded_file):
    lists_info = {}
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            with zip_ref.open('project.json') as f:
                project_data = json.load(f)
            for target in project_data['targets']:
                if 'lists' in target:
                    for lid, ldata in target['lists'].items():
                        lists_info[ldata[0]] = ldata[1]
        return lists_info, project_data
    except Exception as e:
        st.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return {}, None

def create_updated_sb3(uploaded_file, project_data, target_list_name, new_list):
    for target in project_data['targets']:
        if 'lists' in target:
            for lid, ldata in target['lists'].items():
                if ldata[0] == target_list_name:
                    ldata[1] = new_list

    output_buffer = io.BytesIO()
    with zipfile.ZipFile(uploaded_file, 'r') as bin_in:
        with zipfile.ZipFile(output_buffer, 'w') as bin_out:
            for item in bin_in.infolist():
                if item.filename == 'project.json':
                    # ensure_ascii=False で日本語を維持
                    json_str = json.dumps(project_data, ensure_ascii=False, indent=0)
                    bin_out.writestr('project.json', json_str.encode('utf-8'))
                else:
                    bin_out.writestr(item.filename, bin_in.read(item.filename))
    return output_buffer.getvalue()

# --- 2. Streamlit UI ---
st.set_page_config(page_title="Scratch List Manager", layout="centered")
st.title("Scratch リスト更新ツール 🛠️")

uploaded_file = st.file_uploader("SB3ファイルをアップロード", type="sb3")

if uploaded_file:
    lists_info, project_data = get_lists_from_sb3(uploaded_file)
    
    if lists_info:
        st.divider()
        list_names = list(lists_info.keys())
        selected_list = st.selectbox("編集するリストを選択してください", list_names)

        if selected_list:
            current_data = lists_info[selected_list]
            
            # --- 追加：現在の内容を表示するセクション ---
            st.subheader("📋 1. 現在のリスト内容（古い内容）")
            st.info(f"リスト名: **{selected_list}** （全 {len(current_data)} 件）")
            
            # 読み取り専用のテキストエリアとして表示（コピーも可能）
            st.text_area(
                "現在のデータ（確認用）",
                value="\n".join(map(str, current_data)),
                height=150,
                disabled=True,
                help="ここを書き換えることはできません。下の「編集エリア」を使ってください。"
            )

            st.divider()

            # --- 編集セクション ---
            st.subheader("✏️ 2. 新しい内容を入力")
            input_text = st.text_area(
                "編集後のリスト（1行に1項目ずつ入力）",
                value="\n".join(map(str, current_data)), # 初期値として現在のデータを入力済み
                height=300
            )

            base_name = os.path.splitext(uploaded_file.name)[0]
            output_name = st.text_input("保存するファイル名", value=f"{base_name}_updated.sb3")

            if st.button("変換を実行して保存"):
                # 分割ロジック（日本語対応）
                new_list = [item.strip() for item in re.split('[\n\t]', input_text) if item.strip()]
                
                updated_sb3_bin = create_updated_sb3(uploaded_file, project_data, selected_list, new_list)
                
                st.success(f"「{selected_list}」を {len(new_list)} 件に更新しました！🎉")
                st.download_button(
                    label="更新済みSB3をダウンロード",
                    data=updated_sb3_bin,
                    file_name=output_name,
                    mime="application/octet-stream"
                )
