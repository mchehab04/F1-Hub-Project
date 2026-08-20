# TODO: train two independent scikit-learn models (per the chatroom's v1
# decision — NOT a fused two-stage model):
#   1. finish-position model: grid -> finish position
#   2. dnf_model: binary DNF/reliability classifier
# Persist trained artifacts (e.g. joblib) for app/api/v1/races.py and
# app/api/v1/explainability.py to load, versioned to match `model_version`
# in the API contract.
