import json
import time
import requests

sample = json.load(open('frontend/sample_data.json'))
print('importing')
r = requests.post('http://127.0.0.1:8000/api/import-data', json=sample)
print(r.status_code, r.json())

segment = {'name': 'Coffee lapsed', 'criteria': {'category': 'Coffee', 'max_last_order_days': 90}}
r = requests.post('http://127.0.0.1:8000/api/segments', json=segment)
print(r.status_code, r.json())
segment_id = r.json()['id']

campaign = {
    'name': 'Re-engage coffee fans',
    'segment_id': segment_id,
    'channel': 'SMS',
    'subject': None,
    'body': 'Hey {name}, enjoy a fresh coffee offer from Astra Coffee just for you!',
}
r = requests.post('http://127.0.0.1:8000/api/campaigns', json=campaign)
print(r.status_code, r.json())

print('waiting 5 seconds for callbacks...')
time.sleep(5)
print('campaign summary:', requests.get('http://127.0.0.1:8000/api/campaigns').json())
print('communications:', requests.get('http://127.0.0.1:8000/api/communications').json())
