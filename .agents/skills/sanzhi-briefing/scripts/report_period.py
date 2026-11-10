"""Print the last complete reporting period in Hong Kong time."""
import argparse
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['weekly', 'quarterly'])
parser.add_argument('--as-of', type=date.fromisoformat)
args = parser.parse_args()
as_of = args.as_of or datetime.now(ZoneInfo('Asia/Hong_Kong')).date()
if args.mode == 'weekly':
    end = as_of - timedelta(days=as_of.weekday() + 1)
    start = end - timedelta(days=6)
    issue_id = end.isoformat()
    label = f'{start:%Y.%m.%d}–{end:%m.%d}'
    kind = '周报'
else:
    current_start = date(as_of.year, ((as_of.month-1)//3)*3+1, 1)
    end = current_start - timedelta(days=1)
    start = date(end.year, ((end.month-1)//3)*3+1, 1)
    quarter = (end.month-1)//3+1
    issue_id = f'{end.year}-q{quarter}'
    label = f'{end.year} Q{quarter}'
    kind = '季度简报'
print(json.dumps({'start': start.isoformat(), 'end': end.isoformat(), 'catalogEntry': {
    'id': issue_id, 'label': label, 'title': '监管与案例简报',
    'type': kind, 'periodEnd': end.isoformat()}}, ensure_ascii=False, indent=2))
