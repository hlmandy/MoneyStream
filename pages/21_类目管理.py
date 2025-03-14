import streamlit as st
import pandas as pd
from datetime import datetime
from util import *


transaction_types = ['支出', '收入']

st.header('类别管理页面')

# 读取数据
transactions_df, categories_df, subcategories_df, accounts_df = load_data()

# 初始化会话状态
if 'previous_categories_df' not in st.session_state:
    st.session_state.previous_categories_df = None
if 'previous_subcategories_df' not in st.session_state:
    st.session_state.previous_subcategories_df = None
if 'show_undo_delete' not in st.session_state:
    st.session_state.show_undo_delete = False

# 查询类别和子类别
col1, col2 = st.columns(2)

with col1:
    # 定义样式函数
    def highlight_type(val):
        if val == '支出':
            return 'background-color: #f0f2f6'
        elif val == '收入':
            return 'background-color: lightblue'
        return ''
    
    # 应用样式
    styled_categories = categories_df.style.apply(lambda x: [''] * len(x) if x.name != 'TransactionType' else [highlight_type(val) for val in x])
    edited_categories = st.data_editor(styled_categories, hide_index=True)

with col2:
    st.subheader('子类别查询')
    selected_category = st.selectbox('选择类别', categories_df['CategoryName'].tolist())
    if selected_category:
        subcategories = subcategories_df[subcategories_df['ParentCategoryName'].isin(
            categories_df[categories_df['CategoryName'] == selected_category]['CategoryName']
        )]
        display_subcategories = subcategories[['SubcategoryName', 'Description']]
        st.dataframe(display_subcategories, hide_index=True)


# 新增类别和子类别
col1, col2 = st.columns(2)

with col1:
    st.subheader('新增类别')
    with st.form('add_category_form'):
        new_category_name = st.text_input('类别名称')
        new_category_type = st.selectbox('类别类型', transaction_types)
        new_category_desc = st.text_input('类别描述')
        submit_category = st.form_submit_button('添加类别')
        
        if submit_category:
            if new_category_name in categories_df['CategoryName'].values:
                st.error('该类别名称已存在！')
            elif not new_category_name:
                st.error('类别名称不能为空！')
            else:
                new_category_id = categories_df['CategoryID'].max() + 1
                new_category = pd.DataFrame({
                    'CategoryID': [new_category_id],
                    'CategoryName': [new_category_name],
                    'Description': [new_category_desc],
                    'TransactionType': [new_category_type]
                })
                categories_df = pd.concat([categories_df, new_category], ignore_index=True)
                save_data(categories_df, 'Categories.csv')
                st.success('类别添加成功！')
                st.rerun()

with col2:
    st.subheader('新增子类别')
    with st.form('add_subcategory_form'):
        parent_category = st.selectbox('所属类别', categories_df['CategoryName'].tolist())
        new_subcategory_name = st.text_input('子类别名称')
        new_subcategory_desc = st.text_input('子类别描述')
        submit_subcategory = st.form_submit_button('添加子类别')
        
        if submit_subcategory:
            if not new_subcategory_name:
                st.error('子类别名称不能为空！')
            else:
                existing_subcategories = subcategories_df[subcategories_df['ParentCategoryName'] == parent_category]['SubcategoryName'].values
                if new_subcategory_name in existing_subcategories:
                    st.error('该子类别名称在所选类别下已存在！')
                else:
                    new_subcategory_id = subcategories_df['SubcategoryID'].max() + 1
                    new_subcategory = pd.DataFrame({
                        'SubcategoryID': [new_subcategory_id],
                        'SubcategoryName': [new_subcategory_name],
                        'ParentCategoryName': [parent_category],
                        'Description': [new_subcategory_desc]
                    })
                    subcategories_df = pd.concat([subcategories_df, new_subcategory], ignore_index=True)
                    save_data(subcategories_df, 'Subcategories.csv')
                    st.success('子类别添加成功！')
                    st.rerun()


# 删除子类别
st.subheader('删除子类别')
col1, col2 = st.columns(2)

with col1:
    delete_parent = st.selectbox('选择父类别', categories_df['CategoryName'].tolist(), key='delete_parent')
    if delete_parent:
        sub_categories = subcategories_df[subcategories_df['ParentCategoryName'] == delete_parent]['SubcategoryName'].tolist()

with col2:
    if sub_categories:
        delete_subcategory = st.selectbox('选择子类别', sub_categories)
    else:
        st.info('该类别下没有子类别')

if st.button('删除子类别'):
    # 检查是否存在使用该子类别的交易记录
    transactions_df = load_transactions_data()
    has_transactions = len(transactions_df[
        (transactions_df['CategoryName'] == delete_parent) & 
        (transactions_df['SubcategoryName'] == delete_subcategory)
    ]) > 0
    
    if has_transactions:
        st.error(f'无法删除子类别 {delete_subcategory}，因为存在使用该子类别的交易记录！')
    else:
        # 保存当前状态用于撤销
        st.session_state.previous_subcategories_df = subcategories_df.copy()
        st.session_state.show_undo_delete = True
        
        # 删除选中的子类别
        subcategories_df = subcategories_df[~((subcategories_df['ParentCategoryName'] == delete_parent) & 
                                                (subcategories_df['SubcategoryName'] == delete_subcategory))]
        
        # 保存更改
        save_data(subcategories_df, 'Subcategories.csv')

        st.success(f'已删除子类别 {delete_subcategory}！')
        st.rerun()

# 撤销删除操作
if st.session_state.show_undo_delete:
    if st.button('撤销删除操作'):
        if st.session_state.previous_subcategories_df is not None:
            subcategories_df = st.session_state.previous_subcategories_df.copy()
            save_data(subcategories_df, 'Subcategories.csv')

        st.session_state.previous_subcategories_df = None
        st.session_state.show_undo_delete = False
        st.success('已撤销上一次删除操作！')
        st.rerun()

# 子类别调整
st.subheader('子类别调整')
col1, col2 = st.columns(2)

with col1:
    adjust_parent = st.selectbox('选择父类别', categories_df['CategoryName'].tolist(), key='adjust_parent')
    if adjust_parent:
        adjust_sub_categories = subcategories_df[subcategories_df['ParentCategoryName'] == adjust_parent]['SubcategoryName'].tolist()
        if adjust_sub_categories:
            old_subcategory = st.selectbox('选择原子类别', adjust_sub_categories, key='old_subcategory')
        else:
            st.info('该类别下没有子类别')

with col2:
    target_parent = st.selectbox('选择目标父类别', categories_df['CategoryName'].tolist(), key='target_parent')
    if target_parent:
        target_sub_categories = subcategories_df[subcategories_df['ParentCategoryName'] == target_parent]['SubcategoryName'].tolist()
        if target_sub_categories:
            new_subcategory = st.selectbox('选择目标子类别', target_sub_categories, key='new_subcategory')
        else:
            st.info('该类别下没有子类别')

if st.button('执行子类别调整'):
    if 'old_subcategory' not in locals() or 'new_subcategory' not in locals():
        st.error('请选择原子类别和目标子类别！')
    elif old_subcategory == new_subcategory and adjust_parent == target_parent:
        st.error('原子类别和目标子类别不能相同！')
    else:
        # 保存当前状态用于撤销
        transactions_df = load_transactions_data()
        st.session_state.previous_subcategories_df = subcategories_df.copy()
        st.session_state.show_undo_delete = True
        
        # 更新交易记录中的子类别
        transactions_df.loc[
            (transactions_df['CategoryName'] == adjust_parent) & 
            (transactions_df['SubcategoryName'] == old_subcategory),
            ['CategoryName', 'SubcategoryName']
        ] = [target_parent, new_subcategory]
        
        # 删除原子类别
        subcategories_df = subcategories_df[~(
            (subcategories_df['ParentCategoryName'] == adjust_parent) & 
            (subcategories_df['SubcategoryName'] == old_subcategory)
        )]
        
        # 保存更改
        save_data(transactions_df, 'Transactions.csv')
        save_data(subcategories_df, 'Subcategories.csv')

        st.success(f'已将子类别 {old_subcategory} 调整为 {new_subcategory}！')
        st.rerun()