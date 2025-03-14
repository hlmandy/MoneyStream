import pandas as pd

transaction_dir = 'Data/Transactions.csv'
categories_dir = 'Data/Categories.csv'
subcategories_dir = 'Data/Subcategories.csv'
account_dir = 'Data/Account.csv'

# 读取数据文件
def load_data():
    return load_transactions_data(), load_categories_data(), load_subcategories_data(), load_account_data()

def load_transactions_data():
    transactions_df = pd.read_csv(transaction_dir, dtype={'RelatedTransactionID': 'Int64', 'Remarks': str}, parse_dates=['Date'])
    return transactions_df

def load_categories_data():
    categories_df = pd.read_csv(categories_dir)
    return categories_df

def load_subcategories_data():
    subcategories_df = pd.read_csv(subcategories_dir)
    return subcategories_df

def load_account_data():
    account_df = pd.read_csv(account_dir, dtype={'AccountSuffix': str})
    return account_df


# 保存数据
def save_data(df, file_name):
    df.to_csv(f'Data/{file_name}', index=False)