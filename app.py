import streamlit as st
import zipfile
import json
import os
import re
import io

st.set_page_config(layout='wide', page_title='Scratch SB3 List Editor')

st.title('Scratch SB3ファイル リストエディター')
st.write('SB3ファイル内のリストの内容を表示・編集し、更新されたSB3ファイルをダウンロードできます。')

# --- 1. ファイルアップロード --- 
st.header('1. SB3ファイルをアップロード')
uploaded_file = st.file_uploader("SB3ファイルをここにドラッグ＆ドロップまたはクリックしてアップロード", type=['sb3'])

# --- 関数定義 --- 
def get_lists_from_sb3(sb3_file_object):
    lists_info = {}
    try:
        # ensure file pointer is at the beginning
        sb3_file_object.seek(0)
        with zipfile.ZipFile(sb3_file_object, 'r') as zip_ref:
            with zip_ref.open('project.json') as f:
                project_data = json.load(f)
            for target in project_data.get('targets', []):
                if 'lists' in target:
                    for lid, ldata in target['lists'].items():
                        # ldata[0] is the list name, ldata[1] is the list content
                        lists_info[ldata[0]] = ldata[1]
    except Exception as e:
        st.error(f"SB3ファイルの読み込み中にエラーが発生しました: {e}")
    return lists_info

def save_updated_sb3(original_sb3_file_object, list_name, new_data, output_filename):
    try:
        original_sb3_file_object.seek(0)
        input_zip_buffer = io.BytesIO(original_sb3_file_object.read())
        output_zip_buffer = io.BytesIO()

        project_data = {}
        with zipfile.ZipFile(input_zip_buffer, 'r') as zip_ref:
            with zip_ref.open('project.json') as f:
                project_data = json.load(f)
            
            # Update the specific list
            found = False
            for target in project_data.get('targets', []):
                if 'lists' in target:
                    for lid, linfo in target['lists'].items():
                        if linfo[0] == list_name:
                            linfo[1] = new_data
                            found = True
                            break
                if found: break

            # Write updated project.json and other files to the new zip
            with zipfile.ZipFile(output_zip_buffer, 'w') as new_zip:
                new_zip.writestr('project.json', json.dumps(project_data, ensure_ascii=False))
                for item in zip_ref.infolist():
                    if item.filename != 'project.json':
                        new_zip.writestr(item, zip_ref.read(item.filename))
        
        output_zip_buffer.seek(0)
        return output_zip_buffer.getvalue()

    except Exception as e:
        st.error(f"SB3ファイルの保存中にエラーが発生しました: {e}")
        return None


if uploaded_file is not None:
    # Determine initial output name
    base_name = os.path.splitext(uploaded_file.name)[0]
    # Clean up names like 'file (1)'
    base_name = re.sub(r'\\s\\(\\d+\\)$', '', base_name)
    initial_output_name = f"{base_name}_updated.sb3"

    lists = get_lists_from_sb3(uploaded_file)

    if lists:
        st.header('2. リストを編集・保存')
        
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader('リスト選択')
            list_names = list(lists.keys())
            selected_list_name = st.selectbox("編集するリストを選択してください", list_names)
            
            current_data = lists.get(selected_list_name, [])
            st.write(f"**現在の内容 ({len(current_data)}件):**")
            formatted_content = "<br>".join([f"{i+1}: {item}" for i, item in enumerate(current_data)])
            st.markdown(f"<div style='border:1px solid #ccc; padding:5px; max-height:200px; overflow-y:auto;'>{formatted_content}</div>", unsafe_allow_html=True)
            
            st.subheader('保存ファイル名')
            output_filename = st.text_input('保存するSB3ファイルの名前:', value=initial_output_name)

        with col2:
            st.subheader('新しいデータを入力')
            st.info('各項目は改行、カンマ、またはスペースで区切って入力してください。')
            new_list_raw_text = st.text_area(
                "新しいリストのデータ",
                value="\\n".join(map(str, current_data)),
                height=300
            )
            
            if st.button('リストを更新してSB3ファイルを生成'):
                st.spinner('ファイルを処理中...')
                new_list_items = [item.strip() for item in re.split('[\\n,\\t;]', new_list_raw_text) if item.strip()]
                
                updated_sb3_bytes = save_updated_sb3(
                    uploaded_file,
                    selected_list_name,
                    new_list_items,
                    output_filename
                )
                
                if updated_sb3_bytes:
                    st.success(f'リストが更新され、新しいSB3ファイルが生成されました。')
                    st.download_button(
                        label=f"ダウンロード: {output_filename}",
                        data=updated_sb3_bytes,
                        file_name=output_filename,
                        mime='application/octet-stream'
                    )
                else:
                    st.error('ファイルの生成に失敗しました。')

    else:
        st.warning("アップロードされたSB3ファイルにはリストが含まれていませんでした。")
else:
    st.info("SB3ファイルをアップロードしてください。")
#"""

"""with open('app.py', 'w') as f:
    f.write(app_py_code)

print("app.py が作成されました。")
"""
