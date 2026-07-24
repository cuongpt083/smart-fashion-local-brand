import pandas as pd
from itertools import combinations

def generate_association_rules(df_invoice_lines, df_products=None, min_support=0.01, min_confidence=0.1):
    """
    Thực thi thuật toán Apriori đơn giản và khai phá luật kết hợp (Association Rules)
    từ dữ liệu chi tiết hóa đơn (Market Basket Analysis cho Combo / Outfit).
    """
    if df_invoice_lines is None or df_invoice_lines.empty:
        return pd.DataFrame()
        
    df_lines = df_invoice_lines.copy()
    if df_products is not None and not df_products.empty:
        df_lines = df_lines.merge(df_products[['product_code', 'product_name', 'category_path', 'brand']], on='product_code', how='left')
        df_lines['item_label'] = df_lines['brand'].fillna('') + " " + df_lines['product_name'].fillna(df_lines['product_code'])
    else:
        df_lines['item_label'] = df_lines['product_code']
        
    # Group items by invoice_code
    basket = df_lines.groupby('invoice_code')['item_label'].unique()
    total_transactions = len(basket)
    
    if total_transactions == 0:
        return pd.DataFrame()
        
    # 1. Item frequencies
    item_counts = {}
    pair_counts = {}
    
    for items in basket:
        for item in items:
            item_counts[item] = item_counts.get(item, 0) + 1
            
        # Unique pairs in transaction
        for p1, p2 in combinations(sorted(items), 2):
            pair_counts[(p1, p2)] = pair_counts.get((p1, p2), 0) + 1
            
    rules = []
    for (item1, item2), count in pair_counts.items():
        support = count / total_transactions
        if support >= min_support:
            conf_1_to_2 = count / item_counts[item1]
            conf_2_to_1 = count / item_counts[item2]
            
            lift_1_to_2 = conf_1_to_2 / (item_counts[item2] / total_transactions)
            lift_2_to_1 = conf_2_to_1 / (item_counts[item1] / total_transactions)
            
            if conf_1_to_2 >= min_confidence:
                rules.append({
                    'antecedent': item1,
                    'consequent': item2,
                    'support': round(support, 4),
                    'confidence': round(conf_1_to_2, 4),
                    'lift': round(lift_1_to_2, 2),
                    'pair_count': count
                })
            if conf_2_to_1 >= min_confidence:
                rules.append({
                    'antecedent': item2,
                    'consequent': item1,
                    'support': round(support, 4),
                    'confidence': round(conf_2_to_1, 4),
                    'lift': round(lift_2_to_1, 2),
                    'pair_count': count
                })
                
    df_rules = pd.DataFrame(rules)
    if not df_rules.empty:
        df_rules = df_rules.sort_values(by=['lift', 'confidence'], ascending=[False, False])
    return df_rules

def get_top_combos(df_rules, top_n=10):
    if df_rules.empty:
        return pd.DataFrame()
    return df_rules.head(top_n)
