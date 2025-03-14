import streamlit as st
import pandas as pd
from datetime import datetime

from util import *

st.header('账目明细')

# 读取数据
transactions_df, _, subcategories_df, _ = load_data()
transactions_df.sort_values('Date', ascending=False, inplace=True)

# 筛选条件

# 日期范围筛选
start_date = st.sidebar.date_input('开始日期', pd.to_datetime(transactions_df['Date']).min())
end_date = st.sidebar.date_input('结束日期', pd.to_datetime(transactions_df['Date']).max())

# 交易类型筛选
transaction_types = ['全部'] + list(transactions_df['TransactionType'].unique())
selected_type = st.sidebar.selectbox('交易类型', transaction_types)

# 账户筛选
accounts = list(transactions_df['AccountName'].unique())
selected_account = st.sidebar.selectbox('账户', ['全部'] + accounts)

# 类别筛选
categories = list(transactions_df['CategoryName'].unique())
selected_category = st.sidebar.selectbox('类别', ['全部'] + categories)

# 子类别筛选
if selected_category != '全部':
    subcategories = list(
        subcategories_df[subcategories_df['ParentCategoryName'] == selected_category]['SubcategoryName'].unique())
    selected_subcategory = st.sidebar.selectbox('子类别', ['全部'] + subcategories)
else:
    subcategories = list(subcategories_df['SubcategoryName'].unique())
    selected_subcategory = '全部'

# 是否为报销项
reimbursable_options = ['全部', '是', '否']
selected_reimbursable = st.sidebar.selectbox('是否已报销', reimbursable_options)

# 应用筛选条件
filtered_df = transactions_df.copy()

# 日期筛选
filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
filtered_df = filtered_df[
    (filtered_df['Date'].dt.date >= start_date) &
    (filtered_df['Date'].dt.date <= end_date)
    ]

# 交易类型筛选
if selected_type != '全部':
    filtered_df = filtered_df[filtered_df['TransactionType'] == selected_type]

# 账户筛选
if selected_account != '全部':
    filtered_df = filtered_df[filtered_df['AccountName'] == selected_account]

# 类别筛选
if selected_category != '全部':
    filtered_df = filtered_df[filtered_df['CategoryName'] == selected_category]

# 子类别筛选
if selected_subcategory != '全部':
    filtered_df = filtered_df[filtered_df['SubcategoryName'] == selected_subcategory] \
 \
# 报销项筛选
if selected_reimbursable != '全部':
    filtered_df = filtered_df[filtered_df['IsRefund'] == selected_reimbursable]

# 显示筛选后的数据
if not filtered_df.empty:
    # 计算总金额
    total_income = filtered_df[filtered_df['TransactionType'] == '收入']['Amount'].sum()
    total_expense = filtered_df[filtered_df['TransactionType'] == '支出']['Amount'].sum()
    net_amount = total_income - total_expense

    # 显示统计信息
    st.markdown('---')
    col1, col2, col3 = st.columns(3)
    col1.metric('总收入', f'¥{total_income:,.2f}')
    col2.metric('总支出', f'¥{total_expense:,.2f}')
    col3.metric('净收入', f'¥{net_amount:,.2f}')
    st.markdown('---')

    # 显示交易记录
    display_columns = ['Date', 'TransactionType', 'CategoryName', 'SubcategoryName',
                       'Amount', 'AccountName', 'Merchant', 'Remarks', 'IsRefund']


    # 设置样式 # todo: 这个对data_editor没用
    def highlight_transaction_type(val):
        if val == '收入':
            return 'background-color: #90EE90'
        elif val == '支出':
            return 'background-color: #FFB6C6'
        return ''


    styled_df = filtered_df.style.apply(lambda x: [''] * len(x) if x.name != '类型'
    else [highlight_transaction_type(val) for val in x])

    edited_transactions_df = st.data_editor(styled_df, column_config={
        'Date': st.column_config.DateColumn('日期'),
        'TransactionType': st.column_config.SelectboxColumn('类型', options=['收入', '支出'], required=True),
        'CategoryName': st.column_config.SelectboxColumn('类别', options=categories, required=True),
        'SubcategoryName': st.column_config.SelectboxColumn('子类别', options=subcategories, required=True),
        'Amount': st.column_config.NumberColumn('金额', format="￥ %.2f",),
        'AccountName': st.column_config.SelectboxColumn('账户', options=accounts, required=True, disabled=True),
        'Merchant': st.column_config.TextColumn('商户'),
        'Remarks': st.column_config.TextColumn('备注'),
        'IsRefund': st.column_config.SelectboxColumn('已报销', options=['是', '否'], required=True)
    }, column_order=display_columns, hide_index=True, use_container_width=True)
    # todo: 子类别还不能和类别联动

    if st.button('保存'):
        updated_transactions_df = transactions_df.set_index('TransactionID')
        edited_transactions_df = edited_transactions_df.set_index('TransactionID')
        updated_transactions_df.loc[
            edited_transactions_df.index, edited_transactions_df.columns] = edited_transactions_df
        updated_transactions_df.reset_index(inplace=True)
        save_data(updated_transactions_df, 'Transactions.csv')
        st.success('交易记录已更新')
        # st.return()

else:
    st.info('没有找到符合条件的交易记录')
