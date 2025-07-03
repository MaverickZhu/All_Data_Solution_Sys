import requests
import os
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_USERNAME = "test_profiler"
TEST_PASSWORD = "testpassword"

def get_auth_token(session):
    """Authenticate and get a token."""
    # Create user first, ignore error if exists
    session.post(f"{BASE_URL}/auth/register", json={
        "username": TEST_USERNAME,
        "email": f"{TEST_USERNAME}@example.com",
        "password": TEST_PASSWORD
    })
    
    response = session.post(f"{BASE_URL}/auth/token", data={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    response.raise_for_status()
    return response.json()["access_token"]

def create_test_project(session, token):
    """Create a test project."""
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {"name": "Profiling Test Project", "description": "A project for testing data profiling."}
    response = session.post(f"{BASE_URL}/projects/", headers=headers, json=project_data)
    response.raise_for_status()
    return response.json()["id"]

def upload_test_file(session, token, project_id):
    """Upload a test CSV file."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a dummy CSV file for testing
    csv_content = "col1,col2,col3\n1,a,x\n2,b,y\n3,c,z\n4,d,x\n5,,z"
    file_path = "test_profile_upload.csv"
    with open(file_path, "w") as f:
        f.write(csv_content)

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "text/csv")}
        response = session.post(
            f"{BASE_URL}/projects/{project_id}/datasources/upload",
            headers=headers,
            files=files
        )
    
    os.remove(file_path) # Clean up the dummy file
    response.raise_for_status()
    return response.json()["id"]

def run_profiling(session, token, data_source_id):
    """Run the profiling task and get the report."""
    headers = {"Authorization": f"Bearer {token}"}
    response = session.post(
        f"{BASE_URL}/processing/profile/{data_source_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    with requests.Session() as s:
        print("🚀 Starting data profiling API test...")

        print("1. Authenticating and getting token...")
        auth_token = get_auth_token(s)
        print("   ✅ Token received.")

        print("2. Creating a test project...")
        project_id = create_test_project(s, auth_token)
        print(f"   ✅ Project created with ID: {project_id}")

        print("3. Uploading a test CSV file...")
        data_source_id = upload_test_file(s, auth_token, project_id)
        print(f"   ✅ File uploaded. Data Source ID: {data_source_id}")

        print(f"4. Running profiling on data source {data_source_id}...")
        report = run_profiling(s, auth_token, data_source_id)
        print("   ✅ Profiling complete!")

        print("\n--- PROFILING REPORT ---")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("------------------------\n")

        print("🎉 Test completed successfully!") 