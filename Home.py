import streamlit as st
import pandas as pd
from datetime import datetime
from util import *

# 初始化会话状态
if 'previous_transactions_df' not in st.session_state:
    st.session_state.previous_transactions_df = None
if 'show_undo' not in st.session_state:
    st.session_state.show_undo = False

# 读取数据
transactions_df, categories_df, subcategories_df, accounts_df = load_data()

st.header('新增交易')
col1, col2, _, _, _ = st.columns(5)
# 使用两列布局显示复选框
col1, col2 = st.columns(2)
with col1:
    is_income = st.checkbox('是否为收入', value=False)
with col2:
    is_backdated = st.checkbox('是否为补记', value=False)

# 使用三列布局
col1, col2, col3 = st.columns(3)
with col1:
    date = st.date_input('日期')
    # 根据是否为收入筛选类别
    filtered_categories = categories_df[categories_df['TransactionType'] == ('收入' if is_income else '支出')]
    category = st.selectbox('类别', filtered_categories['CategoryName'])
    # 根据选择的类别筛选子类别
    subcategories = pd.read_csv('c:\\Users\\mandy\\hl_Documents\\MoneyStream\\Data\\Subcategories.csv')
    filtered_subcategories = subcategories[subcategories['ParentCategoryName'] == category]['SubcategoryName'].tolist()
    subcategory = st.selectbox('子类别', filtered_subcategories)

with col2:
    account = st.selectbox('账户', accounts_df['AccountName'])
    # 获取所有已有的商户列表
    existing_merchants = transactions_df['Merchant'].dropna().unique().tolist()
    merchant = st.selectbox('商户', [''] + existing_merchants, key='merchant')
    if merchant == '':
        merchant = st.text_input('新商户', placeholder='请输入新商户名称')

with col3:
    item = st.text_input('商品item', placeholder='请输入商品名称')
    amount = st.number_input('金额', min_value=0.0)
    remarks = st.text_input('备注', placeholder='请输入交易备注（可选）')

if st.button('添加交易'):
    # 获取CategoryID和AccountID
    category_id = categories_df[categories_df['CategoryName'] == category]['CategoryID'].iloc[0]
    account_id = accounts_df[accounts_df['AccountName'] == account]['AccountID'].iloc[0]
    
    # 生成新的交易记录
    new_transaction = pd.DataFrame({
        'TransactionID': [0 if transactions_df.shape[0]==0 else max(transactions_df['TransactionID']) + 1],
        'Date': [date.strftime('%Y-%m-%d %H:%M:%S')],
        'TransactionType': ['收入' if is_income else '支出'],
        'CategoryName': [category],
        'SubcategoryName': [subcategory],
        'Amount': [amount],
        'AccountName': [account],
        'Remarks': [remarks],
        'Merchant': [merchant],
        'Item': [item],
        'UpdatedDate': [datetime.now().strftime('%Y-%m-%d')],
        'IsRefund': ['否'],
        'RelatedTransactionID':[None]
    })
    
    # 保存当前状态用于撤销
    st.session_state.previous_transactions_df = transactions_df.copy()
    st.session_state.show_undo = True
    
    # 仅在非补记的情况下更新账户余额
    if not is_backdated:
        balance_change = amount if is_income else -amount
        accounts_df.loc[accounts_df['AccountName'] == account, 'Balance'] = \
            (accounts_df.loc[accounts_df['AccountName'] == account, 'Balance'] + balance_change).round(2)
        accounts_df.loc[accounts_df['AccountName'] == account, 'LastModifiedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        accounts_df.to_csv('c:\\Users\\mandy\\hl_Documents\\MoneyStream\\Data\\Account.csv', index=False)
    
    # 添加新交易记录
    transactions_df = pd.concat([new_transaction, transactions_df], ignore_index=True)
    transactions_df.to_csv('c:\\Users\\mandy\\hl_Documents\\MoneyStream\\Data\\Transactions.csv', index=False)
    st.success('交易已添加！')
    # st.experimental_rerun()

# 显示撤销按钮
if st.session_state.show_undo:
    if st.button('撤销上一次添加'):
        transactions_df = st.session_state.previous_transactions_df.copy()
        transactions_df.to_csv('c:\\Users\\mandy\\hl_Documents\\MoneyStream\\Data\\Transactions.csv', index=False)
        st.session_state.previous_transactions_df = None
        st.session_state.show_undo = False
        st.success('已撤销上一次添加操作！')
        # st.experimental_rerun()

st.header('新增转账')
is_transfer_backdated = st.checkbox('是否为补记', value=False, key='is_transfer_backdated')
# 使用三列布局
col1, col2, col3 = st.columns(3)
with col1:
    transfer_date = st.date_input('转账日期', key='transfer_date')
    from_account = st.selectbox('转出账户', accounts_df['AccountName'], key='from_account')

with col2:
    transfer_amount = st.number_input('转账金额', min_value=0.0, key='transfer_amount')
    to_account = st.selectbox('转入账户', accounts_df['AccountName'], key='to_account')

with col3:
    
    transfer_remarks = st.text_input('转账备注', placeholder='请输入转账备注（可选）')

if st.button('确认转账'):
    if from_account == to_account:
        st.error('转出账户和转入账户不能相同！')
    elif transfer_amount <= 0:
        st.error('转账金额必须大于0！')
    else:
        # 保存当前状态用于撤销
        st.session_state.previous_transactions_df = transactions_df.copy()
        st.session_state.show_undo = True

        # 生成转出和转入两笔交易记录
        transfer_out = pd.DataFrame({
            'TransactionID': [transactions_df['TransactionID'].max() + 1],
            'Date': [transfer_date.strftime('%Y-%m-%d %H:%M:%S')],
            'TransactionType': ['支出'],
            'CategoryName': ['转账'],
            'SubcategoryName': ['转账'],
            'Amount': [transfer_amount],
            'AccountName': [from_account],
            'Merchant': ['系统转账'],
            'Remarks': [f'转账至{to_account}'+transfer_remarks],
            'Item' : ['转账'],
            'UpdatedDate': [datetime.now().strftime('%Y-%m-%d')],
            'IsRefund': ['否'],
            'RelatedTransactionID':[int(transactions_df['TransactionID'].max() + 2)]

        })
        
        transfer_in = pd.DataFrame({
            'TransactionID': [transactions_df['TransactionID'].max() + 2],
            'Date': [transfer_date.strftime('%Y-%m-%d %H:%M:%S')],
            'TransactionType': ['收入'],
            'CategoryName': ['转账'],
            'SubcategoryName': ['转账'],
            'Amount': [transfer_amount],
            'AccountName': [to_account],
            'UpdatedDate': [datetime.now().strftime('%Y-%m-%d')],
            'Merchant': ['系统转账'],
            'Remarks': [f'来自{from_account}的转账'+transfer_remarks],
            'Item' : ['转账'],
            'UpdatedDate': [datetime.now().strftime('%Y-%m-%d')],
            'IsRefund': ['否'],
            'RelatedTransactionID':[int(transactions_df['TransactionID'].max() + 1)]
        })
        
        # 仅在非补记的情况下更新账户余额
        if not is_transfer_backdated:
            accounts_df.loc[accounts_df['AccountName'] == from_account, 'Balance'] -= transfer_amount
            accounts_df.loc[accounts_df['AccountName'] == to_account, 'Balance'] += transfer_amount
            accounts_df.loc[accounts_df['AccountName'] == from_account, 'LastModifiedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            accounts_df.loc[accounts_df['AccountName'] == to_account, 'LastModifiedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            accounts_df.to_csv('c:\\Users\\mandy\\hl_Documents\\MoneyStream\\Data\\Account.csv', index=False)
        
        # 添加转出和转入两笔交易记录
        transactions_df = pd.concat([transactions_df, transfer_out, transfer_in], ignore_index=True)
        transactions_df.to_csv('c:\\Users\\mandy\\hl_Documents\\MoneyStream\\Data\\Transactions.csv', index=False)
        st.success('转账成功！')
        # st.experimental_rerun()

