import streamlit as st
import pandas as pd
import os
from util import *
from datetime import datetime, timedelta

merchants = ['淘宝', '京东']
baoxiao_category_list = ['交通','食品','出差','旅游']

st.title('报销退款管理')

# 加载数据
transactions_df, categories_df, subcategories_df, account_df = load_data()

# 创建两个标签页
tab1, tab2 = st.tabs(['退款管理', '报销/AA管理'])

# 退款管理标签页
with tab1:
    st.header('退款管理')
    
    # 添加日期范围选择
    default_end_date = datetime.now()
    default_start_date = default_end_date - timedelta(days=30)
    col1, col2, col3 = st.columns(3)
    with col1:
        
        start_date = st.date_input('开始日期', value=default_start_date)
    with col2:
        end_date = st.date_input('结束日期', value=default_end_date)
    with col3:
        # 筛选有可退款交易的商户
        refundable_merchants = transactions_df[
            (transactions_df['TransactionType'] == '支出') & 
            (transactions_df['IsRefund'] == '否') &
            (transactions_df['CategoryName'] != '转账') &
            (pd.to_datetime(transactions_df['Date']).dt.date >= start_date) &
            (pd.to_datetime(transactions_df['Date']).dt.date <= end_date)
        ]['Merchant'].unique().tolist()
        
        # 添加商户选择下拉框
        selected_merchant = st.selectbox(
            '选择商户',
            refundable_merchants,
            format_func=lambda x: x if pd.notna(x) else '未知商户'
        )
    
    # 根据选择的商户筛选交易
    refund_transactions = transactions_df[
        (transactions_df['Merchant'] == selected_merchant) & 
        (transactions_df['TransactionType'] == '支出') & 
        (transactions_df['IsRefund'] == '否') &
        (transactions_df['CategoryName'] != '转账') &
        (pd.to_datetime(transactions_df['Date']).dt.date >= start_date) &
        (pd.to_datetime(transactions_df['Date']).dt.date <= end_date)
    ]
    
    if not refund_transactions.empty:
        st.dataframe(refund_transactions[['Date', 'Merchant', 'Amount', 'Item', 'AccountName']])
        
        # 选择要退款的交易
        selected_transaction = st.selectbox(
            '选择要退款的交易',
            refund_transactions['TransactionID'].tolist(),
            format_func=lambda x: f"ID:{x} - {refund_transactions[refund_transactions['TransactionID']==x]['Merchant'].iloc[0]} - \
                                ¥{refund_transactions[refund_transactions['TransactionID']==x]['Amount'].iloc[0]}"
        )
        
        if st.button('确认退款'):
            # 更新交易记录
            selected_row = refund_transactions[refund_transactions['TransactionID'] == selected_transaction].iloc[0]
            
            # 创建新的退款记录
            new_transaction_id = transactions_df['TransactionID'].max() + 1
            new_transaction = pd.DataFrame({
                'TransactionID': [new_transaction_id],
                'Date': [pd.Timestamp.now().strftime('%Y-%m-%d')],
                'TransactionType': ['收入'],
                'CategoryName': ['收入'],
                'SubcategoryName': ['退款'],
                'Amount': [selected_row['Amount']],
                'AccountName': [selected_row['AccountName']],
                'Remarks': ['退款'],
                'Merchant': [selected_row['Merchant']],
                'Item': [f'退款-{selected_row["Item"]}'],
                'UpdatedDate': [pd.Timestamp.now().strftime('%Y-%m-%d')],
                'IsRefund': ['是'],
                'RelatedTransactionID': [int(selected_transaction)]
            })
            
            # 更新原交易的退款状态
            transactions_df.loc[transactions_df['TransactionID'] == selected_transaction, 'IsRefund'] = '是'
            transactions_df.loc[transactions_df['TransactionID'] == selected_transaction, 'RelatedTransactionID'] = new_transaction_id
            
            # 合并新记录
            transactions_df = pd.concat([transactions_df, new_transaction], ignore_index=True)
            
            # 更新账户余额
            account_name = selected_row['AccountName']
            refund_amount = selected_row['Amount']
            account_df.loc[account_df['AccountName'] == account_name, 'Balance'] += refund_amount
            account_df.loc[account_df['AccountName'] == account_name, 'LastModifiedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存更新后的数据
            save_data(transactions_df, 'Transactions.csv')
            save_data(account_df, 'Account.csv')
            
            st.success('退款处理成功！')
            # st.rerun()
    else:
        st.info('没有找到可退款的交易记录')

# 报销管理标签页
with tab2:
    st.header('报销/AA管理')
    # 筛选出差相关交易
    business_transactions = transactions_df[
        (transactions_df['CategoryName'].isin(baoxiao_category_list)) & 
        (transactions_df['TransactionType'] == '支出') & 
        (transactions_df['IsRefund'] == '否')
    ]
    
    if not business_transactions.empty:
        st.dataframe(business_transactions[['Date', 'CategoryName', 'SubcategoryName', 'Amount', 'Merchant', 'Item', 'AccountName']])
        
        # 选择要报销的交易
        selected_transactions = st.multiselect(
            '选择要报销的交易',
            business_transactions['TransactionID'].tolist(),
            format_func=lambda x: f"ID:{x} - {business_transactions[business_transactions['TransactionID']==x]['Merchant'].iloc[0]} - \
                                ¥{business_transactions[business_transactions['TransactionID']==x]['Amount'].iloc[0]}"
        )
        
        # 添加账户选择
        col1,col2,col3 = st.columns(3)
        with col1:
            reimbursement_account = st.selectbox(
                '选择报销入账账户',
                account_df['AccountName'].tolist()
            )
        with col2:
            # 添加报销金额输入
            if selected_transactions:
                reimbursement_amounts = {}
                for transaction_id in selected_transactions:
                    selected_row = business_transactions[business_transactions['TransactionID'] == transaction_id].iloc[0]
                    reimbursement_amounts[transaction_id] = st.number_input(
                        f'输入报销金额 (原金额: ¥{selected_row["Amount"]})',
                        min_value=0.0,
                        value=float(selected_row['Amount']),
                        step=0.01,
                        format='%.2f',
                        key=f'amount_{transaction_id}'
                    )
        with col3:
            # 添加报销商户输入
            if selected_transactions:
                reimbursement_merchants = {}
                for transaction_id in selected_transactions:
                    selected_row = business_transactions[business_transactions['TransactionID'] == transaction_id].iloc[0]
                    reimbursement_merchants[transaction_id] = st.text_input(
                        f'输入报销商户 (原商户: {selected_row["Merchant"]})',
                        value=selected_row['Merchant']
                    )
        
        if st.button('确认报销'):
            if selected_transactions:
                for transaction_id in selected_transactions:
                    selected_row = business_transactions[business_transactions['TransactionID'] == transaction_id].iloc[0]
                    
                    # 使用用户输入的报销金额
                    reimbursement_amount = reimbursement_amounts[transaction_id]
                    # 使用用户输入的报销商户
                    reimbursement_merchant = reimbursement_merchants[transaction_id]
                    
                    # 创建新的报销记录
                    new_transaction_id = transactions_df['TransactionID'].max() + 1
                    new_transaction = pd.DataFrame({
                        'TransactionID': [new_transaction_id],
                        'Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
                        'TransactionType': ['收入'],
                        'CategoryName': ['收入'],
                        'SubcategoryName': ['报销'],
                        'Amount': [reimbursement_amount],
                        'AccountName': [reimbursement_account],
                        'Remarks': [''],
                        'Merchant': [reimbursement_merchant],
                        'Item': [f"{selected_row['Merchant']}_{selected_row['Item']}报销"],
                        'UpdatedDate': [pd.Timestamp.now().strftime('%Y-%m-%d')],
                        'IsRefund': ['否'],
                        'RelatedTransactionID': [int(transaction_id)]
                    })
                    
                    # 更新原交易的报销状态
                    transactions_df.loc[transactions_df['TransactionID'] == transaction_id, 'IsRefund'] = '是'
                    transactions_df.loc[transactions_df['TransactionID'] == transaction_id, 'RelatedTransactionID'] = new_transaction_id
                    
                    # 合并新记录
                    transactions_df = pd.concat([new_transaction, transactions_df], ignore_index=True)
                    
                    # 更新账户余额
                    account_df.loc[account_df['AccountName'] == reimbursement_account, 'Balance'] += reimbursement_amount
                    account_df.loc[account_df['AccountName'] == reimbursement_account, 'LastModifiedTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 保存更新后的数据
                save_data(transactions_df, 'Transactions.csv')
                save_data(account_df, 'Account.csv')
                
                st.success('报销处理成功！')
                # st.rerun()
            else:
                st.warning('请选择要报销的交易')
    else:
        st.info('没有找到可报销的交易记录')
