import streamlit as st
import pandas as pd
from datetime import datetime
from util import *

account_types = ['借记卡', '信用卡','电子钱包', '理财']

# 读取数据
transactions_df, categories_df, subcategories_df, accounts_df = load_data()

st.set_page_config(layout="wide")

st.header('账户管理页面')

# 初始化会话状态
if 'previous_accounts_df' not in st.session_state:
    st.session_state.previous_accounts_df = None
if 'show_undo_add' not in st.session_state:
    st.session_state.show_undo_add = False
if 'show_undo_delete' not in st.session_state:
    st.session_state.show_undo_delete = False
if 'show_undo_edit' not in st.session_state:
    st.session_state.show_undo_edit = False

# 显示按类型分组的账户余额
# st.subheader('按类型显示账户余额')
show_balance = st.checkbox('显示余额', value=False)

if show_balance:
    # 按账户类型分组并计算总余额
    type_balance = accounts_df.groupby('AccountType').agg({
        'Balance': ['sum', 'count']
    }).round(2)
    type_balance.columns = ['总余额', '账户数']
    type_balance = type_balance.reset_index()

    # 创建一个多列布局来显示每种类型的账户
    cols = st.columns(len(account_types))
    for i, acc_type in enumerate(account_types):
        with cols[i]:
            st.markdown(f'### {acc_type}')
            type_data = type_balance[type_balance['AccountType'] == acc_type]
            if not type_data.empty:
                total = type_data['总余额'].iloc[0]
                count = type_data['账户数'].iloc[0]
                st.metric(
                    label=f'账户数: {int(count)}',
                    value=f'¥{total:,.2f}',
                    delta=None
                )
                
                # 显示该类型的所有账户详情
                type_accounts = accounts_df[accounts_df['AccountType'] == acc_type]
                for _, acc in type_accounts.iterrows():
                    if abs(acc['Balance']) > 100:
                        st.markdown(f"**{acc['AccountName']}**")
                        st.markdown(f"¥{acc['Balance']:,.2f}")
            else:
                st.metric(
                    label='账户数: 0',
                    value='¥0.00',
                    delta=None
                )

# 查询账户
st.subheader('查询账户')


# 根据复选框状态决定显示的列
display_columns = ['AccountName', 'AccountType','AccountSuffix', 'Description', 'IsLocked']
if show_balance:
    display_columns.append('Balance')

# 应用样式并显示数据框
def highlight_locked(val):
    color = 'background-color: lightblue' if val == '是' else ''
    return color

def highlight_balance(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return 'background-color: lightblue'
        elif val < 0:
            return 'background-color: #FFB6C6'
    return ''

accounts_df.sort_values(['IsLocked', 'Balance'], ascending=[True, False], inplace=True)
styled_df = accounts_df[display_columns].style.map(highlight_locked, subset=['IsLocked'])
# 格式化余额为两位小数并添加千位分隔符
if 'Balance' in display_columns:
    accounts_df['Balance'] = accounts_df['Balance'].round(2)
    styled_df = styled_df.map(highlight_balance, subset=['Balance'])\
        .format({'Balance': lambda x: f'{x:,.2f}'})
st.dataframe(styled_df,hide_index=True, use_container_width=True)

# 新增账户
st.subheader('新增账户')
with st.form('add_account_form'):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        add_name = st.text_input('账户名称')
        add_balance = st.number_input('初始余额', value=0.0, step=0.01)
    
    with col2:
        add_type = st.selectbox('账户类型', account_types)
        add_suffix = st.text_input('账户后缀（可选）')
    
    with col3:
        add_description = st.text_input('账户描述')
        add_is_locked = '是' if st.checkbox('是否锁定', value=False) else '否'

    
    add_submit = st.form_submit_button('添加账户')
    
    if add_submit:
        if add_name in accounts_df['AccountName'].values:
            st.error('该账户名称已存在！')
        elif not add_name:
            st.error('账户名称不能为空！')
        else:
            # 保存当前状态
            st.session_state.previous_accounts_df = accounts_df.copy()
            st.session_state.show_undo_add = True
            st.session_state.show_undo_delete = False
            st.session_state.show_undo_edit = False
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_account = pd.DataFrame({
                'AccountID': [max(accounts_df['AccountID']) + 1],
                'AccountName': [add_name],
                'AccountType': [add_type],
                'Description': [add_description],
                'AccountSuffix': [add_suffix if add_suffix else None],
                'IsLocked': [add_is_locked],
                'Balance': [add_balance],
                'IsValid': ['是'],
                'LastModifiedTime': [current_time]
            })
            accounts_df = pd.concat([accounts_df, new_account], ignore_index=True)
            accounts_df.to_csv(account_dir, index=False)
            st.success('账户添加成功！')
            st.rerun()

if st.session_state.show_undo_add:
    if st.button('撤销新增操作'):
        accounts_df = st.session_state.previous_accounts_df.copy()
        accounts_df.to_csv(account_dir, index=False)
        st.session_state.previous_accounts_df = None
        st.session_state.show_undo_add = False
        st.session_state.show_undo_delete = False
        st.session_state.show_undo_edit = False
        st.success('已撤销上一次操作！')
        st.rerun()

# 修改账户
st.subheader('修改账户')
edit_account = st.selectbox('选择要修改的账户', accounts_df['AccountName'].tolist())

if edit_account:
    account_data = accounts_df[accounts_df['AccountName'] == edit_account].iloc[0]
    
    with st.form('edit_account_form'):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_name = st.text_input('账户名称', value=account_data['AccountName'])
            new_type = st.selectbox('账户类型', account_types, index=account_types.index(account_data['AccountType']))
        
        with col2:
            new_description = st.text_input('账户描述', value=account_data['Description'])
            new_suffix = st.text_input('账户后缀', value=str(account_data['AccountSuffix']) if pd.notna(account_data['AccountSuffix']) else '')
        
        with col3:
            new_balance = st.number_input('余额', value=float(account_data['Balance']), step=1.0)
            new_is_locked = '是' if st.checkbox('是否锁定', value=account_data['IsLocked']=='是') else '否'
        
        submit_button = st.form_submit_button('保存修改')
        
        if submit_button:
            if new_name and new_name != edit_account and new_name in accounts_df['AccountName'].values:
                st.error('该账户名称已存在！')
            else:
                # 保存当前状态
                st.session_state.previous_accounts_df = accounts_df.copy()
                st.session_state.show_undo_edit = True
                st.session_state.show_undo_add = False
                st.session_state.show_undo_delete = False
                
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 使用一次性更新所有字段
                update_data = {
                    'AccountName': new_name,
                    'AccountType': new_type,
                    'Description': new_description,
                    'AccountSuffix': new_suffix if new_suffix else None,
                    'IsLocked': new_is_locked,
                    'Balance': new_balance,
                    'IsValid': '是',
                    'LastModifiedTime': current_time
                }
                accounts_df.loc[accounts_df['AccountName'] == edit_account, update_data.keys()] = update_data.values()
                
                # 更新交易记录中的账户名称
                if new_name != edit_account:
                    transactions_df = pd.read_csv(transaction_dir)
                    transactions_df.loc[transactions_df['AccountName'] == edit_account, 'AccountName'] = new_name
                    transactions_df.to_csv(transaction_dir, index=False)

                accounts_df.to_csv(account_dir, index=False)
                st.success('账户信息已更新！')
                st.rerun()

if st.session_state.show_undo_edit:
    if st.button('撤销修改操作'):
        accounts_df = st.session_state.previous_accounts_df.copy()
        accounts_df.to_csv(account_dir, index=False)
        st.session_state.previous_accounts_df = None
        st.session_state.show_undo_add = False
        st.session_state.show_undo_delete = False
        st.session_state.show_undo_edit = False
        st.success('已撤销上一次操作！')
        st.rerun()

# 删除账户
st.subheader('删除账户')
delete_account = st.selectbox('要删除的账户名称', accounts_df['AccountName'].tolist())
if st.button('删除账户'):
    if delete_account in accounts_df['AccountName'].values:
        # 保存当前状态
        st.session_state.previous_accounts_df = accounts_df.copy()
        st.session_state.show_undo_delete = True
        st.session_state.show_undo_add = False
        st.session_state.show_undo_edit = False
        
        # 将账户标记为无效，而不是直接删除
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        accounts_df.loc[accounts_df['AccountName'] == delete_account, 'IsValid'] = '否'
        accounts_df.loc[accounts_df['AccountName'] == delete_account, 'LastModifiedTime'] = current_time
        accounts_df.to_csv(account_dir, index=False)
        st.success(f'账户 {delete_account} 已标记为无效！')
        st.rerun()
    else:
        st.error('未找到该账户！')

if st.session_state.show_undo_delete:
    if st.button('撤销删除操作'):
        accounts_df = st.session_state.previous_accounts_df.copy()
        accounts_df.to_csv(account_dir, index=False)
        st.session_state.previous_accounts_df = None
        st.session_state.show_undo_add = False
        st.session_state.show_undo_delete = False
        st.session_state.show_undo_edit = False
        st.success('已撤销上一次操作！')
        st.rerun()
