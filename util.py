import pandas as pd

# 读取数据文件
def load_data():
    transactions_df = pd.read_csv('Data/Transactions.csv', dtype={'RelatedTransactionID': 'Int64', 'Remarks': str}, parse_dates=['Date'])
    categories_df = pd.read_csv('Data/Categories.csv')
    subcategories_df = pd.read_csv('Data/Subcategories.csv')
    account_df = pd.read_csv('Data/Account.csv', dtype={'AccountSuffix': str})
    return transactions_df, categories_df, subcategories_df, account_df

# 保存数据
def save_data(df, file_name):
    df.to_csv(f'Data/{file_name}', index=False)