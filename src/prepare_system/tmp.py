import requests

syst = "http://192.168.97.2:8001/"

# Record come dizionario Python
record = {
                    "session_id":32,
                    "source":'expert',
                    "value":  "moderate"
        }
"""
record = {
    "UUID": "a923-45b7-gh12-8902",
    "label": "moderate",
    "mean_abs_diff_ts": 1.0,
    "mean_abs_diff_am": 1.0,
    "median_long": -144.7689488495527,
    "median_lat": -90.0,
    "median_targetIP": "192.168.123.48",
    "median_destIP": "192.168.197.213"
}
"""
# Passa il dizionario al parametro json
risp = requests.post(syst, json=record)
print(risp)
