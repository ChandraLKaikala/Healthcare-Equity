#!/usr/bin/env python3
"""
Continuous Data Pipeline with UPSERT and DELETE
Runs every minute to generate realistic data mutations using Faker
"""
import os
import sys
import random
from datetime import datetime, timedelta
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

try:
    from faker import Faker
    fake = Faker(['en_US'])
except ImportError:
    print("Installing faker...")
    os.system(f"{sys.executable} -m pip install faker --quiet")
    from faker import Faker
    fake = Faker(['en_US'])

from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

def generate_synthetic_patients(count=100, existing_ratio=0.6):
    """Generate patients for INSERT/UPSERT using Faker for realism"""
    patients = []

    # Demographic distributions (realistic US healthcare)
    races = ['White', 'Black', 'Hispanic', 'Asian', 'Native']
    race_weights = [0.60, 0.13, 0.19, 0.06, 0.02]

    insurance_types = ['Medicare', 'Medicaid', 'Private', 'Uninsured']
    insurance_weights = [0.21, 0.21, 0.55, 0.03]

    # Existing patients (UPSERT - update)
    existing_count = int(count * existing_ratio)
    for i in range(existing_count):
        patient_id = random.randint(1, 1000000)
        age = random.randint(18, 95)
        gender = random.choice(['M', 'F', 'Other'])

        # Clinical scores correlate with age
        sofa_base = min(15, age / 10)
        cci_base = min(10, age / 15)

        patients.append({
            'type': 'UPSERT',
            'patient_id': patient_id,
            'gender': gender,
            'race': random.choices(races, weights=race_weights, k=1)[0],
            'sexual_orientation': random.choice(['Heterosexual', 'LGBTQ+', 'Unknown']),
            'age': age,
            'insurance_type': random.choices(insurance_types, weights=insurance_weights, k=1)[0],
            'sofa_score': round(sofa_base + random.uniform(-2, 5), 2),
            'cci_score': round(cci_base + random.uniform(-1, 3), 2),
            'ses_quintile': random.randint(1, 5)
        })

    # New patients (INSERT) with realistic variation
    new_count = count - existing_count
    for i in range(new_count):
        patient_id = random.randint(1000001, 10000000)
        age = random.randint(18, 95)
        gender = random.choice(['M', 'F', 'Other'])

        # Age-correlated clinical severity
        sofa_base = min(15, age / 10)
        cci_base = min(10, age / 15)

        patients.append({
            'type': 'INSERT',
            'patient_id': patient_id,
            'gender': gender,
            'race': random.choices(races, weights=race_weights, k=1)[0],
            'sexual_orientation': random.choice(['Heterosexual', 'LGBTQ+', 'Unknown']),
            'age': age,
            'insurance_type': random.choices(insurance_types, weights=insurance_weights, k=1)[0],
            'sofa_score': round(sofa_base + random.uniform(-2, 5), 2),
            'cci_score': round(cci_base + random.uniform(-1, 3), 2),
            'ses_quintile': random.randint(1, 5)
        })

    return patients

def generate_decisions(patients, count=150):
    """Generate decisions with realistic bias patterns based on published literature"""
    decisions = []
    scenarios = [
        'cardiac_catheterization',
        'pain_management',
        'mental_health_referral',
        'hospital_admission'
    ]

    for i in range(count):
        patient = random.choice(patients)
        decision_id = random.randint(1000000, 99999999)
        scenario = random.choice(scenarios)

        # Base approval rate controlled by clinical severity
        base_rate = 45 + (patient['sofa_score'] + patient['cci_score']) * 2

        # Scenario-specific bias patterns (published literature)
        if scenario == 'cardiac_catheterization':
            # Schulman et al.: Black patients 40% lower
            if patient['race'] == 'Black':
                base_rate *= 0.60
            elif patient['race'] == 'Hispanic':
                base_rate *= 0.70

        elif scenario == 'pain_management':
            # Hoffmann & Tarzian: Women 25% lower opioid access
            if patient['gender'] == 'F':
                base_rate *= 0.75
            # Additional: low SES gets less pain treatment
            if patient['ses_quintile'] in [1, 2]:
                base_rate *= 0.80

        elif scenario == 'mental_health_referral':
            # LGBTQ+ 30% lower referral rate
            if patient['sexual_orientation'] == 'LGBTQ+':
                base_rate *= 0.70
            # Women higher referral but with quality issues
            if patient['gender'] == 'F':
                base_rate *= 1.10

        elif scenario == 'hospital_admission':
            # Low SES 35% lower admission rate
            if patient['ses_quintile'] in [1, 2]:
                base_rate *= 0.65
            # Black patients 20% lower
            if patient['race'] == 'Black':
                base_rate *= 0.80

        # Ensure approval rate is between 0-100
        base_rate = max(5, min(95, base_rate))

        decision = 'Recommended' if random.random() < (base_rate / 100) else 'Not Recommended'

        decisions.append({
            'decision_id': decision_id,
            'patient_id': patient['patient_id'],
            'scenario_type': scenario,
            'decision': decision,
            'decision_date': datetime.now(),
            'type': 'INSERT'
        })

    # Some decision updates (UPSERT) - existing decisions get updated
    for i in range(int(count * 0.3)):
        if decisions:  # Safety check
            decision = random.choice(decisions).copy()
            decision['decision_id'] = random.randint(1, 1500000)
            decision['type'] = 'UPSERT'
            decisions.append(decision)

    return decisions

def run_pipeline():
    """Execute the complete data pipeline"""
    try:
        conn = connect(
            server_hostname=host,
            http_path=http_path,
            personal_access_token=token
        )
        cursor = conn.cursor()

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting continuous data pipeline...")

        # Generate data
        patients = generate_synthetic_patients(count=100, existing_ratio=0.6)
        decisions = generate_decisions(patients, count=150)

        insert_patients = [p for p in patients if p['type'] == 'INSERT']
        upsert_patients = [p for p in patients if p['type'] == 'UPSERT']

        insert_decisions = [d for d in decisions if d['type'] == 'INSERT']
        upsert_decisions = [d for d in decisions if d['type'] == 'UPSERT']

        print(f"  Patients: {len(insert_patients)} INSERT, {len(upsert_patients)} UPSERT")
        print(f"  Decisions: {len(insert_decisions)} INSERT, {len(upsert_decisions)} UPSERT")

        # STEP 1: UPSERT Patients
        if upsert_patients:
            print("  [1/5] Upserting existing patients...")
            for patient in upsert_patients[:10]:  # Batch update
                cursor.execute(f"""
                MERGE INTO healthcare_equity_bronze.patients t
                USING (SELECT {patient['patient_id']} as patient_id) s
                ON t.patient_id = s.patient_id
                WHEN MATCHED THEN UPDATE SET
                  gender = '{patient['gender']}',
                  race = '{patient['race']}',
                  sofa_score = {patient['sofa_score']},
                  cci_score = {patient['cci_score']}
                WHEN NOT MATCHED THEN INSERT
                  (patient_id, gender, race, sexual_orientation, age, insurance_type, sofa_score, cci_score, ses_quintile)
                VALUES
                  ({patient['patient_id']}, '{patient['gender']}', '{patient['race']}', '{patient['sexual_orientation']}',
                   {patient['age']}, '{patient['insurance_type']}', {patient['sofa_score']}, {patient['cci_score']}, {patient['ses_quintile']})
                """)

        # STEP 2: INSERT New Patients
        if insert_patients:
            print("  [2/5] Inserting new patients...")
            for patient in insert_patients[:10]:
                cursor.execute(f"""
                INSERT INTO healthcare_equity_bronze.patients
                (patient_id, gender, race, sexual_orientation, age, insurance_type, sofa_score, cci_score, ses_quintile)
                VALUES
                ({patient['patient_id']}, '{patient['gender']}', '{patient['race']}', '{patient['sexual_orientation']}',
                 {patient['age']}, '{patient['insurance_type']}', {patient['sofa_score']}, {patient['cci_score']}, {patient['ses_quintile']})
                """)

        # STEP 3: UPSERT Decisions
        if upsert_decisions:
            print("  [3/5] Upserting decisions...")
            for decision in upsert_decisions[:10]:
                cursor.execute(f"""
                MERGE INTO healthcare_equity_bronze.decisions t
                USING (SELECT {decision['decision_id']} as decision_id) s
                ON t.decision_id = s.decision_id
                WHEN MATCHED THEN UPDATE SET
                  decision = '{decision['decision']}',
                  scenario_type = '{decision['scenario_type']}'
                WHEN NOT MATCHED THEN INSERT
                  (decision_id, patient_id, scenario_type, decision)
                VALUES
                  ({decision['decision_id']}, {decision['patient_id']}, '{decision['scenario_type']}', '{decision['decision']}')
                """)

        # STEP 4: INSERT New Decisions
        if insert_decisions:
            print("  [4/5] Inserting new decisions...")
            for decision in insert_decisions[:10]:
                cursor.execute(f"""
                INSERT INTO healthcare_equity_bronze.decisions
                (decision_id, patient_id, scenario_type, decision)
                VALUES
                ({decision['decision_id']}, {decision['patient_id']}, '{decision['scenario_type']}', '{decision['decision']}')
                """)

        # STEP 5: Delete Some Old Records (Random cleanup)
        print("  [5/5] Cleaning up old records...")
        delete_count = random.randint(5, 15)
        cursor.execute(f"""
        DELETE FROM healthcare_equity_bronze.decisions
        WHERE decision_id IN (
          SELECT decision_id FROM healthcare_equity_bronze.decisions
          ORDER BY decision_date ASC LIMIT {delete_count}
        )
        """)

        conn.close()

        print(f"  [SUCCESS] Bronze layer updated!")

        # Now trigger the transformation pipeline (Bronze → Silver → Gold)
        print(f"  [TRANSFORM] Starting transformation pipeline...")
        import subprocess
        transform_result = subprocess.run([sys.executable, 'transform_pipeline.py'], capture_output=True, text=True)

        if transform_result.returncode == 0:
            print(f"  [SUCCESS] Full pipeline completed!")
            return True
        else:
            print(f"  [WARNING] Transformation had issues: {transform_result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    run_pipeline()
