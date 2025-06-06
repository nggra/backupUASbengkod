# -*- coding: utf-8 -*-
"""backupUAS.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KDn_P_2qpD-BdiYvnO8Mo5aN-Ro-45dQ
"""

#!pip install streamlit
#!pip install joblib
#!pip install numpy
#!pip install pandas
#!pip install matplotlib
#!pip install seaborn
#!pip install sklearn
#!pip install imblearn

import streamlit as st
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
import warnings
warnings.filterwarnings('ignore')

# --- Load dataset dan preprocessing seperti di kode kamu ---

file_path = 'ObesityDataSet.csv'
df = pd.read_csv(file_path)

# Konversi kolom numerik ke float
numeric_columns = ['Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df_clean = df.drop_duplicates()

# Imputasi kategori dengan modus
cat_columns = ['Gender', 'family_history_with_overweight', 'FAVC', 'CAEC', 'SMOKE', 'SCC', 'CALC', 'MTRANS']
cat_imputer = SimpleImputer(strategy='most_frequent')
df_clean[cat_columns] = cat_imputer.fit_transform(df_clean[cat_columns])

# Hapus outlier berdasarkan IQR
for col in numeric_columns:
    Q1 = df_clean[col].quantile(0.25)
    Q3 = df_clean[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]

# Encoding kategori
encoder = LabelEncoder()
for col in cat_columns:
    df_clean[col] = encoder.fit_transform(df_clean[col])

# Encode target
df_clean['NObeyesdad'] = encoder.fit_transform(df_clean['NObeyesdad'])

# Standarisasi fitur numerik
scaler = StandardScaler()
df_clean[numeric_columns] = scaler.fit_transform(df_clean[numeric_columns])

# Save scaler
joblib.dump(scaler, "scaler.pkl")

# Fitur dan target
X = df_clean.drop('NObeyesdad', axis=1)
y = df_clean['NObeyesdad']

# SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X, y)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)

# Grid Search Random Forest
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2],
    'bootstrap': [True, False]
}
rf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(rf, param_grid, cv=3, n_jobs=-1, verbose=1, scoring='accuracy')
grid_search.fit(X_train, y_train)
best_rf = grid_search.best_estimator_
print("Best Parameters:", grid_search.best_params_)

# Simpan model terbaik
joblib.dump(best_rf, "random_forest_model.pkl")

# --- Streamlit UI ---

st.title("Prediksi Tingkat Obesitas")
st.write("Isi data berikut untuk memprediksi status berat badan Anda:")

# Load model dan scaler yang sudah disimpan
model = joblib.load("random_forest_model.pkl")
scaler = joblib.load("scaler.pkl")

# Input pengguna untuk semua fitur yang dipakai model (numerik + kategorikal)
age = st.slider("Usia", 10, 100)
height = st.slider("Tinggi Badan (meter)", 1.0, 2.5, step=0.01)
weight = st.slider("Berat Badan (kg)", 20.0, 200.0, step=0.5)
fcvc = st.slider("Konsumsi Sayur (1 - jarang, 3 - sering)", 1, 3)
ncp = st.slider("Jumlah makan besar per hari", 1, 4)
ch2o = st.slider("Konsumsi air harian (1 - sedikit, 3 - banyak)", 1, 3)
faf = st.slider("Frekuensi aktivitas fisik (0 - tidak pernah, 3 - rutin)", 0, 3)
tue = st.slider("Waktu screen time (jam/hari)", 0, 3)

# Input fitur kategori (harus sama seperti di training)
gender = st.selectbox("Gender", ["Female", "Male"])
family_history_with_overweight = st.selectbox("Riwayat Keluarga Kegemukan", ["No", "Yes"])
favc = st.selectbox("Frekuensi Konsumsi Makanan Tinggi Kalori (FAVC)", ["No", "Yes"])
caec = st.selectbox("Konsumsi Makanan Cepat Saji (CAEC)", ["No", "Sometimes", "Frequently", "Always"])
smoke = st.selectbox("Merokok", ["No", "Yes"])
scc = st.selectbox("Apakah Mengkonsumsi Alkohol (SCC)", ["No", "Yes"])
calc = st.selectbox("Konsumsi Suplemen Kalsium (CALC)", ["No", "Sometimes", "Frequently", "Always"])
mtrans = st.selectbox("Jenis Transportasi (MTRANS)", ["Automobile", "Motorbike", "Public_Transportation", "Walking"])

# Ubah kategori ke label encoding sesuai training
def encode_input(value, col_name):
    mapping = dict(zip(df_clean[col_name].unique(), df_clean[col_name].values))
    # karena kita sudah pakai LabelEncoder pada kolom tersebut,
    # lebih aman buat ulang encoder di sini
    le = LabelEncoder()
    le.fit(df_clean[col_name])
    return le.transform([value])[0]

gender_enc = encoder.fit_transform(["Female", "Male"]).tolist()
gender_val = 1 if gender == "Male" else 0

family_history_with_overweight_enc = encoder.fit_transform(["No", "Yes"]).tolist()
family_history_val = 1 if family_history_with_overweight == "Yes" else 0

favc_val = 1 if favc == "Yes" else 0

caec_mapping = {"No":0, "Sometimes":1, "Frequently":2, "Always":3}
caec_val = caec_mapping.get(caec, 0)

smoke_val = 1 if smoke == "Yes" else 0
scc_val = 1 if scc == "Yes" else 0

calc_val = caec_val  # asumsikan sama mapping seperti CAEC, bisa disesuaikan jika beda
calc_mapping = {"No":0, "Sometimes":1, "Frequently":2, "Always":3}
calc_val = calc_mapping.get(calc, 0)

mtrans_mapping = {"Automobile":0, "Motorbike":1, "Public_Transportation":2, "Walking":3}
mtrans_val = mtrans_mapping.get(mtrans, 0)

# Buat array input lengkap (urutan kolom harus sesuai X_train.columns)
input_data = np.array([[age, height, weight, fcvc, ncp, ch2o, faf, tue,
                        gender_val, family_history_val, favc_val, caec_val, smoke_val,
                        scc_val, calc_val, mtrans_val]])

# Standarisasi numerik (hanya kolom numerik di awal)
input_data[:, :8] = scaler.transform(input_data[:, :8])

if st.button("Prediksi"):
    prediction = model.predict(input_data)
    label_map = {
        0: "Insufficient_Weight",
        1: "Normal_Weight",
        2: "Overweight_Level_I",
        3: "Overweight_Level_II",
        4: "Obesity_Type_I",
        5: "Obesity_Type_II",
        6: "Obesity_Type_III"
    }
    label = label_map.get(prediction[0], "Unknown")
    st.success(f"Hasil Prediksi: {label}")
