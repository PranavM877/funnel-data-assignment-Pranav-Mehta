import pandas as pd
import argparse
import os
import json
import matplotlib.pyplot as plt

def load_data(events_path, messages_path, orders_path):
    events = pd.read_csv(events_path, parse_dates=['ts'])
    messages = pd.read_csv(messages_path, parse_dates=['ts'])
    orders = pd.read_csv(orders_path, parse_dates=['created_at', 'canceled_at'], keep_default_na=False)
    orders['canceled_at'] = orders['canceled_at'].replace({'': pd.NaT})
    return events, messages, orders

def compute_funnel(events):
    sessions = events.groupby(['device', 'session_id'])['event_name'].apply(list).reset_index()

    def mark_step(events_list, step_name):
        return 1 if step_name in events_list else 0

    sessions['Loaded'] = sessions['event_name'].apply(lambda l: mark_step(l, 'Loaded'))
    sessions['Interact'] = sessions['event_name'].apply(lambda l: mark_step(l, 'Interact'))
    sessions['Clicks'] = sessions['event_name'].apply(lambda l: mark_step(l, 'Clicks'))
    sessions['Purchase'] = sessions['event_name'].apply(lambda l: mark_step(l, 'Purchase'))

    step_counts = []
    for device in sessions['device'].unique():
        device_df = sessions[sessions['device'] == device]
        loaded_users = len(device_df[device_df['Loaded'] == 1])

        steps = ['Loaded', 'Interact', 'Clicks', 'Purchase']
        prev_users = None
        for step in steps:
            users = len(device_df[device_df[step] == 1])
            conv_from_prev_pct = round(users / prev_users * 100, 2) if prev_users else 100.0
            conv_from_start_pct = round(users / loaded_users * 100, 2) if loaded_users else 0
            step_counts.append({
                'step': step,
                'users': users,
                'conv_from_prev_pct': conv_from_prev_pct,
                'conv_from_start_pct': conv_from_start_pct,
                'device': device
            })
            prev_users = users

    return step_counts

def compute_intents(messages, orders):
    messages['intent'] = messages['detected_intent'].replace('', 'unknown').fillna('unknown')

    intent_counts = messages['intent'].value_counts().reset_index()
    intent_counts.columns = ['intent', 'count']
    intent_counts['pct_of_total'] = round(100 * intent_counts['count'] / intent_counts['count'].sum(), 2)

    purchased_sessions = orders[orders['canceled_at'].isna()]['session_id'].unique()
    top_intents_df = messages[messages['session_id'].isin(purchased_sessions)]
    top2 = top_intents_df.groupby('intent')['session_id'].nunique().reset_index()
    top2 = top2.sort_values('session_id', ascending=False).head(2)
    top2_intents = top2['intent'].tolist()

    return intent_counts.to_dict(orient='records'), top2_intents

def compute_cancellation_sla(orders):
    total_orders = len(orders)
    canceled = orders['canceled_at'].notna().sum()
    violations = orders.loc[(orders['canceled_at'] - orders['created_at']).dt.total_seconds() > 3600].shape[0]
    violation_rate_pct = round(violations / canceled * 100, 2) if canceled > 0 else 0

    return {
        'total_orders': total_orders,
        'canceled': canceled,
        'violations': violations,
        'violation_rate_pct': violation_rate_pct
    }

def plot_funnel(funnel_data, out_dir):
    df = pd.DataFrame(funnel_data)
    print(f"DEBUG: Funnel data rows: {df.shape[0]}, total users: {df['users'].sum()}")

    if df.empty or df['users'].sum() == 0:
        print("Warning: No funnel data to plot.")
        return

    fig, ax = plt.subplots()
    for device in df['device'].unique():
        device_df = df[df['device'] == device]
        ax.plot(device_df['step'], device_df['users'], marker='o', label=device)

    ax.set_title('Funnel Conversion by Step')
    ax.set_xlabel('Step')
    ax.set_ylabel('Users')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'funnel.png'))
    plt.close()
    print("funnel.png saved successfully.")

def plot_intents(intent_data, out_dir):
    df = pd.DataFrame(intent_data).sort_values('count', ascending=False).head(10)
    print(f"DEBUG: Intents data rows: {df.shape[0]}, total count: {df['count'].sum()}")

    if df.empty or df['count'].sum() == 0:
        print("Warning: No intent data to plot.")
        return

    fig, ax = plt.subplots()
    ax.bar(df['intent'], df['count'])
    ax.set_title('Top 10 Intents by Count')
    ax.set_xlabel('Intent')
    ax.set_ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'intents.png'))
    plt.close()
    print("intents.png saved successfully.")

def convert_types(obj):
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(x) for x in obj]
    elif isinstance(obj, (pd.Int64Dtype, pd.Float64Dtype, pd.Series)):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif isinstance(obj, (int, float, str)):
        return obj
    else:
        return int(obj) if hasattr(obj, 'item') else obj

def main(args):
    os.makedirs(args.out, exist_ok=True)

    events, messages, orders = load_data(args.events, args.messages, args.orders)

    funnel = compute_funnel(events)
    intents, top2_intents = compute_intents(messages, orders)
    cancellation_sla = compute_cancellation_sla(orders)

    report = {
        'funnel': funnel,
        'intents': intents,
        'cancellation_sla': cancellation_sla
    }

    with open(os.path.join(args.out, 'report.json'), 'w') as f:
        json.dump(convert_types(report), f, indent=4)

    plot_funnel(funnel, args.out)
    plot_intents(intents, args.out)

    print("Top 2 intents most correlated with Purchase:", top2_intents)
    print("Report and charts saved successfully.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', required=True)
    parser.add_argument('--messages', required=True)
    parser.add_argument('--orders', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    main(args)
