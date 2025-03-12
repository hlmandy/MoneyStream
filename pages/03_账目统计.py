import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from util import *

st.header('收支统计')

# 读取数据
transactions_df, _, subcategories_df, _ = load_data()
# 选择交易类型
transaction_type = st.sidebar.radio("交易类型", ['支出', '收入'])

selected_transaction_df = transactions_df[(transactions_df['TransactionType'] == transaction_type) &
                             (transactions_df['IsRefund'] == '否') & (transactions_df['Amount'] > 0)
                             & (transactions_df['SubcategoryName']!='退款')].copy()
selected_transaction_df['Month'] = selected_transaction_df['Date'].dt.strftime('%Y/%m')
categories = sorted(selected_transaction_df['CategoryName'].unique().tolist())

# 创建统一的颜色序列
# colors = ['#B5EAD7', '#C7CEEA', '#FFDAC1', '#E2F0CB', '#FFB7B2', '#D4A5A5', '#99C3CC', '#F8E9A2', '#CBE4F9', '#DAB3FF', '#A8D8B9', '#FFEEE4', '#B0E0E6', '#FDD2B5', '#C4E1D3', '#F4BBD3', '#CCE2EB', '#FFF5BA', '#D3E0EA', '#E9C7C6', '#B4EBB7', '#FED8B1', '#CBDEF8', '#E6D3E7']
# color_map = {cat:color for cat, color in zip(categories, colors[:len(categories)])}
grouped_transaction_df = selected_transaction_df.groupby(by=['Month', 'CategoryName'])['Amount'].sum().reset_index()
bar = px.bar(grouped_transaction_df.sort_values(['Month', 'CategoryName']), x='Month', y='Amount', color='CategoryName',
             category_orders={'CategoryName': categories}, color_discrete_sequence=px.colors.qualitative.Pastel_r)
st.plotly_chart(bar)

# 选择月份
# 从交易数据中提取所有月份并按时间顺序排序
all_months = sorted(selected_transaction_df['Month'].unique())
month = st.sidebar.selectbox('选择月份', ['全部']+all_months)
# 选择类别
category = st.sidebar.selectbox('选择类别', categories)

# 根据选择的月份筛选数据，并只保留支出类型且不可报销的交易
if month == '全部':
    selected_data = selected_transaction_df[
    (selected_transaction_df['CategoryName'] == category)
    ].sort_values('Date', ascending=False)
else:
    selected_data = selected_transaction_df[
        (selected_transaction_df['Date'].str.startswith(month))
        & (selected_transaction_df['CategoryName'] == category)
        ].sort_values('Date', ascending=False)

sub_category_sums = selected_data.groupby(['SubcategoryName'])['Amount'].sum().reset_index()

pie=px.pie(sub_category_sums, names='SubcategoryName', values='Amount')
st.plotly_chart(pie)

# 子类别筛选
subcategories = ['全部'] + list(subcategories_df[subcategories_df['ParentCategoryName'] == category]['SubcategoryName'].unique())
selected_subcategory = st.sidebar.selectbox('子类别', subcategories)

if selected_subcategory != '全部':
    selected_data = selected_data[(selected_data['SubcategoryName'] == selected_subcategory)]

drop_columns = ['Month']
edited_transactions_df = st.data_editor(selected_data.drop(columns=drop_columns), column_config={
    'Date': st.column_config.DateColumn('日期'),
    'TransactionType': st.column_config.TextColumn('类型', width='small'),
    'CategoryName': st.column_config.TextColumn('类别', width='small'),
    'SubcategoryName': st.column_config.TextColumn('子类别'),
    'Amount': st.column_config.NumberColumn('金额', format="￥ %.2f"),
    'AccountName': st.column_config.TextColumn('账户'),
    'Merchant': st.column_config.TextColumn('商户', width='medium'),
    'Remarks': st.column_config.TextColumn('备注', width='medium'),
    'Item': st.column_config.TextColumn('商品', width='medium')
}, column_order=['Date', 'TransactionType', 'AccountName', 'Amount', 'CategoryName', 'SubcategoryName', 'Merchant',
                 'Item', 'Remarks'], hide_index=True, use_container_width=True)

if st.button('保存'):
    updated_transactions_df = transactions_df.set_index('TransactionID')
    edited_transactions_df = edited_transactions_df.set_index('TransactionID')
    updated_transactions_df.loc[
        edited_transactions_df.index, edited_transactions_df.columns] = edited_transactions_df
    updated_transactions_df.reset_index(inplace=True)
    save_data(updated_transactions_df, 'Transactions.csv')
    st.success('交易记录已更新')

# # 按类别汇总金额
# category_sums = selected_month_data.groupby(['Month', 'CategoryName'])['Amount'].sum().reset_index()
#
# # 添加类别名称，只保留支出类型的类别
# category_sums = category_sums.merge(
#     categories_df[categories_df['TransactionType'] == '支出'][['CategoryName']],
#     on='CategoryName'
# )
# pie=px.pie(category_sums, names='CategoryName', values='Amount',category_orders={'CategoryName': categories}, color_discrete_sequence=px.colors.qualitative.Pastel_r)
# st.plotly_chart(pie)
